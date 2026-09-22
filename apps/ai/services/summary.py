from django.utils import timezone

from ..llm.huggingface import HuggingFaceLLMProvider
from ..prompts.rag import SYSTEM_PROMPT
from ..prompts.claim_summary import CLAIM_SUMMARY_SCHEMA, build_claim_summary_prompt

from apps.claims.models import Claim, ClaimAIAnalysis, AIAnalysisStatus

from .missing_documents import MissingDocumentService
from .retrieval import DocumentRetrievalService
from .summary_context import ClaimSummaryContextBuilder


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

            self._store_ai_missing_information(
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
