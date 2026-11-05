"""Distributed, reduced-order hydrodynamic loads for MuJoCo bodies.

This is a body-wise buoyancy plus quadratic-drag model, not CFD or FSI.
Displaced volumes, projected areas and drag coefficients are experimental inputs.
"""
from __future__ import annotations

import numpy as np


def distributed_hydrodynamic_forces(
    body_velocities_m_s: np.ndarray,
    body_masses_kg: np.ndarray,
    total_displaced_volume_m3: float,
    total_projected_area_m2: float,
    fluid_density_kg_m3: float = 997.0,
    drag_coefficient: float = 1.1,
    gravity_m_s2: float = 9.81,
) -> np.ndarray:
    """Return one world-frame [Fx,Fy,Fz] load per body, excluding gravity.

    Buoyancy and projected area are apportioned by body mass. The caller should
    enable gravity in MuJoCo; this function adds buoyancy and drag only.
    """
    velocities = np.asarray(body_velocities_m_s, dtype=float)
    masses = np.asarray(body_masses_kg, dtype=float)
    if velocities.ndim != 2 or velocities.shape[1] != 3:
        raise ValueError("body_velocities_m_s must have shape (bodies, 3)")
    if masses.shape != (velocities.shape[0],) or np.any(masses <= 0):
        raise ValueError("body_masses_kg must be positive with one value per body")
    scalars = (total_displaced_volume_m3, total_projected_area_m2,
               fluid_density_kg_m3, drag_coefficient, gravity_m_s2)
    if not np.all(np.isfinite(scalars)) or any(x < 0 for x in scalars):
        raise ValueError("Hydrodynamic parameters must be finite and nonnegative")
    if fluid_density_kg_m3 == 0 or gravity_m_s2 == 0:
        raise ValueError("Fluid density and gravity must be positive")
    if not np.all(np.isfinite(velocities)):
        raise ValueError("Body velocities must be finite")

    weights = masses / np.sum(masses)
    volumes = total_displaced_volume_m3 * weights
    areas = total_projected_area_m2 * weights
    speeds = np.linalg.norm(velocities, axis=1)
    drag = (-0.5 * fluid_density_kg_m3 * drag_coefficient
            * areas[:, None] * speeds[:, None] * velocities)
    buoyancy = np.zeros_like(velocities)
    buoyancy[:, 2] = fluid_density_kg_m3 * gravity_m_s2 * volumes
    return buoyancy + drag
