"""Compile and sanity-check the MuJoCo model."""
from __future__ import annotations

import mujoco
import numpy as np

from .model import load_model


def main() -> None:
    model, data = load_model()
    body_names = {model.body(i).name for i in range(model.nbody)}
    core_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_core")
    if core_id < 0:
        raise RuntimeError("Missing central body")

    expected = [f"arm{i:02d}_B_first" for i in range(1, 9)]
    missing = [name for name in expected if name not in body_names]
    if missing:
        raise RuntimeError(f"Missing cable root bodies: {missing}")

    for name in expected:
        body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
        if model.body_parentid[body_id] != core_id:
            raise RuntimeError(f"{name} is not structurally attached to octopus_core")

    if mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "core_free") < 0:
        raise RuntimeError("Central body must be free-floating")

    for _ in range(100):
        mujoco.mj_step(model, data)

    if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
        raise RuntimeError("Non-finite simulation state")
    print(
        f"MuJoCo model OK: {model.nbody} bodies, {model.njnt} joints, "
        f"{model.ngeom} geoms, {model.nplugin} plugin instances; "
        "8 cable roots attached to free-floating core"
    )


if __name__ == "__main__":
    main()
