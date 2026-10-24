$ErrorActionPreference = 'Stop'
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python -ErrorAction Stop).Source }
& $python -m unittest discover -s (Join-Path $PSScriptRoot 'tests') -v
exit $LASTEXITCODE
