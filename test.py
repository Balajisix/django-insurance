from huggingface_hub import InferenceClient

client = InferenceClient(
    api_key="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"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {
            "role": "user",
            "content": "hello"
        }
    ]
)

print(response)