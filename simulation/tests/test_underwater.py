import numpy as np
import pytest
from octopus_dt.underwater import buoyancy_force, quadratic_drag


def test_buoyancy_points_up():
    force = buoyancy_force(0.001)
    assert force[2] > 0
    assert np.allclose(force[:2], 0)


def test_drag_opposes_velocity():
    velocity = np.array([1.0, -2.0, 0.5])
    force = quadratic_drag(velocity, area_m2=0.02)
    assert np.dot(force, velocity) < 0


def test_invalid_velocity_shape():
    with pytest.raises(ValueError):
        quadratic_drag(np.array([1.0, 2.0]), 0.1)
