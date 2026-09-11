from django.db import transaction
from django.utils import timezone

from apps.documents.models import ClaimDocument

from .extractors.pdf import PDFTextExtractor
from .models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractionMethod,
    ProcessingStatus,
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
        """
        Create a new processing job for a document.
        """

        document = (
            ClaimDocument.objects
            .select_related("claim")
            .filter(id=document_id)
            .first()
        )

        if document is None:
            raise ValueError("Document not found.")

        active_job_exists = DocumentProcessingJob.objects.filter(
            document=document,
            status__in=[
                ProcessingStatus.PENDING,
                ProcessingStatus.PROCESSING,
            ],
        ).exists()

        if active_job_exists:
            raise ValueError(
                "Document already has an active processing job."
            )

        previous_attempts = DocumentProcessingJob.objects.filter(
            document=document,
        ).count()

        job = DocumentProcessingJob.objects.create(
            document=document,
            status=ProcessingStatus.PENDING,
            attempt_number=previous_attempts + 1,
            created_by=created_by,
        )

        return job

    @staticmethod
    def process_document(
        *,
        job_id: int,
    ) -> DocumentProcessingJob:
        """
        Process a single document processing job.

        Current implementation supports text-based PDFs.
        """

        job = (
            DocumentProcessingJob.objects
            .select_related("document")
            .filter(id=job_id)
            .first()
        )

        if job is None:
            raise ValueError("Processing job not found.")

        if job.status == ProcessingStatus.COMPLETED:
            return job

        if job.status == ProcessingStatus.PROCESSING:
            raise ValueError(
                "Document processing job is already running."
            )

        if job.status not in [
            ProcessingStatus.PENDING,
            ProcessingStatus.FAILED,
        ]:
            raise ValueError(
                f"Cannot process job in status: {job.status}"
            )

        job.status = ProcessingStatus.PROCESSING
        job.started_at = timezone.now()
        job.completed_at = None
        job.error_message = ""

        job.document.status = "PROCESSING"
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
            document = job.document

            extracted_text = PDFTextExtractor.extract_from_storage(
                document.s3_key
            )

            with transaction.atomic():
                extraction, _ = (
                    DocumentExtraction.objects.update_or_create(
                        document=document,
                        defaults={
                            "extracted_text": extracted_text,
                            "extraction_method": (
                                ExtractionMethod.TEXT
                            ),
                            "extractor_version": "pypdf-v1",
                            "character_count": len(extracted_text),
                        },
                    )
                )

                document.status = "PROCESSED"
                document.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                job.status = ProcessingStatus.COMPLETED
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

            job.document.status = "FAILED"
            job.document.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            job.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_message",
                    "updated_at",
                ]
            )

            raise