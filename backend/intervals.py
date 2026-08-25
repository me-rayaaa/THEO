import requests

session_key = 9877

url = f"https://api.openf1.org/v1/intervals?session_key={session_key}"

data = requests.get(url).json()

for item in data[:20]:
    print(
        "driver:",
        item["driver_number"],
        "- gap to leader:",
        item["gap_to_leader"],
        "- interval:",
        item["interval"]
    )