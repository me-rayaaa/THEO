import json
from statistics import median

from race_state import get_race_state

laps_file = "../data/mexico_2025/laps.json"
pit_file = "../data/mexico_2025/pit.json"
race_control_file = "../data/mexico_2025/race_control.json"

with open(laps_file, "r", encoding="utf-8") as file:
    laps = json.load(file)

with open(pit_file, "r", encoding="utf-8") as file:
    pits = json.load(file)

with open(race_control_file, "r", encoding="utf-8") as file:
    race_control = json.load(file)


def get_clean_laps(target_lap):
    invalid_race_control_laps = set()

    for event in race_control:
        lap_number = event["lap_number"]

        if lap_number is None or lap_number > target_lap:
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
        lap_number = pit["lap_number"]

        if lap_number is None or lap_number > target_lap:
            continue

        driver_number = pit["driver_number"]

        pit_affected_laps.add((driver_number, lap_number))
        pit_affected_laps.add((driver_number, lap_number + 1))

    clean_laps = []

    for lap in laps:
        lap_number = lap["lap_number"]

        if lap_number is None:
            continue

        if lap_number > target_lap:
            continue

        if lap_number == 1:
            continue

        if lap["lap_duration"] is None:
            continue

        if lap["lap_duration"] <= 0:
            continue

        if lap_number in invalid_race_control_laps:
            continue

        if (
            lap["driver_number"],
            lap_number
        ) in pit_affected_laps:
            continue

        clean_laps.append(lap)

    return clean_laps


def get_recent_pace(target_lap, laps_count=5):
    race_state = get_race_state(target_lap)
    clean_laps = get_clean_laps(target_lap)

    result = []

    for driver in race_state["drivers"]:
        driver_number = driver["driver_number"]

        driver_laps = [
            lap
            for lap in clean_laps
            if lap["driver_number"] == driver_number
        ]

        driver_laps = sorted(
            driver_laps,
            key=lambda x: x["lap_number"]
        )

        recent_laps = driver_laps[-laps_count:]

        result.append({
            "driver_number": driver_number,
            "name": driver["name"],
            "position": driver["position"],
            "laps": [
                {
                    "lap": lap["lap_number"],
                    "time": lap["lap_duration"]
                }
                for lap in recent_laps
            ]
        })

    return result


def calculate_pace(target_lap, laps_count=5):
    recent_pace = get_recent_pace(target_lap, laps_count)

    result = []

    for driver in recent_pace:
        lap_times = [
            lap["time"]
            for lap in driver["laps"]
        ]

        median_pace = None

        if lap_times:
            median_pace = round(median(lap_times), 3)

        result.append({
            "driver_number": driver["driver_number"],
            "name": driver["name"],
            "position": driver["position"],
            "median_pace": median_pace,
            "laps_used": len(lap_times)
        })

    return result


def calculate_pace_trend(target_lap, laps_count=5):
    race_state = get_race_state(target_lap)
    clean_laps = get_clean_laps(target_lap)

    result = []

    for driver in race_state["drivers"]:
        driver_number = driver["driver_number"]

        driver_laps = [
            lap
            for lap in clean_laps
            if lap["driver_number"] == driver_number
        ]

        driver_laps = sorted(
            driver_laps,
            key=lambda x: x["lap_number"]
        )

        needed_laps = laps_count * 2
        recent_laps = driver_laps[-needed_laps:]

        previous_window = recent_laps[:laps_count]
        current_window = recent_laps[laps_count:]

        previous_pace = None
        current_pace = None
        pace_delta = None
        trend = "UNKNOWN"

        if len(previous_window) == laps_count:
            previous_pace = round(
                median(
                    lap["lap_duration"]
                    for lap in previous_window
                ),
                3
            )

        if len(current_window) == laps_count:
            current_pace = round(
                median(
                    lap["lap_duration"]
                    for lap in current_window
                ),
                3
            )

        if previous_pace is not None and current_pace is not None:
            pace_delta = round(
                current_pace - previous_pace,
                3
            )

            if pace_delta <= -0.15:
                trend = "IMPROVING"

            elif pace_delta >= 0.15:
                trend = "DEGRADING"

            else:
                trend = "STABLE"

        result.append({
            "driver_number": driver_number,
            "name": driver["name"],
            "position": driver["position"],
            "previous_pace": previous_pace,
            "current_pace": current_pace,
            "pace_delta": pace_delta,
            "trend": trend
        })

    return result


if __name__ == "__main__":
    trends = calculate_pace_trend(25)

    for driver in trends:
        print(
            f'P{driver["position"]} - '
            f'{driver["name"]} - '
            f'previous: {driver["previous_pace"]} - '
            f'current: {driver["current_pace"]} - '
            f'delta: {driver["pace_delta"]} - '
            f'trend: {driver["trend"]}'
        )