from race_intelligence import build_race_intelligence
from tyre_degradation import calculate_tyre_degradation


def build_tyre_intelligence(target_lap):
    race_intelligence = build_race_intelligence(target_lap)
    tyre_data = calculate_tyre_degradation(target_lap)

    tyre_by_driver = {
        item["driver_number"]: item
        for item in tyre_data["drivers"]
    }

    results = []

    for battle in race_intelligence["battles"]:
        driver_tyre = tyre_by_driver.get(battle["driver_number"])
        target_tyre = tyre_by_driver.get(battle["target_number"])

        if driver_tyre is None or target_tyre is None:
            continue

        results.append({
            "driver_number": battle["driver_number"],
            "target_number": battle["target_number"],
            "driver": battle["driver"],
            "position": battle["position"],
            "target": battle["target"],
            "target_position": battle["target_position"],
            "gap": battle["current_gap"],
            "closing_rate": battle["closing_rate"],
            "gap_trend": battle["gap_trend"],
            "driver_compound": driver_tyre["compound"],
            "driver_tyre_age": driver_tyre["tyre_age"],
            "driver_degradation_rate": driver_tyre["degradation_rate"],
            "driver_degradation_level": driver_tyre["degradation_level"],
            "target_compound": target_tyre["compound"],
            "target_tyre_age": target_tyre["tyre_age"],
            "target_degradation_rate": target_tyre["degradation_rate"],
            "target_degradation_level": target_tyre["degradation_level"]
        })

    return {
        "lap": target_lap,
        "battles": results
    }


if __name__ == "__main__":
    for battle in build_tyre_intelligence(60)["battles"]:
        print(
            f'P{battle["position"]} {battle["driver"]} -> '
            f'P{battle["target_position"]} {battle["target"]} | '
            f'{battle["driver_degradation_level"]} vs '
            f'{battle["target_degradation_level"]}'
        )
