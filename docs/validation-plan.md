# Validation plan

## Gate 0 — Software correctness

- Load the MJCF with the pinned MuJoCo runtime.
- Assert all expected arm roots and tips exist.
- Run a short zero-input simulation and check for finite state values.
- Record MuJoCo/Python versions and model hash.

## Gate 1 — Single-arm mechanical calibration

- Build and test one arm before claiming full eight-arm soft-body fidelity.
- Record specimen geometry and material batch.
- Measure pressure, tip position/orientation, and (where possible) force.
- Fit parameters on a calibration set and report residuals on held-out trials.
- Document uncertainty and repeatability.

## Gate 2 — Eight-arm integration

- Verify independent arm indexing and actuation.
- Check timestep sensitivity, energy/stability behavior, and self-collision strategy.
- Compare symmetric and asymmetric commands.

## Gate 3 — Underwater validation

- Measure mass, displaced volume, and neutral buoyancy.
- Estimate drag coefficients from controlled tow or decay tests.
- Compare simulated and measured trajectories across multiple speeds.

## Reporting rules

Separate CAD design inputs, estimated parameters, calibrated values, and measured observations. Include units, conditions, and uncertainty. Do not call a result validated unless the corresponding gate has been passed.
