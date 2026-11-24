import csv

from exports import CSV_FIELDS, export_trials_csv
from models import TrialRecord


def test_export_csv_contains_trial_results_and_top_score(tmp_path):
    path = tmp_path / "scoreboard.csv"
    trials = [
        TrialRecord(2, 4, 8, 10, True, 12),
        TrialRecord(3, 4, 9, 12, True, 15),
        TrialRecord(1, 1, 1, 1, False, 4, 7, "required support disconnected"),
    ]
    export_trials_csv(path, trials)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == CSV_FIELDS
    assert len(rows) == 3
    assert rows[1]["max_acceleration_ft_s2"] == "12"
    assert rows[1]["top_score"] == "True"
    assert rows[2]["failed_piece_id"] == "7"
    assert rows[2]["failure_reason"] == "required support disconnected"


def test_export_empty_scoreboard_still_writes_headers(tmp_path):
    path = tmp_path / "empty.csv"
    export_trials_csv(path, [])
    assert path.read_text(encoding="utf-8-sig").strip() == ",".join(CSV_FIELDS)

