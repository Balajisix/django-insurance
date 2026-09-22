import uuid

from django.conf import settings


def generate_document_s3_key(
    *,
    claim_number,
    original_file_name,
):
    unique_id = uuid.uuid4().hex

    return (
        f"claims/{claim_number}/documents/"
        f"{unique_id}/{original_file_name}"
    )