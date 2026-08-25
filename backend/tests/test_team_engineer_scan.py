import _bootstrap
from strategy_commentary import build_strategy_commentary
from rival_strategy_decision import build_rival_strategy_decision
from tyre_degradation import calculate_tyre_degradation
from battle_analysis import analyze_battles
from race_state import get_race_state


def get_driver_degradation(target_lap, driver_name):
    data = calculate_tyre_degradation(target_lap)

    for item in data["drivers"]:
        if item["driver"] == driver_name:
            return item

    return None


def get_driver_battle(target_lap, driver_name):
    data = analyze_battles(target_lap)

    if isinstance(data, dict):
        battles = data.get("battles", [])
    else:
        battles = data

    for battle in battles:
        if battle.get("driver") == driver_name:
            return battle

    return None


def get_rival_decision(
    target_lap,
    driver_number,
    driver_position,
    race_state
):
    if driver_position <= 1:
        return None

    target = next(
        (
            item
            for item in race_state["drivers"]
            if item["position"] == driver_position - 1
        ),
        None
    )

    if target is None:
        return None

    return build_rival_strategy_decision(
        target_lap=target_lap,
        driver_number=driver_number,
        target_driver_number=target["driver_number"]
    )


def build_team_engineer_strategy(
    target_lap,
    driver_number
):
    race_state = get_race_state(target_lap)

    driver = next(
        (
            item
            for item in race_state["drivers"]
            if item["driver_number"] == driver_number
        ),
        None
    )

    if driver is None:
        return {
            "lap": target_lap,
            "decision": "NO_DATA",
            "message": "No driver data available."
        }

    strategy = build_strategy_commentary(
        target_lap=target_lap,
        driver_number=driver_number
    )

    degradation = get_driver_degradation(
        target_lap,
        driver["name"]
    )

    battle = get_driver_battle(
        target_lap,
        driver["name"]
    )

    rival = get_rival_decision(
        target_lap=target_lap,
        driver_number=driver_number,
        driver_position=driver["position"],
        race_state=race_state
    )

    pit_recommendation = strategy["recommendation"]

    degradation_level = (
        degradation["degradation_level"]
        if degradation
        else "INSUFFICIENT_DATA"
    )

    battle_priority = (
        battle["priority"]
        if battle
        else None
    )

    rival_decision = (
        rival["decision"]
        if rival
        else None
    )

    pit_now_trigger = False
    pit_window_trigger = False

    if pit_recommendation == "PIT":

        if degradation_level == "HIGH":
            pit_now_trigger = True

        elif (
            rival_decision == "UNDERCUT_PREFERRED"
            and battle_priority == "HIGH"
        ):
            pit_now_trigger = True

        elif (
            rival_decision == "UNDERCUT_PREFERRED"
            and degradation_level in {
                "MODERATE",
                "HIGH"
            }
        ):
            pit_now_trigger = True

        else:
            pit_window_trigger = True

    elif pit_recommendation == "CONSIDER":

        if (
            degradation_level == "HIGH"
            and rival_decision == "UNDERCUT_PREFERRED"
        ):
            pit_window_trigger = True

        elif (
            degradation_level == "HIGH"
            and battle_priority == "HIGH"
        ):
            pit_window_trigger = True

    if pit_recommendation == "STAY_OUT":
        final_decision = "STAY_OUT"

    elif pit_now_trigger:
        final_decision = "PIT_NOW"

    elif pit_window_trigger:
        final_decision = "PIT_WINDOW_OPEN"

    elif pit_recommendation == "PIT":
        final_decision = "PIT_WINDOW_OPEN"

    elif pit_recommendation == "CONSIDER":
        final_decision = "HOLD_AND_MONITOR"

    else:
        final_decision = "HOLD_AND_MONITOR"

    reasons = []

    if pit_recommendation == "PIT":
        reasons.append(
            "The current pit model shows an active pit window."
        )

    elif pit_recommendation == "CONSIDER":
        reasons.append(
            "A pit stop is worth considering, but the base model does not yet support an immediate stop."
        )

    elif pit_recommendation == "STAY_OUT":
        reasons.append(
            "The current pit model favors staying out."
        )

    if degradation_level == "HIGH":
        reasons.append(
            "Tyre degradation is showing a strong pace-loss signal."
        )

    elif degradation_level == "MODERATE":
        reasons.append(
            "Tyre degradation is becoming relevant."
        )

    elif degradation_level == "LOW":
        reasons.append(
            "Tyre degradation is currently limited."
        )

    elif degradation_level == "NO_CLEAR_DEGRADATION_SIGNAL":
        reasons.append(
            "There is no clear tyre degradation signal at the moment."
        )

    if rival_decision == "UNDERCUT_PREFERRED":
        reasons.append(
            "The undercut is currently the stronger option against the car ahead."
        )

    elif rival_decision == "OVERCUT_PREFERRED":
        reasons.append(
            "The overcut is currently the stronger option against the car ahead."
        )

    elif rival_decision == "BOTH_POSSIBLE":
        reasons.append(
            "Both undercut and overcut remain viable against the car ahead."
        )

    elif rival_decision == "NO_CLEAR_ADVANTAGE":
        reasons.append(
            "There is no clear strategic advantage against the car ahead."
        )

    if battle_priority == "HIGH":
        reasons.append(
            "The driver is involved in a high-priority battle."
        )

    elif battle_priority == "MEDIUM":
        reasons.append(
            "There is moderate battle pressure around the driver."
        )

    if final_decision == "PIT_NOW":
        reasons.append(
            "Multiple strategic signals support committing to the stop now."
        )

    elif final_decision == "PIT_WINDOW_OPEN":
        reasons.append(
            "The pit window is open, but the evidence is not strong enough to require an immediate stop."
        )

    elif final_decision == "HOLD_AND_MONITOR":
        reasons.append(
            "The situation should be monitored before committing to a stop."
        )

    elif final_decision == "STAY_OUT":
        reasons.append(
            "No secondary signal is strong enough to override the stay-out recommendation."
        )

    message = " ".join(reasons)

    return {
        "lap": target_lap,
        "driver": driver["name"],
        "position": driver["position"],
        "decision": final_decision,
        "pit_recommendation": pit_recommendation,
        "degradation_level": degradation_level,
        "rival_decision": rival_decision,
        "battle_priority": battle_priority,
        "pit_now_trigger": pit_now_trigger,
        "pit_window_trigger": pit_window_trigger,
        "message": message
    }


if __name__ == "__main__":
    tests = [
        (25, 4),
        (25, 16),
        (38, 31),
        (45, 1),
        (60, 12)
    ]

    for lap, driver_number in tests:
        result = build_team_engineer_strategy(
            target_lap=lap,
            driver_number=driver_number
        )

        print()
        print("=" * 70)
        print(result)