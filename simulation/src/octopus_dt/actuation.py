"""Actuation signal generators.

Pressure amplitudes are software test inputs until hardware pressure limits and
the pressure-to-joint calibration have been measured.
"""
from __future__ import annotations

import math


def travelling_wave_pressure(time_s: float, arm_index: int, chamber_index: int,
                             arm_count: int = 8, chamber_count: int = 10,
                             baseline_pa: float = 0.0, amplitude_pa: float = 20_000.0,
                             frequency_hz: float = 0.25) -> float:
    """Generate a bounded travelling-wave pressure command for software tests."""
    if arm_count < 1 or chamber_count < 1:
        raise ValueError("arm_count and chamber_count must be positive")
    if not (0 <= arm_index < arm_count and 0 <= chamber_index < chamber_count):
        raise IndexError("Arm or chamber index out of range")
    if time_s < 0 or baseline_pa < 0 or amplitude_pa < 0 or frequency_hz < 0:
        raise ValueError("Time, pressure and frequency inputs must be nonnegative")
    phase = 2.0 * math.pi * (frequency_hz * time_s
                             - chamber_index / chamber_count
                             + arm_index / arm_count)
    return max(0.0, baseline_pa + amplitude_pa * (0.5 + 0.5 * math.sin(phase)))


def travelling_wave_joint_targets(
    time_s: float,
    arm_count: int = 8,
    amplitude_rad: float = 0.35,
    frequency_hz: float = 0.25,
    phase_lag_rad: float = 0.45,
) -> list[float]:
    """Return exploratory hinge targets for an eight-arm gait (radians).

    This is a kinematic gait input, not a pneumatic pressure law.
    """
    if arm_count < 1 or time_s < 0 or frequency_hz < 0:
        raise ValueError("Arm count must be positive; time and frequency nonnegative")
    if amplitude_rad < 0 or phase_lag_rad < 0:
        raise ValueError("Gait amplitude and phase lag must be nonnegative")
    return [
        amplitude_rad * math.sin(2.0 * math.pi * frequency_hz * time_s
                                 - index * phase_lag_rad)
        for index in range(arm_count)
    ]
