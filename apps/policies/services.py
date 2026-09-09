from datetime import date

from django.db import transaction

from apps.common.exceptions import (
    PolicyValidationError,
)
from apps.customers.models import Customer

from .models import Coverage, Policy, PolicyStatus


class PolicyService:
    @staticmethod
    @transaction.atomic
    def create_policy(
        *,
        customer_id,
        policy_type,
        start_date,
        end_date,
        premium,
    ) -> Policy:
        try:
            customer = Customer.objects.get(
                id=customer_id
            )
        except Customer.DoesNotExist as exc:
            raise PolicyValidationError(
                "The specified customer does not exist."
            ) from exc

        if start_date > end_date:
            raise PolicyValidationError(
                "Policy end date cannot be before start date."
            )

        if start_date < date.today():
            raise PolicyValidationError(
                "Policy start date cannot be in the past."
            )

        if premium < 0:
            raise PolicyValidationError(
                "Policy premium cannot be negative."
            )

        policy = Policy.objects.create(
            customer=customer,
            policy_type=policy_type,
            start_date=start_date,
            end_date=end_date,
            premium=premium,
            status=PolicyStatus.ACTIVE,
        )

        return policy

    @staticmethod
    @transaction.atomic
    def add_coverage(
        *,
        policy_id,
        coverage_code,
        name,
        description="",
        coverage_limit=None,
        deductible=0,
    ) -> Coverage:
        try:
            policy = Policy.objects.get(
                id=policy_id
            )
        except Policy.DoesNotExist as exc:
            raise PolicyValidationError(
                "The specified policy does not exist."
            ) from exc

        if policy.status != PolicyStatus.ACTIVE:
            raise PolicyValidationError(
                "Coverage can only be added to an active policy."
            )

        if coverage_limit is not None and coverage_limit < 0:
            raise PolicyValidationError(
                "Coverage limit cannot be negative."
            )

        if deductible < 0:
            raise PolicyValidationError(
                "Deductible cannot be negative."
            )

        return Coverage.objects.create(
            policy=policy,
            coverage_code=coverage_code,
            name=name,
            description=description,
            coverage_limit=coverage_limit,
            deductible=deductible,
        )