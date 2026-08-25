import requests

session_key = 9877

url = f"https://api.openf1.org/v1/pit?session_key={session_key}"

data = requests.get(url).json()

for pit in data:
    print(
        "driver:",
        pit["driver_number"],
        "- lap:",
        pit["lap_number"],
        "- pit duration:",
        pit["pit_duration"]
    )