import json
from statistics import median

from race_state import get_race_state
from pace_analysis import get_clean_laps

stints_file = "../data/mexico_2025/stints.json"

with open(stints_file, "r", encoding="utf-8") as file:
    stints = json.load(file)


def classify_degradation(rate, laps_used):
    if rate is None or laps_used < 8:
        return "INSUFFICIENT_DATA"

    if rate < 0:
        return "NO_CLEAR_DEGRADATION_SIGNAL"

    if rate < 0.02:
        return "LOW"

    if rate < 0.05:
        return "MODERATE"

    return "HIGH"


def calculate_tyre_degradation(target_lap, min_laps=5):
    race_state = get_race_state(target_lap)
    clean_laps = get_clean_laps(target_lap)

    results = []

    for driver in race_state["drivers"]:
        driver_number = driver["driver_number"]

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

        if current_stint is None:
            continue

        stint_laps = [
            lap
            for lap in clean_laps
            if lap["driver_number"] == driver_number
            and current_stint["lap_start"] <= lap["lap_number"] <= target_lap
        ]

        stint_laps = sorted(
            stint_laps,
            key=lambda x: x["lap_number"]
        )

        degradation_rate = None

        if len(stint_laps) >= min_laps:
            split_index = len(stint_laps) // 2

            first_half = stint_laps[:split_index]
            second_half = stint_laps[split_index:]

            first_median = median(
                lap["lap_duration"]
                for lap in first_half
            )

            second_median = median(
                lap["lap_duration"]
                for lap in second_half
            )

            lap_difference = (
                median(
                    lap["lap_number"]
                    for lap in second_half
                )
                -
                median(
                    lap["lap_number"]
                    for lap in first_half
                )
            )

            if lap_difference > 0:
                degradation_rate = round(
                    (second_median - first_median) / lap_difference,
                    3
                )

        degradation_level = classify_degradation(
            degradation_rate,
            len(stint_laps)
        )

        results.append({
            "driver": driver["name"],
            "position": driver["position"],
            "compound": current_stint["compound"],
            "tyre_age": driver["tyre_age"],
            "laps_used": len(stint_laps),
            "degradation_rate": degradation_rate,
            "degradation_level": degradation_level
        })

    return {
        "lap": target_lap,
        "drivers": results
    }


if __name__ == "__main__":
    result = calculate_tyre_degradation(60)

    for item in result["drivers"]:
        print(
            f'P{item["position"]} - '
            f'{item["driver"]} - '
            f'{item["compound"]} - '
            f'age: {item["tyre_age"]} - '
            f'laps used: {item["laps_used"]} - '
            f'degradation: {item["degradation_rate"]} - '
            f'level: {item["degradation_level"]}'
        )