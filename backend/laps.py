import requests

session_key = 9877

url = f"https://api.openf1.org/v1/laps?session_key={session_key}"

data = requests.get(url).json()

for lap in data[:20]:
    print(
        "driver:",
        lap["driver_number"],
        "- lap:",
        lap["lap_number"],
        "- time:",
        lap["lap_duration"]
    )