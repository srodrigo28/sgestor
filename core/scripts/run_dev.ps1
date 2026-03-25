[CmdletBinding()]
param(
  [string]$EnvFile = "",
  [int]$Port = 5050
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($EnvFile)) {
  $EnvFile = Join-Path $ProjectRoot ".env.dev"
}

$env:ENV_FILE = $EnvFile
$env:PORT = "$Port"

$venvPython = Join-Path $ProjectRoot "venv\\Scripts\\python.exe"
$mainFile = Join-Path $ProjectRoot "manage.py"

if (Test-Path $venvPython) {
  & $venvPython $mainFile
} else {
  python $mainFile
}

