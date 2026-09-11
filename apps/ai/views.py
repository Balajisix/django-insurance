from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import ClaimDocument

from .models import DocumentExtraction, DocumentProcessingJob
from .serializers import (
    DocumentExtractionSerializer,
    DocumentProcessingJobSerializer,
)
from .services import DocumentProcessingService


class DocumentProcessingStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        try:
            document = ClaimDocument.objects.get(
                id=document_id
            )

            job = DocumentProcessingService.create_processing_job(
                document_id=document.id,
                created_by=request.user,
            )

            try:
                job = DocumentProcessingService.process_document(
                    job_id=job.id,
                )
            except Exception:
                job.refresh_from_db()
                serializer = DocumentProcessingJobSerializer(job)

                return Response(
                    serializer.data,
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            serializer = DocumentProcessingJobSerializer(job)

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        except ClaimDocument.DoesNotExist:
            return Response(
                {
                    "detail": "Document not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DocumentProcessingJobListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        jobs = (
            DocumentProcessingJob.objects
            .filter(document_id=document_id)
            .select_related(
                "document",
                "created_by",
            )
            .order_by("-created_at")
        )

        serializer = DocumentProcessingJobSerializer(
            jobs,
            many=True,
        )

        return Response(serializer.data)


class DocumentExtractionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        extraction = (
            DocumentExtraction.objects
            .filter(document_id=document_id)
            .select_related("document")
            .first()
        )

        if extraction is None:
            return Response(
                {
                    "detail": (
                        "No extraction is available "
                        "for this document yet."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DocumentExtractionSerializer(
            extraction
        )

        return Response(serializer.data)