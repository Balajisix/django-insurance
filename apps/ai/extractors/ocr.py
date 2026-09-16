from io import BytesIO

import pytesseract
from django.conf import settings
from django.core.files.storage import default_storage
from PIL import Image, ImageOps


class OCRExtractionError(Exception):
    """
    Raised when OCR processing fails.
    """

    pass


class TesseractOCRExtractor:
    """
    Extract text from images using local Tesseract OCR.

    Files are read through Django's storage abstraction,
    which means the same code works with our S3 backend.
    """

    def __init__(self):
        tesseract_cmd = getattr(
            settings,
            "TESSERACT_CMD",
            "",
        )

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = (
                tesseract_cmd
            )

    @staticmethod
    def _prepare_image(
        image: Image.Image,
    ) -> Image.Image:
        """
        Perform basic image preprocessing.
        """

        image = image.convert("L")

        image = ImageOps.autocontrast(image)

        return image

    def extract_from_storage(
        self,
        storage_key: str,
    ) -> str:
        """
        Read an image from configured Django storage
        and run OCR.
        """

        if not storage_key:
            raise OCRExtractionError(
                "Storage key cannot be empty."
            )

        if not default_storage.exists(storage_key):
            raise OCRExtractionError(
                f"Document not found in storage: "
                f"{storage_key}"
            )

        try:
            with default_storage.open(
                storage_key,
                "rb",
            ) as stored_file:
                file_bytes = stored_file.read()

        except Exception as exc:
            raise OCRExtractionError(
                f"Unable to read document from storage: "
                f"{exc}"
            ) from exc

        return self.extract_from_bytes(
            file_bytes
        )

    def extract_from_bytes(
        self,
        file_bytes: bytes,
    ) -> str:
        """
        Extract text from image bytes.
        """

        if not file_bytes:
            raise OCRExtractionError(
                "Image file is empty."
            )

        try:
            image = Image.open(
                BytesIO(file_bytes)
            )

            image = self._prepare_image(image)

            extracted_text = (
                pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--psm 6",
                )
            )

        except Exception as exc:
            raise OCRExtractionError(
                f"OCR processing failed: {exc}"
            ) from exc

        extracted_text = extracted_text.strip()

        if not extracted_text:
            raise OCRExtractionError(
                "OCR completed but no text was detected."
            )

        return extracted_text