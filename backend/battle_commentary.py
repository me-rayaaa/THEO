from battle_analysis import analyze_battles
from catch_prediction import predict_catch
from tyre_intelligence import build_tyre_intelligence


def build_battle_commentary(target_lap):
    analysis = analyze_battles(target_lap)
    catch_data = predict_catch(target_lap)
    tyre_data = build_tyre_intelligence(target_lap)

    catch_by_pair = {
        (item["driver_number"], item["target_number"]): item
        for item in catch_data["predictions"]
    }

    tyre_by_pair = {
        (item["driver_number"], item["target_number"]): item
        for item in tyre_data["battles"]
    }

    messages = []

    for battle in analysis["battles"]:
        if battle["priority"] == "LOW":
            continue

        driver = battle["driver"]
        target = battle["target"]
        pair = (battle["driver_number"], battle["target_number"])

        if battle["gap_trend"] == "CLOSING":
            text = (
                f'{driver} is closing on {target}. '
                f'The gap is {battle["current_gap"]} seconds, '
                f'with a closing rate of about '
                f'{battle["closing_rate"]} seconds per lap.'
            )

            catch = catch_by_pair.get(pair)

            if (
                catch
                and battle["closing_rate"] >= 0.2
                and catch["laps_to_catch"] <= 10
            ):
                text += (
                    f' If this trend continues, '
                    f'{driver} could reach {target} in around '
                    f'{round(catch["laps_to_catch"])} laps.'
                )

            tyre = tyre_by_pair.get(pair)

            if tyre:
                driver_level = tyre["driver_degradation_level"]
                target_level = tyre["target_degradation_level"]

                if (
                    target_level == "HIGH"
                    and driver_level in {"LOW", "MODERATE"}
                ):
                    text += (
                        f' {target} is also showing a stronger '
                        f'tyre-related pace-loss signal than {driver}, '
                        f'which may be contributing to the closing gap.'
                    )

        elif battle["gap_trend"] == "STABLE":
            text = (
                f'{driver} is running close to {target}, '
                f'but the gap is currently stable at '
                f'{battle["current_gap"]} seconds.'
            )

        else:
            text = (
                f'{driver} is dropping back from {target}. '
                f'The current gap is '
                f'{battle["current_gap"]} seconds.'
            )

        messages.append({
            "priority": battle["priority"],
            "driver": driver,
            "target": target,
            "message": text
        })

    if not messages:
        messages.append({
            "priority": "INFO",
            "driver": None,
            "target": None,
            "message": "No significant on-track battles detected."
        })

    return {
        "lap": target_lap,
        "messages": messages
    }


if __name__ == "__main__":
    for item in build_battle_commentary(60)["messages"]:
        print(item["priority"], "-", item["message"])
