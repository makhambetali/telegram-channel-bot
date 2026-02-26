import os
import re
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

ABAI_FILE = Path(os.getenv("ABAI_FILE", "abai_words.json"))

SOURCE_URL = "https://www.gov.kz/memleket/entities/mfa-kuveyt/press/article/details/16598?lang=ru"

ORDINALS = [
    "Первое","Второе","Третье","Четвёртое","Пятое","Шестое","Седьмое","Восьмое","Девятое","Десятое",
    "Одиннадцатое","Двенадцатое","Тринадцатое","Четырнадцатое","Пятнадцатое",
    "Шестнадцатое","Семнадцатое","Восемнадцатое","Девятнадцатое","Двадцатое",
    "Двадцать первое","Двадцать второе","Двадцать третье","Двадцать Четвертое","Двадцать пятое",
    "Двадцать шестое","Двадцать седьмое","Двадцать восьмое","Двадцать девятое","Тридцатое",
    "Тридцать первое","Тридцать второе","Тридцать третье","Тридцать Четвертое","Тридцать пятое",
    "Тридцать шестое","Тридцать седьмое","Тридцать восьмое","Тридцать девятое","Сороковое",
    "Сорок первое","Сорок второе","Сорок третье","Сорок Четвертое","Сорок пятое"
]

def normalize(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def main():
    html = requests.get(SOURCE_URL, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")
    text = normalize(text)

    words = []

    for i, ord_name in enumerate(ORDINALS):
        pattern = rf"Слово\s+{ord_name}.*?(?=Слово\s+|$)"
        match = re.search(pattern, text, flags=re.S | re.I)

        if not match:
            raise RuntimeError(f"Не найдено: Слово {ord_name}")

        chunk = match.group(0).strip()
        words.append(chunk)

    if len(words) != 45:
        raise RuntimeError(f"Ожидалось 45, найдено {len(words)}")

    ABAI_FILE.write_text(
        json.dumps(words, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("OK: создан abai_words.json (45 слов)")

if __name__ == "__main__":
    main()