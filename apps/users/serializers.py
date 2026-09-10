from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.customers.models import Customer

from .models import User, UserRole


class UserSerializer(serializers.ModelSerializer):
    """
    Safe representation of the authenticated user.
    """

    class Meta:
        model = User

        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]


class RegisterSerializer(serializers.Serializer):
    """
    Customer registration payload.
    """

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    first_name = serializers.CharField(
        required=True,
        max_length=150,
    )

    last_name = serializers.CharField(
        required=True,
        max_length=150,
    )

    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
    )

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
    )

    address_line = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )

    city = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    state = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    postal_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
    )

    def validate_email(self, value):
        value = value.lower().strip()

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate(self, attrs):
        password = attrs["password"]
        password_confirm = attrs["password_confirm"]

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Passwords do not match."
                    )
                }
            )

        validate_password(password)

        return attrs


class LoginSerializer(serializers.Serializer):
    """
    Login payload.
    """

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        user = authenticate(
            email=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        attrs["user"] = user

        return attrs


class RegistrationResponseSerializer(serializers.Serializer):
    """
    Response returned after successful registration.
    """

    user = UserSerializer()
    customer = serializers.SerializerMethodField()

    def get_customer(self, obj):
        customer = obj.get("customer")

        if customer is None:
            return None

        return {
            "id": customer.id,
            "customer_number": (
                customer.customer_number
            ),
        }


class LoginResponseSerializer(serializers.Serializer):
    """
    Response returned after successful login.
    """

    token = serializers.CharField()
    user = UserSerializer()