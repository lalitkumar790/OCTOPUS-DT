"""FastAPI service that runs the CAD MJCF in the real MuJoCo engine.

Run from the repository root with:
  cd simulation && pip install -e ".[server]" && uvicorn octopus_dt.server:app --reload

The CAD model is intentionally required. This service does not silently fall
back to the browser preview or the old cable scaffold.
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Any

import mujoco
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .actuation import travelling_wave_joint_targets
from .calibration import fit_pressure_to_joint_angles, predict_joint_angles
from .hydrodynamics import distributed_hydrodynamic_forces


ROOT = Path(__file__).resolve().parents[3]
SIMULATION_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("OCTOPUS_MODEL_PATH", SIMULATION_DIR / "models" / "octopus_dt_cad.xml"))
CONTINUUM_PATH = Path(__file__).resolve().parents[2] / "models" / "octopus_arm_continuum.xml"
CALIBRATION_DIR = Path(os.getenv("OCTOPUS_CALIBRATION_DIR", ROOT / "research" / "calibration"))
ARM_COUNT = 8
CHAMBER_COUNT = 10


class PressureCommand(BaseModel):
    arm_index: int = Field(ge=0, lt=ARM_COUNT)
    pressures_kpa: list[float] = Field(min_length=CHAMBER_COUNT, max_length=CHAMBER_COUNT)
    steps: int = Field(default=25, ge=1, le=2000)


class JointCommand(BaseModel):
    joint_targets_rad: list[float] = Field(min_length=ARM_COUNT, max_length=ARM_COUNT)
    steps: int = Field(default=25, ge=1, le=2000)


class LocomotionRequest(BaseModel):
    duration_s: float = Field(default=8.0, gt=0, le=120)
    frequency_hz: float = Field(default=0.25, gt=0, le=3)
    amplitude_rad: float = Field(default=0.35, ge=0, le=1.2)
    phase_lag_rad: float = Field(default=0.45, ge=0, le=3.14)
    water_density_kg_m3: float = Field(default=997.0, gt=0, le=1300)
    displaced_volume_m3: float = Field(default=0.001, gt=0, le=0.02)
    projected_area_m2: float = Field(default=0.06, gt=0, le=1)
    drag_coefficient: float = Field(default=1.1, ge=0, le=5)
    record_every: int = Field(default=10, ge=1, le=1000)


class CalibrationRequest(BaseModel):
    pressures_kpa: list[list[float]]
    joint_angles_rad: list[list[float]]
    ridge: float = Field(default=1e-6, ge=0)


class ContinuumPressureRequest(BaseModel):
    pressures_kpa: list[float] = Field(min_length=CHAMBER_COUNT, max_length=CHAMBER_COUNT)
    steps: int = Field(default=25, ge=1, le=2000)


class SimulationEngine:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.model: mujoco.MjModel | None = None
        self.data: mujoco.MjData | None = None
        self.arm_joint_ids: list[int] = []
        self.arm_actuator_ids: list[int] = []
        self.continuum_model: mujoco.MjModel | None = None
        self.continuum_data: mujoco.MjData | None = None

    def load(self) -> None:
        with self.lock:
            if self.model is not None:
                return
            if not MODEL_PATH.is_file():
                raise FileNotFoundError(
                    f"CAD MJCF not found at {MODEL_PATH}. Install the CAD mesh package first."
                )
            model = mujoco.MjModel.from_xml_path(str(MODEL_PATH))
            data = mujoco.MjData(model)
            base = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base")
            if base < 0:
                raise RuntimeError("Selected MJCF is not the CAD assembly: octopus_base is missing")
            joints, actuators = [], []
            for arm in range(1, ARM_COUNT + 1):
                joint = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT,
                                          f"arm_{arm:02d}_hinge")
                actuator = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR,
                                             f"arm_{arm:02d}_position")
                if joint < 0 or actuator < 0:
                    raise RuntimeError(f"CAD arm {arm:02d} hinge/actuator is missing")
                joints.append(joint)
                actuators.append(actuator)
            self.model, self.data = model, data
            self.arm_joint_ids, self.arm_actuator_ids = joints, actuators
            mujoco.mj_forward(model, data)

    def require(self) -> tuple[mujoco.MjModel, mujoco.MjData]:
        self.load()
        assert self.model is not None and self.data is not None
        return self.model, self.data

    def state(self) -> dict[str, Any]:
        model, data = self.require()
        with self.lock:
            base = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base")
            arms = []
            for index, (joint_id, actuator_id) in enumerate(
                zip(self.arm_joint_ids, self.arm_actuator_ids, strict=True)
            ):
                qadr = int(model.jnt_qposadr[joint_id])
                dadr = int(model.jnt_dofadr[joint_id])
                arms.append({
                    "arm_index": index,
                    "joint_angle_rad": float(data.qpos[qadr]),
                    "joint_velocity_rad_s": float(data.qvel[dadr]),
                    "actuator_target_rad": float(data.ctrl[actuator_id]),
                })
            return {
                "engine": "MuJoCo",
                "model": "CAD-derived rigid eight-arm assembly",
                "simulation_time_s": float(data.time),
                "base_position_m": data.xpos[base].tolist(),
                "arms": arms,
                "nq": int(model.nq), "nv": int(model.nv),
                "nbody": int(model.nbody), "ngeom": int(model.ngeom), "nu": int(model.nu),
            }

    def set_targets(self, targets: list[float], steps: int) -> dict[str, Any]:
        model, data = self.require()
        if len(targets) != ARM_COUNT or not np.all(np.isfinite(targets)):
            raise ValueError("Exactly eight finite joint targets are required")
        with self.lock:
            for actuator_id, target in zip(self.arm_actuator_ids, targets, strict=True):
                data.ctrl[actuator_id] = float(np.clip(target, -1.2, 1.2))
            for _ in range(steps):
                mujoco.mj_step(model, data)
            return self.state()

    def step_gait(self, request: LocomotionRequest) -> dict[str, Any]:
        model, data = self.require()
        with self.lock:
            mujoco.mj_resetData(model, data)
            model.opt.gravity[:] = [0.0, 0.0, -9.81]
            base_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "octopus_base")
            dynamic_ids = [base_id] + [
                mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, f"arm_{i:02d}")
                for i in range(1, ARM_COUNT + 1)
            ]
            masses = np.array([model.body_mass[i] for i in dynamic_ids], dtype=float)
            if np.any(masses <= 0):
                raise RuntimeError("CAD model body masses must be calibrated before hydrodynamic runs")
            dt = float(model.opt.timestep)
            steps = int(request.duration_s / dt)
            start = data.xpos[base_id].copy()
            energy_j = 0.0
            trace: list[dict[str, Any]] = []
            for step in range(steps):
                t = float(data.time)
                targets = travelling_wave_joint_targets(
                    t, amplitude_rad=request.amplitude_rad,
                    frequency_hz=request.frequency_hz,
                    phase_lag_rad=request.phase_lag_rad,
                )
                for actuator_id, target in zip(self.arm_actuator_ids, targets, strict=True):
                    data.ctrl[actuator_id] = target
                velocities = []
                for body_id in dynamic_ids:
                    spatial = np.zeros(6, dtype=float)
                    mujoco.mj_objectVelocity(
                        model, data, mujoco.mjtObj.mjOBJ_BODY, body_id, spatial, 0
                    )
                    velocities.append(spatial[3:6].copy())
                loads = distributed_hydrodynamic_forces(
                    np.asarray(velocities), masses, request.displaced_volume_m3,
                    request.projected_area_m2, request.water_density_kg_m3,
                    request.drag_coefficient,
                )
                data.xfrc_applied[:] = 0.0
                for body_id, force in zip(dynamic_ids, loads, strict=True):
                    data.xfrc_applied[body_id, 3:6] = force
                mujoco.mj_step(model, data)
                power = float(np.sum(np.abs(data.actuator_force * data.actuator_velocity)))
                energy_j += power * dt
                if step % request.record_every == 0 or step == steps - 1:
                    position = data.xpos[base_id].copy()
                    trace.append({
                        "time_s": float(data.time),
                        "base_position_m": position.tolist(),
                        "speed_m_s": float(np.linalg.norm(data.qvel[3:6])),
                        "actuator_power_w": power,
                    })
            end = data.xpos[base_id].copy()
            return {
                "engine": "MuJoCo",
                "model": "CAD-derived rigid eight-arm assembly",
                "duration_s": float(data.time),
                "steps": steps,
                "displacement_m": float(np.linalg.norm(end - start)),
                "forward_displacement_x_m": float(end[0] - start[0]),
                "energy_j": energy_j,
                "cost_of_transport_proxy": float(energy_j / (masses.sum() * 9.81 *
                    max(float(np.linalg.norm(end - start)), 1e-6))),
                "final_base_position_m": end.tolist(),
                "trace": trace,
                "limitations": [
                    "rigid single-hinge CAD arms, not deformable pneumatic tentacles",
                    "body-wise quadratic drag and mass-proportional buoyancy are reduced-order",
                    "mass, displaced volume, projected area and drag coefficient need measurement",
                    "travelling-wave joint targets are exploratory kinematics, not pressure control",
                ],
            }


engine = SimulationEngine()
app = FastAPI(title="OCTOPUS-DT MuJoCo Research API", version="0.2.0")
origins = [x.strip() for x in os.getenv("OCTOPUS_CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["*"],
)



@app.get("/assets/meshes/{filename}")
def cad_mesh(filename: str) -> FileResponse:
    if Path(filename).name != filename or not filename.endswith(".stl"):
        raise HTTPException(status_code=404, detail="Mesh not found")
    mesh_path = MODEL_PATH.parent / "meshes" / filename
    if not mesh_path.is_file():
        raise HTTPException(status_code=404, detail=f"CAD mesh asset is missing: {filename}")
    return FileResponse(mesh_path, media_type="model/stl", filename=filename)

@app.get("/health")
def health() -> dict[str, Any]:
    try:
        model, _ = engine.require()
        return {"status": "ready", "engine": "MuJoCo", "model": str(MODEL_PATH),
                "cad_model": True, "nu": int(model.nu)}
    except Exception as exc:  # noqa: BLE001  # noqa: BLE001
        return {"status": "unavailable", "engine": "MuJoCo", "cad_model": False,
                "detail": str(exc)}


@app.get("/api/model")
def model_info() -> dict[str, Any]:
    try:
        return engine.state()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/sim/reset")
def reset_simulation() -> dict[str, Any]:
    try:
        model, data = engine.require()
        with engine.lock:
            mujoco.mj_resetData(model, data)
            mujoco.mj_forward(model, data)
        return engine.state()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/sim/joints")
def set_joint_targets(command: JointCommand) -> dict[str, Any]:
    try:
        return engine.set_targets(command.joint_targets_rad, command.steps)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sim/pressure")
def set_pressure(command: PressureCommand) -> dict[str, Any]:
    if not np.all(np.isfinite(command.pressures_kpa)) or any(
        value < 0 or value > 80 for value in command.pressures_kpa
    ):
        raise HTTPException(status_code=422, detail="Pressures must be between 0 and 80 kPa")
    path = CALIBRATION_DIR / f"arm_{command.arm_index + 1:02d}.json"
    if not path.is_file():
        raise HTTPException(status_code=409, detail=(
            f"No measured calibration exists for arm {command.arm_index + 1}. "
            "Upload measured pressure/tip-angle data before pressure commands can drive MuJoCo."
        ))
    try:
        calibration = json.loads(path.read_text(encoding="utf-8"))
        target = float(calibration["intercept_rad"] + np.dot(
            calibration["coefficients_rad_per_kpa"], command.pressures_kpa
        ))
        targets = [0.0] * ARM_COUNT
        targets[command.arm_index] = float(np.clip(target, -1.2, 1.2))
        return engine.set_targets(targets, command.steps)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/experiments/locomotion")
def locomotion_experiment(request: LocomotionRequest) -> dict[str, Any]:
    try:
        return engine.step_gait(request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/calibration/continuum")
def calibrate_continuum(request: CalibrationRequest) -> dict[str, Any]:
    try:
        result = fit_pressure_to_joint_angles(
            np.asarray(request.pressures_kpa), np.asarray(request.joint_angles_rad),
            request.ridge,
        )
        CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
        (CALIBRATION_DIR / "continuum_arm.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/continuum/pressure")
def continuum_pressure(request: ContinuumPressureRequest) -> dict[str, Any]:
    if not np.all(np.isfinite(request.pressures_kpa)) or any(
        value < 0 or value > 80 for value in request.pressures_kpa
    ):
        raise HTTPException(status_code=422, detail="Pressures must be between 0 and 80 kPa")
    calibration_path = CALIBRATION_DIR / "continuum_arm.json"
    if not calibration_path.is_file():
        raise HTTPException(status_code=409, detail="Fit and save measured continuum calibration first")
    try:
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        targets = predict_joint_angles(calibration, np.asarray(request.pressures_kpa))
        if len(targets) != CHAMBER_COUNT:
            raise ValueError("Continuum calibration must contain ten segment outputs")
        if engine.continuum_model is None:
            engine.continuum_model = mujoco.MjModel.from_xml_path(str(CONTINUUM_PATH))
            engine.continuum_data = mujoco.MjData(engine.continuum_model)
        model, data = engine.continuum_model, engine.continuum_data
        assert data is not None
        with engine.lock:
            for i, target in enumerate(targets):
                data.ctrl[i] = float(np.clip(target, -0.8, 0.8))
            for _ in range(request.steps):
                mujoco.mj_step(model, data)
            tip_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "arm_tip")
            return {"engine": "MuJoCo", "model": "10-segment single-arm continuum approximation",
                    "simulation_time_s": float(data.time), "pressures_kpa": request.pressures_kpa,
                    "joint_angles_rad": data.qpos[:CHAMBER_COUNT].tolist(),
                    "tip_position_m": data.site_xpos[tip_id].tolist(),
                    "calibration_rmse_rad": calibration["rmse_rad_per_segment"],
                    "calibrated": True}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.websocket("/ws")
async def stream_state(socket: WebSocket) -> None:
    await socket.accept()
    try:
        while True:
            try:
                model, data = engine.require()
                with engine.lock:
                    mujoco.mj_step(model, data)
                    state = engine.state()
                await socket.send_json(state)
            except Exception as exc:  # noqa: BLE001
                await socket.send_json({"engine": "MuJoCo", "status": "unavailable",
                                        "detail": str(exc)})
                await asyncio.sleep(1.0)
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        return
