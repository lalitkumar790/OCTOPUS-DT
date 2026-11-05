# OCTOPUS-DT Simulation Package

The browser application is a Three.js renderer. The authoritative physics engine is the
separate Python MuJoCo service in `octopus_dt.server`.

## Run the real CAD MuJoCo backend

The CAD MJCF and its 30 STL assets must both be installed in `models/`. From the
repository root:

```bash
cd simulation
python -m pip install -e ".[server,dev]"
OCTOPUS_MODEL_PATH="$PWD/models/octopus_dt_cad.xml" uvicorn octopus_dt.server:app --host 0.0.0.0 --port 8000
```

On Windows PowerShell, set the environment variable with
`$env:OCTOPUS_MODEL_PATH = "$PWD\models\octopus_dt_cad.xml"` before starting Uvicorn.

`GET /health` reports unavailable if the CAD XML or referenced STL files are missing.
It will not silently substitute the browser visualization or the cable scaffold.

## API

- `GET /health`: compile and model availability status.
- `GET /api/model`: MuJoCo joint state, actuator targets and base pose.
- `POST /api/sim/joints`: direct exploratory position targets in radians.
- `POST /api/sim/pressure`: requires a measured per-arm pressure calibration JSON.
- `POST /api/experiments/locomotion`: MuJoCo travelling-wave hinge experiment with body-wise buoyancy and drag.
- `POST /api/calibration/continuum`: fit ten pressure inputs to ten measured segment joint angles.
- `POST /api/continuum/pressure`: run the ten-segment single-arm model using saved calibration.
- `WS /ws`: live MuJoCo state stream.

## Single-arm continuum approximation

`models/octopus_arm_continuum.xml` divides the approximately 275 mm CAD arm into
ten 27.5 mm articulated segments. It is an engineering surrogate for early
controller/calibration experiments, not a validated silicone hyperelastic model.
Its 20 g segment masses, capsule radius and actuator gains are explicit placeholders.
Replace them with measured segment mass/inertia, chamber geometry, bending tests,
and material characterization before quantitative claims.

The multi-output calibration requires independently varied measured pressure
vectors and measured segment angles. With ten chambers, use at least eleven
independent samples; in practice collect substantially more, with repeated
loading/unloading sweeps to expose hysteresis. Do not use synthetic values as
physical calibration.

## Underwater model boundary

The eight-arm CAD experiment applies buoyancy and quadratic drag to each body,
with displaced volume and projected area apportioned by body mass. The gait is
a travelling wave of hinge targets. This is a real MuJoCo integration, but not
CFD, vortex shedding, added-mass modelling, or fluid-structure interaction.
The CAD model currently has rigid tentacles with one hinge per arm. Reported
displacement and actuator work are simulation outputs conditional on the
declared mass, fluid and drag assumptions, not validated swimming performance.

## Deployment

Use `docker build -f simulation/Dockerfile -t octopus-dt-sim .` from the repo
root, then run the container on a persistent Python host. Point the Vercel
dashboard's `NEXT_PUBLIC_SIM_API_URL` at the public HTTPS API origin. Do not
run MuJoCo inside a Vercel serverless function. Protect write endpoints with
authentication/rate limits before exposing the API publicly.
