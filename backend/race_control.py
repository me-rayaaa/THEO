import requests

session_key = 9877

url = f"https://api.openf1.org/v1/race_control?session_key={session_key}"

data = requests.get(url).json()

for item in data:
    print(
        "lap:",
        item["lap_number"],
        "- category:",
        item["category"],
        "- message:",
        item["message"]
    )