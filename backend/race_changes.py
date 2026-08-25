from race_state import get_race_state


def compare_states(previous_state, current_state):
    previous_drivers = {
        driver["driver_number"]: driver
        for driver in previous_state["drivers"]
    }

    current_drivers = {
        driver["driver_number"]: driver
        for driver in current_state["drivers"]
    }

    changes = []

    for driver_number, current in current_drivers.items():
        previous = previous_drivers.get(driver_number)

        if previous is None:
            changes.append({
                "type": "ENTERED_TOP10",
                "driver": current["name"],
                "position": current["position"]
            })
            continue

        if current["position"] != previous["position"]:
            changes.append({
                "type": "POSITION_CHANGE",
                "driver": current["name"],
                "from": previous["position"],
                "to": current["position"]
            })

        if current["pit_stops"] > previous["pit_stops"]:
            changes.append({
                "type": "PIT_STOP",
                "driver": current["name"],
                "pit_stops": current["pit_stops"]
            })

        if current["compound"] != previous["compound"]:
            changes.append({
                "type": "TYRE_CHANGE",
                "driver": current["name"],
                "from": previous["compound"],
                "to": current["compound"]
            })

    for driver_number, previous in previous_drivers.items():
        if driver_number not in current_drivers:
            changes.append({
                "type": "LEFT_TOP10",
                "driver": previous["name"],
                "position": previous["position"]
            })

    return changes


def get_lap_changes(lap_number):
    previous_state = get_race_state(lap_number - 1)
    current_state = get_race_state(lap_number)

    return compare_states(previous_state, current_state)


if __name__ == "__main__":
    changes = get_lap_changes(25)

    for change in changes:
        print(change)