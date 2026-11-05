"""Compile CAD and ten-segment MuJoCo models; fall back only for absent CAD assets."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np

from .model import load_model


def require_name(model: mujoco.MjModel, object_type: mujoco.mjtObj, name: str) -> int:
    object_id = mujoco.mj_name2id(model, object_type, name)
    if object_id < 0:
        raise RuntimeError(f"Missing MuJoCo object: {name}")
    return object_id


def select_full_model() -> tuple[mujoco.MjModel, mujoco.MjData, str]:
    models = Path(__file__).resolve().parents[2] / "models"
    cad_path = models / "octopus_dt_cad.xml"
    if cad_path.is_file():
        root = ET.parse(cad_path).getroot()
        meshes = [models / "meshes" / item.attrib["file"]
                  for item in root.findall("./asset/mesh")]
        if meshes and all(path.is_file() for path in meshes):
            model = mujoco.MjModel.from_xml_path(str(cad_path))
            base = require_name(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base")
            require_name(model, mujoco.mjtObj.mjOBJ_JOINT, "base_free")
            for index in range(1, 9):
                name = f"arm_{index:02d}"
                body = require_name(model, mujoco.mjtObj.mjOBJ_BODY, name)
                require_name(model, mujoco.mjtObj.mjOBJ_JOINT, name + "_hinge")
                require_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name + "_position")
                if model.body_parentid[body] != base:
                    raise RuntimeError(f"{name} is not attached to octopus_base")
                if not np.isclose(np.linalg.norm(model.body_quat[body]), 1.0, atol=1e-6):
                    raise RuntimeError(f"{name} has an invalid radial frame quaternion")
            return model, mujoco.MjData(model), "CAD assembly with eight radial rigid arms"
    model, data = load_model()
    core = require_name(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_core")
    require_name(model, mujoco.mjtObj.mjOBJ_JOINT, "core_free")
    for index in range(1, 9):
        body = require_name(model, mujoco.mjtObj.mjOBJ_BODY, f"arm{index:02d}_B_first")
        if model.body_parentid[body] != core:
            raise RuntimeError("Legacy cable root is not attached to octopus_core")
    return model, data, "legacy cable scaffold (CAD mesh assets not installed)"


def main() -> None:
    model, data, description = select_full_model()
    for _ in range(100):
        mujoco.mj_step(model, data)
    if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
        raise RuntimeError("Full model produced a non-finite state")

    path = Path(__file__).resolve().parents[2] / "models" / "octopus_arm_continuum.xml"
    continuum = mujoco.MjModel.from_xml_path(str(path))
    continuum_data = mujoco.MjData(continuum)
    if continuum.njnt != 10 or continuum.nu != 10:
        raise RuntimeError("Continuum model must have ten joints and ten actuators")
    for _ in range(100):
        mujoco.mj_step(continuum, continuum_data)
    if not np.all(np.isfinite(continuum_data.qpos)):
        raise RuntimeError("Continuum model produced a non-finite state")
    print(
        f"MuJoCo OK: {model.nbody} bodies, {model.njnt} joints, "
        f"{model.ngeom} geoms, {model.nu} actuators; {description}"
    )
    print(
        f"Continuum OK: {continuum.nbody} bodies, {continuum.njnt} joints, "
        f"{continuum.nu} actuators"
    )


if __name__ == "__main__":
    main()
