from race_state import get_race_state


def normalize_race_status(status):
    if status is None:
        return "UNKNOWN"

    value = str(status).upper().strip()

    if "VSC" in value or "VIRTUAL SAFETY" in value:
        return "VSC"

    if (
        "SAFETY CAR" in value
        or value == "SC"
    ):
        return "SAFETY_CAR"

    if (
        "RED" in value
        or "RED FLAG" in value
    ):
        return "RED_FLAG"

    if (
        "YELLOW" in value
        or "DOUBLE YELLOW" in value
    ):
        return "YELLOW"

    if (
        "GREEN" in value
        or "CLEAR" in value
    ):
        return "GREEN"

    return value


def get_neutralization_context(target_lap):
    race_state = get_race_state(target_lap)

    raw_status = race_state.get(
        "race_status"
    )

    status = normalize_race_status(
        raw_status
    )

    neutralized = status in {
        "VSC",
        "SAFETY_CAR"
    }

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
    tests = [
        25,
        60,
        70
    ]

    for lap in tests:
        print()
        print("=" * 70)

        try:
            result = get_neutralization_context(
                lap
            )

            print(result)

        except Exception as error:
            print(
                {
                    "lap": lap,
                    "error": str(error)
                }
            )