import json
from statistics import median

from race_state import get_race_state
from pit_gain_calibration import calculate_phase_gains
from tyre_degradation import calculate_tyre_degradation


pit_file = "../data/mexico_2025/pit.json"

with open(
    pit_file,
    "r",
    encoding="utf-8"
) as file:
    pits = json.load(file)


def calculate_pit_loss():
    durations = []

    for pit in pits:
        duration = pit.get("lane_duration")

        if duration is None:
            duration = pit.get("pit_duration")

        if duration is None:
            continue

        if duration <= 0:
            continue

        durations.append(duration)

    if not durations:
        return None

    return round(
        median(durations),
        3
    )


def get_race_phase(lap_number):
    if lap_number <= 25:
        return "EARLY"

    if lap_number <= 45:
        return "MIDDLE"

    return "LATE"


def get_phase_gain(lap_number):
    phase = get_race_phase(
        lap_number
    )

    phase_gains = calculate_phase_gains()

    data = phase_gains.get(
        phase
    )

    if data is None:
        return None

    return data["median_gain"]


def get_numeric_gap(gap):
    if gap is None:
        return None

    if isinstance(
        gap,
        (int, float)
    ):
        return float(gap)

    if isinstance(gap, str):

        if "LAP" in gap.upper():
            return None

        try:
            return float(gap)

        except ValueError:
            return None

    return None


def calculate_rejoin(
    target_lap,
    driver_number
):
    race_state = get_race_state(
        target_lap
    )

    pit_loss = calculate_pit_loss()

    driver = next(
        (
            item
            for item in race_state["drivers"]
            if item["driver_number"]
            == driver_number
        ),
        None
    )

    if (
        driver is None
        or pit_loss is None
    ):
        return None

    driver_gap = driver["gap"]

    if not isinstance(
        driver_gap,
        (int, float)
    ):
        return None

    projected_gap = (
        driver_gap
        + pit_loss
    )

    projected_position = 1

    for other in race_state["drivers"]:

        if (
            other["driver_number"]
            == driver_number
        ):
            continue

        other_gap = other["gap"]

        if not isinstance(
            other_gap,
            (int, float)
        ):
            continue

        if other_gap < projected_gap:
            projected_position += 1

    return {
        "lap": target_lap,
        "driver": driver["name"],
        "current_position":
            driver["position"],
        "current_gap":
            driver_gap,
        "tyre_age":
            driver["tyre_age"],
        "pit_loss":
            pit_loss,
        "projected_gap":
            round(
                projected_gap,
                3
            ),
        "projected_rejoin_position":
            projected_position
    }


def analyze_rejoin_traffic(
    target_lap,
    driver_number,
    projected_gap,
    traffic_threshold=2.0
):
    race_state = get_race_state(
        target_lap
    )

    other_drivers = []

    for driver in race_state["drivers"]:

        if (
            driver["driver_number"]
            == driver_number
        ):
            continue

        gap = get_numeric_gap(
            driver["gap"]
        )

        if gap is None:
            continue

        other_drivers.append({
            "name": driver["name"],
            "gap": gap
        })

    drivers_ahead = [
        driver
        for driver in other_drivers
        if driver["gap"]
        < projected_gap
    ]

    drivers_behind = [
        driver
        for driver in other_drivers
        if driver["gap"]
        > projected_gap
    ]

    car_ahead = None
    car_behind = None

    if drivers_ahead:
        car_ahead = max(
            drivers_ahead,
            key=lambda driver:
                driver["gap"]
        )

    if drivers_behind:
        car_behind = min(
            drivers_behind,
            key=lambda driver:
                driver["gap"]
        )

    gap_ahead = None
    gap_behind = None

    if car_ahead:
        gap_ahead = round(
            projected_gap
            - car_ahead["gap"],
            3
        )

    if car_behind:
        gap_behind = round(
            car_behind["gap"]
            - projected_gap,
            3
        )

    traffic_score = 0

    if (
        gap_ahead is not None
        and gap_ahead
        < traffic_threshold
    ):
        traffic_score += 1

    if (
        gap_behind is not None
        and gap_behind
        < traffic_threshold
    ):
        traffic_score += 1

    if traffic_score == 0:
        traffic_level = "CLEAR"

    elif traffic_score == 1:
        traffic_level = "MODERATE"

    else:
        traffic_level = "HEAVY"

    return {
        "traffic_level":
            traffic_level,
        "car_ahead":
            car_ahead["name"]
            if car_ahead
            else None,
        "gap_ahead":
            gap_ahead,
        "car_behind":
            car_behind["name"]
            if car_behind
            else None,
        "gap_behind":
            gap_behind
    }


def get_degradation_for_driver(
    target_lap,
    driver_name
):
    degradation = (
        calculate_tyre_degradation(
            target_lap
        )
    )

    for driver in degradation["drivers"]:

        if (
            driver["driver"]
            == driver_name
        ):
            return driver

    return None


def calculate_strategy_score(item):
    score = 0.0

    position_loss = (
        item[
            "projected_rejoin_position"
        ]
        - item[
            "current_position"
        ]
    )

    score -= position_loss * 3

    tyre_age = item[
        "tyre_age"
    ]

    if tyre_age is not None:

        if tyre_age >= 30:
            score += 3

        elif tyre_age >= 20:
            score += 2

        elif tyre_age >= 10:
            score += 1

    degradation_level = item[
        "degradation_level"
    ]

    if degradation_level == "HIGH":
        score += 3

    elif degradation_level == "MODERATE":
        score += 2

    elif degradation_level == "LOW":
        score += 1

    fresh_gain = item[
        "fresh_tyre_gain_per_lap"
    ]

    if fresh_gain is not None:

        if fresh_gain >= 1.5:
            score += 3

        elif fresh_gain >= 1.0:
            score += 2

        elif fresh_gain >= 0.5:
            score += 1

    traffic_level = item[
        "traffic_level"
    ]

    if traffic_level == "MODERATE":
        score -= 2

    elif traffic_level == "HEAVY":
        score -= 4

    effective_gap = item[
        "effective_projected_gap"
    ]

    if effective_gap is not None:
        score -= (
            effective_gap
            / 20
        )

    return round(
        score,
        2
    )


def classify_strategy(score):
    if score >= 2:
        return "PIT"

    if score >= 0:
        return "CONSIDER"

    return "STAY_OUT"


def find_continuous_window(
    results
):
    eligible = [
        item["lap"]
        for item in results
        if item["decision"]
        in {
            "PIT",
            "CONSIDER"
        }
    ]

    if not eligible:
        return []

    groups = []
    current_group = [
        eligible[0]
    ]

    for lap in eligible[1:]:

        if (
            lap
            == current_group[-1] + 1
        ):
            current_group.append(
                lap
            )

        else:
            groups.append(
                current_group
            )

            current_group = [
                lap
            ]

    groups.append(
        current_group
    )

    best_group = max(
        groups,
        key=lambda group: (
            len(group),
            max(
                item[
                    "strategy_score"
                ]
                for item in results
                if item["lap"]
                in group
            )
        )
    )

    return best_group


def calculate_pit_window(
    start_lap,
    driver_number,
    window_size=5,
    post_pit_laps=3
):
    results = []

    for lap in range(
        start_lap,
        start_lap + window_size
    ):

        try:
            rejoin = calculate_rejoin(
                lap,
                driver_number
            )

        except (
            ValueError,
            IndexError
        ):
            break

        except Exception:
            break

        if rejoin is None:
            continue

        fresh_tyre_gain = (
            get_phase_gain(
                lap
            )
        )

        expected_gain = None
        effective_projected_gap = None

        if fresh_tyre_gain is not None:

            expected_gain = round(
                fresh_tyre_gain
                * post_pit_laps,
                3
            )

            effective_projected_gap = round(
                rejoin["projected_gap"]
                - expected_gain,
                3
            )

        try:
            degradation = (
                get_degradation_for_driver(
                    lap,
                    rejoin["driver"]
                )
            )

        except Exception:
            degradation = None

        degradation_level = (
            "INSUFFICIENT_DATA"
        )

        if degradation:
            degradation_level = (
                degradation[
                    "degradation_level"
                ]
            )

        try:
            traffic = (
                analyze_rejoin_traffic(
                    lap,
                    driver_number,
                    rejoin[
                        "projected_gap"
                    ]
                )
            )

        except Exception:
            traffic = {
                "traffic_level":
                    "UNKNOWN",
                "car_ahead":
                    None,
                "gap_ahead":
                    None,
                "car_behind":
                    None,
                "gap_behind":
                    None
            }

        result = {
            **rejoin,
            "phase":
                get_race_phase(lap),
            "fresh_tyre_gain_per_lap":
                fresh_tyre_gain,
            "post_pit_laps":
                post_pit_laps,
            "expected_gain":
                expected_gain,
            "effective_projected_gap":
                effective_projected_gap,
            "degradation_level":
                degradation_level,
            "traffic_level":
                traffic[
                    "traffic_level"
                ],
            "car_ahead":
                traffic[
                    "car_ahead"
                ],
            "gap_ahead":
                traffic[
                    "gap_ahead"
                ],
            "car_behind":
                traffic[
                    "car_behind"
                ],
            "gap_behind":
                traffic[
                    "gap_behind"
                ]
        }

        strategy_score = (
            calculate_strategy_score(
                result
            )
        )

        result[
            "strategy_score"
        ] = strategy_score

        result[
            "decision"
        ] = classify_strategy(
            strategy_score
        )

        results.append(
            result
        )

    if not results:
        return {
            "driver_number":
                driver_number,
            "window":
                [],
            "best_lap":
                None,
            "best_score":
                None,
            "best_projected_position":
                None,
            "optimal_window":
                [],
            "recommendation":
                "NO_DATA"
        }

    best_result = max(
        results,
        key=lambda item:
            item[
                "strategy_score"
            ]
    )

    optimal_window = (
        find_continuous_window(
            results
        )
    )

    if (
        best_result["decision"]
        == "PIT"
    ):
        recommendation = "PIT"

    elif (
        best_result["decision"]
        == "CONSIDER"
    ):
        recommendation = "CONSIDER"

    else:
        recommendation = "STAY_OUT"

    if (
        recommendation
        == "STAY_OUT"
    ):
        optimal_window = []

    return {
        "driver_number":
            driver_number,
        "window":
            results,
        "best_lap":
            (
                best_result["lap"]
                if recommendation
                != "STAY_OUT"
                else None
            ),
        "best_score":
            best_result[
                "strategy_score"
            ],
        "best_projected_position":
            best_result[
                "projected_rejoin_position"
            ],
        "optimal_window":
            optimal_window,
        "recommendation":
            recommendation
    }


if __name__ == "__main__":
    tests = [
        (25, 4),
        (60, 12),
        (70, 4)
    ]

    for lap, driver_number in tests:

        print()
        print("=" * 70)

        try:
            result = calculate_pit_window(
                start_lap=lap,
                driver_number=driver_number,
                window_size=5,
                post_pit_laps=3
            )

            print(
                "lap:",
                lap
            )

            print(
                "recommendation:",
                result[
                    "recommendation"
                ]
            )

            print(
                "best lap:",
                result[
                    "best_lap"
                ]
            )

            print(
                "window:",
                [
                    item["lap"]
                    for item
                    in result["window"]
                ]
            )

        except Exception as error:
            print(
                {
                    "lap": lap,
                    "error":
                        str(error)
                }
            )