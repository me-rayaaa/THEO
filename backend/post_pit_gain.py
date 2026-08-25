from tyre_degradation import calculate_tyre_degradation


def estimate_post_pit_gain(target_lap):
    tyre_data = calculate_tyre_degradation(target_lap)

    results = []

    for driver in tyre_data["drivers"]:
        rate = driver["degradation_rate"]
        tyre_age = driver["tyre_age"]

        gain = 0.0

        if (
            rate is not None
            and rate > 0
            and tyre_age is not None
        ):
            gain = rate * tyre_age
            gain = min(gain, 1.5)

        results.append({
            "driver": driver["driver"],
            "position": driver["position"],
            "compound": driver["compound"],
            "tyre_age": tyre_age,
            "degradation_rate": rate,
            "degradation_level": driver["degradation_level"],
            "estimated_fresh_tyre_gain": round(gain, 3)
        })

    return {
        "lap": target_lap,
        "drivers": results
    }


if __name__ == "__main__":
    result = estimate_post_pit_gain(25)

    for driver in result["drivers"]:
        print(
            f'P{driver["position"]} - '
            f'{driver["driver"]} - '
            f'age: {driver["tyre_age"]} - '
            f'degradation: {driver["degradation_rate"]} - '
            f'fresh tyre gain: '
            f'{driver["estimated_fresh_tyre_gain"]} s/lap'
        )