from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.users.models import UserRole

from .models import Customer

User = get_user_model()


class CustomerRolePermissionTests(APITestCase):
    """
    Verifies Stage 1: a customer sees only their own profile
    and cannot self-service create a customer record (that
    happens through /auth/register/); staff manage profiles
    for existing users.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="AdminPass123!",
            first_name="Ana",
            last_name="Admin",
            role=UserRole.ADMIN,
        )

        self.customer_a_user = User.objects.create_user(
            email="customer.a@example.com",
            password="CustomerPass123!",
            first_name="Alice",
            last_name="A",
            role=UserRole.CUSTOMER,
        )

        self.customer_a = Customer.objects.create(
            user=self.customer_a_user,
        )

        self.customer_b_user = User.objects.create_user(
            email="customer.b@example.com",
            password="CustomerPass123!",
            first_name="Bob",
            last_name="B",
            role=UserRole.CUSTOMER,
        )

        self.customer_b = Customer.objects.create(
            user=self.customer_b_user,
        )

        # A plain user with no customer profile yet, for the
        # staff-creates-a-profile flow.
        self.new_user = User.objects.create_user(
            email="new.customer@example.com",
            password="NewCustomerPass123!",
            first_name="Nora",
            last_name="New",
            role=UserRole.CUSTOMER,
        )

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_customer_sees_only_self_in_list(self):
        self._auth_as(self.customer_a_user)

        response = self.client.get("/api/v1/customers/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["id"],
            self.customer_a.id,
        )

    def test_customer_cannot_view_other_customer_detail(self):
        self._auth_as(self.customer_a_user)

        response = self.client.get(
            f"/api/v1/customers/{self.customer_b.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_cannot_create_customer_profile(self):
        self._auth_as(self.customer_a_user)

        response = self.client.post(
            "/api/v1/customers/",
            data={"user_id": self.new_user.id},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_can_create_customer_profile(self):
        self._auth_as(self.admin)

        response = self.client.post(
            "/api/v1/customers/",
            data={"user_id": self.new_user.id},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            Customer.objects.filter(
                user=self.new_user
            ).exists()
        )
