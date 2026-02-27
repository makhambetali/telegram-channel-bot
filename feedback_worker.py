import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import ReactionEmoji

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
STATE_PATH = Path(os.getenv("STATE_FILE", "state.json"))

UP = "👍"
DOWN = "👎"


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def get_reaction_count(msg, emoticon: str) -> int:
    """
    Возвращает количество реакций (счётчик) для emoji на конкретном сообщении.
    Работает в каналах.
    """
    r = getattr(msg, "reactions", None)
    if not r or not getattr(r, "results", None):
        return 0

    for item in r.results:
        # item.reaction может быть ReactionEmoji / ReactionCustomEmoji и т.д.
        reaction = getattr(item, "reaction", None)
        if isinstance(reaction, ReactionEmoji) and reaction.emoticon == emoticon:
            return int(getattr(item, "count", 0) or 0)
    return 0


def apply_feedback(taste: dict, up: bool) -> dict:
    if up:
        taste["harshness"] = clamp(taste["harshness"] + 0.05)
        taste["depth"] = clamp(taste["depth"] + 0.03)
        taste["provocation"] = clamp(taste["provocation"] + 0.05)
        taste["length"] = clamp(taste["length"] + 0.02)
    else:
        taste["harshness"] = clamp(taste["harshness"] - 0.07)
        taste["depth"] = clamp(taste["depth"] - 0.03)
        taste["provocation"] = clamp(taste["provocation"] - 0.05)
        taste["length"] = clamp(taste["length"] - 0.03)
    return taste


async def main():
    state = load_state()
    last = state.get("last_post", {})
    msg_id = last.get("message_id")

    if not msg_id:
        print("Нет message_id — нечего оценивать")
        return

    if last.get("feedback_applied"):
        print("Feedback уже применён")
        return

    tg = TelegramClient("session_name", API_ID, API_HASH)
    async with tg:
        msg = await tg.get_messages(CHANNEL_ID, ids=msg_id)

    if not msg:
        print("Сообщение не найдено (возможно удалено?)")
        return

    up_count = get_reaction_count(msg, UP)
    down_count = get_reaction_count(msg, DOWN)

    if up_count > 0 and down_count > 0:
        print("На сообщении стоят и 👍 и 👎 — оставь одну реакцию")
        return

    if up_count == 0 and down_count == 0:
        print("Реакции нет — taste не меняем")
        return

    is_up = up_count > 0
    state["taste"] = apply_feedback(state["taste"], up=is_up)
    state["last_post"]["feedback_applied"] = True
    save_state(state)

    print("Applied:", "UP" if is_up else "DOWN", state["taste"])


if __name__ == "__main__":
    asyncio.run(main())