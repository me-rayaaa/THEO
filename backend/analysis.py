from race_state import get_race_state
from race_changes import get_lap_changes


def build_analysis(lap_number):
    race_state = get_race_state(lap_number)
    changes = get_lap_changes(lap_number)

    main_events = []

    for change in changes:
        if change["type"] in {
            "PIT_STOP",
            "TYRE_CHANGE",
            "POSITION_CHANGE",
            "ENTERED_TOP10",
            "LEFT_TOP10"
        }:
            main_events.append(change)

    return {
        "lap": lap_number,
        "race_status": race_state["race_status"],
        "weather": race_state["weather"],
        "main_events": main_events
    }


if __name__ == "__main__":
    print(build_analysis(25))