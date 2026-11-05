"""Compile the CAD MJCF when its mesh assets are installed; otherwise test scaffold."""
from __future__ import annotations

from pathlib import Path

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
        body_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        _require_name(model, mujoco.mjtObj.mjOBJ_JOINT, f"{body_name}_hinge")
        _require_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"{body_name}_position")
        if model.body_parentid[body_id] != base_id:
            raise RuntimeError(f"{body_name} is not attached to octopus_base")
        if not np.isclose(np.linalg.norm(model.body_quat[body_id]), 1.0, atol=1e-6):
            raise RuntimeError(f"{body_name} has an invalid radial frame quaternion")
    return "CAD assembly: 8 radial rigid arm meshes, hinges and position actuators"


def _check_scaffold(model: mujoco.MjModel) -> str:
    core_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_core")
    _require_name(model, mujoco.mjtObj.mjOBJ_JOINT, "core_free")
    for index in range(1, 9):
        body_name = f"arm{index:02d}_B_first"
        body_id = _require_name(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
        if model.body_parentid[body_id] != core_id:
            raise RuntimeError(f"{body_name} is not attached to octopus_core")
    return "legacy elastic cable scaffold"


def _select_model() -> tuple[mujoco.MjModel, mujoco.MjData, str]:
    models = Path(__file__).resolve().parents[2] / "models"
    cad_path = models / "octopus_dt_cad.xml"
    if cad_path.is_file():
        import xml.etree.ElementTree as ET

        root = ET.parse(cad_path).getroot()
        mesh_files = [models / "meshes" / item.attrib["file"]
                      for item in root.findall("./asset/mesh")]
        if mesh_files and all(path.is_file() for path in mesh_files):
            model = mujoco.MjModel.from_xml_path(str(cad_path))
            return model, mujoco.MjData(model), _check_cad_assembly(model)
    model, data = load_model()
    return model, data, _check_scaffold(model)


def main() -> None:
    model, data, description = _select_model()
    for _ in range(100):
        mujoco.mj_step(model, data)
    if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
        raise RuntimeError("Non-finite simulation state")
    print(
        f"MuJoCo model OK: {model.nbody} bodies, {model.njnt} joints, "
        f"{model.ngeom} geoms, {model.nu} actuators, "
        f"{model.nplugin} plugin instances; {description}"
    )


if __name__ == "__main__":
    main()
