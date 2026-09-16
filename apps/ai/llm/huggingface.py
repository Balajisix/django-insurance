from django.conf import settings
from huggingface_hub import InferenceClient


class HuggingFaceLLMProvider:
    """
    Generates responses using a Hugging Face-hosted
    chat-completion model.
    """

    MODEL_NAME = settings.HF_LLM_MODEL

    def __init__(self):
        token = settings.HF_API_TOKEN

        if not token:
            raise ValueError(
                "HF_API_TOKEN is not configured."
            )

        self.client = InferenceClient(
            api_key=token,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> str:

        if not system_prompt.strip():
            raise ValueError(
                "System prompt cannot be empty."
            )

        if not user_prompt.strip():
            raise ValueError(
                "User prompt cannot be empty."
            )

        response = (
            self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )
        )

        if not response.choices:
            raise ValueError(
                "LLM returned no choices."
            )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "LLM returned an empty response."
            )

        return content.strip()