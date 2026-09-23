from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyStatus, PolicyType
from apps.users.models import UserRole

from .models import Claim, ClaimStatus, ClaimType

User = get_user_model()


class ClaimRolePermissionTests(APITestCase):
    """
    Verifies Stage 1 role and ownership enforcement on the
    claim workflow and its read-only sub-resources.
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

        self.customer_b = Customer.objects.create(
            user=self.customer_b_user,
        )

        self.policy_a = Policy.objects.create(
            customer=self.customer_a,
            policy_type=PolicyType.MOTOR,
            status=PolicyStatus.ACTIVE,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            premium="12000.00",
        )

        self.claim_a = Claim.objects.create(
            policy=self.policy_a,
            claim_type=ClaimType.ACCIDENT,
            incident_date=date.today(),
            incident_description="Rear-end collision.",
            estimated_loss="50000.00",
        )

        # ACCIDENT claims get 3 document requirements
        # via ClaimService.submit_claim(); this bypasses
        # that service, so requirements are absent here on
        # purpose for tests that don't need them.

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_customer_cannot_call_workflow_action(self):
        self._auth_as(self.customer_a_user)

        response = self.client.post(
            f"/api/v1/claims/{self.claim_a.id}/start-processing/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.claim_a.refresh_from_db()
        self.assertEqual(
            self.claim_a.status,
            ClaimStatus.SUBMITTED,
        )

    def test_claims_officer_can_start_processing(self):
        self._auth_as(self.officer)

        response = self.client.post(
            f"/api/v1/claims/{self.claim_a.id}/start-processing/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.claim_a.refresh_from_db()
        self.assertEqual(
            self.claim_a.status,
            ClaimStatus.DOCUMENT_PROCESSING,
        )

    def test_customer_can_view_own_claim_events_after_transition(self):
        self._auth_as(self.officer)
        self.client.post(
            f"/api/v1/claims/{self.claim_a.id}/start-processing/"
        )

        self._auth_as(self.customer_a_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/events/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 1)

    def test_other_customer_cannot_view_claim_events(self):
        self._auth_as(self.officer)
        self.client.post(
            f"/api/v1/claims/{self.claim_a.id}/start-processing/"
        )

        self._auth_as(self.customer_b_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/events/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 0)

    def test_settlement_detail_404_instead_of_crashing(self):
        # No settlement exists yet for this claim; the view
        # must return a clean 404, not an unhandled exception.
        self._auth_as(self.customer_a_user)

        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/settlement/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_other_customer_cannot_view_requirements(self):
        from .models import ClaimDocumentRequirement

        ClaimDocumentRequirement.objects.create(
            claim=self.claim_a,
            document_type="ACCIDENT_PHOTO",
            description="Accident photographs",
            is_required=True,
        )

        self._auth_as(self.customer_b_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/requirements/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(len(response.data), 0)

        self._auth_as(self.customer_a_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/requirements/"
        )

        self.assertEqual(len(response.data), 1)
