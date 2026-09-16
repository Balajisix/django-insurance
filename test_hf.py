from django.conf import settings
from huggingface_hub import InferenceClient


client = InferenceClient(
    provider="hf-inference",
    api_key=settings.HF_API_TOKEN,
)

result = client.feature_extraction(
    text="The estimated repair cost is 185000 rupees.",
    model=settings.HF_EMBEDDING_MODEL,
    normalize=True,
)

print(type(result))
print(result)