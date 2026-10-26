from data_store import NEUTRALIZED_STATUSES, RaceStatus, get_numeric_gap
from race_state import get_race_state

SKIP_STATUSES = NEUTRALIZED_STATUSES | {
    RaceStatus.RED_FLAG.value,
    RaceStatus.FINISHED.value,
}


def had_pit_stop_in_window(
    driver_number,
    previous_state,
    current_state
):
    previous_driver = next(
        (
            driver
            for driver in previous_state["drivers"]
            if driver["driver_number"] == driver_number
        ),
        None
    )

    current_driver = next(
        (
            driver
            for driver in current_state["drivers"]
            if driver["driver_number"] == driver_number
        ),
        None
    )

    if previous_driver is None or current_driver is None:
        return True

    return (
        current_driver["pit_stops"]
        > previous_driver["pit_stops"]
    )


def calculate_gap_trend(
    target_lap,
    comparison_laps=3,
    max_battle_gap=15.0
):
    previous_lap = target_lap - comparison_laps

    if previous_lap < 2:
        return []

    # Нейтрализация на ЛЮБОМ круге окна искажает отрывы.
    for lap in range(previous_lap, target_lap + 1):
        if get_race_state(lap)["race_status"] in SKIP_STATUSES:
            return []

    current_state = get_race_state(target_lap)
    previous_state = get_race_state(previous_lap)

    current_drivers = {
        driver["driver_number"]: driver
        for driver in current_state["drivers"]
    }

    previous_drivers = {
        driver["driver_number"]: driver
        for driver in previous_state["drivers"]
    }

    result = []

    current_order = sorted(
        current_state["drivers"],
        key=lambda driver: driver["position"]
    )

    for index in range(1, len(current_order)):
        driver = current_order[index]
        driver_ahead = current_order[index - 1]

        driver_number = driver["driver_number"]
        ahead_number = driver_ahead["driver_number"]

        current_driver = current_drivers.get(driver_number)
        current_ahead = current_drivers.get(ahead_number)

        previous_driver = previous_drivers.get(driver_number)
        previous_ahead = previous_drivers.get(ahead_number)

        if (
            current_driver is None
            or current_ahead is None
            or previous_driver is None
            or previous_ahead is None
        ):
            continue

        if had_pit_stop_in_window(
            driver_number,
            previous_state,
            current_state
        ):
            continue

        if had_pit_stop_in_window(
            ahead_number,
            previous_state,
            current_state
        ):
            continue

        current_driver_gap = get_numeric_gap(current_driver["gap"])
        current_ahead_gap = get_numeric_gap(current_ahead["gap"])
        previous_driver_gap = get_numeric_gap(previous_driver["gap"])
        previous_ahead_gap = get_numeric_gap(previous_ahead["gap"])

        if (
            current_driver_gap is None
            or current_ahead_gap is None
            or previous_driver_gap is None
            or previous_ahead_gap is None
        ):
            continue

        current_gap = round(
            current_driver_gap - current_ahead_gap,
            3
        )

        previous_gap = round(
            previous_driver_gap - previous_ahead_gap,
            3
        )

        if current_gap <= 0:
            continue

        if previous_gap <= 0:
            continue

        if current_gap > max_battle_gap:
            continue

        gap_change = round(
            current_gap - previous_gap,
            3
        )

        closing_rate = round(
            -gap_change / comparison_laps,
            3
        )

        if abs(closing_rate) > 2.0:
            continue

        if gap_change <= -0.5:
            trend = "CLOSING"

        elif gap_change >= 0.5:
            trend = "DROPPING_BACK"

        else:
            trend = "STABLE"

        result.append({
            "driver_number": driver_number,
            "target_number": ahead_number,
            "driver": driver["name"],
            "position": driver["position"],
            "target": driver_ahead["name"],
            "target_position": driver_ahead["position"],
            "previous_gap": previous_gap,
            "current_gap": current_gap,
            "gap_change": gap_change,
            "closing_rate": closing_rate,
            "trend": trend
        })

    return result


if __name__ == "__main__":
    for item in calculate_gap_trend(25, 3):
        print(
            f'P{item["position"]} {item["driver"]} -> '
            f'P{item["target_position"]} {item["target"]} - '
            f'gap: {item["previous_gap"]} -> {item["current_gap"]} - '
            f'{item["trend"]}'
        )
