from django.contrib.auth import get_user_model
from django.db import transaction

from apps.common.exceptions import (
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
)

from .models import Customer

User = get_user_model()

class CustomerService:
    @staticmethod
    @transaction.atomic
    def create_customer(
        *,
        user_id,
        phone_number="",
        date_of_birth=None,
        address_line="",
        city="",
        state="",
        postal_code="",
    ) -> Customer:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise CustomerNotFoundError(
                "The specified user does not exist."
            ) from exc

        if Customer.objects.filter(user=user).exists():
            raise CustomerAlreadyExistsError(
                "A customer profile already exists for this user."
            )

        customer = Customer.objects.create(
            user=user,
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            address_line=address_line,
            city=city,
            state=state,
            postal_code=postal_code,
        )

        return customer