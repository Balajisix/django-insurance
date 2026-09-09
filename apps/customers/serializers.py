from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Customer

User = get_user_model()

class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True, 
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = Customer

        fields = [
            "id",
            "customer_number",
            "username",
            "email",
            "date_of_birth",
            "phone_number",
            "address_line",
            "city",
            "state",
            "postal_code",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "customer_number",
            "username",
            "email",
            "created_at",
            "updated_at",
        ]

class CustomerCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
    )

    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
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

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "User does not exist."
            )

        if Customer.objects.filter(user_id=value).exists():
            raise serializers.ValidationError(
                "A customer profile already exists for this user."
            )

        return value