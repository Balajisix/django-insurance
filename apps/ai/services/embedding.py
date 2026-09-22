from django.utils import timezone

from ..embeddings.huggingface import HuggingFaceEmbeddingProvider
from ..models import DocumentChunk


class DocumentEmbeddingService:
    """
    Generates embeddings using Hugging Face and
    stores them in FAISS.
    """

    def __init__(self):
        self.provider = (
            HuggingFaceEmbeddingProvider()
        )

    def embed_document(
        self,
        *,
        document_id: int,
    ) -> list[DocumentChunk]:

        chunks = list(
            DocumentChunk.objects
            .filter(
                document_id=document_id
            )
            .order_by("chunk_index")
        )

        if not chunks:
            raise ValueError(
                "No chunks found for this document."
            )

        texts = [
            chunk.text
            for chunk in chunks
        ]

        vectors = self.provider.embed_many(
            texts
        )

        if len(vectors) != len(chunks):
            raise ValueError(
                "Embedding response count does not "
                "match chunk count."
            )

        from ..vectorstores.faiss_store import (
            FAISSVectorStore,
        )

        vector_store = FAISSVectorStore()

        faiss_ids = [
            chunk.id
            for chunk in chunks
        ]

        vector_store.add_vectors(
            vectors=vectors,
            ids=faiss_ids,
        )

        now = timezone.now()

        for chunk in chunks:
            chunk.embedding_model = (
                self.provider.MODEL_NAME
            )
            chunk.embedded_at = now
            chunk.faiss_index_id = chunk.id

        DocumentChunk.objects.bulk_update(
            chunks,
            [
                "embedding_model",
                "embedded_at",
                "faiss_index_id",
                "updated_at",
            ],
        )

        return chunks
