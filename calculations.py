"""NumPy calculations kept separate from the Tkinter window code."""

from __future__ import annotations

import math

import numpy as np


G_FT_S2 = 32.174


def amplitude_ft(amplitude_in: float) -> float:
    return max(0.0, float(amplitude_in)) / 12.0


def angular_frequency(frequency_hz: float) -> float:
    return 2.0 * math.pi * max(0.0, float(frequency_hz))


def shake_displacement(t_s: float, amplitude_in: float, frequency_hz: float) -> float:
    return amplitude_ft(amplitude_in) * math.sin(angular_frequency(frequency_hz) * t_s)


def shake_velocity(t_s: float, amplitude_in: float, frequency_hz: float) -> float:
    omega = angular_frequency(frequency_hz)
    return amplitude_ft(amplitude_in) * omega * math.cos(omega * t_s)


def shake_acceleration(t_s: float, amplitude_in: float, frequency_hz: float) -> float:
    omega = angular_frequency(frequency_hz)
    return -amplitude_ft(amplitude_in) * omega**2 * math.sin(omega * t_s)


def maximum_speed(amplitude_in: float, frequency_hz: float) -> float:
    return amplitude_ft(amplitude_in) * angular_frequency(frequency_hz)


def maximum_acceleration(amplitude_in: float, frequency_hz: float) -> float:
    return amplitude_ft(amplitude_in) * angular_frequency(frequency_hz) ** 2


def free_fall_time(height_ft: float) -> float:
    return math.sqrt(2.0 * max(0.0, height_ft) / G_FT_S2)


def score_key(max_acceleration_ft_s2: float, frequency_hz: float) -> tuple[float, float]:
    return (max_acceleration_ft_s2, frequency_hz)


def best_successful_trial(trials):
    successful = [trial for trial in trials if trial.checkpoint_reached]
    return max(
        successful,
        key=lambda trial: score_key(trial.max_acceleration_ft_s2, trial.frequency_hz),
        default=None,
    )


def validation_samples() -> dict[str, float]:
    """Return the documented free-fall checks for quick test/reporting use."""
    heights = np.array([3.0, 4.0, 5.0])
    times = np.sqrt(2.0 * heights / G_FT_S2)
    return {f"{height:g}ft": float(time) for height, time in zip(heights, times)}

