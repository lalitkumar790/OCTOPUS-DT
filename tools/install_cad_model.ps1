param(
  [Parameter(Mandatory = $true)]
  [string]$PackageZip
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$TempRoot = Join-Path $env:TEMP ("octopus-dt-cad-" + [guid]::NewGuid().ToString("N"))

try {
  Expand-Archive -LiteralPath (Resolve-Path $PackageZip).Path -DestinationPath $TempRoot -Force
  $SourceModels = Join-Path $TempRoot "simulation/models"
  if (-not (Test-Path (Join-Path $SourceModels "octopus_dt_v0_1.xml"))) {
    throw "Package layout not recognized: simulation/models/octopus_dt_v0_1.xml is missing."
  }
  $TargetModels = Join-Path $RepoRoot "simulation/models"
  New-Item -ItemType Directory -Force -Path $TargetModels | Out-Null
  Copy-Item -Path (Join-Path $SourceModels "*") -Destination $TargetModels -Recurse -Force

  Write-Host "CAD model files copied into $TargetModels"
  Write-Host "Checking mesh assets..."
  $XmlPath = Join-Path $TargetModels "octopus_dt_v0_1.xml"
  [xml]$Mjcf = Get-Content -Raw -LiteralPath $XmlPath
  $MeshDir = Join-Path $TargetModels "meshes"
  $Missing = @()
  foreach ($Mesh in $Mjcf.mujoco.asset.mesh) {
    $MeshFile = Join-Path $MeshDir $Mesh.file
    if (-not (Test-Path $MeshFile)) { $Missing += $Mesh.file }
  }
  if ($Missing.Count -gt 0) {
    throw ("Missing mesh assets: " + ($Missing -join ", "))
  }

  Push-Location $RepoRoot
  try {
    git add simulation/models
    git commit -m "feat(simulation): replace generic MJCF with CAD-derived octopus assembly"
    git push origin main
  } finally {
    Pop-Location
  }
  Write-Host "CAD model committed and pushed. Next: run MuJoCo compile/test workflow."
} finally {
  if (Test-Path $TempRoot) { Remove-Item -LiteralPath $TempRoot -Recurse -Force }
}
