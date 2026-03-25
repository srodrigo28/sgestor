[CmdletBinding()]
param(
  # Source (VPS) connection comes from a dotenv file with: DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
  [string]$SourceEnvFile = ".\\.env.prod",

  # Path to XAMPP MySQL binaries (mysql.exe, mysqldump.exe)
  [string]$XamppMysqlBin = "C:\\xampp\\mysql\\bin",

  # Target (local XAMPP) connection
  [string]$TargetHost = "127.0.0.1",
  [int]$TargetPort = 3306,
  [string]$TargetUser = "root",
  [string]$TargetPassword = "",

  # If empty, uses DB_NAME from the source env file
  [string]$TargetDbName = "",

  # Overwrite target database without prompting
  [switch]$Force,

  # Skip table/row verification step
  [switch]$SkipVerify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-DotEnvToHashtable([string]$path) {
  if (-not (Test-Path $path)) {
    throw "Env file not found: $path"
  }

  $map = @{}
  foreach ($raw in Get-Content $path) {
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith("#")) { continue }
    if ($line.StartsWith("export ")) { $line = $line.Substring(7).Trim() }

    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { continue }

    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()

    if ($val.Length -ge 2 -and (
        ($val[0] -eq '"' -and $val[$val.Length - 1] -eq '"') -or
        ($val[0] -eq "'" -and $val[$val.Length - 1] -eq "'")
      )) {
      $val = $val.Substring(1, $val.Length - 2)
    }

    if (-not [string]::IsNullOrWhiteSpace($key)) {
      $map[$key] = $val
    }
  }

  return $map
}

function Require-Key($map, [string]$key) {
  if (-not $map.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($map[$key])) {
    throw "Missing required key in env file: $key"
  }
}

function With-MySqlPwd([string]$pwd, [scriptblock]$action) {
  $had = Test-Path Env:\\MYSQL_PWD
  $prev = $env:MYSQL_PWD
  try {
    if ([string]::IsNullOrEmpty($pwd)) {
      Remove-Item Env:\\MYSQL_PWD -ErrorAction SilentlyContinue
    } else {
      Set-Item -Path Env:MYSQL_PWD -Value $pwd
    }
    & $action
  } finally {
    if ($had) {
      Set-Item -Path Env:MYSQL_PWD -Value $prev
    } else {
      Remove-Item Env:\\MYSQL_PWD -ErrorAction SilentlyContinue
    }
  }
}

$envMap = Load-DotEnvToHashtable $SourceEnvFile
Require-Key $envMap "DB_HOST"
Require-Key $envMap "DB_PORT"
Require-Key $envMap "DB_USER"
Require-Key $envMap "DB_PASS"
Require-Key $envMap "DB_NAME"

$srcHost = $envMap["DB_HOST"]
$srcPort = [int]$envMap["DB_PORT"]
$srcUser = $envMap["DB_USER"]
$srcPass = $envMap["DB_PASS"]
$srcDb = $envMap["DB_NAME"]

if ([string]::IsNullOrWhiteSpace($TargetDbName)) {
  $TargetDbName = $srcDb
}

$mysql = Join-Path $XamppMysqlBin "mysql.exe"
$mysqldump = Join-Path $XamppMysqlBin "mysqldump.exe"

if (-not (Test-Path $mysql)) { throw "mysql.exe not found at: $mysql" }
if (-not (Test-Path $mysqldump)) { throw "mysqldump.exe not found at: $mysqldump" }

$dumpDir = Join-Path (Get-Location) "backups"
New-Item -ItemType Directory -Force -Path $dumpDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$dumpFile = Join-Path $dumpDir ("vps_{0}_{1}.sql" -f $srcDb, $ts)

Write-Host "Dumping VPS database '$srcDb' to: $dumpFile"
With-MySqlPwd $srcPass {
  & $mysqldump --protocol=tcp --host=$srcHost --port=$srcPort --user=$srcUser `
    --default-character-set=utf8mb4 --single-transaction --quick --skip-lock-tables --hex-blob `
    --add-drop-table --routines --events --triggers `
    $srcDb --result-file=$dumpFile
  if ($LASTEXITCODE -ne 0) { throw "mysqldump failed (exit code $LASTEXITCODE)." }
}

Write-Host "Preparing target database '$TargetDbName' on ${TargetHost}:$TargetPort ..."
With-MySqlPwd $TargetPassword {
  $existingTables = & $mysql --protocol=tcp -h $TargetHost -P $TargetPort -u $TargetUser -N -e `
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$TargetDbName' AND table_type='BASE TABLE';"

  if (-not $Force -and [int]$existingTables -gt 0) {
    $ans = Read-Host "Target DB has $existingTables tables. Overwrite (DROP DB + import)? Type YES to continue"
    if ($ans -ne "YES") {
      throw "Aborted by user."
    }
  }

  & $mysql --protocol=tcp -h $TargetHost -P $TargetPort -u $TargetUser -e `
    "DROP DATABASE IF EXISTS $TargetDbName; CREATE DATABASE $TargetDbName CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  if ($LASTEXITCODE -ne 0) { throw "Failed to (re)create target database (exit code $LASTEXITCODE)." }
}

Write-Host "Importing dump into target ..."
With-MySqlPwd $TargetPassword {
  # Use cmd.exe redirection to avoid PowerShell encoding issues.
  $cmd = "`"$mysql`" --protocol=tcp -h $TargetHost -P $TargetPort -u $TargetUser --default-character-set=utf8mb4 `"$TargetDbName`" < `"$dumpFile`""
  cmd.exe /c $cmd
  if ($LASTEXITCODE -ne 0) { throw "Import failed (exit code $LASTEXITCODE)." }
}

if (-not $SkipVerify) {
  Write-Host "Verifying tables and row counts ..."

  $remoteTables = With-MySqlPwd $srcPass {
    & $mysql --protocol=tcp -h $srcHost -P $srcPort -u $srcUser -N -e `
      "SELECT table_name FROM information_schema.tables WHERE table_schema='$srcDb' AND table_type='BASE TABLE' ORDER BY table_name;"
  }

  $localTables = With-MySqlPwd $TargetPassword {
    & $mysql --protocol=tcp -h $TargetHost -P $TargetPort -u $TargetUser -N -e `
      "SELECT table_name FROM information_schema.tables WHERE table_schema='$TargetDbName' AND table_type='BASE TABLE' ORDER BY table_name;"
  }

  $missingLocally = Compare-Object -ReferenceObject $remoteTables -DifferenceObject $localTables -PassThru | Where-Object { $_.SideIndicator -eq "<=" }
  $extraLocally = Compare-Object -ReferenceObject $remoteTables -DifferenceObject $localTables -PassThru | Where-Object { $_.SideIndicator -eq "=>" }

  if ($missingLocally) { throw ("Missing tables locally: " + ($missingLocally -join ", ")) }
  if ($extraLocally) { throw ("Extra tables locally: " + ($extraLocally -join ", ")) }

  foreach ($t in $remoteTables) {
    $r = With-MySqlPwd $srcPass {
      & $mysql --protocol=tcp -h $srcHost -P $srcPort -u $srcUser -D $srcDb -N -e "SELECT COUNT(*) FROM $t;"
    }
    $l = With-MySqlPwd $TargetPassword {
      & $mysql --protocol=tcp -h $TargetHost -P $TargetPort -u $TargetUser -D $TargetDbName -N -e "SELECT COUNT(*) FROM $t;"
    }

    if ([int64]$r -ne [int64]$l) {
      throw "Row count mismatch on '$t' (vps=$r local=$l)."
    }
  }

  Write-Host "Verification OK."
}

Write-Host "Sync complete."
Write-Host "Dump file: $dumpFile"
