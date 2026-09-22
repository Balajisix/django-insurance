from django.db import transaction
from django.utils import timezone

from apps.documents.models import (
    ClaimDocument,
    DocumentStatus,
)

from ..extractors.ocr import TesseractOCRExtractor
from ..extractors.pdf import PDFTextExtractor
from ..models import (
    DocumentExtraction,
    DocumentProcessingJob,
    ExtractionMethod,
    ProcessingStatus,
)
from .vision_analysis import DocumentVisualAnalysisService


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
        content_type = (
            document.content_type or ""
        ).lower()

        document_type = (
            document.document_type or ""
        ).upper()

        # Accident photos → Vision
        if document_type == "ACCIDENT_PHOTO":

            if content_type not in [
                "image/jpeg",
                "image/png",
            ]:
                raise ValueError(
                    "ACCIDENT_PHOTO must be a JPEG or PNG image."
                )

            analysis_service = (
                DocumentVisualAnalysisService()
            )

            analysis = (
                analysis_service.analyze(
                    document=document
                )
            )

            return (
                analysis.summary,
                ExtractionMethod.VISION,
                (
                    "huggingface-vision-v1"
                ),
            )

        # Other images → OCR
        if content_type in [
            "image/jpeg",
            "image/png",
        ]:

            extractor = (
                TesseractOCRExtractor()
            )

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

        # PDF → normal PDF extraction
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

        raise ValueError(
            f"Unsupported document content type: "
            f"{document.content_type}"
        )
