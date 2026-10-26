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

stints = requests.get(
    f"https://api.openf1.org/v1/stints?session_key={session_key}",
    timeout=30
).json()

drivers_by_number = {
    driver["driver_number"]: driver
    for driver in drivers
}

latest_positions = {}
for item in positions:
    latest_positions[item["driver_number"]] = item

latest_stints = {}
for stint in stints:
    driver_number = stint["driver_number"]

    if (
        driver_number not in latest_stints
        or stint["stint_number"] > latest_stints[driver_number]["stint_number"]
    ):
        latest_stints[driver_number] = stint

sorted_positions = sorted(
    latest_positions.values(),
    key=lambda x: x["position"]
)

for item in sorted_positions:
    driver_number = item["driver_number"]
    driver = drivers_by_number[driver_number]

    stint = latest_stints.get(driver_number)

    if stint:
        compound = stint["compound"]
        tyre_age = stint["tyre_age_at_start"] + (
            stint["lap_end"] - stint["lap_start"] + 1
        )
    else:
        compound = "UNKNOWN"
        tyre_age = "-"

    print(
        item["position"],
        "-",
        driver["full_name"],
        "-",
        driver["team_name"],
        "-",
        compound,
        "- tyre age:",
        tyre_age
    )