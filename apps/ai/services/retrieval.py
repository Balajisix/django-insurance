from ..embeddings.huggingface import HuggingFaceEmbeddingProvider
from ..models import DocumentChunk


class DocumentRetrievalService:
    DEFAULT_TOP_K = 5
    MAX_TOP_K = 20

    def __init__(self):
        self.embedding_provider = (
            HuggingFaceEmbeddingProvider()
        )

        from ..vectorstores.faiss_store import (
            FAISSVectorStore,
        )

        self.vector_store = FAISSVectorStore()

    def search(
        self,
        *,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        claim_id: int | None = None,
    ) -> list[dict]:

        query = query.strip()

        if not query:
            raise ValueError(
                "Search query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        top_k = min(
            top_k,
            self.MAX_TOP_K,
        )

        query_vector = (
            self.embedding_provider.embed_text(
                query
            )
        )

        # Retrieve more candidates than we
        # ultimately return because we may need
        # to filter them by claim.
        candidate_k = top_k

        if claim_id is not None:
            candidate_k = min(
                top_k * 5,
                self.vector_store.count(),
            )

        faiss_results = (
            self.vector_store.search(
                query_vector=query_vector,
                top_k=candidate_k,
            )
        )

        if not faiss_results:
            return []

        faiss_ids = [
            item["faiss_index_id"]
            for item in faiss_results
        ]

        chunks_query = (
            DocumentChunk.objects
            .select_related(
                "document",
                "document__claim",
            )
            .filter(
                faiss_index_id__in=faiss_ids
            )
        )

        if claim_id is not None:
            chunks_query = chunks_query.filter(
                document__claim_id=claim_id
            )

        chunks_by_faiss_id = {
            chunk.faiss_index_id: chunk
            for chunk in chunks_query
        }

        results = []

        for item in faiss_results:

            chunk = chunks_by_faiss_id.get(
                item["faiss_index_id"]
            )

            if chunk is None:
                continue

            results.append(
                {
                    "chunk_id": chunk.id,
                    "score": item["score"],
                    "document_id": (
                        chunk.document_id
                    ),
                    "document_name": (
                        chunk.document
                        .original_file_name
                    ),
                    "document_type": (
                        chunk.document
                        .document_type
                    ),
                    "claim_id": (
                        chunk.document.claim_id
                    ),
                    "chunk_index": (
                        chunk.chunk_index
                    ),
                    "text": chunk.text,
                }
            )

            if len(results) >= top_k:
                break

        return results


class RAGContextBuilder:
    """
    Converts retrieved chunks into a context block
    that can be passed to the LLM.
    """

    @staticmethod
    def build(
        results: list[dict],
    ) -> str:

        if not results:
            return ""

        sections = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            section = (
                f"[Source {index}]\n"
                f"Document: "
                f"{result['document_name']}\n"
                f"Document Type: "
                f"{result['document_type']}\n"
                f"Chunk Index: "
                f"{result['chunk_index']}\n"
                f"Similarity Score: "
                f"{result['score']:.4f}\n"
                f"Content:\n"
                f"{result['text']}"
            )

            sections.append(section)

        return "\n\n".join(sections)
