from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    RegistrationResponseSerializer,
    RegisterSerializer,
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