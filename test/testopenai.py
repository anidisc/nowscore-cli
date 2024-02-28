import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key="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"
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="gpt-3.5-turbo",
)