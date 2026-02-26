from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-4.1-mini",
    input="Сгенерируй короткое назидание в стиле Абая про труд."
)

print(response.output[0].content[0].text)