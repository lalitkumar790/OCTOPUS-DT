"""Reduced-order underwater force helpers (not CFD)."""
from __future__ import annotations

import numpy as np


def buoyancy_force(displaced_volume_m3: float, fluid_density_kg_m3: float = 997.0,
                   gravity_m_s2: float = 9.81) -> np.ndarray:
    """Return upward buoyancy force in world coordinates (z-up)."""
    if displaced_volume_m3 < 0 or fluid_density_kg_m3 <= 0 or gravity_m_s2 <= 0:
        raise ValueError("Volume must be nonnegative and density/gravity must be positive")
    return np.array([0.0, 0.0, fluid_density_kg_m3 * displaced_volume_m3 * gravity_m_s2])


def quadratic_drag(velocity_world: np.ndarray, area_m2: float,
                   drag_coefficient: float = 1.0,
                   fluid_density_kg_m3: float = 997.0) -> np.ndarray:
    """Simple isotropic quadratic drag approximation."""
    velocity = np.asarray(velocity_world, dtype=float)
    if velocity.shape != (3,):
        raise ValueError("velocity_world must have shape (3,)")
    if area_m2 < 0 or drag_coefficient < 0 or fluid_density_kg_m3 <= 0:
        raise ValueError("Area/Cd must be nonnegative and density positive")
    speed = float(np.linalg.norm(velocity))
    return -0.5 * fluid_density_kg_m3 * drag_coefficient * area_m2 * speed * velocity
