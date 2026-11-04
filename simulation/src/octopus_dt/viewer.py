"""Open the eight-arm MuJoCo model in the interactive viewer."""
from __future__ import annotations

import mujoco.viewer

from .model import load_model


def main() -> None:
    model, data = load_model()
    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            mujoco.mj_step(model, data)
            viewer.sync()


if __name__ == "__main__":
    main()
