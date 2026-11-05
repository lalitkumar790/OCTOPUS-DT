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

  # Each STL is expressed in its interface-local +X frame; rotate the body
  # frame so all eight tentacles radiate from the centre at 45-degree spacing.
  $Rotations = @(
    "1 0 0 0",
    "0.923879533 0 0 0.382683432",
    "0.707106781 0 0 0.707106781",
    "0.382683432 0 0 0.923879533",
    "0 0 0 1",
    "0.382683432 0 0 -0.923879533",
    "0.707106781 0 0 -0.707106781",
    "0.923879533 0 0 -0.382683432"
  )
  $XmlPath = Join-Path $TargetModels "octopus_dt_v0_1.xml"
  $XmlText = Get-Content -Raw -LiteralPath $XmlPath
  for ($i = 1; $i -le 8; $i++) {
    $Arm = "arm_{0:D2}" -f $i
    $Pattern = '(<body name="' + $Arm + '" pos="[^"]+")'
    $Replacement = '$1 quat="' + $Rotations[$i - 1] + '"'
    $XmlText = [regex]::Replace($XmlText, $Pattern, $Replacement)
  }
  Set-Content -LiteralPath $XmlPath -Value $XmlText -Encoding utf8
  Copy-Item -LiteralPath $XmlPath -Destination (Join-Path $TargetModels "octopus_dt_cad.xml") -Force

  Write-Host "CAD model files copied into $TargetModels"
  Write-Host "Checking mesh assets..."
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
    git commit -m "feat(simulation): install and orient CAD-derived octopus assembly"
    git push origin main
  } finally {
    Pop-Location
  }
  Write-Host "CAD meshes and corrected radial arm frames pushed. Run GitHub Actions to compile the CAD MJCF."
} finally {
  if (Test-Path $TempRoot) { Remove-Item -LiteralPath $TempRoot -Recurse -Force }
}
