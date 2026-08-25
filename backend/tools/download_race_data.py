import requests
import json
import os

session_key = 9877

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

folder = "../data/mexico_2025"

os.makedirs(folder, exist_ok=True)

for endpoint in endpoints:
    url = f"https://api.openf1.org/v1/{endpoint}?session_key={session_key}"

    response = requests.get(url)
    data = response.json()

    file_path = f"{folder}/{endpoint}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"{endpoint}: saved")

print("Done")