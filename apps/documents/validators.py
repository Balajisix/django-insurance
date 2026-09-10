from pathlib import Path

from rest_framework.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}

ALLOWED_CONTENT_TYPES = {
    ".pdf": {
        "application/pdf",
        "application/octet-stream",
    },
    ".jpg": {
        "image/jpeg",
        "application/octet-stream",
    },
    ".jpeg": {
        "image/jpeg",
        "application/octet-stream",
    },
    ".png": {
        "image/png",
        "application/octet-stream",
    },
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_uploaded_file(uploaded_file):
    if uploaded_file is None:
        raise ValidationError(
            {
                "file": [
                    "A document file must be provided."
                ]
            }
        )

    file_name = uploaded_file.name or ""

    extension = Path(
        file_name
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            {
                "file": [
                    "Only PDF, JPEG and PNG files are supported."
                ]
            }
        )

    if uploaded_file.size == 0:
        raise ValidationError(
            {
                "file": [
                    "The uploaded file is empty."
                ]
            }
        )

    if uploaded_file.size > MAX_FILE_SIZE:
        raise ValidationError(
            {
                "file": [
                    "The uploaded file must not exceed 10 MB."
                ]
            }
        )

    content_type = getattr(
        uploaded_file,
        "content_type",
        None,
    )

    accepted_content_types = ALLOWED_CONTENT_TYPES[
        extension
    ]

    if content_type not in accepted_content_types:
        raise ValidationError(
            {
                "file": [
                    (
                        "The uploaded file has an unsupported "
                        f"content type: {content_type or 'unknown'}."
                    )
                ]
            }
        )

    _validate_file_signature(
        uploaded_file=uploaded_file,
        extension=extension,
    )


def _validate_file_signature(
    *,
    uploaded_file,
    extension,
):
    """
    Validate the actual file header instead of relying only
    on the extension and client-provided content type.
    """

    uploaded_file.seek(0)

    signature = uploaded_file.read(12)

    uploaded_file.seek(0)

    if extension == ".pdf":
        if not signature.startswith(b"%PDF-"):
            raise ValidationError(
                {
                    "file": [
                        "The uploaded file is not a valid PDF."
                    ]
                }
            )

    elif extension in {".jpg", ".jpeg"}:
        if not signature.startswith(b"\xff\xd8\xff"):
            raise ValidationError(
                {
                    "file": [
                        "The uploaded file is not a valid JPEG image."
                    ]
                }
            )

    elif extension == ".png":
        png_signature = b"\x89PNG\r\n\x1a\n"

        if not signature.startswith(png_signature):
            raise ValidationError(
                {
                    "file": [
                        "The uploaded file is not a valid PNG image."
                    ]
                }
            )