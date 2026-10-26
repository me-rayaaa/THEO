from pit_strategy import calculate_pit_window


def laps_text(laps):
    if len(laps) == 1:
        return f'lap {laps[0]}'

    return f'laps {laps[0]}–{laps[-1]}'


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
        # Та же форма ответа, что и обычно: фронтенд не должен падать.
        return {
            "lap": target_lap,
            "driver": None,
            "recommendation": "NO_DATA",
            "best_lap": None,
            "optimal_window": [],
            "traffic_level": None,
            "projected_rejoin_position": None,
            "message": "No strategy data available."
        }

    driver = strategy["window"][0]["driver"]

    best_available = max(
        strategy["window"],
        key=lambda item: item["strategy_score"]
    )

    traffic_level = best_available["traffic_level"]
    projected_position = best_available["projected_rejoin_position"]

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
        pit_laps = [i["lap"] for i in strategy["window"] if i["decision"] == "PIT"]
        consider_laps = [i["lap"] for i in strategy["window"] if i["decision"] == "CONSIDER"]

        message_parts = [f'{driver}: pit window is open.']

        if pit_laps:
            message_parts.append(
                f'The preferred pit window is {laps_text(pit_laps)}, '
                f'with lap {strategy["best_lap"]} currently scoring highest.'
            )

        if consider_laps:
            message_parts.append(
                f'A stop around {laps_text(consider_laps)} '
                f'is also worth considering.'
            )

        message_parts.append(traffic_text)
        message = " ".join(message_parts)

    elif recommendation == "CONSIDER":
        optimal_window = strategy["optimal_window"]

        if optimal_window:
            message = (
                f'{driver}: a pit stop is worth considering around '
                f'{laps_text(optimal_window)}, but the model does not show '
                f'a strong enough advantage for an immediate stop. '
                f'{traffic_text}'
            )
        else:
            message = (
                f'{driver}: a pit stop is worth considering, '
                f'but there is no clear optimal window yet. '
                f'{traffic_text}'
            )

    elif traffic_level == "CLEAR":
        message = (
            f'{driver}: stay out. '
            f'A stop now is projected to rejoin around '
            f'P{projected_position} in clear air, but the estimated '
            f'fresh-tyre benefit does not yet outweigh the cost '
            f'of stopping.'
        )

    elif traffic_level == "MODERATE":
        message = (
            f'{driver}: stay out. '
            f'A stop now is projected to rejoin around '
            f'P{projected_position} in moderate traffic. '
            f'The track-position loss and traffic risk outweigh '
            f'the estimated fresh-tyre benefit.'
        )

    else:
        message = (
            f'{driver}: stay out. '
            f'A stop now is projected to rejoin around '
            f'P{projected_position} in heavy traffic. '
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
    for lap, driver_number in [(25, 4), (25, 16), (40, 63)]:
        result = build_strategy_commentary(lap, driver_number)
        print(result["recommendation"], "-", result["message"])
