from functools import lru_cache
from statistics import median

from clean_laps import get_clean_laps
from data_store import get_race_phase, pits


def calculate_observed_pit_gain(
    target_lap,
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

        # Только стопы, чьё окно «после» уже полностью в прошлом.
        if pit_lap + laps_after + 1 > target_lap:
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

        before_pace = median(lap["lap_duration"] for lap in before_laps)
        after_pace = median(lap["lap_duration"] for lap in after_laps)

        results.append({
            "driver_number": driver_number,
            "pit_lap": pit_lap,
            "phase": get_race_phase(pit_lap),
            "before_pace": round(before_pace, 3),
            "after_pace": round(after_pace, 3),
            "observed_gain": round(before_pace - after_pace, 3)
        })

    return results


@lru_cache(maxsize=None)
def calculate_phase_gains(target_lap):
    results = calculate_observed_pit_gain(target_lap)

    phases = {
        "EARLY": [],
        "MIDDLE": [],
        "LATE": []
    }

    # Отрицательные выигрыши не выбрасываем: иначе медиана завышена.
    for item in results:
        phases[item["phase"]].append(item["observed_gain"])

    phase_gains = {
        "ALL": {
            "median_gain": (
                round(median(r["observed_gain"] for r in results), 3)
                if results else None
            ),
            "samples": len(results)
        }
    }

    for phase, gains in phases.items():
        phase_gains[phase] = {
            "median_gain": round(median(gains), 3) if gains else None,
            "samples": len(gains)
        }

    return phase_gains


if __name__ == "__main__":
    for phase, data in calculate_phase_gains(71).items():
        print(phase, "| median gain:", data["median_gain"], "| samples:", data["samples"])
