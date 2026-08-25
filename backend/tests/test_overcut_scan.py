import _bootstrap

from race_state import get_race_state
from overcut_analysis import analyze_overcut


START_LAP = 10
END_LAP = 69

found = []

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

        if result["overcut_status"] not in {
            "POSSIBLE",
            "STRONG"
        }:
            continue

        found.append(result)

        print("\n" + "=" * 70)

        print(
            f'LAP {lap} | '
            f'{result["overcut_status"]} | '
            f'P{result["driver_position"]} '
            f'{result["driver"]} -> '
            f'P{result["target_position"]} '
            f'{result["target"]}'
        )

        print(
            "current gap:",
            result["current_gap"]
        )

        print(
            "driver recent pace:",
            result["driver_recent_pace"]
        )

        print(
            "target recent pace:",
            result["target_recent_pace"]
        )

        print(
            "relative pace/lap:",
            result["relative_pace_per_lap"]
        )

        print(
            "gap after target stop:",
            result["gap_after_target_stop"]
        )

        print(
            "gap before driver stop:",
            result["gap_before_driver_stop"]
        )

        print(
            "gap after full pit cycle:",
            result["gap_after_driver_stop"]
        )

        print(
            "driver projected rejoin:",
            f'P{result["driver_projected_rejoin_position"]}'
        )

        print(
            "position loss:",
            result["position_loss"]
        )


print("\n" + "=" * 70)
print("SCAN COMPLETE")
print("Opportunities found:", len(found))