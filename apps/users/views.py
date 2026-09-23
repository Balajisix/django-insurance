from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin
from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    RegistrationResponseSerializer,
    RegisterSerializer,
    StaffUserCreateSerializer,
    UserRoleUpdateSerializer,
    UserSerializer,
)
from .services import AuthenticationService


class RegisterView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        user, customer = (
            AuthenticationService.register_customer(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone_number=data.get(
                    "phone_number",
                    "",
                ),
                date_of_birth=data.get(
                    "date_of_birth"
                ),
                address_line=data.get(
                    "address_line",
                    "",
                ),
                city=data.get(
                    "city",
                    "",
                ),
                state=data.get(
                    "state",
                    "",
                ),
                postal_code=data.get(
                    "postal_code",
                    "",
                ),
            )
        )

        response_serializer = (
            RegistrationResponseSerializer(
                {
                    "user": user,
                    "customer": customer,
                }
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.validated_data[
            "user"
        ]

        token = (
            AuthenticationService.login_user(
                user
            )
        )

        response_serializer = (
            LoginResponseSerializer(
                {
                    "token": token.key,
                    "user": user,
                }
            )
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        AuthenticationService.logout_user(
            request.user
        )

        return Response(
            {
                "message": "Logged out successfully."
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        serializer = UserSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class UserListView(generics.ListAPIView):
    """
    GET /api/v1/auth/users/

    Admin only. Lists every user account.
    Supports an optional ?role= filter.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by(
            "-created_at"
        )

        role = self.request.query_params.get(
            "role"
        )

        if role:
            queryset = queryset.filter(
                role=role
            )

        return queryset


class StaffUserCreateView(APIView):
    """
    POST /api/v1/auth/users/create-staff/

    Admin only. Creates a claims officer,
    manager or admin account.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def post(self, request):
        serializer = StaffUserCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        user = (
            AuthenticationService.create_staff_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=data["role"],
            )
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class UserRoleUpdateView(APIView):
    """
    PATCH /api/v1/auth/users/{id}/role/

    Admin only. Changes an existing staff
    member's role.
    """

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def patch(self, request, pk):
        try:
            target_user = User.objects.get(
                id=pk
            )
        except User.DoesNotExist:
            return Response(
                {
                    "detail": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if target_user.id == request.user.id:
            return Response(
                {
                    "detail": (
                        "You cannot change your "
                        "own role."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(
            target_user,
            "customer_profile",
        ):
            return Response(
                {
                    "detail": (
                        "This user has a customer "
                        "profile and cannot be "
                        "converted to a staff role "
                        "here."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserRoleUpdateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_user = (
            AuthenticationService.update_user_role(
                user=target_user,
                role=serializer.validated_data[
                    "role"
                ],
            )
        )

        return Response(
            UserSerializer(updated_user).data,
            status=status.HTTP_200_OK,
        )