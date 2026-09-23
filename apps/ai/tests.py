from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.claims.models import Claim, ClaimType
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyStatus, PolicyType
from apps.users.models import UserRole

User = get_user_model()


class AIEndpointRolePermissionTests(APITestCase):
    """
    Verifies Stage 1 role enforcement on the AI endpoints:
    staff only (CLAIMS_OFFICER / MANAGER / ADMIN), customers
    blocked entirely.

    Only endpoints that do pure DB reads (no LLM/embedding/
    S3 calls) are exercised here, so this suite runs offline.
    """

    def setUp(self):
        self.officer = User.objects.create_user(
            email="officer@example.com",
            password="OfficerPass123!",
            first_name="Olivia",
            last_name="Officer",
            role=UserRole.CLAIMS_OFFICER,
        )

        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="ManagerPass123!",
            first_name="Mona",
            last_name="Manager",
            role=UserRole.MANAGER,
        )

        self.customer_user = User.objects.create_user(
            email="customer@example.com",
            password="CustomerPass123!",
            first_name="Cara",
            last_name="Customer",
            role=UserRole.CUSTOMER,
        )

        self.customer = Customer.objects.create(
            user=self.customer_user,
        )

        self.policy = Policy.objects.create(
            customer=self.customer,
            policy_type=PolicyType.MOTOR,
            status=PolicyStatus.ACTIVE,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            premium="12000.00",
        )

        self.claim = Claim.objects.create(
            policy=self.policy,
            claim_type=ClaimType.ACCIDENT,
            incident_date=date.today(),
            incident_description="Rear-end collision.",
            estimated_loss="50000.00",
        )

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_customer_cannot_access_unified_intelligence(self):
        self._auth_as(self.customer_user)

        response = self.client.get(
            f"/api/v1/ai/claims/{self.claim.id}/intelligence/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_claims_officer_can_access_unified_intelligence(self):
        self._auth_as(self.officer)

        response = self.client.get(
            f"/api/v1/ai/claims/{self.claim.id}/intelligence/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["claim_id"],
            self.claim.id,
        )

    def test_manager_can_access_missing_documents(self):
        self._auth_as(self.manager)

        response = self.client.get(
            f"/api/v1/ai/claims/{self.claim.id}/missing-documents/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_customer_cannot_trigger_ai_workflow(self):
        self._auth_as(self.customer_user)

        response = self.client.post(
            f"/api/v1/ai/claims/{self.claim.id}/process/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(
            f"/api/v1/ai/claims/{self.claim.id}/intelligence/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
