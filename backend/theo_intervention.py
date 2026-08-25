from team_engineer_strategy import build_team_engineer_strategy


def get_strategy_signature(strategy):
    if strategy is None:
        return None

    if strategy.get("decision") in {
        None,
        "NO_DATA"
    }:
        return None

    return (
        strategy.get("decision"),
        strategy.get("pit_recommendation"),
        strategy.get("degradation_level"),
        strategy.get("rival_decision"),
        strategy.get("battle_priority"),
        strategy.get("race_status"),
        strategy.get("neutralized"),
    )


def is_valid_previous_state(strategy):
    if strategy is None:
        return False

    if strategy.get("decision") in {
        None,
        "NO_DATA"
    }:
        return False

    if strategy.get("driver") is None:
        return False

    return True


def get_intervention_priority(strategy):
    if strategy is None:
        return "INFO"

    decision = strategy.get("decision")
    degradation = strategy.get("degradation_level")
    rival_decision = strategy.get("rival_decision")
    battle_priority = strategy.get("battle_priority")
    race_status = strategy.get("race_status")
    neutralization_trigger = strategy.get(
        "neutralization_trigger",
        False
    )

    if decision == "PIT_NOW":
        return "CRITICAL"

    if (
        race_status in {
            "VSC",
            "SAFETY_CAR"
        }
        and neutralization_trigger
    ):
        return "CRITICAL"

    if decision == "PIT_WINDOW_OPEN":
        return "HIGH"

    if rival_decision in {
        "UNDERCUT_PREFERRED",
        "OVERCUT_PREFERRED"
    }:
        return "HIGH"

    if degradation == "HIGH":
        return "HIGH"

    if battle_priority == "HIGH":
        return "HIGH"

    return "INFO"


def build_change_message(
    current,
    previous
):
    if not is_valid_previous_state(previous):
        return None

    changes = []

    if (
        current.get("decision")
        != previous.get("decision")
    ):
        changes.append(
            f'Team Engineer decision changed from '
            f'{previous.get("decision")} to '
            f'{current.get("decision")}.'
        )

    if (
        current.get("rival_decision")
        != previous.get("rival_decision")
    ):
        previous_rival = previous.get(
            "rival_decision"
        )

        current_rival = current.get(
            "rival_decision"
        )

        if current_rival not in {
            None,
            "NO_DATA"
        }:
            changes.append(
                f'Rival strategy changed to '
                f'{current_rival}.'
            )

        elif (
            previous_rival not in {
                None,
                "NO_DATA"
            }
        ):
            changes.append(
                "The previous rival strategy signal is no longer active."
            )

    if (
        current.get("degradation_level")
        != previous.get("degradation_level")
    ):
        previous_degradation = previous.get(
            "degradation_level"
        )

        current_degradation = current.get(
            "degradation_level"
        )

        if (
            previous_degradation is not None
            and current_degradation is not None
        ):
            changes.append(
                f'Tyre degradation changed from '
                f'{previous_degradation} '
                f'to {current_degradation}.'
            )

    if (
        current.get("battle_priority")
        != previous.get("battle_priority")
    ):
        previous_battle = previous.get(
            "battle_priority"
        )

        current_battle = current.get(
            "battle_priority"
        )

        if current_battle is not None:
            changes.append(
                f'Battle pressure is now '
                f'{current_battle}.'
            )

        elif previous_battle is not None:
            changes.append(
                "The previous battle-pressure signal is no longer active."
            )

    if (
        current.get("race_status")
        != previous.get("race_status")
    ):
        previous_status = previous.get(
            "race_status"
        )

        current_status = current.get(
            "race_status"
        )

        if (
            previous_status is not None
            and current_status is not None
        ):
            changes.append(
                f'Race status changed from '
                f'{previous_status} '
                f'to {current_status}.'
            )

    if not changes:
        return None

    return " ".join(changes)


def build_theo_intervention(
    target_lap,
    driver_number
):
    try:
        current = build_team_engineer_strategy(
            target_lap=target_lap,
            driver_number=driver_number
        )

    except Exception as error:
        return {
            "lap": target_lap,
            "driver_number": driver_number,
            "emit": False,
            "priority": "INFO",
            "reason": "CURRENT_DATA_ERROR",
            "message": str(error)
        }

    if current.get("decision") == "NO_DATA":
        return {
            "lap": target_lap,
            "driver": current.get("driver"),
            "emit": False,
            "priority": "INFO",
            "reason": "NO_DATA",
            "message": None
        }

    previous = None

    if target_lap > 2:

        try:
            previous_candidate = (
                build_team_engineer_strategy(
                    target_lap=target_lap - 1,
                    driver_number=driver_number
                )
            )

            if is_valid_previous_state(
                previous_candidate
            ):
                previous = previous_candidate

        except Exception:
            previous = None

    current_signature = get_strategy_signature(
        current
    )

    previous_signature = get_strategy_signature(
        previous
    )

    priority = get_intervention_priority(
        current
    )

    has_previous_state = (
        previous_signature is not None
    )

    strategy_changed = (
        has_previous_state
        and current_signature
        != previous_signature
    )

    change_message = build_change_message(
        current,
        previous
    )

    current_decision = current.get(
        "decision"
    )

    previous_decision = (
        previous.get("decision")
        if previous
        else None
    )

    if priority == "CRITICAL":

        if not has_previous_state:
            emit = True
            reason = "CRITICAL_STRATEGY_SIGNAL"

        elif strategy_changed:
            emit = True
            reason = "CRITICAL_STRATEGY_CHANGED"

        elif (
            current_decision == "PIT_NOW"
            and previous_decision == "PIT_NOW"
        ):
            emit = False
            reason = "CRITICAL_SIGNAL_ALREADY_ACTIVE"

        else:
            emit = False
            reason = "CRITICAL_SIGNAL_ALREADY_ACTIVE"

    elif strategy_changed:
        emit = True
        reason = "STRATEGY_CHANGED"

    elif (
        priority == "HIGH"
        and not has_previous_state
    ):
        emit = True
        reason = "NEW_HIGH_PRIORITY_SIGNAL"

    elif priority == "HIGH":
        emit = False
        reason = "HIGH_SIGNAL_ALREADY_ACTIVE"

    else:
        emit = False
        reason = "NO_SIGNIFICANT_CHANGE"

    if emit:
        message_parts = []

        if change_message:
            message_parts.append(
                change_message
            )

        if current.get("message"):
            message_parts.append(
                current["message"]
            )

        message = " ".join(
            message_parts
        )

    else:
        message = None

    return {
        "lap": target_lap,
        "driver": current.get("driver"),
        "position": current.get("position"),
        "emit": emit,
        "priority": priority,
        "reason": reason,
        "decision": current.get("decision"),
        "pit_recommendation":
            current.get("pit_recommendation"),
        "degradation_level":
            current.get("degradation_level"),
        "rival_decision":
            current.get("rival_decision"),
        "battle_priority":
            current.get("battle_priority"),
        "race_status":
            current.get("race_status"),
        "neutralized":
            current.get("neutralized"),
        "strategy_changed":
            strategy_changed,
        "message": message
    }


if __name__ == "__main__":
    tests = [
        (24, 4),
        (25, 4),

        (37, 31),
        (38, 31),
        (39, 31),

        (44, 1),
        (45, 1),

        (69, 4),
        (70, 4),
    ]

    for lap, driver_number in tests:
        print()
        print("=" * 70)

        result = build_theo_intervention(
            target_lap=lap,
            driver_number=driver_number
        )

        print(result)