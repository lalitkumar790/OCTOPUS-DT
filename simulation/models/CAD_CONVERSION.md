# OCTOPUS-DT — CAD-derived MuJoCo model

This package was generated from the uploaded `OctopusRobot(2).FCStd` FreeCAD document.

## Files
- `octopus_dt_cad.xml` — MJCF assembly with the CAD-derived mesh assets.
- `meshes/*.stl` — triangulated BREP solids from the source document.
- `conversion_manifest.json` — conversion provenance, included/excluded objects, frame and modelling notes.

## Load in MuJoCo
From this directory:

```python
import mujoco
model = mujoco.MjModel.from_xml_path("octopus_dt_cad.xml")
data = mujoco.MjData(model)
```

The `arm_01_hinge` ... `arm_08_hinge` joints are controllable revolute joints at the CAD arm-interface frames. Position actuator controls are in radians, within ±1.2 rad.

## Important modelling boundary
This is a CAD-faithful **rigid assembly with eight rigidly hinged tentacle meshes**, not yet a physically validated pneumatic soft-robot simulation. The original tentacle solids are preserved as mesh geometry. The arm bodies do not deform along their length. Collision uses simplified capsule/ellipsoid proxies; the detailed CAD meshes are visual-only. Base/arm inertial properties and actuator gains are placeholders pending mass-property extraction and calibration. Buoyancy, hydrodynamics, chamber pressure, silicone hyperelasticity, and fluid-structure interaction are not implemented.

The next physically meaningful step is to segment each tentacle CAD solid into its ten chamber/pitch regions and replace each rigid arm with a calibrated articulated or continuum representation. That is where the pneumatic chamber geometry and material data should drive the physics rather than being guessed from the external mesh.
