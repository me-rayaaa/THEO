import json
from datetime import datetime

drivers_file = "../data/mexico_2025/drivers.json"
positions_file = "../data/mexico_2025/position.json"
intervals_file = "../data/mexico_2025/intervals.json"
stints_file = "../data/mexico_2025/stints.json"
pit_file = "../data/mexico_2025/pit.json"
laps_file = "../data/mexico_2025/laps.json"
weather_file = "../data/mexico_2025/weather.json"
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

with open(weather_file, "r", encoding="utf-8") as file:
    weather = json.load(file)

with open(race_control_file, "r", encoding="utf-8") as file:
    race_control = json.load(file)

drivers_by_number = {
    driver["driver_number"]: driver
    for driver in drivers
}


def parse_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def get_race_state(target_lap):
    target_laps = [
        lap
        for lap in laps
        if lap["lap_number"] == target_lap
        and lap["date_start"] is not None
        and lap["lap_duration"] is not None
    ]

    lap_end_times = []

    for lap in target_laps:
        start = parse_date(lap["date_start"])
        end_timestamp = start.timestamp() + lap["lap_duration"]
        lap_end_times.append(end_timestamp)

    target_time = min(lap_end_times)

    latest_positions = {}

    for item in positions:
        item_time = parse_date(item["date"]).timestamp()

        if item_time <= target_time:
            latest_positions[item["driver_number"]] = item

    latest_intervals = {}

    for item in intervals:
        if item["date"] is None:
            continue

        item_time = parse_date(item["date"]).timestamp()

        if item_time <= target_time and item["gap_to_leader"] is not None:
            latest_intervals[item["driver_number"]] = item

    pit_counts = {}

    for pit in pits:
        if pit["date"] is None:
            continue

        pit_time = parse_date(pit["date"]).timestamp()

        if pit_time <= target_time:
            driver_number = pit["driver_number"]
            pit_counts[driver_number] = pit_counts.get(driver_number, 0) + 1

    latest_weather = None

    for item in weather:
        if item["date"] is None:
            continue

        weather_time = parse_date(item["date"]).timestamp()

        if weather_time <= target_time:
            latest_weather = item

    race_status = "GREEN"

    for event in race_control:
        if event["date"] is None:
            continue

        event_time = parse_date(event["date"]).timestamp()

        if event_time > target_time:
            continue

        category = event["category"]
        message = event["message"].upper()

        if "SESSION FINISHED" in message:
            race_status = "FINISHED"

        elif category == "SafetyCar" and "VIRTUAL SAFETY CAR DEPLOYED" in message:
            race_status = "VSC"

        elif category == "SafetyCar" and "VIRTUAL SAFETY CAR ENDING" in message:
            race_status = "GREEN"

        elif category == "SafetyCar" and "SAFETY CAR DEPLOYED" in message:
            race_status = "SAFETY CAR"

        elif category == "SafetyCar" and "SAFETY CAR IN THIS LAP" in message:
            race_status = "GREEN"

    invalid_race_control_laps = set()

    for event in race_control:
        lap_number = event["lap_number"]

        if lap_number is None:
            continue

        if lap_number > target_lap:
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
        if pit["lap_number"] is None:
            continue

        if pit["lap_number"] > target_lap:
            continue

        driver_number = pit["driver_number"]
        lap_number = pit["lap_number"]

        pit_affected_laps.add((driver_number, lap_number))
        pit_affected_laps.add((driver_number, lap_number + 1))

    latest_clean_laps = {}

    for lap in laps:
        if lap["lap_number"] is None:
            continue

        if lap["lap_number"] > target_lap:
            continue

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

        driver_number = lap["driver_number"]

        if (
            driver_number not in latest_clean_laps
            or lap["lap_number"] > latest_clean_laps[driver_number]["lap_number"]
        ):
            latest_clean_laps[driver_number] = lap

    drivers_state = []

    for driver_number, position in latest_positions.items():
        driver = drivers_by_number.get(driver_number)

        if driver is None:
            continue

        interval = latest_intervals.get(driver_number)

        gap = None
        if interval:
            gap = interval["gap_to_leader"]

        current_stint = None

        for stint in stints:
            if stint["driver_number"] != driver_number:
                continue

            lap_start = stint["lap_start"]
            lap_end = stint["lap_end"]

            if lap_start is None:
                continue

            if lap_start <= target_lap and (
                lap_end is None or target_lap <= lap_end
            ):
                current_stint = stint

        compound = "UNKNOWN"
        tyre_age = None

        if current_stint:
            compound = current_stint["compound"]

            tyre_age = (
                current_stint["tyre_age_at_start"]
                + (target_lap - current_stint["lap_start"] + 1)
            )

        last_clean_lap = None
        clean_lap = latest_clean_laps.get(driver_number)

        if clean_lap:
            last_clean_lap = clean_lap["lap_duration"]

        drivers_state.append({
            "driver_number": driver_number,
            "position": position["position"],
            "name": driver["full_name"],
            "team": driver["team_name"],
            "gap": gap,
            "compound": compound,
            "tyre_age": tyre_age,
            "pit_stops": pit_counts.get(driver_number, 0),
            "last_clean_lap": last_clean_lap
        })

    drivers_state = sorted(
        drivers_state,
        key=lambda x: x["position"]
    )

    weather_state = None

    if latest_weather:
        weather_state = {
            "air_temperature": latest_weather["air_temperature"],
            "track_temperature": latest_weather["track_temperature"],
            "rainfall": latest_weather["rainfall"],
            "humidity": latest_weather["humidity"],
            "wind_speed": latest_weather["wind_speed"]
        }

    return {
        "grand_prix": "Mexico City Grand Prix 2025",
        "current_lap": target_lap,
        "race_status": race_status,
        "weather": weather_state,
        "drivers": drivers_state[:10]
    }


if __name__ == "__main__":
    race_state = get_race_state(25)

    print("Grand Prix:", race_state["grand_prix"])
    print("Current lap:", race_state["current_lap"])
    print("Race status:", race_state["race_status"])
    print("Weather:", race_state["weather"])

    print("\nTOP 10")

    for driver in race_state["drivers"]:
        print(
            "P" + str(driver["position"]),
            "-",
            driver["name"],
            "- gap:",
            driver["gap"],
            "- tyre:",
            driver["compound"],
            "- age:",
            driver["tyre_age"],
            "- pits:",
            driver["pit_stops"],
            "- last clean lap:",
            driver["last_clean_lap"]
        )