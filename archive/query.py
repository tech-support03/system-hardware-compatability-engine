from openai import OpenAI

# Point to LM Studio's local API instead of OpenAI's
client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",  # e.g. "mistral-7b-instruct-v0.2"
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "how do I print hello world in python"}
    ]
)

print(response.choices[0].message.content)

