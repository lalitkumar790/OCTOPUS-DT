"""Data-driven chamber pressure calibration; no guessed pressure gains."""
from __future__ import annotations

from typing import Any

import numpy as np


def _design_matrix(pressures_kpa: np.ndarray, ridge: float) -> tuple[np.ndarray, np.ndarray]:
    pressure = np.asarray(pressures_kpa, dtype=float)
    if pressure.ndim != 2 or pressure.shape[0] < 2 or pressure.shape[1] < 1:
        raise ValueError("pressures_kpa must be a 2D samples-by-chambers matrix")
    if not np.all(np.isfinite(pressure)) or np.any(pressure < 0):
        raise ValueError("Pressure data must be finite and nonnegative")
    if not np.isfinite(ridge) or ridge < 0:
        raise ValueError("ridge must be finite and nonnegative")
    design = np.column_stack((np.ones(pressure.shape[0]), pressure))
    if pressure.shape[0] < design.shape[1]:
        raise ValueError(f"Need at least {design.shape[1]} independent samples")
    if np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("Pressure dataset is rank-deficient; vary chambers independently")
    penalty = np.eye(design.shape[1]) * ridge
    penalty[0, 0] = 0.0
    return design, penalty


def fit_pressure_to_tip_angle(
    pressures_kpa: np.ndarray,
    tip_angles_rad: np.ndarray,
    ridge: float = 1e-6,
) -> dict[str, Any]:
    """Fit measured ten-chamber pressure vectors to measured tip angle."""
    design, penalty = _design_matrix(pressures_kpa, ridge)
    angles = np.asarray(tip_angles_rad, dtype=float)
    if angles.shape != (design.shape[0],) or not np.all(np.isfinite(angles)):
        raise ValueError("tip_angles_rad must be a finite vector with one value per sample")
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ angles)
    residual = angles - design @ coefficients
    total = float(np.sum((angles - np.mean(angles)) ** 2))
    rmse = float(np.sqrt(np.mean(residual**2)))
    r2 = 1.0 if total == 0 and rmse == 0 else (0.0 if total == 0 else
         1.0 - float(np.sum(residual**2)) / total)
    return {
        "schema_version": 1, "method": "ridge_linear_pressure_to_tip_angle",
        "chamber_count": int(design.shape[1] - 1), "sample_count": int(design.shape[0]),
        "intercept_rad": float(coefficients[0]),
        "coefficients_rad_per_kpa": coefficients[1:].tolist(),
        "ridge": float(ridge), "rmse_rad": rmse, "r_squared": r2, "calibrated": True,
    }


def predict_tip_angle(calibration: dict[str, Any], pressures_kpa: np.ndarray) -> float:
    pressure = np.asarray(pressures_kpa, dtype=float)
    count = int(calibration.get("chamber_count", 0))
    coefficients = np.asarray(calibration.get("coefficients_rad_per_kpa", []), dtype=float)
    if pressure.shape != (count,) or coefficients.shape != (count,):
        raise ValueError("Pressure vector does not match calibration chamber count")
    if not np.all(np.isfinite(pressure)) or np.any(pressure < 0):
        raise ValueError("Pressure vector must be finite and nonnegative")
    return float(calibration["intercept_rad"] + np.dot(coefficients, pressure))


def fit_pressure_to_joint_angles(
    pressures_kpa: np.ndarray,
    joint_angles_rad: np.ndarray,
    ridge: float = 1e-6,
) -> dict[str, Any]:
    """Fit chamber pressures to measured per-segment joint angles.

    joint_angles_rad must have shape (samples, segments). A ten-segment arm
    therefore learns a distinct target angle for every segment from the
    ten measured chamber pressures. Use independently varied pressure samples.
    """
    design, penalty = _design_matrix(pressures_kpa, ridge)
    angles = np.asarray(joint_angles_rad, dtype=float)
    if angles.ndim != 2 or angles.shape[0] != design.shape[0] or angles.shape[1] < 1:
        raise ValueError("joint_angles_rad must have shape (samples, segments)")
    if not np.all(np.isfinite(angles)):
        raise ValueError("Joint-angle measurements must be finite")
    coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ angles)
    predicted = design @ coefficients
    residual = angles - predicted
    rmse = np.sqrt(np.mean(residual**2, axis=0))
    return {
        "schema_version": 1, "method": "ridge_pressure_to_segment_joint_angles",
        "chamber_count": int(design.shape[1] - 1),
        "segment_count": int(angles.shape[1]), "sample_count": int(design.shape[0]),
        "intercept_rad": coefficients[0].tolist(),
        "coefficients_rad_per_kpa": coefficients[1:].T.tolist(),
        "rmse_rad_per_segment": rmse.tolist(), "ridge": float(ridge),
        "calibrated": True,
    }


def predict_joint_angles(calibration: dict[str, Any], pressures_kpa: np.ndarray) -> list[float]:
    """Predict each continuum segment's target angle from a ten-chamber pressure vector."""
    pressure = np.asarray(pressures_kpa, dtype=float)
    chambers = int(calibration.get("chamber_count", 0))
    segments = int(calibration.get("segment_count", 0))
    intercept = np.asarray(calibration.get("intercept_rad", []), dtype=float)
    coefficients = np.asarray(calibration.get("coefficients_rad_per_kpa", []), dtype=float)
    if pressure.shape != (chambers,) or intercept.shape != (segments,) or coefficients.shape != (segments, chambers):
        raise ValueError("Pressure vector does not match calibration dimensions")
    if not np.all(np.isfinite(pressure)) or np.any(pressure < 0):
        raise ValueError("Pressure vector must be finite and nonnegative")
    return (intercept + coefficients @ pressure).tolist()
