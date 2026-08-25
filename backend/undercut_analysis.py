from race_state import get_race_state
from pit_strategy import (
    calculate_rejoin,
    get_phase_gain,
    analyze_rejoin_traffic,
)


def downgrade_status(status):
    if status == "STRONG":
        return "POSSIBLE"

    if status == "POSSIBLE":
        return "WEAK"

    return "WEAK"


def analyze_undercut(
    target_lap,
    driver_number,
    target_driver_number,
    comparison_laps=3
):
    race_state = get_race_state(target_lap)

    driver = next(
        (
            item
            for item in race_state["drivers"]
            if item["driver_number"] == driver_number
        ),
        None
    )

    target = next(
        (
            item
            for item in race_state["drivers"]
            if item["driver_number"] == target_driver_number
        ),
        None
    )

    if driver is None or target is None:
        return None

    driver_gap = driver["gap"]
    target_gap = target["gap"]

    if not isinstance(driver_gap, (int, float)):
        return None

    if not isinstance(target_gap, (int, float)):
        return None

    current_gap = round(
        driver_gap - target_gap,
        3
    )

    if current_gap <= 0:
        return None

    rejoin = calculate_rejoin(
        target_lap,
        driver_number
    )

    if rejoin is None:
        return None

    fresh_tyre_gain = get_phase_gain(
        target_lap
    )

    if fresh_tyre_gain is None:
        return None

    estimated_gain = round(
        fresh_tyre_gain * comparison_laps,
        3
    )

    projected_gap_after_undercut = round(
        current_gap - estimated_gain,
        3
    )

    if projected_gap_after_undercut <= 0:
        undercut_status = "STRONG"

    elif projected_gap_after_undercut <= 2.0:
        undercut_status = "POSSIBLE"

    else:
        undercut_status = "WEAK"

    position_loss = (
        rejoin["projected_rejoin_position"]
        - driver["position"]
    )

    traffic = analyze_rejoin_traffic(
        target_lap,
        driver_number,
        rejoin["projected_gap"]
    )

    traffic_level = traffic["traffic_level"]

    if position_loss >= 4:
        undercut_status = "WEAK"

    elif position_loss >= 2:
        undercut_status = downgrade_status(
            undercut_status
        )

    if traffic_level == "HEAVY":
        undercut_status = "WEAK"

    elif traffic_level == "MODERATE":
        undercut_status = downgrade_status(
            undercut_status
        )

    projected_rejoin_position = rejoin[
        "projected_rejoin_position"
    ]

    target_position = target["position"]

    if (
        projected_rejoin_position
        >= target_position + 4
    ):
        undercut_status = "WEAK"

    if (
        current_gap <= 2.0
        and estimated_gain < current_gap
        and position_loss <= 1
        and traffic_level == "CLEAR"
    ):
        overcut_status = "POSSIBLE"
    else:
        overcut_status = "WEAK"

    return {
        "lap": target_lap,
        "driver": driver["name"],
        "driver_position": driver["position"],
        "target": target["name"],
        "target_position": target["position"],
        "current_gap": current_gap,
        "fresh_tyre_gain_per_lap": fresh_tyre_gain,
        "comparison_laps": comparison_laps,
        "estimated_gain": estimated_gain,
        "projected_gap_after_undercut":
            projected_gap_after_undercut,
        "position_loss": position_loss,
        "projected_rejoin_position":
            projected_rejoin_position,
        "traffic_level": traffic_level,
        "car_ahead": traffic["car_ahead"],
        "gap_ahead": traffic["gap_ahead"],
        "undercut_status": undercut_status,
        "overcut_status": overcut_status
    }


if __name__ == "__main__":
    tests = [
        (25, 16, 4),
        (25, 1, 16),
        (60, 12, 63)
    ]

    for lap, driver_number, target_driver_number in tests:
        result = analyze_undercut(
            lap,
            driver_number,
            target_driver_number
        )

        print(result)