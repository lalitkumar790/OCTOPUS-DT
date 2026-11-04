"""MuJoCo model loading helpers."""
from __future__ import annotations

from pathlib import Path

import mujoco

# Package layout: repository/simulation/src/octopus_dt/model.py
DEFAULT_MODEL = Path(__file__).resolve().parents[2] / "models" / "octopus_dt_v0_1.xml"


def load_model(path: str | Path = DEFAULT_MODEL) -> tuple[mujoco.MjModel, mujoco.MjData]:
    model_path = Path(path)
    if not model_path.is_file():
        raise FileNotFoundError(f"MuJoCo model not found: {model_path}")
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    return model, data
