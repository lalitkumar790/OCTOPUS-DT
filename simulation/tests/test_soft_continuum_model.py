from pathlib import Path

import mujoco
import numpy as np

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "octopus_soft_continuum.xml"


def test_eight_arm_continuum_model_compiles_with_80_pressure_actuators():
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))

    assert model.nu == 80
    assert model.njnt == 81  # one floating base + 80 segment hinges
    for arm in range(1, 9):
        assert mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_SITE, f"arm_{arm}_tip"
        ) >= 0
        for segment in range(1, 11):
            assert mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"pressure_{arm}_{segment}"
            ) >= 0


def test_uniform_pressure_bends_each_serial_segment_not_a_single_root_hinge():
    model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
    data = mujoco.MjData(model)
    initial_tip_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "arm_1_tip")
    mujoco.mj_forward(model, data)
    initial_tip = data.site_xpos[initial_tip_id].copy()

    for segment in range(1, 11):
        actuator_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_ACTUATOR, f"pressure_1_{segment}"
        )
        data.ctrl[actuator_id] = 40.0

    for _ in range(600):
        mujoco.mj_step(model, data)

    joint_angles = []
    for segment in range(1, 11):
        joint_id = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_JOINT, f"arm_1_joint_{segment:02d}"
        )
        joint_angles.append(data.qpos[int(model.jnt_qposadr[joint_id])])

    assert np.all(np.asarray(joint_angles) > 0.02)
    assert float(np.sum(joint_angles)) > 0.5
    assert float(np.linalg.norm(data.site_xpos[initial_tip_id] - initial_tip)) > 0.02
