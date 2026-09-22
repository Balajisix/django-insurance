from apps.documents.models import ClaimDocument, DocumentStatus

from ..models import DocumentExtraction, DocumentChunk

from .chunking import DocumentChunkingService
from .embedding import DocumentEmbeddingService
from .inconsistency import ClaimInconsistencyService
from .missing_documents import MissingDocumentService
from .processing import DocumentProcessingService
from .summary import ClaimAISummaryService


class ClaimAIWorkflowService:
    @staticmethod
    def process_claim(
        *,
        claim_id: int,
        actor=None,
    ) -> dict:

        from apps.claims.models import Claim

        claim = (
            Claim.objects
            .filter(id=claim_id)
            .first()
        )

        if claim is None:
            raise ValueError(
                "Claim not found."
            )

        documents = list(
            ClaimDocument.objects
            .filter(
                claim_id=claim_id
            )
            .order_by("id")
        )

        if not documents:
            raise ValueError(
                "Claim has no documents to process."
            )

        processing_results = []

        for document in documents:

            processing_results.append(
                ClaimAIWorkflowService
                ._process_document(
                    document=document,
                    actor=actor,
                )
            )

        # Generate claim-level embeddings/results
        summary_service = (
            ClaimAISummaryService()
        )

        summary = summary_service.generate(
            claim_id=claim_id
        )

        # Missing information
        required_documents = (
            MissingDocumentService
            .get_required_document_status(
                claim_id=claim_id
            )
        )

        missing_required = (
            MissingDocumentService
            .get_missing_required_documents(
                claim_id=claim_id
            )
        )

        # Inconsistency analysis
        inconsistency_service = (
            ClaimInconsistencyService()
        )

        inconsistencies = (
            inconsistency_service.analyze(
                claim_id=claim_id
            )
        )

        return {
            "claim_id": claim.id,
            "claim_number": (
                claim.claim_number
            ),
            "documents_processed": (
                processing_results
            ),
            "summary": summary,
            "required_documents": (
                required_documents
            ),
            "missing_required_documents": (
                missing_required
            ),
            "inconsistencies": (
                inconsistencies
            ),
        }

    @staticmethod
    def _process_document(
        *,
        document,
        actor=None,
    ) -> dict:
        extraction_exists = (
            DocumentExtraction.objects
            .filter(
                document_id=document.id,
            )
            .exists()
        )

        chunk_exists = (
            DocumentChunk.objects
            .filter(
                document_id=document.id,
            )
            .exists()
        )

        embedding_exists = (
            DocumentChunk.objects
            .filter(
                document_id=document.id,
                faiss_index_id__isnull=False,
            )
            .exclude(
                embedding_model="",
            )
            .exclude(
                embedding_model__isnull=True,
            )
            .exists()
        )

        if (
            document.status == DocumentStatus.PROCESSED
            and extraction_exists
            and chunk_exists
            and embedding_exists
        ):
            chunk_count = (
                DocumentChunk.objects
                .filter(
                    document_id=document.id,
                )
                .count()
            )

            embedded_count = (
                DocumentChunk.objects
                .filter(
                    document_id=document.id,
                    faiss_index_id__isnull=False,
                )
                .count()
            )

            return {
                "document_id": document.id,
                "document_name": (
                    document.original_file_name
                ),
                "processing_job_id": None,
                "processing_status": "SKIPPED",
                "chunk_count": chunk_count,
                "embedded_chunk_count": embedded_count,
            }

        job = (
            DocumentProcessingService
            .create_processing_job(
                document_id=document.id,
                created_by=actor,
            )
        )

        if job is None:
            raise ValueError(
                (
                    "Unable to create a processing job for "
                    f"document {document.id}."
                )
            )

        job = (
            DocumentProcessingService
            .process_document(
                job_id=job.id,
            )
        )

        if job is None:
            raise ValueError(
                (
                    "Document processing returned no job for "
                    f"document {document.id}."
                )
            )

        chunks = (
            DocumentChunkingService
            .create_chunks(
                document_id=document.id,
            )
        )

        if chunks is None:
            raise ValueError(
                (
                    "Chunk creation returned None for "
                    f"document {document.id}. "
                    "Ensure create_chunks() returns a list "
                    "or QuerySet."
                )
            )

        embedding_service = DocumentEmbeddingService()

        embedded_chunks = (
            embedding_service
            .embed_document(
                document_id=document.id,
            )
        )

        if embedded_chunks is None:
            raise ValueError(
                (
                    "Embedding creation returned None for "
                    f"document {document.id}. "
                    "Ensure embed_document() returns a list "
                    "or QuerySet."
                )
            )

        return {
            "document_id": document.id,
            "document_name": (
                document.original_file_name
            ),
            "processing_job_id": job.id,
            "processing_status": job.status,
            "chunk_count": len(chunks),
            "embedded_chunk_count": len(
                embedded_chunks
            ),
        }

    @staticmethod
    def process_claim_workflow(
        *,
        claim_id: int,
        actor,
    ) -> dict:

        from apps.claims.models import Claim
        from apps.claims.workflow import (
            ClaimWorkflowService,
        )

        claim = (
            Claim.objects
            .filter(id=claim_id)
            .first()
        )

        if claim is None:
            raise ValueError(
                "Claim not found."
            )

        # Start document processing
        ClaimWorkflowService.start_ai_processing(
            claim=claim,
            actor=actor,
        )

        try:

            result = (
                ClaimAIWorkflowService
                .process_claim(
                    claim_id=claim_id,
                    actor=actor,
                )
            )

            claim.refresh_from_db()

            # Move to human review
            ClaimWorkflowService.complete_ai_processing(
                claim=claim,
                actor=actor,
            )

            claim.refresh_from_db()

            result["final_claim_status"] = (
                claim.status
            )

            return result

        except Exception:
            claim.refresh_from_db()
            raise
