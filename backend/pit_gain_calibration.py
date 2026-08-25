import json
from statistics import median

from pace_analysis import get_clean_laps

pit_file = "../data/mexico_2025/pit.json"

with open(pit_file, "r", encoding="utf-8") as file:
    pits = json.load(file)


def calculate_observed_pit_gain(
    target_lap=71,
    laps_before=3,
    laps_after=3
):
    clean_laps = get_clean_laps(target_lap)

    results = []

    for pit in pits:
        driver_number = pit["driver_number"]
        pit_lap = pit["lap_number"]

        if pit_lap is None:
            continue

        before_laps = [
            lap
            for lap in clean_laps
            if lap["driver_number"] == driver_number
            and pit_lap - laps_before <= lap["lap_number"] < pit_lap
        ]

        after_laps = [
            lap
            for lap in clean_laps
            if lap["driver_number"] == driver_number
            and pit_lap + 1 < lap["lap_number"] <= pit_lap + laps_after + 1
        ]

        if len(before_laps) < 2 or len(after_laps) < 2:
            continue

        before_pace = median(
            lap["lap_duration"]
            for lap in before_laps
        )

        after_pace = median(
            lap["lap_duration"]
            for lap in after_laps
        )

        observed_gain = round(
            before_pace - after_pace,
            3
        )

        if pit_lap <= 25:
            phase = "EARLY"
        elif pit_lap <= 45:
            phase = "MIDDLE"
        else:
            phase = "LATE"

        results.append({
            "driver_number": driver_number,
            "pit_lap": pit_lap,
            "phase": phase,
            "before_pace": round(before_pace, 3),
            "after_pace": round(after_pace, 3),
            "observed_gain": observed_gain
        })

    return results


def calculate_phase_gains():
    results = calculate_observed_pit_gain()

    phases = {
        "EARLY": [],
        "MIDDLE": [],
        "LATE": []
    }

    for item in results:
        if item["observed_gain"] <= 0:
            continue

        phases[item["phase"]].append(
            item["observed_gain"]
        )

    phase_gains = {}

    for phase, gains in phases.items():
        if gains:
            phase_gains[phase] = {
                "median_gain": round(
                    median(gains),
                    3
                ),
                "samples": len(gains)
            }
        else:
            phase_gains[phase] = {
                "median_gain": None,
                "samples": 0
            }

    return phase_gains


if __name__ == "__main__":
    results = calculate_observed_pit_gain()

    for item in results:
        print(
            f'driver {item["driver_number"]} | '
            f'pit lap {item["pit_lap"]} | '
            f'{item["phase"]} | '
            f'gain {item["observed_gain"]}'
        )

    print("\nPHASE GAINS")

    phase_gains = calculate_phase_gains()

    for phase, data in phase_gains.items():
        print(
            phase,
            "| median gain:",
            data["median_gain"],
            "| samples:",
            data["samples"]
        )