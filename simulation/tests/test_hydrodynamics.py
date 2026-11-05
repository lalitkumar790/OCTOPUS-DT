import numpy as np
import pytest

from octopus_dt.hydrodynamics import distributed_hydrodynamic_forces


def test_distributed_buoyancy_sums_to_archimedes_force():
    velocities = np.zeros((3, 3))
    masses = np.array([1.0, 2.0, 1.0])
    rho, volume, gravity = 997.0, 0.0012, 9.81
    forces = distributed_hydrodynamic_forces(
        velocities, masses, volume, 0.0, rho, 0.0, gravity
    )
    assert forces[:, 2].sum() == pytest.approx(rho * volume * gravity)
    assert forces[:, :2].sum() == pytest.approx([0.0, 0.0])


def test_drag_opposes_body_velocity():
    velocities = np.array([[1.0, 0.0, 0.0], [0.0, -0.5, 0.0]])
    forces = distributed_hydrodynamic_forces(
        velocities, np.ones(2), 0.0, 0.04, 997.0, 1.0
    )
    assert forces[0, 0] < 0
    assert forces[1, 1] > 0


def test_rejects_invalid_body_shapes():
    with pytest.raises(ValueError, match="shape"):
        distributed_hydrodynamic_forces(np.zeros((2, 2)), np.ones(2), .001, .02)
