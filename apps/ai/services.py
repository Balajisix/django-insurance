from django.db import transaction

from apps.documents.models import ClaimDocument

from .models import DocumentProcessingJob, ProcessingStatus


class DocumentProcessingService:
    """
    Business logic for document processing jobs.
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