from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone

from apps.claims.models import (
    Claim,
    ClaimDocumentRequirement,
)
from apps.common.exceptions import ClaimNotFoundError

from .models import ClaimDocument
from .storage import generate_document_s3_key
from .validators import validate_uploaded_file


class DocumentService:
    """
    Business operations related to claim documents.
    """

    @staticmethod
    @transaction.atomic
    def upload_claim_document(
        *,
        claim_id,
        uploaded_by,
        document_type,
        uploaded_file,
    ) -> ClaimDocument:
        """
        Upload a claim document to S3 and create
        its metadata record in PostgreSQL.
        """

        try:
            claim = Claim.objects.get(
                id=claim_id
            )
        except Claim.DoesNotExist as exc:
            raise ClaimNotFoundError(
                "The specified claim does not exist."
            ) from exc

        validate_uploaded_file(
            uploaded_file
        )

        s3_key = generate_document_s3_key(
            claim_number=claim.claim_number,
            original_file_name=uploaded_file.name,
        )

        saved_key = default_storage.save(
            s3_key,
            ContentFile(
                uploaded_file.read()
            ),
        )

        document = ClaimDocument.objects.create(
            claim=claim,
            document_type=document_type,
            original_file_name=uploaded_file.name,
            s3_key=saved_key,
            content_type=(
                uploaded_file.content_type
                or "application/octet-stream"
            ),
            file_size=uploaded_file.size,
            uploaded_by=uploaded_by,
        )

        ClaimDocumentRequirement.objects.filter(
            claim=claim,
            document_type=document_type,
            is_fulfilled=False,
        ).update(
            is_fulfilled=True,
            fulfilled_at=timezone.now(),
        )

        return document

    @staticmethod
    @transaction.atomic
    def delete_document(
        *,
        document_id,
    ):
        """
        Delete the document from S3 and PostgreSQL.
        Re-open the document requirement if no documents
        of that type remain.
        """

        try:
            document = ClaimDocument.objects.get(
                id=document_id
            )
        except ClaimDocument.DoesNotExist:
            return

        claim_id = document.claim_id
        document_type = document.document_type

        default_storage.delete(
            document.s3_key
        )

        document.delete()

        remaining_documents = (
            ClaimDocument.objects.filter(
                claim_id=claim_id,
                document_type=document_type,
            ).exists()
        )

        if not remaining_documents:
            ClaimDocumentRequirement.objects.filter(
                claim_id=claim_id,
                document_type=document_type,
            ).update(
                is_fulfilled=False,
                fulfilled_at=None,
            )