import json
from datetime import datetime
from enum import Enum
from pathlib import Path

# --- Настройки гонки (всё, что раньше было зашито по модулям) ---

SESSION_KEY = 9877
GRAND_PRIX = "Mexico City Grand Prix 2025"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "mexico_2025"

EARLY_PHASE_END = 25
MIDDLE_PHASE_END = 45

# Значения до гонки: используются, пока в самой гонке не набралось своих стопов.
DEFAULT_PIT_LOSS = 22.5           # с, априорная потеря на пит-стоп для трассы
MIN_PIT_SAMPLES = 3               # сколько своих стопов нужно, чтобы им доверять
PIT_LANE_TIME_ON_TRACK = 0.0      # с, проезд того же участка по трассе (задать для трассы)
NEUTRALIZED_PIT_LOSS_FACTOR = {   # ориентировочно, уточнить по данным
    "VSC": 0.6,
    "SAFETY_CAR": 0.5,
}
FUEL_EFFECT_PER_LAP = 0.035       # с/круг, ориентировочно


class RaceStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    VSC = "VSC"
    SAFETY_CAR = "SAFETY_CAR"
    RED_FLAG = "RED_FLAG"
    FINISHED = "FINISHED"


NEUTRALIZED_STATUSES = {RaceStatus.VSC.value, RaceStatus.SAFETY_CAR.value}


class LapOutOfRange(ValueError):
    pass


def _load(name):
    with open(DATA_DIR / f"{name}.json", "r", encoding="utf-8") as file:
        return json.load(file)


def parse_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


drivers = _load("drivers")
positions = _load("position")
intervals = _load("intervals")
stints = _load("stints")
pits = _load("pit")
laps = _load("laps")
weather = _load("weather")
race_control = _load("race_control")

# Даты разбираются один раз при загрузке, а не при каждом запросе.
for collection in (positions, intervals, pits, weather, race_control):
    for item in collection:
        item["ts"] = parse_date(item["date"]) if item.get("date") else None

for lap in laps:
    if lap["date_start"] is not None and lap["lap_duration"] is not None:
        lap["end_ts"] = parse_date(lap["date_start"]) + lap["lap_duration"]
    else:
        lap["end_ts"] = None

drivers_by_number = {
    driver["driver_number"]: driver
    for driver in drivers
}

FIRST_LAP = 1
LAST_LAP = max(lap["lap_number"] for lap in laps)

# Момент снимка круга N = момент, когда лидер закончил круг N.
snapshot_times = {}

for lap in laps:
    if lap["end_ts"] is None:
        continue

    number = lap["lap_number"]
    snapshot_times[number] = min(
        snapshot_times.get(number, lap["end_ts"]),
        lap["end_ts"]
    )


def check_lap(target_lap):
    if not FIRST_LAP <= target_lap <= LAST_LAP:
        raise LapOutOfRange(
            f"Lap {target_lap} is outside {FIRST_LAP}-{LAST_LAP}"
        )


def get_snapshot_time(target_lap):
    check_lap(target_lap)
    return snapshot_times[target_lap]


def get_race_phase(lap_number):
    if lap_number <= EARLY_PHASE_END:
        return "EARLY"

    if lap_number <= MIDDLE_PHASE_END:
        return "MIDDLE"

    return "LATE"


def get_numeric_gap(gap):
    if isinstance(gap, (int, float)):
        return float(gap)

    if isinstance(gap, str) and "LAP" not in gap.upper():
        try:
            return float(gap)
        except ValueError:
            return None

    return None


def fuel_corrected(lap):
    # Ранние круги медленнее из-за топлива: приводим их к пустому баку.
    laps_of_fuel_left = LAST_LAP - lap["lap_number"]
    return lap["lap_duration"] - FUEL_EFFECT_PER_LAP * laps_of_fuel_left
