from race_intelligence import build_race_intelligence


def calculate_battle_priority(battle):
    score = 0

    gap = battle["current_gap"]
    closing_rate = battle["closing_rate"]
    gap_trend = battle["gap_trend"]

    if gap <= 1.0:
        score += 4
    elif gap <= 2.0:
        score += 3
    elif gap <= 5.0:
        score += 2
    elif gap <= 10.0:
        score += 1

    if gap_trend == "CLOSING":
        score += 2

        if closing_rate >= 0.5:
            score += 2
        elif closing_rate >= 0.2:
            score += 1

    elif gap_trend == "DROPPING_BACK":
        score -= 1

    if (
        battle["driver_pace_trend"] == "IMPROVING"
        and battle["target_pace_trend"] == "DEGRADING"
    ):
        score += 1

    if score >= 6:
        priority = "HIGH"
    elif score >= 3:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    return score, priority


def analyze_battles(target_lap):
    intelligence = build_race_intelligence(target_lap)

    battles = []

    for battle in intelligence["battles"]:
        score, priority = calculate_battle_priority(battle)

        battle_result = battle.copy()

        battle_result["battle_score"] = score
        battle_result["priority"] = priority

        battles.append(battle_result)

    battles = sorted(
        battles,
        key=lambda item: item["battle_score"],
        reverse=True
    )

    return {
        "lap": target_lap,
        "battles": battles
    }


if __name__ == "__main__":
    analysis = analyze_battles(25)

    for battle in analysis["battles"]:
        print(
            f'{battle["priority"]} | '
            f'score: {battle["battle_score"]} | '
            f'P{battle["position"]} {battle["driver"]} -> '
            f'P{battle["target_position"]} {battle["target"]} | '
            f'gap: {battle["current_gap"]} | '
            f'rate: {battle["closing_rate"]} | '
            f'{battle["gap_trend"]}'
        )