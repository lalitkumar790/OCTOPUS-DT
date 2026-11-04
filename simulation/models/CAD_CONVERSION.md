# OCTOPUS-DT — CAD-derived MuJoCo model

Generated from the uploaded `OctopusRobot(2).FCStd` FreeCAD assembly.

## Package contents
- `octopus_dt_cad.xml` — MJCF assembly referencing the triangulated CAD mesh assets.
- `meshes/*.stl` — 30 BREP-derived STL meshes (22 static components and 8 placed tentacle instances).
- `conversion_manifest.json` — conversion provenance, included/excluded objects, frames and modelling notes.

## Load
Run from this directory:

```python
import mujoco
model = mujoco.MjModel.from_xml_path("octopus_dt_cad.xml")
data = mujoco.MjData(model)
```

The `arm_01_hinge` ... `arm_08_hinge` joints are revolute joints at the CAD arm-interface frames. Position actuator controls are in radians, within ±1.2 rad.

## Modelling boundary
This is a CAD-faithful **rigid assembly with eight rigidly hinged tentacle meshes**, not yet a validated pneumatic soft-robot simulation. The arms do not deform along their length. Collision uses simplified capsule/ellipsoid proxies; detailed CAD meshes are visual-only. Base/arm inertial properties and actuator gains are placeholders pending mass-property extraction and calibration. Buoyancy, hydrodynamics, chamber pressure, silicone hyperelasticity and fluid-structure interaction are not implemented.

The CAD parameter sheet identifies ten pneumatic chambers per tentacle. A meaningful next phase is to segment the actual arm solids by chamber/pitch regions and replace each rigid arm with a calibrated articulated or continuum model. Do not interpret the current hinge actuators as pneumatic pressure control.

**Validation status:** XML well-formedness, mesh references and STL geometry were checked during conversion. MuJoCo runtime compilation has not yet been verified.
