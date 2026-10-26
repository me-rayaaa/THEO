import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_store import DATA_DIR, SESSION_KEY  # noqa: E402

endpoints = [
    "drivers",
    "position",
    "stints",
    "laps",
    "pit",
    "intervals",
    "weather",
    "race_control"
]

DATA_DIR.mkdir(parents=True, exist_ok=True)

for endpoint in endpoints:
    url = f"https://api.openf1.org/v1/{endpoint}?session_key={SESSION_KEY}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Ошибка API приходит словарём, а не списком: такой ответ не сохраняем.
    if not isinstance(data, list) or not data:
        raise ValueError(f"{endpoint}: unexpected response {str(data)[:200]}")

    file_path = DATA_DIR / f"{endpoint}.json"
    temp_path = file_path.with_suffix(".json.tmp")

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    # Старый файл заменяется только целиком записанным новым.
    temp_path.replace(file_path)

    print(f"{endpoint}: saved {len(data)} records")

print("Done")
