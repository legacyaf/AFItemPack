# Rebuilds the Jerrycan Hauler models and packs AFItemPack.pbo into @AFItemPack\Addons.
# Close any DayZ that has this mod loaded first: it keeps the PBO locked.
#   powershell -ExecutionPolicy Bypass -File tools\build.ps1            (models + pack)
#   powershell -ExecutionPolicy Bypass -File tools\build.ps1 -PackOnly  (config/script changes only)
param([switch]$PackOnly)

$ErrorActionPreference = 'Stop'
$repo      = Split-Path $PSScriptRoot -Parent
$workdrive = 'C:\DayZWorkdrive'
$tools     = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools'
$blender   = 'C:\Program Files\Blender Foundation\Blender 5.3\blender.exe'
$temp      = Join-Path $env:TEMP 'AFItemPack_build'

$pbo = Join-Path $repo '@AFItemPack\Addons\AFItemPack.pbo'
if (Test-Path $pbo) {
    try { $lock = [IO.File]::Open($pbo, 'Open', 'ReadWrite', 'None'); $lock.Close() }
    catch { throw 'AFItemPack.pbo is in use; close the DayZ that has the mod loaded first.' }
}
if (-not (Test-Path 'P:\')) { subst P: $workdrive }
if (-not (Test-Path 'P:\AFItemPack\JerrycanHauler\config.cpp')) { throw 'P:\AFItemPack is missing (it should be a link to the repo folder).' }

if (-not $PackOnly) {
    & $blender -b --python (Join-Path $PSScriptRoot 'build_hauler_p3d.py') -- $repo 2>&1 |
        Select-String -Pattern 'EXPORTED|Error|Traceback|Exception' | ForEach-Object Line
    if ($LASTEXITCODE -ne 0) { throw "Blender exited with code $LASTEXITCODE" }
}

New-Item -ItemType Directory -Force $temp, (Join-Path $repo '@AFItemPack\Addons') | Out-Null
$log = Join-Path $temp 'addonbuilder.log'
$p = Start-Process (Join-Path $tools 'Bin\AddonBuilder\AddonBuilder.exe') -ArgumentList @(
    'P:\AFItemPack', "`"$(Join-Path $repo '@AFItemPack\Addons')`"", '-clear', '-prefix=AFItemPack', '-project=P:\',
    "-temp=`"$temp`"", "-include=`"$(Join-Path $PSScriptRoot 'addonbuilder_include.txt')`"", "-toolsDirectory=`"$tools`""
) -RedirectStandardOutput $log -NoNewWindow -PassThru -Wait
Get-Content $log | Select-String 'Build |ERROR' | ForEach-Object Line
if ($p.ExitCode -ne 0 -or -not (Select-String -Path $log -Pattern 'Build Successful' -Quiet)) { throw "Addon Builder failed; see $log" }

# Re-sign: a rebuilt PBO no longer matches its old signature. The private key stays in
# keys\ (not in git); without it the stale signature is removed and the PBO is left unsigned.
$addons = Join-Path $repo '@AFItemPack\Addons'
$key    = Join-Path $repo 'keys\AFItemPack.biprivatekey'
Get-ChildItem $addons -Filter '*.bisign' | Remove-Item -Confirm:$false
if (Test-Path $key) {
    & (Join-Path $tools 'Bin\DsUtils\DSSignFile.exe') $key (Join-Path $addons 'AFItemPack.pbo')
    if ($LASTEXITCODE -ne 0) { throw 'Signing failed.' }
    New-Item -ItemType Directory -Force (Join-Path $repo '@AFItemPack\Keys') | Out-Null
    Copy-Item (Join-Path $repo 'keys\AFItemPack.bikey') (Join-Path $repo '@AFItemPack\Keys\') -Force
} else { Write-Warning 'keys\AFItemPack.biprivatekey not found; the PBO is unsigned.' }
Get-ChildItem $addons | Select-Object Name, Length, LastWriteTime
