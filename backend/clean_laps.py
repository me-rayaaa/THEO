import json

laps_file = "../data/mexico_2025/laps.json"

with open(laps_file, "r", encoding="utf-8") as file:
    laps = json.load(file)

race_control_file = "../data/mexico_2025/race_control.json"

with open(race_control_file, "r", encoding="utf-8") as file:
    race_control = json.load(file)

pit_file = "../data/mexico_2025/pit.json"

with open(pit_file, "r", encoding="utf-8") as file:
    pits = json.load(file)

invalid_race_control_laps = set()

for event in race_control:
    lap_number = event["lap_number"]

    if lap_number is None:
        continue

    message = event["message"].upper()
    category = event["category"]

    if (
        category == "SafetyCar"
        or "YELLOW" in message
        or "DOUBLE YELLOW" in message
        or "VIRTUAL SAFETY CAR" in message
    ):
        invalid_race_control_laps.add(lap_number)

pit_affected_laps = set()

for pit in pits:
    driver = pit["driver_number"]
    lap = pit["lap_number"]

    pit_affected_laps.add((driver, lap))
    pit_affected_laps.add((driver, lap + 1))

clean_laps = []

for lap in laps:
    if lap["lap_number"] == 1:
        continue

    if lap["lap_duration"] is None:
        continue

    if lap["lap_duration"] <= 0:
        continue

    if lap["lap_number"] in invalid_race_control_laps:
        continue

    if (
        lap["driver_number"],
        lap["lap_number"]
    ) in pit_affected_laps:
        continue

    clean_laps.append(lap)

print("Всего записей:", len(laps))
print("После очистки:", len(clean_laps))
print("Удалено:", len(laps) - len(clean_laps))

lap_times = [
    lap["lap_duration"]
    for lap in clean_laps
]

print("Самый быстрый круг:", min(lap_times))
print("Самый медленный круг:", max(lap_times))

slowest_laps = sorted(
    clean_laps,
    key=lambda x: x["lap_duration"],
    reverse=True
)[:20]

print("\n20 самых медленных оставшихся кругов:")

for lap in slowest_laps:
    print(
        "driver:", lap["driver_number"],
        "- lap:", lap["lap_number"],
        "- time:", lap["lap_duration"]
    )