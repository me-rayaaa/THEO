from functools import lru_cache

from data_store import (
    RaceStatus,
    get_snapshot_time,
    laps,
    pits,
    race_control,
)


def classify_event(event):
    """Что сообщение Race Control начинает или заканчивает."""
    message = event["message"].upper()
    flag = event.get("flag")

    if event["category"] == "SafetyCar":
        kind = "VSC" if "VIRTUAL" in message else "SAFETY_CAR"

        if "DEPLOYED" in message:
            return kind, "START"

        if "ENDING" in message or "IN THIS LAP" in message:
            return kind, "END"

        return None, None

    if event["category"] != "Flag":
        return None, None

    if flag in {"YELLOW", "DOUBLE YELLOW"}:
        return ("YELLOW", event.get("sector")), "START"

    if flag == "CLEAR":
        if event.get("scope") == "Sector":
            return ("YELLOW", event.get("sector")), "END"

        return "YELLOW", "END_ALL"

    if flag == "RED":
        return "RED_FLAG", "START"

    if flag == "GREEN":
        return "RED_FLAG", "END"

    return None, None


def _is_yellow(key):
    return isinstance(key, tuple) and key[0] == "YELLOW"


@lru_cache(maxsize=None)
def get_neutralized_laps(target_lap):
    """Круги под жёлтым флагом, VSC, SC или красным флагом — от начала до конца периода."""
    invalid = set()
    active = {}

    for event in race_control:
        lap = event["lap_number"]

        if lap is None or lap > target_lap:
            continue

        key, action = classify_event(event)

        if action == "START":
            active.setdefault(key, lap)
            invalid.add(lap)

        elif action == "END" and key in active:
            invalid.update(range(active.pop(key), lap + 1))

        elif action == "END_ALL":
            for open_key in [k for k in active if _is_yellow(k)]:
                invalid.update(range(active.pop(open_key), lap + 1))

    for start in active.values():
        invalid.update(range(start, target_lap + 1))

    return frozenset(invalid)


def get_race_status(target_ts):
    active = set()
    finished = False

    for event in race_control:
        if event["ts"] is None or event["ts"] > target_ts:
            continue

        if (
            event["category"] == "SessionStatus"
            and "FINISHED" in event["message"].upper()
        ):
            finished = True

        key, action = classify_event(event)

        if action == "START":
            active.add(key)

        elif action == "END":
            active.discard(key)

        elif action == "END_ALL":
            active = {k for k in active if not _is_yellow(k)}

    if finished:
        return RaceStatus.FINISHED.value

    for status in (
        RaceStatus.RED_FLAG,
        RaceStatus.SAFETY_CAR,
        RaceStatus.VSC,
    ):
        if status.value in active:
            return status.value

    if any(_is_yellow(key) for key in active):
        return RaceStatus.YELLOW.value

    return RaceStatus.GREEN.value


@lru_cache(maxsize=None)
def get_clean_laps(target_lap):
    """Единственное место, где решается, какой круг «чистый»."""
    snapshot_ts = get_snapshot_time(target_lap)
    invalid_laps = get_neutralized_laps(target_lap)

    pit_affected = set()

    for pit in pits:
        if pit["lap_number"] is None or pit["lap_number"] > target_lap:
            continue

        pit_affected.add((pit["driver_number"], pit["lap_number"]))
        pit_affected.add((pit["driver_number"], pit["lap_number"] + 1))

    clean = []

    for lap in laps:
        number = lap["lap_number"]

        if number is None or number == 1 or number > target_lap:
            continue

        if lap["lap_duration"] is None or lap["lap_duration"] <= 0:
            continue

        # Круг, который на момент снимка ещё не закончен, — это будущее.
        if lap["end_ts"] is None or lap["end_ts"] > snapshot_ts:
            continue

        if number in invalid_laps:
            continue

        if (lap["driver_number"], number) in pit_affected:
            continue

        clean.append(lap)

    return tuple(clean)
