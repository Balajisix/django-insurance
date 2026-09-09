from datetime import date

from django.db import transaction

from apps.common.exceptions import ClaimValidationError
from apps.policies.models import Policy, PolicyStatus

from .models import Claim


class ClaimService:
    @staticmethod
    @transaction.atomic
    def submit_claim(
        *,
        policy_id,
        claim_type,
        incident_date,
        incident_description,
        estimated_loss,
    ) -> Claim:
        try:
            policy = Policy.objects.get(
                id=policy_id
            )
        except Policy.DoesNotExist as exc:
            raise ClaimValidationError(
                "The specified policy does not exist."
            ) from exc

        if policy.status != PolicyStatus.ACTIVE:
            raise ClaimValidationError(
                "A claim can only be submitted against an active policy."
            )

        if incident_date > date.today():
            raise ClaimValidationError(
                "Incident date cannot be in the future."
            )

        if incident_date < policy.start_date:
            raise ClaimValidationError(
                "Incident date cannot be before the policy start date."
            )

        if incident_date > policy.end_date:
            raise ClaimValidationError(
                "Incident date cannot be after the policy end date."
            )

        if not incident_description.strip():
            raise ClaimValidationError(
                "Incident description is required."
            )

        if estimated_loss < 0:
            raise ClaimValidationError(
                "Estimated loss cannot be negative."
            )

        claim = Claim.objects.create(
            policy=policy,
            claim_type=claim_type,
            incident_date=incident_date,
            incident_description=incident_description.strip(),
            estimated_loss=estimated_loss,
        )

        return claim