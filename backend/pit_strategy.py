from statistics import median

from data_store import (
    DEFAULT_PIT_LOSS,
    LAST_LAP,
    MIN_PIT_SAMPLES,
    NEUTRALIZED_PIT_LOSS_FACTOR,
    PIT_LANE_TIME_ON_TRACK,
    get_numeric_gap,
    get_race_phase,
    pits,
)
from pit_gain_calibration import calculate_phase_gains
from race_state import get_race_state
from tyre_degradation import calculate_tyre_degradation


# Пороги возраста шин (кругов) для +1/+2/+3 к оценке. Ориентировочно, подобрать по данным.
TYRE_AGE_THRESHOLDS = {
    "SOFT": (7, 14, 20),
    "MEDIUM": (10, 20, 30),
    "HARD": (15, 28, 40),
}


def calculate_pit_loss(target_lap, race_status=None):
    # Только стопы, которые уже случились к этому кругу.
    durations = []

    for pit in pits:
        if pit["lap_number"] is None or pit["lap_number"] > target_lap:
            continue

        duration = pit.get("lane_duration")

        if duration is None:
            duration = pit.get("pit_duration")

        if duration is None or duration <= 0:
            continue

        durations.append(duration)

    if len(durations) >= MIN_PIT_SAMPLES:
        lane_time = median(durations)
    else:
        lane_time = DEFAULT_PIT_LOSS

    # Потеря = время в пит-лейне минус проезд того же участка по трассе.
    loss = lane_time - PIT_LANE_TIME_ON_TRACK

    # Под VSC/SC соперники едут медленно, стоп обходится дешевле.
    loss *= NEUTRALIZED_PIT_LOSS_FACTOR.get(race_status, 1.0)

    return round(loss, 3)


def get_phase_gain(phase_lap, known_until_lap=None):
    if known_until_lap is None:
        known_until_lap = phase_lap

    # Калибровка только по стопам до текущего круга.
    phase_gains = calculate_phase_gains(known_until_lap)

    data = phase_gains.get(get_race_phase(phase_lap))

    if data is None or data["median_gain"] is None:
        data = phase_gains["ALL"]

    return data["median_gain"]


def find_driver(race_state, driver_number):
    return next(
        (
            item
            for item in race_state["drivers"]
            if item["driver_number"] == driver_number
        ),
        None
    )


def calculate_rejoin(
    target_lap,
    driver_number,
    race_state=None
):
    if race_state is None:
        race_state = get_race_state(target_lap)

    driver = find_driver(race_state, driver_number)

    if driver is None:
        return None

    driver_gap = get_numeric_gap(driver["gap"])

    if driver_gap is None:
        return None

    pit_loss = calculate_pit_loss(
        target_lap,
        race_state["race_status"]
    )

    projected_gap = driver_gap + pit_loss

    projected_position = 1
    net_position = 1

    # Весь пелотон, а не только топ-10.
    for other in race_state["drivers"]:
        if other["driver_number"] == driver_number:
            continue

        other_gap = get_numeric_gap(other["gap"])

        if other_gap is None:
            continue

        if other_gap < projected_gap:
            projected_position += 1

        # Обязательный стоп: кто ещё не заезжал, потеряет pit_loss позже.
        owes_stop = other["pit_stops"] == 0
        other_net_gap = other_gap + (pit_loss if owes_stop else 0.0)

        if other_net_gap < projected_gap:
            net_position += 1

    return {
        "lap": target_lap,
        "driver": driver["name"],
        "current_position": driver["position"],
        "current_gap": driver_gap,
        "compound": driver["compound"],
        "tyre_age": driver["tyre_age"],
        "pit_loss": pit_loss,
        "projected_gap": round(projected_gap, 3),
        "projected_rejoin_position": projected_position,
        "projected_net_position": net_position
    }


def analyze_rejoin_traffic(
    target_lap,
    driver_number,
    projected_gap,
    traffic_threshold=2.0,
    race_state=None
):
    if race_state is None:
        race_state = get_race_state(target_lap)

    other_drivers = []

    for driver in race_state["drivers"]:
        if driver["driver_number"] == driver_number:
            continue

        gap = get_numeric_gap(driver["gap"])

        if gap is None:
            continue

        other_drivers.append({
            "name": driver["name"],
            "gap": gap
        })

    drivers_ahead = [d for d in other_drivers if d["gap"] < projected_gap]
    drivers_behind = [d for d in other_drivers if d["gap"] > projected_gap]

    car_ahead = max(drivers_ahead, key=lambda d: d["gap"]) if drivers_ahead else None
    car_behind = min(drivers_behind, key=lambda d: d["gap"]) if drivers_behind else None

    gap_ahead = round(projected_gap - car_ahead["gap"], 3) if car_ahead else None
    gap_behind = round(car_behind["gap"] - projected_gap, 3) if car_behind else None

    traffic_score = 0

    if gap_ahead is not None and gap_ahead < traffic_threshold:
        traffic_score += 1

    if gap_behind is not None and gap_behind < traffic_threshold:
        traffic_score += 1

    if traffic_score == 0:
        traffic_level = "CLEAR"
    elif traffic_score == 1:
        traffic_level = "MODERATE"
    else:
        traffic_level = "HEAVY"

    return {
        "traffic_level": traffic_level,
        "car_ahead": car_ahead["name"] if car_ahead else None,
        "gap_ahead": gap_ahead,
        "car_behind": car_behind["name"] if car_behind else None,
        "gap_behind": gap_behind
    }


def get_degradation_for_driver(target_lap, driver_number):
    degradation = calculate_tyre_degradation(target_lap)

    for driver in degradation["drivers"]:
        if driver["driver_number"] == driver_number:
            return driver

    return None


def calculate_strategy_score(item):
    score = 0.0

    # Чистая потеря: места, которые вернутся после стопов соперников, не считаем.
    position_loss = max(
        0,
        item["projected_net_position"] - item["current_position"]
    )

    score -= position_loss * 3

    tyre_age = item["tyre_age"]

    if tyre_age is not None:
        low, mid, high = TYRE_AGE_THRESHOLDS.get(
            item["compound"],
            TYRE_AGE_THRESHOLDS["MEDIUM"]
        )

        if tyre_age >= high:
            score += 3
        elif tyre_age >= mid:
            score += 2
        elif tyre_age >= low:
            score += 1

    degradation_level = item["degradation_level"]

    if degradation_level == "HIGH":
        score += 3
    elif degradation_level == "MODERATE":
        score += 2
    elif degradation_level == "LOW":
        score += 1

    fresh_gain = item["fresh_tyre_gain_per_lap"]

    if fresh_gain is not None:
        if fresh_gain >= 1.5:
            score += 3
        elif fresh_gain >= 1.0:
            score += 2
        elif fresh_gain >= 0.5:
            score += 1

    traffic_level = item["traffic_level"]

    if traffic_level == "MODERATE":
        score -= 2
    elif traffic_level == "HEAVY":
        score -= 4

    # Штраф за отрыв от лидера удалён: он не связан с выгодой стопа.

    return round(score, 2)


def downgrade_status(status):
    if status == "STRONG":
        return "POSSIBLE"

    return "WEAK"


def classify_strategy(score):
    if score >= 2:
        return "PIT"

    if score >= 0:
        return "CONSIDER"

    return "STAY_OUT"


def find_continuous_window(results):
    eligible = [
        item["lap"]
        for item in results
        if item["decision"] in {"PIT", "CONSIDER"}
    ]

    if not eligible:
        return []

    groups = []
    current_group = [eligible[0]]

    for lap in eligible[1:]:
        if lap == current_group[-1] + 1:
            current_group.append(lap)
        else:
            groups.append(current_group)
            current_group = [lap]

    groups.append(current_group)

    return max(
        groups,
        key=lambda group: (
            len(group),
            max(
                item["strategy_score"]
                for item in results
                if item["lap"] in group
            )
        )
    )


def calculate_pit_window(
    start_lap,
    driver_number,
    window_size=5,
    post_pit_laps=3
):
    # Всё считается по состоянию на start_lap. Будущие круги не читаются:
    # отрывы держим как сейчас, растёт только возраст шин.
    race_state = get_race_state(start_lap)

    rejoin = calculate_rejoin(start_lap, driver_number, race_state)

    empty = {
        "driver_number": driver_number,
        "window": [],
        "best_lap": None,
        "best_score": None,
        "best_projected_position": None,
        "optimal_window": [],
        "recommendation": "NO_DATA"
    }

    if rejoin is None:
        return empty

    degradation = get_degradation_for_driver(start_lap, driver_number)

    degradation_level = (
        degradation["degradation_level"]
        if degradation
        else "INSUFFICIENT_DATA"
    )

    traffic = analyze_rejoin_traffic(
        start_lap,
        driver_number,
        rejoin["projected_gap"],
        race_state=race_state
    )

    results = []

    for offset in range(window_size):
        lap = start_lap + offset

        if lap > LAST_LAP:
            break

        fresh_tyre_gain = get_phase_gain(lap, start_lap)

        expected_gain = None
        effective_projected_gap = None

        if fresh_tyre_gain is not None:
            expected_gain = round(fresh_tyre_gain * post_pit_laps, 3)
            effective_projected_gap = round(
                rejoin["projected_gap"] - expected_gain,
                3
            )

        tyre_age = (
            rejoin["tyre_age"] + offset
            if rejoin["tyre_age"] is not None
            else None
        )

        result = {
            **rejoin,
            "lap": lap,
            "tyre_age": tyre_age,
            "phase": get_race_phase(lap),
            "fresh_tyre_gain_per_lap": fresh_tyre_gain,
            "post_pit_laps": post_pit_laps,
            "expected_gain": expected_gain,
            "effective_projected_gap": effective_projected_gap,
            "degradation_level": degradation_level,
            **traffic
        }

        result["strategy_score"] = calculate_strategy_score(result)
        result["decision"] = classify_strategy(result["strategy_score"])

        results.append(result)

    if not results:
        return empty

    best_result = max(results, key=lambda item: item["strategy_score"])

    recommendation = best_result["decision"]

    optimal_window = (
        []
        if recommendation == "STAY_OUT"
        else find_continuous_window(results)
    )

    return {
        "driver_number": driver_number,
        "window": results,
        "best_lap": (
            best_result["lap"]
            if recommendation != "STAY_OUT"
            else None
        ),
        "best_score": best_result["strategy_score"],
        "best_projected_position": best_result["projected_rejoin_position"],
        "optimal_window": optimal_window,
        "recommendation": recommendation
    }


if __name__ == "__main__":
    for lap, driver_number in [(25, 4), (60, 12), (70, 4)]:
        result = calculate_pit_window(start_lap=lap, driver_number=driver_number)

        print(
            "lap:", lap,
            "| recommendation:", result["recommendation"],
            "| best lap:", result["best_lap"],
            "| window:", [item["lap"] for item in result["window"]]
        )
