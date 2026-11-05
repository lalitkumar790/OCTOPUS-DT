import numpy as np
import pytest

from octopus_dt.calibration import fit_pressure_to_tip_angle, predict_tip_angle


def test_fit_recovers_measured_linear_pressure_response():
    rng = np.random.default_rng(7)
    pressures = rng.uniform(0.0, 70.0, size=(40, 3))
    expected = np.array([0.02, 0.0015, -0.0007, 0.0022])
    angles = expected[0] + pressures @ expected[1:]
    calibration = fit_pressure_to_tip_angle(pressures, angles, ridge=0.0)

    assert calibration["calibrated"] is True
    assert calibration["sample_count"] == 40
    assert calibration["r_squared"] == pytest.approx(1.0)
    assert calibration["intercept_rad"] == pytest.approx(expected[0])
    assert calibration["coefficients_rad_per_kpa"] == pytest.approx(
        expected[1:].tolist()
    )
    assert predict_tip_angle(calibration, pressures[0]) == pytest.approx(angles[0])


def test_fit_rejects_rank_deficient_pressure_dataset():
    pressures = np.ones((12, 10)) * 20.0
    angles = np.linspace(0.0, 0.2, 12)
    with pytest.raises(ValueError, match="rank-deficient"):
        fit_pressure_to_tip_angle(pressures, angles)


def test_fit_rejects_too_few_samples():
    with pytest.raises(ValueError, match="at least"):
        fit_pressure_to_tip_angle(np.ones((5, 10)), np.ones(5))


def test_predict_rejects_wrong_chamber_count():
    calibration = {
        "chamber_count": 2,
        "intercept_rad": 0.0,
        "coefficients_rad_per_kpa": [0.001, 0.002],
    }
    with pytest.raises(ValueError, match="does not match"):
        predict_tip_angle(calibration, np.array([10.0]))
