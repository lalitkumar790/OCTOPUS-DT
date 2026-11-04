# Model assumptions and scope

## Geometry

The first model is driven by the recovered FreeCAD parameter sheet. The body is represented by a simple rigid ellipsoid, and each arm is represented by a centerline elastic cable with an equivalent radius derived from the nominal width/height envelope. These simplifications are for early integration and visualization.

## Material mapping

The CAD notes include a Yeoh C10 reference for Ecoflex 0030 of 0.0322 MPa. For a nearly incompressible isotropic material, a small-strain estimate is:

- shear modulus: G ≈ 2 C10 = 64.4 kPa
- Young's modulus: E ≈ 6 C10 = 193.2 kPa

This is only a rough small-strain estimate. It is not a validated conversion of the full Yeoh model into the MuJoCo cable plugin's parameters. Higher-order Yeoh coefficients, rate dependence, manufacturing variation, and measured stress-strain curves are currently missing.

## Actuation

The pressure-to-generalized-torque gain is a placeholder used to exercise the software pipeline. It is not a physical calibration. Real pneumatic bending depends on chamber geometry, neutral-axis offset, constraints, pressure, and material behavior. Do not interpret the placeholder as predicted force or safe pressure.

## Underwater environment

The initial environment applies simplified buoyancy and velocity-dependent drag forces. It is not a fluid solver, does not resolve wake interactions, and does not capture added mass or fluid-structure coupling. Coefficients require calibration.

## What the cable model does not represent

- Chamber inflation and pressure-volume response
- 3D hyperelastic deformation of the silicone
- The limiting layer and kirigami/segmented reinforcement mechanics
- Contact, self-collision, and arm-arm fluid interactions at research fidelity
- Hysteresis, viscoelasticity, fatigue, and manufacturing tolerances

The next physics milestone is a single-arm model calibrated against measured tip displacement and pressure-response data.
