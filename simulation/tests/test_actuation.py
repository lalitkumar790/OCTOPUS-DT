import pytest
from octopus_dt.actuation import travelling_wave_pressure


def test_pressure_is_nonnegative():
    for arm in range(8):
        for chamber in range(10):
            assert travelling_wave_pressure(0.0, arm, chamber) >= 0


def test_invalid_indices_rejected():
    with pytest.raises(IndexError):
        travelling_wave_pressure(0.0, 8, 0)
