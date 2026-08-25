import json

drivers_file = "../data/mexico_2025/drivers.json"
positions_file = "../data/mexico_2025/position.json"
intervals_file = "../data/mexico_2025/intervals.json"
stints_file = "../data/mexico_2025/stints.json"
pit_file = "../data/mexico_2025/pit.json"
laps_file = "../data/mexico_2025/laps.json"
race_control_file = "../data/mexico_2025/race_control.json"

with open(drivers_file, "r", encoding="utf-8") as file:
    drivers = json.load(file)

with open(positions_file, "r", encoding="utf-8") as file:
    positions = json.load(file)

with open(intervals_file, "r", encoding="utf-8") as file:
    intervals = json.load(file)

with open(stints_file, "r", encoding="utf-8") as file:
    stints = json.load(file)

with open(pit_file, "r", encoding="utf-8") as file:
    pits = json.load(file)

with open(laps_file, "r", encoding="utf-8") as file:
    laps = json.load(file)

with open(race_control_file, "r", encoding="utf-8") as file:
    race_control = json.load(file)

drivers_by_number = {
    driver["driver_number"]: driver
    for driver in drivers
}

latest_positions = {}

for item in positions:
    latest_positions[item["driver_number"]] = item

latest_intervals = {}

for item in intervals:
    driver_number = item["driver_number"]

    if item["gap_to_leader"] is not None:
        latest_intervals[driver_number] = item

latest_stints = {}

for stint in stints:
    driver_number = stint["driver_number"]

    if (
        driver_number not in latest_stints
        or stint["stint_number"] > latest_stints[driver_number]["stint_number"]
    ):
        latest_stints[driver_number] = stint

pit_counts = {}

for pit in pits:
    driver_number = pit["driver_number"]
    pit_counts[driver_number] = pit_counts.get(driver_number, 0) + 1

invalid_race_control_laps = set()

for event in race_control:
    lap_number = event["lap_number"]

    if lap_number is None:
        continue

    message = event["message"].upper()
    category = event["category"]

    if (
        category == "SafetyCar"
        or "YELLOW" in message
        or "DOUBLE YELLOW" in message
        or "VIRTUAL SAFETY CAR" in message
    ):
        invalid_race_control_laps.add(lap_number)

pit_affected_laps = set()

for pit in pits:
    driver_number = pit["driver_number"]
    lap_number = pit["lap_number"]

    pit_affected_laps.add((driver_number, lap_number))
    pit_affected_laps.add((driver_number, lap_number + 1))

clean_laps = []

for lap in laps:
    if lap["lap_number"] == 1:
        continue

    if lap["lap_duration"] is None:
        continue

    if lap["lap_duration"] <= 0:
        continue

    if lap["lap_number"] in invalid_race_control_laps:
        continue

    if (
        lap["driver_number"],
        lap["lap_number"]
    ) in pit_affected_laps:
        continue

    clean_laps.append(lap)

latest_clean_laps = {}

for lap in clean_laps:
    driver_number = lap["driver_number"]

    if (
        driver_number not in latest_clean_laps
        or lap["lap_number"] > latest_clean_laps[driver_number]["lap_number"]
    ):
        latest_clean_laps[driver_number] = lap

driver_data = {}

for driver_number, position in latest_positions.items():
    driver = drivers_by_number[driver_number]

    interval = latest_intervals.get(driver_number)
    stint = latest_stints.get(driver_number)
    clean_lap = latest_clean_laps.get(driver_number)

    gap = None

    if interval:
        gap = interval["gap_to_leader"]

    compound = "UNKNOWN"
    tyre_age = None

    if stint:
        compound = stint["compound"]

        if stint["lap_end"] is not None:
            tyre_age = stint["tyre_age_at_start"] + (
                stint["lap_end"] - stint["lap_start"] + 1
            )

    pit_stops = pit_counts.get(driver_number, 0)

    last_clean_lap = None

    if clean_lap:
        last_clean_lap = clean_lap["lap_duration"]

    driver_data[driver_number] = {
        "name": driver["full_name"],
        "team": driver["team_name"],
        "position": position["position"],
        "gap": gap,
        "compound": compound,
        "tyre_age": tyre_age,
        "pit_stops": pit_stops,
        "last_clean_lap": last_clean_lap
    }

sorted_drivers = sorted(
    driver_data.values(),
    key=lambda x: x["position"]
)

if __name__ == "__main__":
    for data in sorted_drivers:
        print(
            "P" + str(data["position"]),
            "-",
            data["name"],
            "-",
            data["team"],
            "- gap:",
            data["gap"],
            "- tyre:",
            data["compound"],
            "- age:",
            data["tyre_age"],
            "- pits:",
            data["pit_stops"],
            "- last clean lap:",
            data["last_clean_lap"]
        )