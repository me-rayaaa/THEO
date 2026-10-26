import copy
from functools import lru_cache

from clean_laps import get_clean_laps, get_race_status
from data_store import (
    GRAND_PRIX,
    drivers_by_number,
    get_snapshot_time,
    intervals,
    pits,
    positions,
    stints,
    weather,
)


def get_current_stint(driver_number, target_lap):
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

    return current_stint


@lru_cache(maxsize=None)
def _build_race_state(target_lap):
    target_time = get_snapshot_time(target_lap)

    latest_positions = {}

    for item in positions:
        if item["ts"] is not None and item["ts"] <= target_time:
            latest_positions[item["driver_number"]] = item

    latest_intervals = {}

    for item in intervals:
        if (
            item["ts"] is not None
            and item["ts"] <= target_time
            and item["gap_to_leader"] is not None
        ):
            latest_intervals[item["driver_number"]] = item

    pit_counts = {}

    for pit in pits:
        if pit["ts"] is not None and pit["ts"] <= target_time:
            driver_number = pit["driver_number"]
            pit_counts[driver_number] = pit_counts.get(driver_number, 0) + 1

    latest_weather = None

    for item in weather:
        if item["ts"] is not None and item["ts"] <= target_time:
            latest_weather = item

    latest_clean_laps = {}

    for lap in get_clean_laps(target_lap):
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
        current_stint = get_current_stint(driver_number, target_lap)

        compound = "UNKNOWN"
        tyre_age = None
        stint_start_lap = None

        if current_stint:
            compound = current_stint["compound"]
            stint_start_lap = current_stint["lap_start"]
            tyre_age = (
                current_stint["tyre_age_at_start"]
                + (target_lap - current_stint["lap_start"] + 1)
            )

        clean_lap = latest_clean_laps.get(driver_number)

        drivers_state.append({
            "driver_number": driver_number,
            "position": position["position"],
            "name": driver["full_name"],
            "team": driver["team_name"],
            "gap": interval["gap_to_leader"] if interval else None,
            "compound": compound,
            "tyre_age": tyre_age,
            "stint_start_lap": stint_start_lap,
            "pit_stops": pit_counts.get(driver_number, 0),
            "last_clean_lap": (
                clean_lap["lap_duration"] if clean_lap else None
            ),
        })

    drivers_state.sort(key=lambda x: x["position"])

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
        "grand_prix": GRAND_PRIX,
        "current_lap": target_lap,
        "race_status": get_race_status(target_time),
        "weather": weather_state,
        # Весь пелотон. До 10 обрезает только API для экрана.
        "drivers": drivers_state
    }


def get_race_state(target_lap):
    # Копия, чтобы вызывающий код не испортил кэш.
    return copy.deepcopy(_build_race_state(target_lap))


if __name__ == "__main__":
    race_state = get_race_state(25)

    print("Grand Prix:", race_state["grand_prix"])
    print("Current lap:", race_state["current_lap"])
    print("Race status:", race_state["race_status"])
    print("Weather:", race_state["weather"])

    for driver in race_state["drivers"]:
        print(
            "P" + str(driver["position"]),
            "-", driver["name"],
            "- gap:", driver["gap"],
            "- tyre:", driver["compound"],
            "- age:", driver["tyre_age"],
            "- pits:", driver["pit_stops"],
        )
