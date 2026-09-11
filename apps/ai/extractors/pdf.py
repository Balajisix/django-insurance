from io import BytesIO

from django.core.files.storage import default_storage
from pypdf import PdfReader


class PDFTextExtractor:
    @staticmethod
    def extract_from_storage(storage_key: str) -> str:
        if not storage_key:
            raise ValueError("Document storage key cannot be empty.")

        if not default_storage.exists(storage_key):
            raise FileNotFoundError(
                f"Document not found in storage: {storage_key}"
            )

        with default_storage.open(storage_key, "rb") as stored_file:
            file_bytes = stored_file.read()

        return PDFTextExtractor.extract_from_bytes(file_bytes)

    @staticmethod
    def extract_from_bytes(file_bytes: bytes) -> str:
        """
        Extract text from PDF bytes.
        """

        if not file_bytes:
            raise ValueError("PDF file is empty.")

        pdf_stream = BytesIO(file_bytes)

        reader = PdfReader(pdf_stream)

        extracted_pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()

            if page_text:
                page_text = page_text.strip()

            if page_text:
                extracted_pages.append(
                    f"[Page {page_number}]\n{page_text}"
                )

        extracted_text = "\n\n".join(extracted_pages).strip()

        if not extracted_text:
            raise ValueError(
                "No text could be extracted from the PDF. "
                "The document may be scanned or image-only."
            )

        return extracted_text