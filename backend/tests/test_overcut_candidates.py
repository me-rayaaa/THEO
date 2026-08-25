import _bootstrap

from race_state import get_race_state
from overcut_analysis import analyze_overcut


START_LAP = 10
END_LAP = 69

candidates = []

for lap in range(START_LAP, END_LAP + 1):
    race_state = get_race_state(lap)

    drivers = sorted(
        race_state["drivers"],
        key=lambda item: item["position"]
    )

    for index in range(1, len(drivers)):
        driver = drivers[index]
        target = drivers[index - 1]

        result = analyze_overcut(
            target_lap=lap,
            driver_number=driver["driver_number"],
            target_driver_number=target["driver_number"],
            stay_out_laps=2
        )

        if result is None:
            continue

        if result["overcut_status"] != "WEAK":
            continue

        score = 0.0

        projected_gap = result[
            "projected_gap_before_driver_stop"
        ]

        position_loss = result["position_loss"]

        traffic = result["target_traffic_level"]

        driver_deg = result[
            "driver_degradation_level"
        ]

        if projected_gap <= 3.0:
            score += 5
        elif projected_gap <= 5.0:
            score += 4
        elif projected_gap <= 8.0:
            score += 2
        elif projected_gap <= 12.0:
            score += 1

        if position_loss <= 0:
            score += 4
        elif position_loss == 1:
            score += 3
        elif position_loss == 2:
            score += 1

        if traffic == "HEAVY":
            score += 3
        elif traffic == "MODERATE":
            score += 2

        if driver_deg == "NO_CLEAR_DEGRADATION_SIGNAL":
            score += 2
        elif driver_deg == "LOW":
            score += 1

        candidate = result.copy()
        candidate["candidate_score"] = score

        candidates.append(candidate)


candidates = sorted(
    candidates,
    key=lambda item: (
        item["candidate_score"],
        -item["projected_gap_before_driver_stop"]
    ),
    reverse=True
)


print("\nTOP 10 WEAK OVERCUT CANDIDATES")

for item in candidates[:10]:
    print("\n" + "=" * 70)

    print(
        f'LAP {item["lap"]} | '
        f'score {item["candidate_score"]} | '
        f'P{item["driver_position"]} '
        f'{item["driver"]} -> '
        f'P{item["target_position"]} '
        f'{item["target"]}'
    )

    print(
        "current gap:",
        item["current_gap"]
    )

    print(
        "projected gap:",
        item["projected_gap_before_driver_stop"]
    )

    print(
        "position loss:",
        item["position_loss"]
    )

    print(
        "target traffic:",
        item["target_traffic_level"]
    )

    print(
        "driver degradation:",
        item["driver_degradation_level"]
    )

    print(
        "target degradation:",
        item["target_degradation_level"]
    )

    print(
        "net target advantage/lap:",
        item["net_target_advantage_per_lap"]
    )