from data_store import NEUTRALIZED_STATUSES, RaceStatus
from race_state import get_race_state

KNOWN_STATUSES = {status.value for status in RaceStatus}


def normalize_race_status(status):
    # Точное сравнение: подстрока "RED" ловила "CHEQUERED" и "CLEARED".
    if status in KNOWN_STATUSES:
        return status

    return "UNKNOWN"


def get_neutralization_context(target_lap):
    race_state = get_race_state(target_lap)

    raw_status = race_state.get(
        "race_status"
    )

    status = normalize_race_status(
        raw_status
    )

    neutralized = status in NEUTRALIZED_STATUSES

    if status == "SAFETY_CAR":
        pit_opportunity = "HIGH"

    elif status == "VSC":
        pit_opportunity = "ELEVATED"

    elif status == "RED_FLAG":
        pit_opportunity = "SPECIAL"

    else:
        pit_opportunity = "NORMAL"

    if status == "SAFETY_CAR":
        message = (
            "Safety Car conditions are active. "
            "The strategic cost of a pit stop may be lower than under green-flag running."
        )

    elif status == "VSC":
        message = (
            "Virtual Safety Car conditions are active. "
            "The pit-stop opportunity is more favorable than under normal green-flag running."
        )

    elif status == "RED_FLAG":
        message = (
            "The race is under red-flag conditions. "
            "Normal pit strategy logic should not be applied without additional race-control context."
        )

    elif status == "YELLOW":
        message = (
            "Yellow-flag conditions are active. "
            "Track conditions are restricted, but normal pit-loss assumptions are not automatically changed."
        )

    elif status == "FINISHED":
        message = (
            "The race has finished. "
            "No further pit strategy applies."
        )

    elif status == "GREEN":
        message = (
            "The race is under green-flag conditions. "
            "Normal strategy assumptions apply."
        )

    else:
        message = (
            "Race neutralization status is unclear. "
            "Normal strategy assumptions should be treated cautiously."
        )

    return {
        "lap": target_lap,
        "raw_status": raw_status,
        "status": status,
        "neutralized": neutralized,
        "pit_opportunity": pit_opportunity,
        "message": message
    }


if __name__ == "__main__":
    for lap in [25, 60, 70]:
        print(get_neutralization_context(lap))