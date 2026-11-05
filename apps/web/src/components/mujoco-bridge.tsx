"use client";

import { useEffect, useState } from "react";

type ArmState = { joint_angle_rad: number; joint_velocity_rad_s: number };
type SimState = { simulation_time_s: number; base_position_m: number[]; arms: ArmState[] };
type RunResult = {
  displacement_m: number;
  forward_displacement_x_m: number;
  energy_j: number;
  cost_of_transport_proxy: number;
  steps: number;
  duration_s: number;
  limitations: string[];
};

const API = (process.env.NEXT_PUBLIC_SIM_API_URL ?? "").replace(/\/$/, "");

export default function MuJoCoBridge() {
  const [status, setStatus] = useState("not configured");
  const [state, setState] = useState<SimState | null>(null);
  const [arm, setArm] = useState(0);
  const [target, setTarget] = useState(0);
  const [pressures, setPressures] = useState<number[]>(Array(10).fill(0));
  const [measuredPressure, setMeasuredPressure] = useState("");
  const [measuredAngles, setMeasuredAngles] = useState("");
  const [calibrationMessage, setCalibrationMessage] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);

  useEffect(() => {
    if (!API) {
      setStatus("API URL not configured");
      return;
    }
    let active = true;
    const poll = async () => {
      try {
        const health = await fetch(API + "/health", { cache: "no-store" });
        const healthData = await health.json();
        if (!active) return;
        if (healthData.status !== "ready") {
          setStatus("CAD MuJoCo unavailable");
          setState(null);
          return;
        }
        const response = await fetch(API + "/api/model", { cache: "no-store" });
        if (!response.ok) throw new Error("MuJoCo state unavailable");
        const payload = await response.json();
        if (active) {
          setStatus("connected · real MuJoCo");
          setState(payload);
        }
      } catch {
        if (active) {
          setStatus("offline");
          setState(null);
        }
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 1000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  const applyHinge = async () => {
    if (!API || !state) return;
    const targets = Array.from({ length: 8 }, (_, index) =>
      index === arm ? target : state.arms[index]?.joint_angle_rad ?? 0,
    );
    try {
      const response = await fetch(API + "/api/sim/joints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ joint_targets_rad: targets, steps: 40 }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "MuJoCo command failed");
      setState(payload);
      setMessage("Command applied to the MuJoCo hinge actuator.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Request failed");
    }
  };

  const applyPressure = async () => {
    if (!API) return;
    try {
      const response = await fetch(API + "/api/continuum/pressure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pressures_kpa: pressures, steps: 50 }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Continuum pressure run failed");
      setMessage(
        `10-segment MuJoCo arm: tip [${payload.tip_position_m.map((x: number) => x.toFixed(3)).join(", ")}] m`,
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Request failed");
    }
  };

  const fitCalibration = async () => {
    if (!API) return;
    try {
      const pressureData = JSON.parse(measuredPressure);
      const angleData = JSON.parse(measuredAngles);
      const response = await fetch(API + "/api/calibration/continuum", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pressures_kpa: pressureData,
          joint_angles_rad: angleData,
          ridge: 0.000001,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Calibration fit failed");
      setCalibrationMessage(
        `Fit saved: ${payload.sample_count} measured samples · ${payload.segment_count} segments · max RMSE ${Math.max(...payload.rmse_rad_per_segment).toFixed(5)} rad`,
      );
    } catch (error) {
      setCalibrationMessage(error instanceof Error ? error.message : "Invalid calibration data");
    }
  };

  const runGait = async () => {
    if (!API) return;
    setBusy(true);
    setResult(null);
    try {
      const response = await fetch(API + "/api/experiments/locomotion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          duration_s: 8,
          frequency_hz: 0.25,
          amplitude_rad: 0.35,
          phase_lag_rad: 0.45,
          water_density_kg_m3: 997,
          displaced_volume_m3: 0.001,
          projected_area_m2: 0.06,
          drag_coefficient: 1.1,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Experiment failed");
      setResult(payload);
      setMessage("Underwater gait experiment completed by MuJoCo.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Experiment failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mujoco-section">
      <div className="section-heading">
        <div>
          <div className="panel-kicker">05 / LIVE SIMULATION BACKEND</div>
          <h2>MuJoCo control & experiment runner</h2>
        </div>
        <span className={status.includes("connected") ? "engine-status ready" : "engine-status offline"}>
          <i /> {status.toUpperCase()}
        </span>
      </div>
      <p className="control-intro">
        These controls send commands to the separate Python MuJoCo service. The Three.js preview is not the physics engine.
        Configure NEXT_PUBLIC_SIM_API_URL to point at the backend's HTTPS origin.
      </p>
      <div className="mujoco-grid">
        <div className="mujoco-card">
          <div className="panel-kicker">CAD ASSEMBLY / 8 REAL HINGES</div>
          <label htmlFor="mujoco-arm">SELECT JOINT
            <select id="mujoco-arm" value={arm} onChange={(event) => setArm(Number(event.target.value))}>
              {Array.from({ length: 8 }, (_, index) => (
                <option key={index} value={index}>Arm {String(index + 1).padStart(2, "0")}</option>
              ))}
            </select>
          </label>
          <label htmlFor="mujoco-target">HINGE TARGET
            <output>{target.toFixed(2)} rad / {(target * 180 / Math.PI).toFixed(1)}°</output>
          </label>
          <input id="mujoco-target" type="range" min="-1.2" max="1.2" step="0.01"
            value={target} onChange={(event) => setTarget(Number(event.target.value))} />
          <button className="run-button" disabled={!state} onClick={applyHinge}>APPLY TO MUJOCO ↗</button>
          {state && <div className="mujoco-state">
            <span>Simulation time <b>{state.simulation_time_s.toFixed(3)} s</b></span>
            <span>Joint angle <b>{state.arms[arm]?.joint_angle_rad.toFixed(4)} rad</b></span>
            <span>Joint velocity <b>{state.arms[arm]?.joint_velocity_rad_s.toFixed(4)} rad/s</b></span>
          </div>}
        </div>
        <div className="mujoco-card">
          <div className="panel-kicker">SINGLE ARM / 10 SEGMENT CONTINUUM SURROGATE</div>
          <p className="control-intro">Enter measured pressure-to-segment-angle data to fit the response. Pressure commands stay disabled until calibration exists.</p>
          <div className="continuum-pressure">
            {pressures.map((pressure, index) => (
              <label key={index}>C{index + 1}
                <input type="number" min="0" max="80" step="1" value={pressure}
                  onChange={(event) => setPressures((old) => old.map((v, i) => i === index ? Number(event.target.value) : v))} />
              </label>
            ))}
          </div>
          <button className="run-button" onClick={applyPressure}>RUN CALIBRATED CONTINUUM ARM</button>
        </div>
        <div className="mujoco-card calibration-card">
          <div className="panel-kicker">MEASURED DATA / CALIBRATION FIT</div>
          <label>PRESSURE SAMPLES (JSON ARRAY)
            <textarea rows={3} value={measuredPressure} onChange={(event) => setMeasuredPressure(event.target.value)}
              placeholder="[[0,0,...],[10,0,...], ...]" />
          </label>
          <label>MEASURED JOINT ANGLES (JSON ARRAY, radians)
            <textarea rows={3} value={measuredAngles} onChange={(event) => setMeasuredAngles(event.target.value)}
              placeholder="[[0,0,...],[0.02,0,...], ...]" />
          </label>
          <button className="reset-button" onClick={fitCalibration}>FIT & SAVE CALIBRATION</button>
          {calibrationMessage && <p className="bridge-message">{calibrationMessage}</p>}
          <small>Use independently varied measured samples. Ten chambers require at least eleven independent rows; collect more for validation and hysteresis analysis.</small>
        </div>
        <div className="mujoco-card">
          <div className="panel-kicker">UNDERWATER / LOCOMOTION EXPERIMENT</div>
          <p className="control-intro">Runs an eight-arm travelling-wave hinge gait with distributed buoyancy and quadratic drag applied inside MuJoCo.</p>
          <button className="run-button" disabled={!state || busy} onClick={runGait}>
            {busy ? "RUNNING MUJOCO…" : "RUN 8 SECOND GAIT"}
          </button>
          {result && <div className="mujoco-results">
            <strong>MUJOCO RESULT</strong>
            <span>Displacement <b>{result.displacement_m.toFixed(5)} m</b></span>
            <span>Forward Δx <b>{result.forward_displacement_x_m.toFixed(5)} m</b></span>
            <span>Actuator work <b>{result.energy_j.toFixed(5)} J</b></span>
            <span>CoT proxy <b>{result.cost_of_transport_proxy.toFixed(5)}</b></span>
            <small>{result.steps} integration steps · {result.duration_s.toFixed(2)} s</small>
          </div>}
        </div>
      </div>
      {message && <p className="bridge-message">{message}</p>}
      <p className="mujoco-footnote">Research boundary: the CAD model is rigid with one hinge per arm. The continuum arm is a ten-link surrogate with placeholder inertias/gains. Underwater forces are reduced-order assumptions, not CFD/FSI. Calibrated performance claims require measured mass properties, displaced volume, drag, pressure and bending data.</p>
    </section>
  );
}
