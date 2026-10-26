from undercut_analysis import analyze_undercut


def build_rival_strategy_commentary(
    target_lap,
    driver_number,
    target_driver_number,
    comparison_laps=3
):
    analysis = analyze_undercut(
        target_lap=target_lap,
        driver_number=driver_number,
        target_driver_number=target_driver_number,
        comparison_laps=comparison_laps
    )

    if analysis is None:
        return {
            "lap": target_lap,
            "status": "NO_DATA",
            "message": "No rival strategy analysis available."
        }

    driver = analysis["driver"]
    target = analysis["target"]
    current_gap = analysis["current_gap"]
    estimated_gain = analysis["estimated_gain"]
    projected_gap = analysis["projected_gap_after_undercut"]
    position_loss = analysis["position_loss"]
    rejoin_position = analysis["projected_rejoin_position"]
    traffic_level = analysis["traffic_level"]
    undercut_status = analysis["undercut_status"]

    reasons = []

    if current_gap > estimated_gain:
        reasons.append(
            f"The current gap of {current_gap} seconds is larger "
            f"than the estimated {estimated_gain} seconds of "
            f"fresh-tyre gain over the next {comparison_laps} laps."
        )
    else:
        reasons.append(
            f"The estimated fresh-tyre gain of {estimated_gain} "
            f"seconds over the next {comparison_laps} laps is "
            f"large enough to theoretically overcome the current "
            f"{current_gap}-second gap."
        )

    if position_loss >= 2:
        reasons.append(
            f"However, stopping now is projected to drop "
            f"{driver} by {position_loss} positions to around "
            f"P{rejoin_position}."
        )
    elif position_loss == 1:
        reasons.append(
            f"A stop is projected to cost around one position, "
            f"with {driver} rejoining near P{rejoin_position}."
        )
    else:
        reasons.append(
            f"The projected stop preserves track position well, "
            f"with a rejoin around P{rejoin_position}."
        )

    if traffic_level == "HEAVY":
        reasons.append(
            "The projected rejoin is also in heavy traffic, "
            "which further reduces the value of the undercut."
        )
    elif traffic_level == "MODERATE":
        reasons.append(
            "The projected rejoin is in moderate traffic, "
            "which adds some strategic risk."
        )
    else:
        reasons.append("The projected rejoin is relatively clear.")

    if undercut_status == "STRONG":
        headline = f"Strong undercut opportunity on {target}."
        conclusion = (
            f"{driver} has enough projected fresh-tyre advantage "
            f"to challenge {target} through the pit cycle."
        )
    elif undercut_status == "POSSIBLE":
        headline = f"Undercut on {target} is possible."
        conclusion = (
            "The opportunity exists, but the expected advantage "
            "is not strong enough to make the move low-risk."
        )
    else:
        headline = f"Undercut on {target} is weak."

        if position_loss >= 2:
            conclusion = (
                "The track-position loss currently outweighs "
                "the theoretical undercut opportunity."
            )
        elif current_gap > estimated_gain:
            conclusion = (
                f"The fresh-tyre advantage is currently not large "
                f"enough to overcome the gap to {target}."
            )
        elif traffic_level in {"MODERATE", "HEAVY"}:
            conclusion = (
                "Traffic after the stop reduces the value of "
                "the theoretical undercut."
            )
        else:
            conclusion = (
                "The model does not currently show enough "
                "strategic advantage to recommend the undercut."
            )

    message = " ".join([headline] + reasons + [conclusion])

    return {
        "lap": target_lap,
        "driver": driver,
        "target": target,
        "undercut_status": undercut_status,
        "current_gap": current_gap,
        "estimated_gain": estimated_gain,
        "projected_gap_after_undercut": projected_gap,
        "projected_rejoin_position": rejoin_position,
        "position_loss": position_loss,
        "traffic_level": traffic_level,
        "message": message
    }


if __name__ == "__main__":
    print(build_rival_strategy_commentary(25, 16, 4)["message"])
