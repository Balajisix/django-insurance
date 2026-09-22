from ..llm.huggingface import HuggingFaceLLMProvider
from ..prompts.rag import SYSTEM_PROMPT, build_user_prompt
from .retrieval import DocumentRetrievalService, RAGContextBuilder


class RAGService:
    """
    Retrieval-Augmented Generation service.
    """

    DEFAULT_TOP_K = 5
    MAX_TOP_K = 10

    def __init__(self):
        self.retrieval_service = (
            DocumentRetrievalService()
        )

        self.llm_provider = (
            HuggingFaceLLMProvider()
        )

    def answer(
        self,
        *,
        question: str,
        claim_id: int | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> dict:

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        top_k = min(
            top_k,
            self.MAX_TOP_K,
        )

        retrieved_results = (
            self.retrieval_service.search(
                query=question,
                top_k=top_k,
                claim_id=claim_id,
            )
        )

        if not retrieved_results:
            return {
                "answer": (
                    "I could not find enough relevant "
                    "information in the provided "
                    "documents to answer this question."
                ),
                "sources": [],
            }

        context = RAGContextBuilder.build(
            retrieved_results
        )

        user_prompt = build_user_prompt(
            question=question,
            context=context,
        )

        answer = self.llm_provider.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        sources = [
            {
                "chunk_id": result["chunk_id"],
                "document_id": result["document_id"],
                "document_name": result[
                    "document_name"
                ],
                "document_type": result[
                    "document_type"
                ],
                "chunk_index": result[
                    "chunk_index"
                ],
                "score": result["score"],
            }
            for result in retrieved_results
        ]

        return {
            "answer": answer,
            "sources": sources,
        }
