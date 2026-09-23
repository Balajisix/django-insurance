from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.users.models import UserRole

from .models import Policy, PolicyStatus, PolicyType

User = get_user_model()


class PolicyRolePermissionTests(APITestCase):
    """
    Verifies Stage 1: issuing a policy or adding coverage is
    a staff-only (underwriting) action; customers may only
    view their own policies.
    """

    def setUp(self):
        self.officer = User.objects.create_user(
            email="officer@example.com",
            password="OfficerPass123!",
            first_name="Olivia",
            last_name="Officer",
            role=UserRole.CLAIMS_OFFICER,
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

        Customer.objects.create(user=self.customer_b_user)

        self.policy_payload = {
            "customer_id": self.customer_a.id,
            "policy_type": PolicyType.MOTOR,
            "start_date": str(date.today() + timedelta(days=1)),
            "end_date": str(date.today() + timedelta(days=365)),
            "premium": "15000.00",
        }

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_customer_cannot_create_policy(self):
        self._auth_as(self.customer_a_user)

        response = self.client.post(
            "/api/v1/policies/",
            data=self.policy_payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(Policy.objects.count(), 0)

    def test_claims_officer_can_create_policy(self):
        self._auth_as(self.officer)

        response = self.client.post(
            "/api/v1/policies/",
            data=self.policy_payload,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(Policy.objects.count(), 1)

    def test_customer_cannot_add_coverage(self):
        self._auth_as(self.officer)
        create_response = self.client.post(
            "/api/v1/policies/",
            data=self.policy_payload,
        )
        policy_id = create_response.data["id"]

        self._auth_as(self.customer_a_user)
        response = self.client.post(
            f"/api/v1/policies/{policy_id}/coverages/",
            data={
                "coverage_code": "TERM_LIFE",
                "name": "Term Life",
                "coverage_limit": "1000000",
                "deductible": "20000",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_customer_sees_only_own_policies(self):
        self._auth_as(self.officer)
        self.client.post(
            "/api/v1/policies/",
            data=self.policy_payload,
        )

        self._auth_as(self.customer_a_user)
        response = self.client.get("/api/v1/policies/")
        self.assertEqual(len(response.data["results"]) if "results" in response.data else len(response.data), 1)

        self._auth_as(self.customer_b_user)
        response = self.client.get("/api/v1/policies/")
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)
