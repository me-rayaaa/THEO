import requests

session_key = 9877

drivers = requests.get(
    f"https://api.openf1.org/v1/drivers?session_key={session_key}",
    timeout=30
).json()

positions = requests.get(
    f"https://api.openf1.org/v1/position?session_key={session_key}",
    timeout=30
).json()

drivers_by_number = {
    driver["driver_number"]: driver
    for driver in drivers
}

latest_positions = {}

for item in positions:
    latest_positions[item["driver_number"]] = item

sorted_positions = sorted(
    latest_positions.values(),
    key=lambda x: x["position"]
)

for item in sorted_positions:
    driver_number = item["driver_number"]
    driver = drivers_by_number[driver_number]

    print(
        item["position"],
        "-",
        driver["full_name"],
        "-",
        driver["team_name"]
    )