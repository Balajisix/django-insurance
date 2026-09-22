from django.utils import timezone

from ..llm.huggingface import HuggingFaceLLMProvider
from ..prompts.inconsistency import (
    INCONSISTENCY_SCHEMA,
    SYSTEM_PROMPT as INCONSISTENCY_SYSTEM_PROMPT,
    build_inconsistency_prompt,
)

from apps.claims.models import Claim, ClaimAIInconsistency

from .retrieval import DocumentRetrievalService
from .summary_context import ClaimSummaryContextBuilder


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
