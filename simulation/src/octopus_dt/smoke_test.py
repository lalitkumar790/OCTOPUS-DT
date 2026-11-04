"""Compile and sanity-check the MuJoCo model."""
from __future__ import annotations

import numpy as np
from .model import load_model


def main() -> None:
    model, data = load_model()
    expected = [f"arm{i:02d}_root" for i in range(1, 9)]
    missing = [name for name in expected if name not in
               {model.body(i).name for i in range(model.nbody)}]
    if missing:
        raise RuntimeError(f"Missing arm root bodies: {missing}")
    for _ in range(20):
        import mujoco
        mujoco.mj_step(model, data)
    if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
        raise RuntimeError("Non-finite simulation state")
    print(f"MuJoCo model OK: {model.nbody} bodies, {model.njnt} joints, {model.ngeom} geoms")


if __name__ == "__main__":
    main()
