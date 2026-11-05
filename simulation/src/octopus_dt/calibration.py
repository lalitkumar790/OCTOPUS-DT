"""Data-driven calibration for chamber-pressure to tip-angle response.

This module deliberately requires measured data. It does not ship guessed
pressure-to-curvature coefficients or treat UI pressure values as calibration.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def fit_pressure_to_tip_angle(
    pressures_kpa: np.ndarray,
    tip_angles_rad: np.ndarray,
    ridge: float = 1e-6,
) -> dict[str, Any]:
    """Fit a linear chamber-pressure response from measured experiments.

    Args:
        pressures_kpa: Matrix shaped (samples, chambers), measured chamber pressures.
        tip_angles_rad: Vector shaped (samples,), measured tip bend angles in radians.
        ridge: Nonnegative L2 regularization for chamber coefficients.

    Returns:
        JSON-serializable calibration metadata and fitted coefficients.

    At least chambers + 1 independent samples are required so every coefficient
    is identifiable. Collect data across the complete intended pressure range.
    """
    pressure = np.asarray(pressures_kpa, dtype=float)
    angles = np.asarray(tip_angles_rad, dtype=float)
    if pressure.ndim != 2 or pressure.shape[0] < 2 or pressure.shape[1] < 1:
        raise ValueError("pressures_kpa must be a 2D samples-by-chambers matrix")
    if angles.shape != (pressure.shape[0],):
        raise ValueError("tip_angles_rad must have one value per pressure sample")
    if not np.all(np.isfinite(pressure)) or not np.all(np.isfinite(angles)):
        raise ValueError("Calibration data must contain only finite values")
    if np.any(pressure < 0):
        raise ValueError("Chamber pressures must be nonnegative")
    if not np.isfinite(ridge) or ridge < 0:
        raise ValueError("ridge must be a finite nonnegative value")

    design = np.column_stack((np.ones(pressure.shape[0]), pressure))
    if pressure.shape[0] < design.shape[1]:
        raise ValueError(
            f"Need at least {design.shape[1]} samples for {pressure.shape[1]} chambers"
        )
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("Pressure dataset is rank-deficient; vary chamber inputs")

    penalty = np.eye(design.shape[1]) * ridge
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ angles)
    predicted = design @ coefficients
    residual = angles - predicted
    rmse = float(np.sqrt(np.mean(residual**2)))
    total = float(np.sum((angles - np.mean(angles)) ** 2))
    r_squared = 1.0 if total == 0.0 and rmse == 0.0 else (
        0.0 if total == 0.0 else 1.0 - float(np.sum(residual**2)) / total
    )
    return {
        "schema_version": 1,
        "method": "ridge_linear_pressure_to_tip_angle",
        "chamber_count": int(pressure.shape[1]),
        "sample_count": int(pressure.shape[0]),
        "intercept_rad": float(coefficients[0]),
        "coefficients_rad_per_kpa": coefficients[1:].tolist(),
        "ridge": float(ridge),
        "rmse_rad": rmse,
        "r_squared": r_squared,
        "calibrated": True,
    }


def predict_tip_angle(
    calibration: dict[str, Any],
    pressures_kpa: np.ndarray,
) -> float:
    """Predict tip angle from a fitted calibration and one pressure vector."""
    pressure = np.asarray(pressures_kpa, dtype=float)
    chamber_count = int(calibration.get("chamber_count", 0))
    coefficients = np.asarray(
        calibration.get("coefficients_rad_per_kpa", []), dtype=float
    )
    if pressure.shape != (chamber_count,) or coefficients.shape != (chamber_count,):
        raise ValueError("Pressure vector does not match calibration chamber count")
    if not np.all(np.isfinite(pressure)) or np.any(pressure < 0):
        raise ValueError("Chamber pressures must be finite and nonnegative")
    intercept = float(calibration["intercept_rad"])
    return float(intercept + np.dot(coefficients, pressure))
