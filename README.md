# OCTOPUS-DT — Open Octopus Digital Twin

An open research platform for a CAD-derived, eight-arm pneumatic soft robotic octopus. The project combines MuJoCo simulation, reduced-order underwater dynamics, reproducible experiments, and an interactive web-based research dashboard.

> **Research status:** early simulation scaffold. The initial cable-based model is a reduced-order approximation, not a validated 3D hyperelastic or pneumatic finite-element model. All estimated material mappings and actuation gains are explicitly marked as unvalidated.

## Project goals

- Reconstruct the robot from CAD-derived dimensions and document assumptions.
- Establish a compileable MuJoCo model with eight independently addressable arms.
- Add a controllable pressure-inspired bending input and basic underwater forces.
- Build reproducible experiment runners and machine-readable outputs.
- Visualize robot state and experiment results in a web dashboard.
- Calibrate model parameters against physical measurements before making performance claims.

## Repository layout

```text
apps/web/                 Next.js dashboard (Vercel)
simulation/models/        MuJoCo MJCF models
simulation/src/octopus_dt Python simulation package
simulation/tests/         Model and physics tests
research/parameters/      CAD-derived parameters and assumptions
research/experiments/     Experiment configurations
research/datasets/        Generated datasets (large files excluded)
docs/                     Model notes, validation and research protocol
.github/workflows/        Continuous integration
```

## CAD baseline

The recovered FreeCAD document describes a central body and eight radial tentacles. Key values currently captured in `research/parameters/cad_parameters.json` include a 200 mm body diameter, 100 mm body height, 220 mm active tentacle length, and ten pneumatic chambers per arm. Treat these as design inputs, not measured manufactured dimensions.

## Quick start (simulation)

Python 3.10+ is recommended. MuJoCo is installed from the Python package.

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e "simulation[dev]"
python -m octopus_dt.smoke_test
python -m octopus_dt.run_underwater --steps 2000 --output research/datasets/smoke_run.csv
```

On Linux/macOS, activate the environment with `source .venv/bin/activate`.

## Dashboard

The dashboard lives in `apps/web` and is designed for Vercel. It is a visualization and experiment-results interface; it does **not** host a persistent MuJoCo simulation process. Run MuJoCo locally or as a separate Python service/worker, then publish experiment artifacts for the dashboard to display.

## Model limitations and validation gates

1. The first arm representation uses MuJoCo's discrete elastic cable plugin. It approximates bending/twist along a centerline; it does not resolve chamber inflation, cross-section deformation, silicone hyperelasticity, limiting-layer mechanics, or pneumatic hysteresis.
2. Buoyancy and drag begin as simplified force terms. They are not CFD and require coefficient calibration.
3. The pressure-to-bending mapping is a placeholder. Pressure values alone do not establish safe operating limits.
4. The initial multi-arm model must pass MuJoCo compilation and stability tests before we add complex control.
5. Compare single-arm bending, tip trajectory, and force response against physical experiments before calibrating the full eight-arm model.

See [docs/model-assumptions.md](docs/model-assumptions.md) and [docs/validation-plan.md](docs/validation-plan.md).

## Development

- Keep each experiment configuration versioned.
- Save raw output with metadata and a configuration fingerprint.
- Label simulated, estimated, and measured quantities separately.
- Never present unvalidated simulation output as experimental evidence.

## License

MIT. See [LICENSE](LICENSE).
