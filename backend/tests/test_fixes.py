import pytest

import race_state
from clean_laps import get_clean_laps
from data_store import LAST_LAP, LapOutOfRange
from pit_strategy import calculate_pit_window, calculate_rejoin
from race_neutralization import normalize_race_status
from strategy_commentary import build_strategy_commentary


def test_lap_out_of_range_raises():
    for lap in (0, LAST_LAP + 1):
        with pytest.raises(LapOutOfRange):
            race_state.get_race_state(lap)


def test_full_field_is_returned():
    assert len(race_state.get_race_state(30)["drivers"]) == 20


def test_lap_under_yellow_is_not_clean():
    # Жёлтый объявлен на круге 3, снят на круге 5: круг 4 тоже под флагом.
    clean_numbers = {lap["lap_number"] for lap in get_clean_laps(10)}
    assert not {3, 4, 5} & clean_numbers


def test_vsc_status():
    assert race_state.get_race_state(70)["race_status"] == "VSC"


def test_status_matching_is_exact():
    assert normalize_race_status("CHEQUERED") == "UNKNOWN"
    assert normalize_race_status("VSC") == "VSC"


def test_rejoin_sees_whole_field():
    # P8 на круге 30 после стопа выезжает далеко за пределы топ-10.
    state = race_state.get_race_state(30)
    p8 = state["drivers"][7]["driver_number"]
    assert calculate_rejoin(30, p8)["projected_rejoin_position"] > 10


def test_pit_window_does_not_read_future_laps(monkeypatch):
    seen = []
    original = race_state.get_race_state

    def spy(lap):
        seen.append(lap)
        return original(lap)

    import pit_strategy
    monkeypatch.setattr(pit_strategy, "get_race_state", spy)
    calculate_pit_window(25, 4)
    assert max(seen) <= 25


def test_strategy_no_data_has_full_shape():
    result = build_strategy_commentary(LAST_LAP, 999)
    assert result["recommendation"] == "NO_DATA"
    assert result["optimal_window"] == []
