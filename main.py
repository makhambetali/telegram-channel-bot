import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from openai import OpenAI


load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

STATE_FILE = Path(os.getenv("STATE_FILE", "state.txt"))
TOTAL_WORDS = 45


def load_counter() -> int:
    """Return current word index (1..TOTAL_WORDS)."""
    if not STATE_FILE.exists():
        return 1
    try:
        n = int(STATE_FILE.read_text(encoding="utf-8").strip())
        if 1 <= n <= TOTAL_WORDS:
            return n
        return 1
    except Exception:
        return 1


def save_counter(n: int) -> None:
    STATE_FILE.write_text(str(n), encoding="utf-8")


def next_counter(n: int) -> int:
    return 1 if n >= TOTAL_WORDS else (n + 1)


def generate_abai_word(n: int) -> str:
    """
    Generate 'Слово назидания' style text.
    (Не цитируем дословно, а стилизуем и делаем компактно.)
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
Сгенерируй "Слово назидания" в духе Абая Кунанбаева, номер {n} из {TOTAL_WORDS}.
Тема: труд, честность, знания, дисциплина.
Формат:
- Заголовок: "Слово {n}"
- 4–7 коротких предложений
- Без дословных цитат из оригинального текста Абая
- Язык: русский
""".strip()

    resp = client.responses.create(
        model=MODEL,
        input=prompt,
        max_output_tokens=220,
    )

    return resp.output[0].content[0].text.strip()


async def send_to_channel(text: str) -> None:
    client = TelegramClient("session_name", API_ID, API_HASH)
    async with client:
        await client.send_message(CHANNEL_ID, text)


async def main():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан в .env")

    n = load_counter()
    text = generate_abai_word(n)

    await send_to_channel(text)

    save_counter(next_counter(n))


if __name__ == "__main__":
    asyncio.run(main())