import math

from calculations import (
    free_fall_time,
    maximum_acceleration,
    maximum_speed,
    shake_acceleration,
    shake_displacement,
)


def test_free_fall_checks():
    assert math.isclose(free_fall_time(3), 0.432, abs_tol=0.002)
    assert math.isclose(free_fall_time(4), 0.498, abs_tol=0.002)
    assert math.isclose(free_fall_time(5), 0.558, abs_tol=0.002)


def test_zero_amplitude_and_frequency():
    assert shake_displacement(1, 0, 3) == 0
    assert shake_acceleration(1, 0, 3) == 0
    assert maximum_acceleration(4, 0) == 0


def test_scaling_rules():
    base = maximum_acceleration(2, 2)
    assert math.isclose(maximum_acceleration(4, 2), 2 * base)
    assert math.isclose(maximum_acceleration(2, 4), 4 * base)


def test_speed_and_acceleration_are_positive_magnitudes():
    assert maximum_speed(5, 5) > 0
    assert maximum_acceleration(5, 5) > 0

