param([string]$Mod, [switch]$DryRun)
$arguments = @('deploy')
if ($Mod) { $arguments += @('--mod', $Mod) }
if ($DryRun) { $arguments += '--dry-run' }
& (Join-Path $PSScriptRoot 'tools\caretakermods.ps1') @arguments
exit $LASTEXITCODE
