import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Это скрипты с печатью, а не тесты pytest: запускать вручную.
collect_ignore = [
    "test_mvp_end_to_end.py",
    "test_overcut_scan.py",
    "test_pit_strategy.py",
]
