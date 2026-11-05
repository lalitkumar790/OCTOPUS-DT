# OCTOPUS-DT Simulation Package

The browser application is a Three.js renderer. The authoritative physics engine is the
separate Python MuJoCo service in `octopus_dt.server`.

## Run the real CAD MuJoCo backend locally

The CAD MJCF and its 30 STL assets must both be installed in `models/`. From the
repository root:

```bash
cd simulation
python -m pip install -e ".[server,dev]"
OCTOPUS_MODEL_PATH="$PWD/models/octopus_dt_cad.xml" uvicorn octopus_dt.server:app --host 0.0.0.0 --port 8000
```

On Windows PowerShell:

```powershell
cd simulation
python -m pip install -e ".[server,dev]"
$env:OCTOPUS_MODEL_PATH = "$PWD\models\octopus_dt_cad.xml"
uvicorn octopus_dt.server:app --host 0.0.0.0 --port 8000
```

`GET /health` reports unavailable if the CAD XML or referenced STL files are missing.
The service will not silently substitute the browser visualization or cable scaffold.

## Deploy the backend on the Raspberry Pi / another persistent host

From the repository root on the host:

```bash
cd simulation
cp .env.example .env
docker compose up -d --build
docker compose logs -f octopus-mujoco
curl http://127.0.0.1:8000/health
```

The service binds only to loopback on port 8000. To expose it, configure a Cloudflare
Tunnel public hostname such as `sim-octopus.your-domain` to
`http://host.docker.internal:8000`. If cloudflared runs in Docker, add
`extra_hosts: ["host.docker.internal:host-gateway"]` to that cloudflared service.
Set `OCTOPUS_CORS_ORIGINS` in `.env` to the exact Vercel origin and restart the
backend. Then add `NEXT_PUBLIC_SIM_API_URL=https://sim-octopus.your-domain` to the
Vercel project's Production environment and redeploy the dashboard.

Do not expose this research API publicly without authentication and rate limits.
The CORS allow-list is not authentication. Keep the calibration volume persistent.

## API

- `GET /health`: compile and model availability status.
- `GET /api/model`: MuJoCo joint state, actuator targets and base pose.
- `POST /api/sim/joints`: direct exploratory position targets in radians.
- `POST /api/sim/pressure`: requires a measured per-arm pressure calibration JSON.
- `POST /api/experiments/locomotion`: MuJoCo travelling-wave hinge experiment with body-wise buoyancy and drag.
- `POST /api/calibration/continuum`: fit ten pressure inputs to ten measured segment joint angles.
- `POST /api/continuum/pressure`: run the ten-segment single-arm model using saved calibration.
- `GET /assets/meshes/{filename}`: serve a CAD STL to the Three.js viewer.
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

## Install the CAD mesh package (Windows)

Download the supplied `OCTOPUS_DT_CAD_MJCF_repo_update.zip` package to Downloads.
Install the simulation dependencies first, then run the repository installer from
the repository root:

```powershell
cd simulation
python -m pip install -e ".[server,dev]"
cd ..
Set-ExecutionPolicy -Scope Process Bypass
.\tools\install_cad_model.ps1 -PackageZip "$HOME\Downloads\OCTOPUS_DT_CAD_MJCF_repo_update.zip"
```

The installer checks all 30 STL references, applies the eight radial arm-frame
quaternions, compiles the CAD MJCF with MuJoCo, runs the simulation smoke test,
and only then commits/pushes the mesh assets and corrected MJCF files.
