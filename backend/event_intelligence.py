from race_changes import get_lap_changes


def build_event_summary(lap_number):
    changes = get_lap_changes(lap_number)

    pit_events = []
    top10_events = []
    position_changes = []

    drivers = {}

    for change in changes:
        driver = change["driver"]

        if driver not in drivers:
            drivers[driver] = []

        drivers[driver].append(change)

    for driver, driver_changes in drivers.items():
        pit_stop = next(
            (item for item in driver_changes if item["type"] == "PIT_STOP"),
            None
        )

        tyre_change = next(
            (item for item in driver_changes if item["type"] == "TYRE_CHANGE"),
            None
        )

        position_change = next(
            (
                item
                for item in driver_changes
                if item["type"] == "POSITION_CHANGE"
            ),
            None
        )

        entered_top10 = next(
            (
                item
                for item in driver_changes
                if item["type"] == "ENTERED_TOP10"
            ),
            None
        )

        left_top10 = next(
            (
                item
                for item in driver_changes
                if item["type"] == "LEFT_TOP10"
            ),
            None
        )

        if pit_stop:
            event = {
                "type": "PIT_STOP",
                "driver": driver
            }

            if position_change:
                event["position_from"] = position_change["from"]
                event["position_to"] = position_change["to"]

            if tyre_change:
                event["tyre_from"] = tyre_change["from"]
                event["tyre_to"] = tyre_change["to"]

            pit_events.append(event)

            continue

        if entered_top10:
            top10_events.append({
                "type": "ENTERED_TOP10",
                "driver": driver,
                "position": entered_top10["position"]
            })

            continue

        if left_top10:
            top10_events.append({
                "type": "LEFT_TOP10",
                "driver": driver,
                "position": left_top10["position"]
            })

            continue

        if position_change:
            position_changes.append(position_change)

    return {
        "lap": lap_number,
        "pit_events": pit_events,
        "top10_events": top10_events,
        "other_position_changes": len(position_changes)
    }


if __name__ == "__main__":
    print(build_event_summary(25))