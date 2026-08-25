import requests

session_key = 9877

url = f"https://api.openf1.org/v1/weather?session_key={session_key}"

data = requests.get(url).json()

for item in data[:20]:
    print(
        "air:",
        item["air_temperature"],
        "- track:",
        item["track_temperature"],
        "- humidity:",
        item["humidity"],
        "- rainfall:",
        item["rainfall"],
        "- wind speed:",
        item["wind_speed"]
    )