param([string]$LuaWheel, [string]$LoaderArchive, [string]$ArchiveSha256)
$arguments = @('bootstrap')
if ($LuaWheel) { $arguments += @('--lua-wheel', $LuaWheel) }
if ($LoaderArchive) { $arguments += @('--loader-archive', $LoaderArchive) }
if ($ArchiveSha256) { $arguments += @('--archive-sha256', $ArchiveSha256) }
& (Join-Path $PSScriptRoot 'caretakermods.ps1') @arguments
exit $LASTEXITCODE
