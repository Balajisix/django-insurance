from django.db import transaction
from django.utils import timezone

from apps.documents.models import (
    ClaimDocument,
    DocumentStatus,
)

from .extractors.ocr import TesseractOCRExtractor
from .extractors.pdf import PDFTextExtractor
from .models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractionMethod,
    ProcessingStatus,
    DocumentChunk
)

from .chunkers.text import TextChunker

from .embeddings.huggingface import HuggingFaceEmbeddingProvider

from .llm.huggingface import HuggingFaceLLMProvider
from .prompts.rag import SYSTEM_PROMPT, build_user_prompt
from .prompts.claim_summary import CLAIM_SUMMARY_SCHEMA, build_claim_summary_prompt
from .prompts.inconsistency import (
    INCONSISTENCY_SCHEMA,
    SYSTEM_PROMPT as INCONSISTENCY_SYSTEM_PROMPT,
    build_inconsistency_prompt,
)

from apps.claims.models import (
    Claim,
    ClaimAIAnalysis,
    AIAnalysisStatus,
    ClaimAIInconsistency,
    ClaimDocumentRequirement,
)


class DocumentProcessingService:
    """
    Business logic for document processing.
    """

    @staticmethod
    @transaction.atomic
    def create_processing_job(
        *,
        document_id: int,
        created_by,
    ) -> DocumentProcessingJob:

        document = (
            ClaimDocument.objects
            .select_related("claim")
            .filter(id=document_id)
            .first()
        )

        if document is None:
            raise ValueError(
                "Document not found."
            )

        active_job_exists = (
            DocumentProcessingJob.objects.filter(
                document=document,
                status__in=[
                    ProcessingStatus.PENDING,
                    ProcessingStatus.PROCESSING,
                ],
            ).exists()
        )

        if active_job_exists:
            raise ValueError(
                "Document already has an active "
                "processing job."
            )

        previous_attempts = (
            DocumentProcessingJob.objects.filter(
                document=document,
            ).count()
        )

        return DocumentProcessingJob.objects.create(
            document=document,
            status=ProcessingStatus.PENDING,
            attempt_number=previous_attempts + 1,
            created_by=created_by,
        )

    @staticmethod
    def process_document(
        *,
        job_id: int,
    ) -> DocumentProcessingJob:

        job = (
            DocumentProcessingJob.objects
            .select_related("document")
            .filter(id=job_id)
            .first()
        )

        if job is None:
            raise ValueError(
                "Processing job not found."
            )

        if job.status == ProcessingStatus.COMPLETED:
            return job

        if job.status == ProcessingStatus.PROCESSING:
            raise ValueError(
                "Document processing job "
                "is already running."
            )

        if job.status not in [
            ProcessingStatus.PENDING,
            ProcessingStatus.FAILED,
        ]:
            raise ValueError(
                f"Cannot process job in status: "
                f"{job.status}"
            )

        job.status = ProcessingStatus.PROCESSING
        job.started_at = timezone.now()
        job.completed_at = None
        job.error_message = ""

        job.document.status = DocumentStatus.PROCESSING

        job.document.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        job.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "error_message",
                "updated_at",
            ]
        )

        try:
            (
                extracted_text,
                extraction_method,
                extractor_version,
            ) = DocumentProcessingService._extract_document(
                job.document
            )

            with transaction.atomic():

                DocumentExtraction.objects.update_or_create(
                    document=job.document,
                    defaults={
                        "extracted_text": extracted_text,
                        "extraction_method": (
                            extraction_method
                        ),
                        "extractor_version": (
                            extractor_version
                        ),
                        "character_count": (
                            len(extracted_text)
                        ),
                    },
                )

                job.document.status = (
                    DocumentStatus.PROCESSED
                )

                job.document.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                job.status = (
                    ProcessingStatus.COMPLETED
                )

                job.completed_at = timezone.now()
                job.error_message = ""

                job.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "error_message",
                        "updated_at",
                    ]
                )

            return job

        except Exception as exc:

            job.status = ProcessingStatus.FAILED
            job.completed_at = timezone.now()
            job.error_message = str(exc)

            job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            job.document.status = (
                DocumentStatus.FAILED
            )

            job.document.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            raise

    @staticmethod
    def _extract_document(
        document: ClaimDocument,
    ):
        """
        Choose the extraction strategy based
        on document content type.
        """

        content_type = (
            document.content_type or ""
        ).lower()

        if content_type == "application/pdf":

            extracted_text = (
                PDFTextExtractor
                .extract_from_storage(
                    document.s3_key
                )
            )

            return (
                extracted_text,
                ExtractionMethod.TEXT,
                "pypdf-v1",
            )

        if content_type in [
            "image/jpeg",
            "image/png",
        ]:

            extractor = TesseractOCRExtractor()

            extracted_text = (
                extractor.extract_from_storage(
                    document.s3_key
                )
            )

            return (
                extracted_text,
                ExtractionMethod.OCR,
                "tesseract-v1",
            )

        raise ValueError(
            f"Unsupported document content type: "
            f"{document.content_type}"
        )

class DocumentChunkingService:
    """
    Creates chunks from a document's extracted text.
    """

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_OVERLAP = 200

    @staticmethod
    @transaction.atomic
    def create_chunks(
        *,
        document_id: int,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> list[DocumentChunk]:

        document = (
            ClaimDocument.objects
            .filter(id=document_id)
            .first()
        )

        if document is None:
            raise ValueError(
                "Document not found."
            )

        extraction = (
            DocumentExtraction.objects
            .filter(document=document)
            .first()
        )

        if extraction is None:
            raise ValueError(
                "Document has no extracted text. "
                "Process the document before chunking."
            )

        chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )

        chunk_data = chunker.split(
            extraction.extracted_text
        )

        if not chunk_data:
            raise ValueError(
                "Document extraction contains no text "
                "to chunk."
            )

        DocumentChunk.objects.filter(
            document=document
        ).delete()

        chunks = [
            DocumentChunk(
                document=document,
                chunk_index=item["chunk_index"],
                text=item["text"],
                character_count=len(
                    item["text"]
                ),
                start_character=item[
                    "start_character"
                ],
                end_character=item[
                    "end_character"
                ],
            )
            for item in chunk_data
        ]

        DocumentChunk.objects.bulk_create(
            chunks
        )

        return list(
            DocumentChunk.objects.filter(
                document=document
            ).order_by("chunk_index")
        )

class DocumentEmbeddingService:
    """
    Generates embeddings using Hugging Face and
    stores them in FAISS.
    """

    def __init__(self):
        self.provider = (
            HuggingFaceEmbeddingProvider()
        )

    def embed_document(
        self,
        *,
        document_id: int,
    ) -> list[DocumentChunk]:

        chunks = list(
            DocumentChunk.objects
            .filter(
                document_id=document_id
            )
            .order_by("chunk_index")
        )

        if not chunks:
            raise ValueError(
                "No chunks found for this document."
            )

        texts = [
            chunk.text
            for chunk in chunks
        ]

        vectors = self.provider.embed_many(
            texts
        )

        if len(vectors) != len(chunks):
            raise ValueError(
                "Embedding response count does not "
                "match chunk count."
            )

        from .vectorstores.faiss_store import (
            FAISSVectorStore,
        )

        vector_store = FAISSVectorStore()

        faiss_ids = [
            chunk.id
            for chunk in chunks
        ]

        vector_store.add_vectors(
            vectors=vectors,
            ids=faiss_ids,
        )

        now = timezone.now()

        for chunk in chunks:
            chunk.embedding_model = (
                self.provider.MODEL_NAME
            )
            chunk.embedded_at = now
            chunk.faiss_index_id = chunk.id

        DocumentChunk.objects.bulk_update(
            chunks,
            [
                "embedding_model",
                "embedded_at",
                "faiss_index_id",
                "updated_at",
            ],
        )

        return 

class DocumentRetrievalService:
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20

    def __init__(self):
        self.embedding_provider = (
            HuggingFaceEmbeddingProvider()
        )

        from .vectorstores.faiss_store import (
            FAISSVectorStore,
        )

        self.vector_store = FAISSVectorStore()

    def search(
        self,
        *,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        claim_id: int | None = None,
    ) -> list[dict]:

        query = query.strip()

        if not query:
            raise ValueError(
                "Search query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        top_k = min(
            top_k,
            self.MAX_TOP_K,
        )

        query_vector = (
            self.embedding_provider.embed_text(
                query
            )
        )

        # Retrieve more candidates than we
        # ultimately return because we may need
        # to filter them by claim.
        candidate_k = top_k

        if claim_id is not None:
            candidate_k = min(
                top_k * 5,
                self.vector_store.count(),
            )

        faiss_results = (
            self.vector_store.search(
                query_vector=query_vector,
                top_k=candidate_k,
            )
        )

        if not faiss_results:
            return []

        faiss_ids = [
            item["faiss_index_id"]
            for item in faiss_results
        ]

        chunks_query = (
            DocumentChunk.objects
            .select_related(
                "document",
                "document__claim",
            )
            .filter(
                faiss_index_id__in=faiss_ids
            )
        )

        if claim_id is not None:
            chunks_query = chunks_query.filter(
                document__claim_id=claim_id
            )

        chunks_by_faiss_id = {
            chunk.faiss_index_id: chunk
            for chunk in chunks_query
        }

        results = []

        for item in faiss_results:

            chunk = chunks_by_faiss_id.get(
                item["faiss_index_id"]
            )

            if chunk is None:
                continue

            results.append(
                {
                    "chunk_id": chunk.id,
                    "score": item["score"],
                    "document_id": (
                        chunk.document_id
                    ),
                    "document_name": (
                        chunk.document
                        .original_file_name
                    ),
                    "document_type": (
                        chunk.document
                        .document_type
                    ),
                    "claim_id": (
                        chunk.document.claim_id
                    ),
                    "chunk_index": (
                        chunk.chunk_index
                    ),
                    "text": chunk.text,
                }
            )

            if len(results) >= top_k:
                break

        return results

class RAGContextBuilder:
    """
    Converts retrieved chunks into a context block
    that can be passed to the LLM.
    """

    @staticmethod
    def build(
        results: list[dict],
    ) -> str:

        if not results:
            return ""

        sections = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            section = (
                f"[Source {index}]\n"
                f"Document: "
                f"{result['document_name']}\n"
                f"Document Type: "
                f"{result['document_type']}\n"
                f"Chunk Index: "
                f"{result['chunk_index']}\n"
                f"Similarity Score: "
                f"{result['score']:.4f}\n"
                f"Content:\n"
                f"{result['text']}"
            )

            sections.append(section)

        return "\n\n".join(sections)

class RAGService:
    """
    Retrieval-Augmented Generation service.
    """

    DEFAULT_TOP_K = 5
    MAX_TOP_K = 10

    def __init__(self):
        self.retrieval_service = (
            DocumentRetrievalService()
        )

        self.llm_provider = (
            HuggingFaceLLMProvider()
        )

    def answer(
        self,
        *,
        question: str,
        claim_id: int | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> dict:

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        top_k = min(
            top_k,
            self.MAX_TOP_K,
        )

        retrieved_results = (
            self.retrieval_service.search(
                query=question,
                top_k=top_k,
                claim_id=claim_id,
            )
        )

        if not retrieved_results:
            return {
                "answer": (
                    "I could not find enough relevant "
                    "information in the provided "
                    "documents to answer this question."
                ),
                "sources": [],
            }

        context = RAGContextBuilder.build(
            retrieved_results
        )

        user_prompt = build_user_prompt(
            question=question,
            context=context,
        )

        answer = self.llm_provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        sources = [
            {
                "chunk_id": result["chunk_id"],
                "document_id": result["document_id"],
                "document_name": result[
                    "document_name"
                ],
                "document_type": result[
                    "document_type"
                ],
                "chunk_index": result[
                    "chunk_index"
                ],
                "score": result["score"],
            }
            for result in retrieved_results
        ]

        return {
            "answer": answer,
            "sources": sources,
        }

class ClaimSummaryContextBuilder:
    @staticmethod
    def build_claim_data(claim) -> str:

        return f"""
Claim Number: {claim.claim_number}
Claim Type: {claim.claim_type}
Claim Status: {claim.status}
Incident Date: {claim.incident_date}
Claim Description: {claim.incident_description}
Estimated Loss: {claim.estimated_loss}
Approved Amount: {claim.approved_amount}
Submitted At: {claim.created_at}
"""

    @staticmethod
    def build_document_context(
        results: list[dict],
    ) -> str:

        if not results:
            return ""

        sections = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            sections.append(
                f"""
[Document Source {index}]
Document: {result["document_name"]}
Document Type: {result["document_type"]}
Chunk Index: {result["chunk_index"]}
Content:
{result["text"]}
"""
            )

        return "\n".join(sections)

    @staticmethod
    def build_requirements_data(
        requirements: list[dict],
    ) -> str:

        if not requirements:
            return "No document requirements were configured."

        lines = []

        for requirement in requirements:
            lines.append(
                (
                    f"Document Type: "
                    f"{requirement['document_type']}\n"
                    f"Description: "
                    f"{requirement['description']}\n"
                    f"Required: "
                    f"{requirement['required']}\n"
                    f"Fulfilled: "
                    f"{requirement['fulfilled']}"
                )
            )

        return "\n\n".join(lines)

class ClaimAISummaryService:
    """
    Generates an AI-assisted structured summary
    for an insurance claim.
    """

    TOP_K = 8

    def __init__(self):
        self.retrieval_service = (
            DocumentRetrievalService()
        )

        self.llm_provider = (
            HuggingFaceLLMProvider()
        )

    def generate(
        self,
        *,
        claim_id: int,
    ) -> ClaimAIAnalysis:

        claim = (
            Claim.objects
            .filter(id=claim_id)
            .first()
        )

        if claim is None:
            raise ValueError(
                "Claim not found."
            )

        analysis, _ = (
            ClaimAIAnalysis.objects
            .get_or_create(
                claim=claim,
            )
        )

        analysis.status = (
            AIAnalysisStatus.PROCESSING
        )

        analysis.error_message = ""

        analysis.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        try:
            claim_data = (
                ClaimSummaryContextBuilder
                .build_claim_data(claim)
            )

            requirement_status = (
                MissingDocumentService
                .get_required_document_status(
                    claim_id=claim_id
                )
            )

            requirements_context = (
                ClaimSummaryContextBuilder
                .build_requirements_data(
                    requirement_status
                )
            )

            # Retrieve multiple semantically relevant
            # chunks from this claim's documents.
            retrieval_results = (
                self.retrieval_service.search(
                    query=(
                        "Provide the key facts, incident "
                        "details, estimated loss, relevant "
                        "documentation, missing information, "
                        "and notable observations for this claim."
                    ),
                    top_k=self.TOP_K,
                    claim_id=claim_id,
                )
            )

            document_context = (
                ClaimSummaryContextBuilder
                .build_document_context(
                    retrieval_results
                )
            )

            if not document_context:
                raise ValueError(
                    "No relevant document context "
                    "was found for this claim."
                )

            user_prompt = (
                build_claim_summary_prompt(
                    claim_data=claim_data,
                    requirements=requirements_context,
                    context=document_context,
                )
            )

            structured_result = (
                self.llm_provider.generate_json(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    schema=(
                        CLAIM_SUMMARY_SCHEMA
                    ),
                    max_tokens=1000,
                    temperature=0.1,
                )
            )

            self._validate_result(
                structured_result
            )

            self.store_ai_missing_information(
                claim=claim,
                items=structured_result[
                    "missing_information"
                ]
            )

            readable_summary = (
                self._build_readable_summary(
                    structured_result
                )
            )

            analysis.status = (
                AIAnalysisStatus.COMPLETED
            )

            analysis.summary = (
                readable_summary
            )

            analysis.structured_result = (
                structured_result
            )

            analysis.model_name = (
                self.llm_provider.MODEL_NAME
            )

            analysis.generated_at = (
                timezone.now()
            )

            analysis.error_message = ""

            analysis.save()

            claim.ai_summary = (
                readable_summary
            )

            claim.save(
                update_fields=[
                    "ai_summary",
                    "updated_at",
                ]
            )

            return analysis

        except Exception as exc:

            analysis.status = (
                AIAnalysisStatus.FAILED
            )

            analysis.error_message = str(exc)

            analysis.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            raise

    @staticmethod
    def _validate_result(
        result: dict,
    ):

        required_fields = [
            "incident_summary",
            "estimated_loss",
            "documents_reviewed",
            "key_facts",
            "missing_information",
            "observations",
            "inconsistencies",
            "human_review_required",
        ]

        for field in required_fields:
            if field not in result:
                raise ValueError(
                    f"AI summary missing required "
                    f"field: {field}"
                )

        list_fields = [
            "documents_reviewed",
            "key_facts",
            "missing_information",
            "observations",
            "inconsistencies",
        ]

        for field in list_fields:
            if not isinstance(
                result[field],
                list,
            ):
                raise ValueError(
                    f"AI summary field '{field}' "
                    f"must be a list."
                )

        if not isinstance(
            result["human_review_required"],
            bool,
        ):
            raise ValueError(
                "human_review_required must be boolean."
            )

    @staticmethod
    def _build_readable_summary(
        result: dict,
    ) -> str:

        lines = []

        lines.append(
            "INCIDENT SUMMARY"
        )

        lines.append(
            result["incident_summary"]
        )

        lines.append(
            "\nESTIMATED LOSS"
        )

        lines.append(
            result["estimated_loss"]
        )

        lines.append(
            "\nDOCUMENTS REVIEWED"
        )

        for item in result[
            "documents_reviewed"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nKEY FACTS"
        )

        for item in result[
            "key_facts"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nMISSING INFORMATION"
        )

        for item in result[
            "missing_information"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nOBSERVATIONS"
        )

        for item in result[
            "observations"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nINCONSISTENCIES"
        )

        for item in result[
            "inconsistencies"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nHUMAN REVIEW REQUIRED"
        )

        lines.append(
            "Yes"
            if result[
                "human_review_required"
            ]
            else "No"
        )

        return "\n".join(lines)

    @staticmethod
    def _store_ai_missing_information(
        *,
        claim,
        items: list[str],
    ):
        from apps.claims.models import (
            ClaimAIMissingInformation,
            MissingInformationSource,
        )

        # Clear previous unresolved AI observations.
        ClaimAIMissingInformation.objects.filter(
            claim=claim,
            source=(
                MissingInformationSource
                .AI_OBSERVATION
            ),
            is_resolved=False,
        ).update(
            is_resolved=True,
            resolved_at=timezone.now(),
        )

        for item in items:
            description = item.strip()

            if not description:
                continue

            ClaimAIMissingInformation.objects.create(
                claim=claim,
                description=description,
                source=(
                    MissingInformationSource
                    .AI_OBSERVATION
                ),
            )

class MissingDocumentService:
    @staticmethod
    def get_required_document_status(
        *,
        claim_id: int,
    ) -> list[dict]:

        requirements = (
            ClaimDocumentRequirement.objects
            .filter(claim_id=claim_id)
            .order_by("document_type")
        )

        return [
            {
                "document_type": (
                    requirement.document_type
                ),
                "description": (
                    requirement.description
                ),
                "required": (
                    requirement.is_required
                ),
                "fulfilled": (
                    requirement.is_fulfilled
                ),
                "fulfilled_at": (
                    requirement.fulfilled_at
                ),
            }
            for requirement in requirements
        ]

    @staticmethod
    def get_missing_required_documents(
        *,
        claim_id: int,
    ) -> list[dict]:

        requirements = (
            ClaimDocumentRequirement.objects
            .filter(
                claim_id=claim_id,
                is_required=True,
                is_fulfilled=False,
            )
            .order_by("document_type")
        )

        return [
            {
                "document_type": (
                    requirement.document_type
                ),
                "description": (
                    requirement.description
                ),
            }
            for requirement in requirements
        ]

class ClaimInconsistencyService:
    """
    Identifies potential inconsistencies between claim
    information and retrieved claim documents.

    Results are advisory observations and require
    human review.
    """

    TOP_K = 10

    def __init__(self):
        self.retrieval_service = (
            DocumentRetrievalService()
        )

        self.llm_provider = (
            HuggingFaceLLMProvider()
        )

    def analyze(
        self,
        *,
        claim_id: int,
    ) -> list[ClaimAIInconsistency]:

        claim = (
            Claim.objects
            .filter(id=claim_id)
            .first()
        )

        if claim is None:
            raise ValueError(
                "Claim not found."
            )

        claim_data = (
            ClaimSummaryContextBuilder
            .build_claim_data(claim)
        )

        retrieval_results = (
            self.retrieval_service.search(
                query=(
                    "Find information about incident "
                    "date, location, vehicle identifiers, "
                    "estimated loss, damage description, "
                    "and other facts that could differ "
                    "between the claim and its documents."
                ),
                top_k=self.TOP_K,
                claim_id=claim_id,
            )
        )

        if not retrieval_results:
            return []

        context = (
            ClaimSummaryContextBuilder
            .build_document_context(
                retrieval_results
            )
        )

        prompt = build_inconsistency_prompt(
            claim_data=claim_data,
            context=context,
        )

        result = self.llm_provider.generate_json(
            system_prompt=(
                INCONSISTENCY_SYSTEM_PROMPT
            ),
            user_prompt=prompt,
            schema=INCONSISTENCY_SCHEMA,
            max_tokens=1200,
            temperature=0.0,
        )

        self._validate_result(result)

        return self._store_results(
            claim=claim,
            inconsistencies=result[
                "inconsistencies"
            ],
        )

    @staticmethod
    def _validate_result(
        result: dict,
    ):

        if "inconsistencies" not in result:
            raise ValueError(
                "AI response is missing "
                "'inconsistencies'."
            )

        if not isinstance(
            result["inconsistencies"],
            list,
        ):
            raise ValueError(
                "'inconsistencies' must be a list."
            )

    @staticmethod
    def _store_results(
        *,
        claim,
        inconsistencies: list[dict],
    ):

        # Resolve previous unresolved AI findings.
        ClaimAIInconsistency.objects.filter(
            claim=claim,
            is_resolved=False,
        ).update(
            is_resolved=True,
            resolved_at=timezone.now(),
        )

        created_results = []

        for item in inconsistencies:

            inconsistency_type = item[
                "type"
            ]

            severity = item[
                "severity"
            ]

            description = item[
                "description"
            ].strip()

            source_documents = item.get(
                "source_documents",
                [],
            )

            requires_review = item.get(
                "requires_human_review",
                True,
            )

            if not description:
                continue

            created_results.append(
                ClaimAIInconsistency.objects.create(
                    claim=claim,
                    inconsistency_type=(
                        inconsistency_type
                    ),
                    severity=severity,
                    description=description,
                    source_documents=(
                        source_documents
                    ),
                    requires_human_review=(
                        requires_review
                    ),
                )
            )

        return created_results