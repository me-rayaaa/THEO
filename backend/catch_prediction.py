from battle_analysis import analyze_battles


def predict_catch(target_lap):
    analysis = analyze_battles(target_lap)

    predictions = []

    for battle in analysis["battles"]:
        if battle["gap_trend"] != "CLOSING":
            continue

        closing_rate = battle["closing_rate"]
        gap = battle["current_gap"]

        if closing_rate <= 0:
            continue

        laps_to_catch = gap / closing_rate

        if laps_to_catch > 15:
            continue

        predictions.append({
            "driver": battle["driver"],
            "target": battle["target"],
            "gap": gap,
            "closing_rate": closing_rate,
            "laps_to_catch": round(laps_to_catch, 1),
            "priority": battle["priority"]
        })

    return {
        "lap": target_lap,
        "predictions": predictions
    }


if __name__ == "__main__":
    result = predict_catch(60)

    for item in result["predictions"]:
        print(
            f'{item["driver"]} -> '
            f'{item["target"]} | '
            f'gap: {item["gap"]} | '
            f'rate: {item["closing_rate"]} | '
            f'catch in: {item["laps_to_catch"]} laps'
        )