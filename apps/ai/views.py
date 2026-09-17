from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import ClaimDocument

from .models import DocumentExtraction, DocumentProcessingJob, DocumentChunk
from .serializers import (
    ClaimAIAnalysisSerializer,
    DocumentExtractionSerializer,
    DocumentProcessingJobSerializer,
    DocumentChunkSerializer,
    DocumentEmbeddingSerializer,
    DocumentSearchSerializer,
    RAGQuerySerializer,
    RequiredDocumentStatusSerializer,
    AIMissingInformationSerializer
)
from .services import (
    ClaimAISummaryService,
    DocumentProcessingService, 
    DocumentChunkingService, 
    DocumentEmbeddingService,
    DocumentRetrievalService,
    RAGService,
    MissingDocumentService
)

from apps.claims.models import ClaimAIAnalysis, Claim, ClaimAIMissingInformation


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

class DocumentChunkingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        try:
            chunks = DocumentChunkingService.create_chunks(
                document_id=document_id,
            )

            serializer = DocumentChunkSerializer(
                chunks,
                many=True,
            )

            return Response(
                {
                    "document_id": document_id,
                    "chunk_count": len(chunks),
                    "chunks": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DocumentChunkListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        chunks = (
            DocumentChunk.objects
            .filter(document_id=document_id)
            .order_by("chunk_index")
        )

        serializer = DocumentChunkSerializer(
            chunks,
            many=True,
        )

        return Response(
            {
                "document_id": document_id,
                "chunk_count": chunks.count(),
                "chunks": serializer.data,
            }
        )

class DocumentEmbeddingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        try:
            service = DocumentEmbeddingService()

            chunks = service.embed_document(
                document_id=document_id
            )

            serializer = (
                DocumentEmbeddingSerializer(
                    chunks,
                    many=True,
                )
            )

            return Response(
                {
                    "document_id": document_id,
                    "embedded_chunk_count": len(
                        chunks
                    ),
                    "model": (
                        service.provider.MODEL_NAME
                    ),
                    "chunks": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class DocumentSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        request_serializer = (
            DocumentSearchSerializer(
                data=request.data
            )
        )

        request_serializer.is_valid(
            raise_exception=True
        )

        data = request_serializer.validated_data

        try:
            service = DocumentRetrievalService()

            results = service.search(
                query=data["query"],
                top_k=data["top_k"],
                claim_id=data.get(
                    "claim_id"
                ),
            )

            return Response(
                {
                    "query": data["query"],
                    "claim_id": data.get(
                        "claim_id"
                    ),
                    "result_count": len(
                        results
                    ),
                    "results": results,
                }
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class RAGQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        request_serializer = (
            RAGQuerySerializer(
                data=request.data
            )
        )

        request_serializer.is_valid(
            raise_exception=True
        )

        data = (
            request_serializer
            .validated_data
        )

        try:
            service = RAGService()

            result = service.answer(
                question=data["question"],
                claim_id=data.get(
                    "claim_id"
                ),
                top_k=data["top_k"],
            )

            response_data = {
                "question": data["question"],
                "claim_id": data.get(
                    "claim_id"
                ),
                "answer": result["answer"],
                "sources": result["sources"],
            }

            return Response(
                response_data,
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class ClaimAISummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        claim_id,
    ):

        try:
            service = ClaimAISummaryService()

            analysis = service.generate(
                claim_id=claim_id,
            )

            serializer = (
                ClaimAIAnalysisSerializer(
                    analysis
                )
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class ClaimAISummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        claim_id,
    ):

        analysis = (
            ClaimAIAnalysis.objects
            .filter(claim_id=claim_id)
            .first()
        )

        if analysis is None:
            return Response(
                {
                    "detail": (
                        "No AI analysis has been "
                        "generated for this claim."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = (
            ClaimAIAnalysisSerializer(
                analysis
            )
        )

        return Response(
            serializer.data
        )

class MissingDocumentIntelligenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        claim_id,
    ):

        try:
            claim = Claim.objects.get(
                id=claim_id
            )
        except Claim.DoesNotExist:
            return Response(
                {
                    "detail": "Claim not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        required_documents = (
            MissingDocumentService
            .get_required_document_status(
                claim_id=claim_id
            )
        )

        missing_required_documents = (
            MissingDocumentService
            .get_missing_required_documents(
                claim_id=claim_id
            )
        )

        ai_observations = (
            ClaimAIMissingInformation.objects
            .filter(
                claim=claim,
                source="AI_OBSERVATION",
                is_resolved=False,
            )
            .order_by("-created_at")
        )

        required_serializer = (
            RequiredDocumentStatusSerializer(
                required_documents,
                many=True,
            )
        )

        ai_serializer = (
            AIMissingInformationSerializer(
                ai_observations,
                many=True,
            )
        )

        return Response(
            {
                "claim_id": claim.id,
                "claim_number": (
                    claim.claim_number
                ),
                "required_documents": (
                    required_serializer.data
                ),
                "missing_required_documents": (
                    missing_required_documents
                ),
                "ai_observed_missing_information": (
                    ai_serializer.data
                ),
            }
        )