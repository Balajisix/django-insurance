from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.models import UserRole
from apps.users.permissions import IsClaimsStaff

from .models import Customer
from .serializers import (
    CustomerCreateSerializer,
    CustomerSerializer,
)
from .services import CustomerService

class CustomerListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/customers/  — a customer sees only their own
                                profile; staff see everyone.
    POST /api/v1/customers/  — staff only. Self-service customers
                                get a profile automatically via
                                /auth/register/ instead.
    """

    queryset = Customer.objects.select_related("user").all()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsClaimsStaff()]

        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(user=user)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CustomerCreateSerializer

        return CustomerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        customer = CustomerService.create_customer(
            user_id=data["user_id"],
            date_of_birth=data.get("date_of_birth"),
            phone_number=data.get("phone_number", ""),
            address_line=data.get("address_line", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
        )

        response_serializer = CustomerSerializer(
            customer
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CustomerDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/customers/{id}/

    A customer may only retrieve their own profile;
    staff may retrieve any.
    """

    permission_classes = [IsAuthenticated]

    queryset = Customer.objects.select_related("user").all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == UserRole.CUSTOMER:
            queryset = queryset.filter(user=user)

        return queryset