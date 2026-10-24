param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ModArguments)
$ErrorActionPreference = 'Stop'
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python -ErrorAction Stop).Source }
& $python (Join-Path $PSScriptRoot 'caretakermods.py') @ModArguments
exit $LASTEXITCODE
