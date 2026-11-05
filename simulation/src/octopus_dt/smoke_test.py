"""Compile and sanity-check either the scaffold or CAD-derived MuJoCo model."""
from __future__ import annotations

import mujoco
import numpy as np

from .model import load_model


def _require_name(model: mujoco.MjModel, object_type: mujoco.mjtObj, name: str) -> int:
    object_id = mujoco.mj_name2id(model, object_type, name)
    if object_id < 0:
        raise RuntimeError(f"Missing MuJoCo object: {name}")
    return object_id


def _check_cad_assembly(model: mujoco.MjModel) -> str:
    base_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base")
    _require_name(model, mujoco.mjtObj.mjOBJ_JOINT, "base_free")
    for index in range(1, 9):
        body_name = f"arm_{index:02d}"
        joint_name = f"arm_{index:02d}_hinge"
        actuator_name = f"arm_{index:02d}_position"
        body_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        _require_name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
        _require_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, actuator_name)
        if model.body_parentid[body_id] != base_id:
            raise RuntimeError(f"{body_name} is not attached to octopus_base")
    return "8 CAD arm bodies, hinges and position actuators attached to octopus_base"


def _check_scaffold(model: mujoco.MjModel) -> str:
    core_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_core")
    _require_name(model, mujoco.mjtObj.mjOBJ_JOINT, "core_free")
    for index in range(1, 9):
        body_name = f"arm{index:02d}_B_first"
        body_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if model.body_parentid[body_id] != core_id:
            raise RuntimeError(f"{body_name} is not attached to octopus_core")
    return "8 elastic cable roots attached to octopus_core"


def main() -> None:
    model, data = load_model()
    if mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base") >= 0:
        model_description = _check_cad_assembly(model)
    else:
        model_description = _check_scaffold(model)

    for _ in range(100):
        mujoco.mj_step(model, data)

    if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
        raise RuntimeError("Non-finite simulation state")
    print(
        f"MuJoCo model OK: {model.nbody} bodies, {model.njnt} joints, "
        f"{model.ngeom} geoms, {model.nu} actuators, "
        f"{model.nplugin} plugin instances; {model_description}"
    )


if __name__ == "__main__":
    main()
