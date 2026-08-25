from undercut_analysis import analyze_undercut
from overcut_analysis import analyze_overcut


STATUS_SCORE = {
    "WEAK": 0,
    "POSSIBLE": 1,
    "STRONG": 2
}


def calculate_undercut_quality(undercut):
    if undercut is None:
        return 0.0

    score = 0.0

    projected_gap = undercut[
        "projected_gap_after_undercut"
    ]

    position_loss = undercut[
        "position_loss"
    ]

    traffic = undercut[
        "traffic_level"
    ]

    if projected_gap <= 0:
        score += 4
    elif projected_gap <= 1:
        score += 3
    elif projected_gap <= 2:
        score += 2
    elif projected_gap <= 5:
        score += 1

    if position_loss <= 0:
        score += 3
    elif position_loss == 1:
        score += 2
    elif position_loss == 2:
        score += 1
    else:
        score -= 2

    if traffic == "CLEAR":
        score += 2
    elif traffic == "MODERATE":
        score += 0
    else:
        score -= 2

    return round(score, 2)


def calculate_overcut_quality(overcut):
    if overcut is None:
        return 0.0

    score = 0.0

    final_gap = overcut[
        "gap_after_driver_stop"
    ]

    position_loss = overcut[
        "position_loss"
    ]

    traffic = overcut[
        "traffic_level"
    ]

    if final_gap <= 0:
        score += 4
    elif final_gap <= 1:
        score += 3
    elif final_gap <= 2:
        score += 2
    elif final_gap <= 5:
        score += 1

    if position_loss <= 0:
        score += 3
    elif position_loss == 1:
        score += 2
    elif position_loss == 2:
        score += 1
    else:
        score -= 2

    if traffic == "CLEAR":
        score += 2
    elif traffic == "MODERATE":
        score += 0
    else:
        score -= 2

    if overcut.get("pace_signal_extreme"):
        score -= 1

    return round(score, 2)


def build_rival_strategy_decision(
    target_lap,
    driver_number,
    target_driver_number
):
    undercut = analyze_undercut(
        target_lap=target_lap,
        driver_number=driver_number,
        target_driver_number=target_driver_number,
        comparison_laps=3
    )

    overcut = analyze_overcut(
        target_lap=target_lap,
        driver_number=driver_number,
        target_driver_number=target_driver_number,
        stay_out_laps=2
    )

    if undercut is None and overcut is None:
        return {
            "lap": target_lap,
            "decision": "NO_DATA",
            "message": "No rival strategy data available."
        }

    if undercut is not None:
        driver = undercut["driver"]
        target = undercut["target"]
    else:
        driver = overcut["driver"]
        target = overcut["target"]

    undercut_status = (
        undercut["undercut_status"]
        if undercut is not None
        else "WEAK"
    )

    overcut_status = (
        overcut["overcut_status"]
        if overcut is not None
        else "WEAK"
    )

    undercut_status_score = STATUS_SCORE.get(
        undercut_status,
        0
    )

    overcut_status_score = STATUS_SCORE.get(
        overcut_status,
        0
    )

    undercut_quality = calculate_undercut_quality(
        undercut
    )

    overcut_quality = calculate_overcut_quality(
        overcut
    )

    quality_difference = round(
        undercut_quality - overcut_quality,
        2
    )

    if (
        undercut_status_score == 0
        and overcut_status_score == 0
    ):
        decision = "NO_CLEAR_ADVANTAGE"

    elif undercut_status_score > overcut_status_score:
        decision = "UNDERCUT_PREFERRED"

    elif overcut_status_score > undercut_status_score:
        decision = "OVERCUT_PREFERRED"

    else:
        if quality_difference >= 2:
            decision = "UNDERCUT_PREFERRED"

        elif quality_difference <= -2:
            decision = "OVERCUT_PREFERRED"

        else:
            decision = "BOTH_POSSIBLE"

    if decision == "UNDERCUT_PREFERRED":
        message = (
            f'{driver}: undercut is currently the stronger option '
            f'against {target}. '
            f'Undercut quality score is {undercut_quality}, '
            f'compared with {overcut_quality} for the overcut.'
        )

    elif decision == "OVERCUT_PREFERRED":
        message = (
            f'{driver}: overcut is currently the stronger option '
            f'against {target}. '
            f'Overcut quality score is {overcut_quality}, '
            f'compared with {undercut_quality} for the undercut.'
        )

    elif decision == "BOTH_POSSIBLE":
        message = (
            f'{driver}: both undercut and overcut remain viable '
            f'against {target}. '
            f'The quality scores are close '
            f'({undercut_quality} vs {overcut_quality}), '
            f'so there is no clear strategic preference yet.'
        )

    else:
        message = (
            f'{driver}: there is currently no clear strategic '
            f'advantage against {target}. '
            f'Both undercut and overcut are rated weak.'
        )

    return {
        "lap": target_lap,
        "driver": driver,
        "target": target,
        "undercut_status": undercut_status,
        "overcut_status": overcut_status,
        "undercut_quality": undercut_quality,
        "overcut_quality": overcut_quality,
        "quality_difference": quality_difference,
        "decision": decision,
        "message": message
    }


if __name__ == "__main__":
    tests = [
        (25, 16, 4),
        (60, 12, 63),
        (45, 1, 44),
        (48, 6, 44)
    ]

    for lap, driver_number, target_driver_number in tests:
        result = build_rival_strategy_decision(
            target_lap=lap,
            driver_number=driver_number,
            target_driver_number=target_driver_number
        )

        print()
        print("=" * 70)

        print(
            result["decision"],
            "| undercut:",
            result.get("undercut_quality"),
            "| overcut:",
            result.get("overcut_quality")
        )

        print(
            result["message"]
        )