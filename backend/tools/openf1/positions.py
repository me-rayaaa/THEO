import requests

url = "https://api.openf1.org/v1/position?session_key=9877"

response = requests.get(url, timeout=30)
data = response.json()

latest_positions = {}

for item in data:
    driver_number = item["driver_number"]
    latest_positions[driver_number] = item

sorted_positions = sorted(
    latest_positions.values(),
    key=lambda x: x["position"]
)

for item in sorted_positions:
    print(
        item["position"],
        "- driver:",
        item["driver_number"]
    )