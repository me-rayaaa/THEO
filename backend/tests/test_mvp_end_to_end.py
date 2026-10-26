import sys
import _bootstrap

from race_state import get_race_state
from event_intelligence import build_event_summary
from theo_commentary import build_theo_commentary
from strategy_commentary import build_strategy_commentary
from team_engineer_strategy import build_team_engineer_strategy
from theo_intervention import build_theo_intervention


START_LAP = 2
END_LAP = 71

summary = {
    "race_state_ok": 0,
    "events_ok": 0,
    "theo_ok": 0,
    "strategy_ok": 0,
    "team_engineer_ok": 0,
    "intervention_ok": 0,
    "errors": 0,
    "no_data": 0,
    "critical_messages": 0,
    "high_messages": 0,
    "emitted_messages": 0
}

errors = []
no_data_cases = []
critical_cases = []
vsc_cases = []


for lap in range(START_LAP, END_LAP + 1):
    print(f"Checking lap {lap}...")

    try:
        race_state = get_race_state(lap)
        summary["race_state_ok"] += 1

    except Exception as error:
        summary["errors"] += 1

        errors.append({
            "lap": lap,
            "layer": "race_state",
            "driver": None,
            "error": str(error)
        })

        continue

    try:
        build_event_summary(lap)
        summary["events_ok"] += 1

    except Exception as error:
        summary["errors"] += 1

        errors.append({
            "lap": lap,
            "layer": "events",
            "driver": None,
            "error": str(error)
        })

    try:
        build_theo_commentary(lap)
        summary["theo_ok"] += 1

    except Exception as error:
        summary["errors"] += 1

        errors.append({
            "lap": lap,
            "layer": "theo",
            "driver": None,
            "error": str(error)
        })

    drivers = race_state["drivers"]

    for driver in drivers:

        driver_number = driver["driver_number"]
        driver_name = driver["name"]

        try:
            strategy = build_strategy_commentary(
                target_lap=lap,
                driver_number=driver_number
            )

            summary["strategy_ok"] += 1

            if (
                strategy.get("recommendation")
                == "NO_DATA"
            ):
                summary["no_data"] += 1

                no_data_cases.append({
                    "lap": lap,
                    "driver": driver_name,
                    "layer": "strategy"
                })

        except Exception as error:
            summary["errors"] += 1

            errors.append({
                "lap": lap,
                "layer": "strategy",
                "driver": driver_name,
                "error": str(error)
            })

        try:
            engineer = build_team_engineer_strategy(
                target_lap=lap,
                driver_number=driver_number
            )

            summary["team_engineer_ok"] += 1

            if engineer.get("decision") == "NO_DATA":
                summary["no_data"] += 1

                no_data_cases.append({
                    "lap": lap,
                    "driver": driver_name,
                    "layer": "team_engineer"
                })

            if engineer.get("race_status") in {
                "VSC",
                "SAFETY_CAR"
            }:
                vsc_cases.append({
                    "lap": lap,
                    "driver": driver_name,
                    "decision": engineer.get(
                        "decision"
                    ),
                    "race_status": engineer.get(
                        "race_status"
                    ),
                    "pit_opportunity": engineer.get(
                        "pit_opportunity"
                    )
                })

        except Exception as error:
            summary["errors"] += 1

            errors.append({
                "lap": lap,
                "layer": "team_engineer",
                "driver": driver_name,
                "error": str(error)
            })

        try:
            intervention = build_theo_intervention(
                target_lap=lap,
                driver_number=driver_number
            )

            summary["intervention_ok"] += 1

            if intervention.get("emit"):
                summary["emitted_messages"] += 1

            if intervention.get("priority") == "CRITICAL":
                summary["critical_messages"] += 1

                critical_cases.append({
                    "lap": lap,
                    "driver": driver_name,
                    "decision": intervention.get(
                        "decision"
                    ),
                    "reason": intervention.get(
                        "reason"
                    ),
                    "emit": intervention.get(
                        "emit"
                    )
                })

            elif intervention.get("priority") == "HIGH":
                summary["high_messages"] += 1

        except Exception as error:
            summary["errors"] += 1

            errors.append({
                "lap": lap,
                "layer": "intervention",
                "driver": driver_name,
                "error": str(error)
            })


print()
print("=" * 70)
print("THEO MVP 1.0 END-TO-END TEST")
print("=" * 70)

for key, value in summary.items():
    print(
        f"{key}: {value}"
    )


print()
print("=" * 70)
print("ERRORS")
print("=" * 70)

if not errors:
    print("No errors.")

else:
    for item in errors[:30]:
        print(
            f'Lap {item["lap"]} | '
            f'{item["layer"]} | '
            f'{item["driver"]} | '
            f'{item["error"]}'
        )

    if len(errors) > 30:
        print(
            f'... and {len(errors) - 30} more errors.'
        )


print()
print("=" * 70)
print("NO_DATA CASES")
print("=" * 70)

if not no_data_cases:
    print("No unexpected NO_DATA cases.")

else:
    for item in no_data_cases[:30]:
        print(
            f'Lap {item["lap"]} | '
            f'{item["driver"]} | '
            f'{item["layer"]}'
        )

    if len(no_data_cases) > 30:
        print(
            f'... and {len(no_data_cases) - 30} more NO_DATA cases.'
        )


print()
print("=" * 70)
print("CRITICAL INTERVENTIONS")
print("=" * 70)

if not critical_cases:
    print("No CRITICAL interventions found.")

else:
    for item in critical_cases[:30]:
        print(
            f'Lap {item["lap"]} | '
            f'{item["driver"]} | '
            f'{item["decision"]} | '
            f'{item["reason"]} | '
            f'emit={item["emit"]}'
        )

    if len(critical_cases) > 30:
        print(
            f'... and {len(critical_cases) - 30} more CRITICAL cases.'
        )


print()
print("=" * 70)
print("NEUTRALIZATION CASES")
print("=" * 70)

if not vsc_cases:
    print("No VSC / Safety Car cases found.")

else:
    for item in vsc_cases[:30]:
        print(
            f'Lap {item["lap"]} | '
            f'{item["driver"]} | '
            f'{item["race_status"]} | '
            f'{item["decision"]} | '
            f'pit opportunity: '
            f'{item["pit_opportunity"]}'
        )

    if len(vsc_cases) > 30:
        print(
            f'... and {len(vsc_cases) - 30} more neutralization cases.'
        )


print()
print("=" * 70)
print("MVP TEST RESULT")
print("=" * 70)

if summary["errors"] == 0:
    print(
        "PASS - No runtime errors detected."
    )
else:
    print(
        "REVIEW - Runtime errors were detected."
    )
    sys.exit(1)