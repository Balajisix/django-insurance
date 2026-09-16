from django.conf import settings
from huggingface_hub import InferenceClient


class HuggingFaceEmbeddingProvider:
    """
    Generates text embeddings using Hugging Face
    hosted inference.
    """

    MODEL_NAME = settings.HF_EMBEDDING_MODEL

    def __init__(self):
        token = settings.HF_API_TOKEN

        if not token:
            raise ValueError(
                "HF_API_TOKEN is not configured."
            )

        self.client = InferenceClient(
            provider="hf-inference",
            api_key=token,
        )

    def embed_text(
        self,
        text: str,
    ) -> list[float]:

        if not text or not text.strip():
            raise ValueError(
                "Text cannot be empty."
            )

        result = self.client.feature_extraction(
            text=text,
            model=self.MODEL_NAME,
            normalize=True,
        )

        return self._convert_result(result)

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        if any(
            not text or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "Embedding input contains empty text."
            )

        result = self.client.feature_extraction(
            text=texts,
            model=self.MODEL_NAME,
            normalize=True,
        )

        return self._convert_batch_result(result)

    @staticmethod
    def _convert_result(result) -> list[float]:
        """
        Convert Hugging Face output into a flat
        Python list.
        """

        if hasattr(result, "tolist"):
            result = result.tolist()

        while (
            isinstance(result, list)
            and len(result) == 1
            and isinstance(result[0], list)
        ):
            result = result[0]

        if not isinstance(result, list):
            raise ValueError(
                "Unexpected embedding response."
            )

        return [
            float(value)
            for value in result
        ]

    @staticmethod
    def _convert_batch_result(result):
        """
        Convert a batch embedding response into
        list[list[float]].
        """

        if hasattr(result, "tolist"):
            result = result.tolist()

        if not isinstance(result, list):
            raise ValueError(
                "Unexpected batch embedding response."
            )

        return [
            [
                float(value)
                for value in embedding
            ]
            for embedding in result
        ]