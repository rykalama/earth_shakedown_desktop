"""Export completed trial results for use outside the desktop app."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from calculations import best_successful_trial
from models import TrialRecord


CSV_FIELDS = [
    "trial_number",
    "amplitude_in",
    "frequency_hz",
    "max_speed_ft_s",
    "max_acceleration_ft_s2",
    "checkpoint_reached",
    "survival_time_s",
    "failed_piece_id",
    "failure_reason",
    "top_score",
]


def export_trials_csv(path: str | Path, trials: Iterable[TrialRecord]) -> None:
    trial_list = list(trials)
    top_trial = best_successful_trial(trial_list)
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for number, trial in enumerate(trial_list, 1):
            writer.writerow({
                "trial_number": number,
                "amplitude_in": trial.amplitude_in,
                "frequency_hz": trial.frequency_hz,
                "max_speed_ft_s": trial.max_speed_ft_s,
                "max_acceleration_ft_s2": trial.max_acceleration_ft_s2,
                "checkpoint_reached": trial.checkpoint_reached,
                "survival_time_s": trial.survival_time_s,
                "failed_piece_id": trial.failed_piece_id or "",
                "failure_reason": trial.failure_reason or "",
                "top_score": trial is top_trial,
            })

