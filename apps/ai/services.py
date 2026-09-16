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
)

from .chunkers.text import TextChunker
from .models import DocumentChunk, DocumentExtraction

from .embeddings.huggingface import HuggingFaceEmbeddingProvider


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