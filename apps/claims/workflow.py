from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import ClaimValidationError

from .models import (
    ClaimEvent,
    ClaimEventType,
    ClaimSettlement,
    ClaimStatus,
)


class ClaimWorkflowService:
    """
    Handles claim status transitions and claim workflow events.
    """

    ALLOWED_TRANSITIONS = {
        ClaimStatus.SUBMITTED: {
            ClaimStatus.DOCUMENT_PROCESSING,
        },
        ClaimStatus.DOCUMENT_PROCESSING: {
            ClaimStatus.UNDER_REVIEW,
        },
        ClaimStatus.UNDER_REVIEW: {
            ClaimStatus.ADDITIONAL_INFO_REQUIRED,
            ClaimStatus.APPROVED,
            ClaimStatus.REJECTED,
        },
        ClaimStatus.ADDITIONAL_INFO_REQUIRED: {
            ClaimStatus.UNDER_REVIEW,
        },
        ClaimStatus.APPROVED: {
            ClaimStatus.SETTLEMENT_IN_PROGRESS,
        },
        ClaimStatus.SETTLEMENT_IN_PROGRESS: {
            ClaimStatus.SETTLED,
        },
        ClaimStatus.SETTLED: {
            ClaimStatus.CLOSED,
        },
        ClaimStatus.REJECTED: set(),
        ClaimStatus.CLOSED: set(),
    }

    EVENT_TYPES = {
        ClaimStatus.DOCUMENT_PROCESSING: (
            ClaimEventType.DOCUMENT_PROCESSING_STARTED
        ),
        ClaimStatus.UNDER_REVIEW: (
            ClaimEventType.REVIEW_STARTED
        ),
        ClaimStatus.ADDITIONAL_INFO_REQUIRED: (
            ClaimEventType.ADDITIONAL_INFORMATION_REQUESTED
        ),
        ClaimStatus.APPROVED: (
            ClaimEventType.APPROVED
        ),
        ClaimStatus.REJECTED: (
            ClaimEventType.REJECTED
        ),
        ClaimStatus.SETTLEMENT_IN_PROGRESS: (
            ClaimEventType.SETTLEMENT_STARTED
        ),
        ClaimStatus.SETTLED: (
            ClaimEventType.SETTLED
        ),
        ClaimStatus.CLOSED: (
            ClaimEventType.CLOSED
        ),
    }

    @staticmethod
    @transaction.atomic
    def transition(
        *,
        claim,
        to_status,
        actor,
        comment="",
    ):
        current_status = claim.status

        allowed_statuses = (
            ClaimWorkflowService
            .ALLOWED_TRANSITIONS
            .get(current_status, set())
        )

        if to_status not in allowed_statuses:
            raise ClaimValidationError(
                (
                    f"Invalid claim transition: "
                    f"{current_status} -> {to_status}."
                )
            )

        event_type = (
            ClaimWorkflowService
            .EVENT_TYPES[to_status]
        )

        claim.status = to_status
        claim.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        event = ClaimEvent.objects.create(
            claim=claim,
            event_type=event_type,
            from_status=current_status,
            to_status=to_status,
            comment=comment,
            actor=actor,
        )

        return event

    @staticmethod
    @transaction.atomic
    def start_document_processing(
        *,
        claim,
        actor,
    ):
        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.DOCUMENT_PROCESSING,
            actor=actor,
            comment="Document processing started.",
        )

    @staticmethod
    @transaction.atomic
    def start_review(
        *,
        claim,
        actor,
    ):
        ClaimWorkflowService._validate_required_documents(
            claim
        )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.UNDER_REVIEW,
            actor=actor,
            comment="Claim moved to review.",
        )

    @staticmethod
    @transaction.atomic
    def request_additional_information(
        *,
        claim,
        actor,
        comment,
    ):
        if not comment.strip():
            raise ClaimValidationError(
                "A reason is required when requesting additional information."
            )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=(
                ClaimStatus.ADDITIONAL_INFO_REQUIRED
            ),
            actor=actor,
            comment=comment.strip(),
        )

    @staticmethod
    @transaction.atomic
    def resume_review(
        *,
        claim,
        actor,
    ):
        ClaimWorkflowService._validate_required_documents(
            claim
        )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.UNDER_REVIEW,
            actor=actor,
            comment="Required information received; review resumed.",
        )

    @staticmethod
    @transaction.atomic
    def approve_claim(
        *,
        claim,
        actor,
        approved_amount,
        comment="",
    ):
        if approved_amount < Decimal("0"):
            raise ClaimValidationError(
                "Approved amount cannot be negative."
            )

        claim.approved_amount = approved_amount
        claim.save(
            update_fields=[
                "approved_amount",
                "updated_at",
            ]
        )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.APPROVED,
            actor=actor,
            comment=comment.strip(),
        )

    @staticmethod
    @transaction.atomic
    def reject_claim(
        *,
        claim,
        actor,
        reason,
    ):
        if not reason.strip():
            raise ClaimValidationError(
                "A rejection reason is required."
            )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.REJECTED,
            actor=actor,
            comment=reason.strip(),
        )

    @staticmethod
    @transaction.atomic
    def start_settlement(
        *,
        claim,
        actor,
    ):
        if claim.approved_amount is None:
            raise ClaimValidationError(
                "An approved amount is required before settlement."
            )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.SETTLEMENT_IN_PROGRESS,
            actor=actor,
            comment="Settlement processing started.",
        )

    @staticmethod
    @transaction.atomic
    def settle_claim(
        *,
        claim,
        actor,
        settlement_amount,
        payment_reference,
    ):
        if settlement_amount < Decimal("0"):
            raise ClaimValidationError(
                "Settlement amount cannot be negative."
            )

        if not payment_reference.strip():
            raise ClaimValidationError(
                "Payment reference is required."
            )

        if ClaimSettlement.objects.filter(
            payment_reference=payment_reference
        ).exists():
            raise ClaimValidationError(
                "Payment reference already exists."
            )

        ClaimSettlement.objects.create(
            claim=claim,
            settlement_amount=settlement_amount,
            payment_reference=payment_reference.strip(),
            settled_at=timezone.now(),
        )

        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.SETTLED,
            actor=actor,
            comment=(
                f"Settlement completed: "
                f"{payment_reference.strip()}"
            ),
        )

    @staticmethod
    @transaction.atomic
    def close_claim(
        *,
        claim,
        actor,
        comment="",
    ):
        return ClaimWorkflowService.transition(
            claim=claim,
            to_status=ClaimStatus.CLOSED,
            actor=actor,
            comment=comment.strip(),
        )

    @staticmethod
    def _validate_required_documents(
        claim,
    ):
        missing_requirements = (
            claim.document_requirements.filter(
                is_required=True,
                is_fulfilled=False,
            )
        )

        if missing_requirements.exists():
            missing_types = list(
                missing_requirements.values_list(
                    "document_type",
                    flat=True,
                )
            )

            raise ClaimValidationError(
                (
                    "Required documents are missing: "
                    + ", ".join(missing_types)
                )
            )