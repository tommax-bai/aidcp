[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$bashCandidates = @()

$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if ($gitCommand) {
  $gitCmdDir = Split-Path -Parent $gitCommand.Source
  $gitRoot = Split-Path -Parent $gitCmdDir
  $bashCandidates += Join-Path $gitRoot 'bin\bash.exe'
}

if ($env:ProgramFiles) {
  $bashCandidates += Join-Path $env:ProgramFiles 'Git\bin\bash.exe'
}
if ($env:LOCALAPPDATA) {
  $bashCandidates += Join-Path $env:LOCALAPPDATA 'Programs\Git\bin\bash.exe'
}

$bashExe = $bashCandidates |
  Select-Object -Unique |
  Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
  Select-Object -First 1

if (-not $bashExe) {
  Write-Error 'Git Bash was not found. Install Git for Windows or run scripts/task-preflight from an existing Bash shell.'
  exit 127
}

$exitCode = 1
Push-Location -LiteralPath $repoRoot
try {
  & $bashExe '--noprofile' '--norc' './scripts/task-preflight'
  $exitCode = $LASTEXITCODE
}
finally {
  Pop-Location
}

exit $exitCode
