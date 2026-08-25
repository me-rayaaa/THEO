from pit_strategy import calculate_pit_window


def build_strategy_commentary(
    target_lap,
    driver_number,
    window_size=5
):
    strategy = calculate_pit_window(
        start_lap=target_lap,
        driver_number=driver_number,
        window_size=window_size,
        post_pit_laps=3
    )

    recommendation = strategy["recommendation"]

    if not strategy["window"]:
        return {
            "lap": target_lap,
            "recommendation": "NO_DATA",
            "message": "No strategy data available."
        }

    first_item = strategy["window"][0]
    driver = first_item["driver"]

    best_available = max(
        strategy["window"],
        key=lambda item: item["strategy_score"]
    )

    traffic_level = best_available["traffic_level"]
    projected_position = best_available[
        "projected_rejoin_position"
    ]

    if traffic_level == "CLEAR":
        traffic_text = (
            f'The projected rejoin around P{projected_position} '
            f'looks relatively clear.'
        )

    elif traffic_level == "MODERATE":
        traffic_text = (
            f'The projected rejoin around P{projected_position} '
            f'would place the car in moderate traffic.'
        )

    else:
        traffic_text = (
            f'The projected rejoin around P{projected_position} '
            f'would place the car in heavy traffic.'
        )

    if recommendation == "PIT":
        pit_laps = [
            item["lap"]
            for item in strategy["window"]
            if item["decision"] == "PIT"
        ]

        consider_laps = [
            item["lap"]
            for item in strategy["window"]
            if item["decision"] == "CONSIDER"
        ]

        message_parts = [
            f'{driver}: pit window is open.'
        ]

        if pit_laps:
            if len(pit_laps) == 1:
                pit_window_text = f'lap {pit_laps[0]}'
            else:
                pit_window_text = (
                    f'laps {pit_laps[0]}–{pit_laps[-1]}'
                )

            message_parts.append(
                f'The preferred pit window is {pit_window_text}, '
                f'with lap {strategy["best_lap"]} currently '
                f'scoring highest.'
            )

        if consider_laps:
            if len(consider_laps) == 1:
                consider_text = f'lap {consider_laps[0]}'
            else:
                consider_text = (
                    f'laps {consider_laps[0]}–'
                    f'{consider_laps[-1]}'
                )

            message_parts.append(
                f'An earlier stop around {consider_text} '
                f'is also worth considering.'
            )

        message_parts.append(traffic_text)

        message = " ".join(message_parts)

    elif recommendation == "CONSIDER":
        optimal_window = strategy["optimal_window"]

        if optimal_window:
            if len(optimal_window) == 1:
                window_text = f'lap {optimal_window[0]}'
            else:
                window_text = (
                    f'laps {optimal_window[0]}–'
                    f'{optimal_window[-1]}'
                )

            message = (
                f'{driver}: a pit stop is worth considering around '
                f'{window_text}, but the model does not show a strong '
                f'enough advantage for an immediate stop. '
                f'{traffic_text}'
            )

        else:
            message = (
                f'{driver}: a pit stop is worth considering, '
                f'but there is no clear optimal window yet. '
                f'{traffic_text}'
            )

    else:
        if traffic_level == "CLEAR":
            message = (
                f'{driver}: stay out. '
                f'A stop in the next {window_size} laps is currently '
                f'projected to lose too much track position, even though '
                f'the rejoin itself would be relatively clear. '
                f'The estimated fresh-tyre benefit is not enough '
                f'to offset that loss.'
            )

        elif traffic_level == "MODERATE":
            message = (
                f'{driver}: stay out. '
                f'A stop in the next {window_size} laps is currently '
                f'projected to rejoin around P{projected_position} '
                f'in moderate traffic. '
                f'The track-position loss and traffic risk outweigh '
                f'the estimated fresh-tyre benefit.'
            )

        else:
            message = (
                f'{driver}: stay out. '
                f'A stop in the next {window_size} laps is currently '
                f'projected to rejoin around P{projected_position} '
                f'in heavy traffic. '
                f'The track-position loss and traffic risk strongly '
                f'outweigh the estimated fresh-tyre benefit.'
            )

    return {
        "lap": target_lap,
        "driver": driver,
        "recommendation": recommendation,
        "best_lap": strategy["best_lap"],
        "optimal_window": strategy["optimal_window"],
        "traffic_level": traffic_level,
        "projected_rejoin_position": projected_position,
        "message": message
    }


if __name__ == "__main__":
    tests = [
        (25, 4),
        (25, 16),
        (25, 1),
        (40, 63),
        (40, 81),
        (55, 12)
    ]

    for lap, driver_number in tests:
        result = build_strategy_commentary(
            lap,
            driver_number
        )

        print(
            result["recommendation"],
            "-",
            result["message"]
        )