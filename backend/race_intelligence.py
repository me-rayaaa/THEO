from race_state import get_race_state
from pace_analysis import calculate_pace_trend
from gap_analysis import calculate_gap_trend


def build_race_intelligence(target_lap):
    race_state = get_race_state(target_lap)
    pace_trends = calculate_pace_trend(target_lap)
    gap_trends = calculate_gap_trend(target_lap, 3)

    pace_by_driver = {
        item["driver_number"]: item
        for item in pace_trends
    }

    drivers_by_number = {
        driver["driver_number"]: driver
        for driver in race_state["drivers"]
    }

    battles = []

    for gap in gap_trends:
        driver = drivers_by_number.get(gap["driver_number"])
        target = drivers_by_number.get(gap["target_number"])

        if driver is None or target is None:
            continue

        driver_pace = pace_by_driver.get(driver["driver_number"])
        target_pace = pace_by_driver.get(target["driver_number"])

        battles.append({
            "driver_number": driver["driver_number"],
            "target_number": target["driver_number"],
            "driver": driver["name"],
            "position": driver["position"],
            "target": target["name"],
            "target_position": target["position"],
            "current_gap": gap["current_gap"],
            "gap_change": gap["gap_change"],
            "closing_rate": gap["closing_rate"],
            "gap_trend": gap["trend"],
            "driver_pace_trend": (
                driver_pace["trend"] if driver_pace else "UNKNOWN"
            ),
            "target_pace_trend": (
                target_pace["trend"] if target_pace else "UNKNOWN"
            ),
            "driver_tyre": driver["compound"],
            "driver_tyre_age": driver["tyre_age"],
            "target_tyre": target["compound"],
            "target_tyre_age": target["tyre_age"]
        })

    return {
        "lap": target_lap,
        "battles": battles
    }


if __name__ == "__main__":
    for battle in build_race_intelligence(25)["battles"]:
        print(
            f'P{battle["position"]} {battle["driver"]} -> '
            f'P{battle["target_position"]} {battle["target"]} | '
            f'gap: {battle["current_gap"]} | {battle["gap_trend"]}'
        )
