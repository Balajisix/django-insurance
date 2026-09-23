from django.db import transaction
from rest_framework.authtoken.models import Token

from apps.customers.models import Customer

from .models import User, UserRole


class AuthenticationService:
    @staticmethod
    @transaction.atomic
    def register_customer(
        *,
        email,
        password,
        first_name,
        last_name,
        phone_number="",
        date_of_birth=None,
        address_line="",
        city="",
        state="",
        postal_code="",
    ):
        """
        Register a new customer user and create
        the corresponding customer profile.
        """

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.CUSTOMER,
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

        return user, customer

    @staticmethod
    def login_user(user):
        token, _ = Token.objects.get_or_create(
            user=user
        )

        return token

    @staticmethod
    def logout_user(user):
        Token.objects.filter(
            user=user
        ).delete()

    @staticmethod
    @transaction.atomic
    def create_staff_user(
        *,
        email,
        password,
        first_name,
        last_name,
        role,
    ):
        """
        Create an internal staff account (claims officer,
        manager or admin). Unlike register_customer(), this
        does not create a Customer profile.
        """

        return User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )

    @staticmethod
    def update_user_role(
        *,
        user,
        role,
    ):
        user.role = role

        user.save(
            update_fields=[
                "role",
                "updated_at",
            ]
        )

        return user