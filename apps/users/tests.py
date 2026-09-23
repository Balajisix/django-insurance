from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.customers.models import Customer

from .models import UserRole

User = get_user_model()


class StaffUserManagementPermissionTests(APITestCase):
    """
    Verifies Stage 1: only Admin can list users, create staff
    accounts, or change a staff member's role. An admin cannot
    change their own role, and a user who already has a
    customer profile cannot be converted to a staff role
    through this endpoint.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Ana",
            last_name="Admin",
            role=UserRole.ADMIN,
        )

        self.officer = User.objects.create_user(
            email="officer@example.com",
            password="OfficerPass123!",
            first_name="Olivia",
            last_name="Officer",
            role=UserRole.CLAIMS_OFFICER,
        )

        self.customer_user = User.objects.create_user(
            email="customer@example.com",
            password="CustomerPass123!",
            first_name="Cara",
            last_name="Customer",
            role=UserRole.CUSTOMER,
        )

        Customer.objects.create(user=self.customer_user)

        self.staff_payload = {
            "email": "new.officer@example.com",
            "password": "NewOfficerPass123!",
            "password_confirm": "NewOfficerPass123!",
            "first_name": "Noah",
            "last_name": "Officer",
            "role": UserRole.CLAIMS_OFFICER,
        }

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_non_admin_cannot_list_users(self):
        self._auth_as(self.officer)

        response = self.client.get("/api/v1/auth/users/")

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_list_users(self):
        self._auth_as(self.admin)

        response = self.client.get("/api/v1/auth/users/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_non_admin_cannot_create_staff_user(self):
        self._auth_as(self.officer)

        response = self.client.post(
            "/api/v1/auth/users/create-staff/",
            data=self.staff_payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_can_create_staff_user(self):
        self._auth_as(self.admin)

        response = self.client.post(
            "/api/v1/auth/users/create-staff/",
            data=self.staff_payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        created_user = User.objects.get(
            email="new.officer@example.com"
        )
        self.assertEqual(
            created_user.role,
            UserRole.CLAIMS_OFFICER,
        )
        self.assertFalse(
            hasattr(created_user, "customer_profile")
        )

    def test_staff_creation_rejects_customer_role(self):
        self._auth_as(self.admin)

        payload = dict(self.staff_payload)
        payload["role"] = UserRole.CUSTOMER

        response = self.client.post(
            "/api/v1/auth/users/create-staff/",
            data=payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_admin_cannot_change_own_role(self):
        self._auth_as(self.admin)

        response = self.client.patch(
            f"/api/v1/auth/users/{self.admin.id}/role/",
            data={"role": UserRole.MANAGER},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_admin_can_change_other_staff_role(self):
        self._auth_as(self.admin)

        response = self.client.patch(
            f"/api/v1/auth/users/{self.officer.id}/role/",
            data={"role": UserRole.MANAGER},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.officer.refresh_from_db()
        self.assertEqual(self.officer.role, UserRole.MANAGER)

    def test_cannot_convert_a_customer_via_role_endpoint(self):
        self._auth_as(self.admin)

        response = self.client.patch(
            f"/api/v1/auth/users/{self.customer_user.id}/role/",
            data={"role": UserRole.CLAIMS_OFFICER},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
