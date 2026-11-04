"""Pressure-inspired input signals; gains are uncalibrated placeholders."""
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
    phase = 2.0 * math.pi * (frequency_hz * time_s
                             - chamber_index / chamber_count
                             + arm_index / arm_count)
    return max(0.0, baseline_pa + amplitude_pa * (0.5 + 0.5 * math.sin(phase)))
