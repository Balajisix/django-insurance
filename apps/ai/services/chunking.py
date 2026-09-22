from django.db import transaction

from apps.documents.models import ClaimDocument

from ..chunkers.text import TextChunker
from ..models import DocumentChunk, DocumentExtraction


class DocumentChunkingService:
    """
    Creates chunks from a document's extracted text.
    """

    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_OVERLAP = 200

    @staticmethod
    @transaction.atomic
    def create_chunks(
        *,
        document_id: int,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> list[DocumentChunk]:

        document = (
            ClaimDocument.objects
            .filter(id=document_id)
            .first()
        )

        if document is None:
            raise ValueError(
                "Document not found."
            )

        extraction = (
            DocumentExtraction.objects
            .filter(document=document)
            .first()
        )

        if extraction is None:
            raise ValueError(
                "Document has no extracted text. "
                "Process the document before chunking."
            )

        chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=overlap,
        )

        chunk_data = chunker.split(
            extraction.extracted_text
        )

        if not chunk_data:
            raise ValueError(
                "Document extraction contains no text "
                "to chunk."
            )

        DocumentChunk.objects.filter(
            document=document
        ).delete()

        chunks = [
            DocumentChunk(
                document=document,
                chunk_index=item["chunk_index"],
                text=item["text"],
                character_count=len(
                    item["text"]
                ),
                start_character=item[
                    "start_character"
                ],
                end_character=item[
                    "end_character"
                ],
            )
            for item in chunk_data
        ]

        DocumentChunk.objects.bulk_create(
            chunks
        )

        return list(
            DocumentChunk.objects.filter(
                document=document
            ).order_by("chunk_index")
        )
