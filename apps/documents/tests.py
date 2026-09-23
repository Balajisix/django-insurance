from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.claims.models import Claim, ClaimType
from apps.customers.models import Customer
from apps.policies.models import Policy, PolicyStatus, PolicyType
from apps.users.models import UserRole

from .models import ClaimDocument, DocumentStatus, DocumentType

User = get_user_model()


class DocumentOwnershipPermissionTests(APITestCase):
    """
    Verifies Stage 1 ownership enforcement on claim documents.

    These tests deliberately avoid the real upload path
    (DocumentService.upload_claim_document), which writes to
    S3, by seeding ClaimDocument rows directly through the ORM
    and only exercising the permission-denied branches that
    return before any storage call is made.
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

        self.document_a = ClaimDocument.objects.create(
            claim=self.claim_a,
            document_type=DocumentType.ACCIDENT_PHOTO,
            original_file_name="damage.jpg",
            s3_key="claims/TEST/documents/fake/damage.jpg",
            content_type="image/jpeg",
            file_size=1024,
            status=DocumentStatus.UPLOADED,
            uploaded_by=self.customer_a_user,
        )

    def _auth_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_customer_cannot_upload_to_others_claim(self):
        self._auth_as(self.customer_b_user)

        response = self.client.post(
            f"/api/v1/claims/{self.claim_a.id}/documents/",
            data={},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_owner_sees_document_non_owner_does_not(self):
        self._auth_as(self.customer_a_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/documents/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        self._auth_as(self.customer_b_user)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/documents/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_staff_sees_any_claims_documents(self):
        self._auth_as(self.officer)
        response = self.client.get(
            f"/api/v1/claims/{self.claim_a.id}/documents/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_non_owner_gets_404_on_document_detail(self):
        self._auth_as(self.customer_b_user)

        response = self.client.get(
            f"/api/v1/documents/{self.document_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_non_owner_cannot_delete_document(self):
        # perform_destroy() would call default_storage.delete()
        # (a real S3 call); a non-owner must be rejected by
        # get_object() before perform_destroy() is ever reached.
        self._auth_as(self.customer_b_user)

        response = self.client.delete(
            f"/api/v1/documents/{self.document_a.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertTrue(
            ClaimDocument.objects.filter(
                id=self.document_a.id
            ).exists()
        )
