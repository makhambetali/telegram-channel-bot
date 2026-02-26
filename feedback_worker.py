import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient, functions

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

async def reacted_by_me(client: TelegramClient, msg_id: int, emoticon: str, my_id: int) -> bool:
    res = await client(functions.messages.GetMessageReactionsListRequest(
        peer=CHANNEL_ID,
        id=msg_id,
        reaction=emoticon,
        offset=0,
        limit=100
    ))
    return any(u.id == my_id for u in res.users)

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
        me = await tg.get_me()
        my_id = me.id

        is_up = await reacted_by_me(tg, msg_id, UP, my_id)
        is_down = await reacted_by_me(tg, msg_id, DOWN, my_id)

    if is_up and is_down:
        print("Стоят обе реакции — оставь одну")
        return
    if not is_up and not is_down:
        print("Реакции от тебя нет — taste не меняем")
        return

    state["taste"] = apply_feedback(state["taste"], up=is_up)
    state["last_post"]["feedback_applied"] = True
    save_state(state)

    print("Applied:", "UP" if is_up else "DOWN", state["taste"])

if __name__ == "__main__":
    asyncio.run(main())