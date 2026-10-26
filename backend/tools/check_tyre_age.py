import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_store import stints  # noqa: E402

drivers_to_check = [44, 63, 87, 12, 81]

for stint in stints:
    if stint["driver_number"] in drivers_to_check and stint["stint_number"] == 1:
        print(
            "driver:", stint["driver_number"],
            "- compound:", stint["compound"],
            "- tyre_age_at_start:", stint["tyre_age_at_start"],
            "- lap_start:", stint["lap_start"]
        )