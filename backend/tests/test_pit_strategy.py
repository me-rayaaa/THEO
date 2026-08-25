import _bootstrap
from pit_strategy import calculate_pit_window


tests = [
    {
        "name": "Norris",
        "driver_number": 4,
        "start_lap": 25
    },
    {
        "name": "Leclerc",
        "driver_number": 16,
        "start_lap": 25
    },
    {
        "name": "Verstappen",
        "driver_number": 1,
        "start_lap": 25
    },
    {
        "name": "Russell",
        "driver_number": 63,
        "start_lap": 40
    },
    {
        "name": "Piastri",
        "driver_number": 81,
        "start_lap": 40
    },
    {
        "name": "Antonelli",
        "driver_number": 12,
        "start_lap": 55
    }
]


for test in tests:
    print("\n" + "=" * 70)
    print(
        test["name"],
        "| start lap:",
        test["start_lap"]
    )

    result = calculate_pit_window(
        start_lap=test["start_lap"],
        driver_number=test["driver_number"],
        window_size=5,
        post_pit_laps=3
    )

    for item in result["window"]:
        print(
            f'Lap {item["lap"]} | '
            f'P{item["current_position"]} -> '
            f'P{item["projected_rejoin_position"]} | '
            f'age {item["tyre_age"]} | '
            f'deg {item["degradation_level"]} | '
            f'traffic {item["traffic_level"]} | '
            f'fresh gain {item["fresh_tyre_gain_per_lap"]} | '
            f'score {item["strategy_score"]} | '
            f'{item["decision"]}'
        )

    print(
        "Recommendation:",
        result["recommendation"]
    )

    print(
        "Best lap:",
        result["best_lap"],
        "| score:",
        result.get("best_score")
    )

    print(
        "Optimal window:",
        result["optimal_window"]
    )