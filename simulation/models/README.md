# Simulation models

- `octopus_dt_v0_1.xml` — CAD-derived MJCF assembly, when installed with the matching `meshes/` directory.
- `octopus_dt_cad.xml` — staged CAD-derived model reference.
- `CAD_CONVERSION.md` and `conversion_manifest.json` — provenance and modelling limits.

The CAD model uses the original FreeCAD assembly's body, interfaces, sensors, cable features and eight placed tentacle instances. It is currently a rigid assembly with one shoulder hinge per tentacle; it is not yet a pneumatic continuum simulation.

**Important:** the CAD MJCF cannot load unless all referenced STL files are present in `meshes/`. Download the repo-update ZIP from the project conversation and run:

```powershell
.\tools\install_cad_model.ps1 -PackageZip "$HOME\Downloads\OCTOPUS_DT_CAD_MJCF_repo_update.zip"
```

The script copies the model and meshes, verifies every referenced STL exists, and then commits/pushes the CAD model to `main`. MuJoCo runtime compilation is a separate validation step.
