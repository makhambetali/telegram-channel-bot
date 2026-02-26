import os
import json
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

STATE_PATH = Path(os.getenv("STATE_FILE", "state.json"))
ABAI_PATH = Path(os.getenv("ABAI_FILE", "abai_words.json"))

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_abai_words() -> list[str]:
    return json.loads(ABAI_PATH.read_text(encoding="utf-8"))

def build_prompt(day: int, taste: dict) -> str:
    profile = """
Адресат:
- амбициозный, требовательный к себе
- ценит дисциплину, знания, силу характера
- не любит посредственность и самообман
- предпочитает прямой, иногда жесткий тон
- не терпит банальностей и "сладкой мотивации"
""".strip()

    controls = f"""
Параметры стиля (0..1):
- harshness: {taste["harshness"]:.2f}
- depth: {taste["depth"]:.2f}
- provocation: {taste["provocation"]:.2f}
- length: {taste["length"]:.2f}

Правила:
- harshness>0.70: тон строже
- depth>0.75: добавь философский слой
- provocation>0.60: добавь вызов/контраст без оскорблений
- length: 0=очень коротко, 1=чуть длиннее
""".strip()

    task = f"""
Сгенерируй "Слово {day}" в духе назиданий Абая (НЕ цитируй дословно оригинал).
Формат:
- Заголовок: "Слово {day}"
- 4–8 предложений (если length>0.6 можно 9–10)
- Тема: дисциплина, труд, честность, знание, ответственность
- В конце отдельной строкой: #aigenerated
Язык: русский.
""".strip()

    return "\n\n".join([profile, controls, task])

def generate_ai_text(prompt: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.responses.create(
        model=MODEL,
        input=prompt,
        max_output_tokens=260,
    )
    text = resp.output[0].content[0].text.strip()
    if "#aigenerated" not in text:
        text += "\n#aigenerated"
    return text

def format_original(text: str) -> str:
    # Отличаем от твоих постов: ставим тег оригинала
    text = text.strip()
    if "#abai" not in text.splitlines()[-1]:
        text += "\n#abai"
    return text

async def main():
    state = load_json(STATE_PATH)
    phase = int(state.get("phase", 1))
    day = int(state.get("day", 1))
    total = int(state.get("total_days", 45))

    if phase == 1:
        words = load_abai_words()
        if len(words) < total:
            raise RuntimeError("abai_words.json должен содержать 45 элементов")
        text = format_original(words[day - 1])
    else:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY не задан в .env")
        prompt = build_prompt(day, state["taste"])
        text = generate_ai_text(prompt)

    tg = TelegramClient("session_name", API_ID, API_HASH)
    async with tg:
        msg = await tg.send_message(CHANNEL_ID, text)

    # сохраняем message_id для последующей оценки
    state["last_post"]["message_id"] = msg.id
    state["last_post"]["feedback_applied"] = False

    # двигаем day/phase
    if phase == 1:
        if day >= total:
            state["phase"] = 2
            state["day"] = 1
        else:
            state["day"] = day + 1
    else:
        state["day"] = day + 1

    save_json(STATE_PATH, state)

if __name__ == "__main__":
    asyncio.run(main())