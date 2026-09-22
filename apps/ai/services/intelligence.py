from apps.claims.models import (
    Claim,
    ClaimAIAnalysis,
    ClaimAIInconsistency,
    ClaimAIMissingInformation,
)

from .missing_documents import MissingDocumentService


class ClaimAIIntelligenceService:
    @staticmethod
    def get_intelligence(
        *,
        claim_id: int,
    ) -> dict:

        claim = (
            Claim.objects
            .filter(id=claim_id)
            .first()
        )

        if claim is None:
            raise ValueError(
                "Claim not found."
            )

        # AI Summary
        analysis = (
            ClaimAIAnalysis.objects
            .filter(claim=claim)
            .first()
        )

        if analysis is None:
            ai_summary = None

        else:
            ai_summary = {
                "status": analysis.status,
                "summary": analysis.summary,
                "structured_result": (
                    analysis.structured_result
                ),
                "model_name": (
                    analysis.model_name
                ),
                "error_message": (
                    analysis.error_message
                ),
                "generated_at": (
                    analysis.generated_at
                ),
            }

        # Required Documents
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

        ai_missing_information = (
            ClaimAIMissingInformation.objects
            .filter(
                claim=claim,
                source="AI_OBSERVATION",
                is_resolved=False,
            )
            .order_by("-created_at")
        )

        ai_missing_information_data = [
            {
                "id": item.id,
                "description": item.description,
                "source": item.source,
                "document_type": (
                    item.document_type
                ),
                "is_resolved": (
                    item.is_resolved
                ),
                "created_at": (
                    item.created_at
                ),
            }
            for item in ai_missing_information
        ]

        # Inconsistencies
        inconsistencies = (
            ClaimAIInconsistency.objects
            .filter(
                claim=claim,
                is_resolved=False,
            )
            .order_by("-created_at")
        )

        inconsistency_data = [
            {
                "id": item.id,
                "type": (
                    item.inconsistency_type
                ),
                "severity": item.severity,
                "description": (
                    item.description
                ),
                "source_documents": (
                    item.source_documents
                ),
                "requires_human_review": (
                    item.requires_human_review
                ),
                "created_at": (
                    item.created_at
                ),
            }
            for item in inconsistencies
        ]

        return {
            "claim_id": claim.id,

            "claim_number": (
                claim.claim_number
            ),

            "ai_summary": ai_summary,

            "documents": {
                "required": (
                    required_documents
                ),
                "missing_required": (
                    missing_required_documents
                ),
                "ai_observed_missing": (
                    ai_missing_information_data
                ),
            },

            "inconsistencies": (
                inconsistency_data
            ),
        }
