from race_state import get_race_state
from pit_strategy import (
    analyze_rejoin_traffic,
    calculate_pit_loss,
    calculate_rejoin,
    downgrade_status,
    get_phase_gain,
)
from pace_analysis import calculate_pace


MAX_RELATIVE_PACE = 1.5


def get_driver_pace(target_lap, driver_number):
    for item in calculate_pace(target_lap, laps_count=5):
        if item["driver_number"] == driver_number:
            return item["median_pace"]

    return None


def analyze_overcut(
    target_lap,
    driver_number,
    target_driver_number,
    stay_out_laps=2
):
    race_state = get_race_state(target_lap)

    driver = next(
        (item for item in race_state["drivers"] if item["driver_number"] == driver_number),
        None
    )

    target = next(
        (item for item in race_state["drivers"] if item["driver_number"] == target_driver_number),
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

    current_gap = round(driver_gap - target_gap, 3)

    if current_gap <= 0:
        return None

    pit_loss = calculate_pit_loss(target_lap, race_state["race_status"])

    driver_pace = get_driver_pace(target_lap, driver_number)
    target_pace = get_driver_pace(target_lap, target_driver_number)

    if driver_pace is None or target_pace is None:
        return None

    target_rejoin = calculate_rejoin(target_lap, target_driver_number, race_state)

    if target_rejoin is None:
        return None

    gap_after_target_stop = round(current_gap - pit_loss, 3)

    # После стопа соперник едет на свежих шинах — это и есть его undercut.
    fresh_tyre_gain = get_phase_gain(target_lap) or 0.0

    relative_pace_per_lap = round(
        driver_pace - (target_pace - fresh_tyre_gain),
        3
    )

    pace_signal_extreme = abs(relative_pace_per_lap) > MAX_RELATIVE_PACE

    relative_pace_effect = round(relative_pace_per_lap * stay_out_laps, 3)

    gap_before_driver_stop = round(gap_after_target_stop + relative_pace_effect, 3)

    # Состояние текущего круга: будущие круги не читаем.
    driver_rejoin = calculate_rejoin(target_lap, driver_number, race_state)

    if driver_rejoin is None:
        return None

    gap_after_driver_stop = round(gap_before_driver_stop + pit_loss, 3)

    if gap_after_driver_stop < 0:
        overcut_status = "STRONG"
    elif gap_after_driver_stop <= 1.0:
        overcut_status = "POSSIBLE"
    else:
        overcut_status = "WEAK"

    position_loss = driver_rejoin["projected_rejoin_position"] - driver["position"]

    driver_traffic = analyze_rejoin_traffic(
        target_lap,
        driver_number,
        driver_rejoin["projected_gap"],
        race_state=race_state
    )

    traffic_level = driver_traffic["traffic_level"]

    if position_loss >= 3:
        overcut_status = "WEAK"
    elif position_loss == 2:
        overcut_status = downgrade_status(overcut_status)

    if traffic_level == "HEAVY":
        overcut_status = "WEAK"
    elif traffic_level == "MODERATE":
        overcut_status = downgrade_status(overcut_status)

    if pace_signal_extreme:
        overcut_status = downgrade_status(overcut_status)

    return {
        "lap": target_lap,
        "driver": driver["name"],
        "driver_position": driver["position"],
        "target": target["name"],
        "target_position": target["position"],
        "current_gap": current_gap,
        "stay_out_laps": stay_out_laps,
        "pit_loss": pit_loss,
        "driver_recent_pace": driver_pace,
        "target_recent_pace": target_pace,
        "relative_pace_per_lap": relative_pace_per_lap,
        "pace_signal_extreme": pace_signal_extreme,
        "gap_after_target_stop": gap_after_target_stop,
        "relative_pace_effect": relative_pace_effect,
        "gap_before_driver_stop": gap_before_driver_stop,
        "gap_after_driver_stop": gap_after_driver_stop,
        "target_projected_rejoin_position": target_rejoin["projected_rejoin_position"],
        "driver_projected_rejoin_position": driver_rejoin["projected_rejoin_position"],
        "position_loss": position_loss,
        "traffic_level": traffic_level,
        "car_ahead": driver_traffic["car_ahead"],
        "gap_ahead": driver_traffic["gap_ahead"],
        "car_behind": driver_traffic["car_behind"],
        "gap_behind": driver_traffic["gap_behind"],
        "overcut_status": overcut_status
    }


if __name__ == "__main__":
    print(analyze_overcut(45, 1, 44))
