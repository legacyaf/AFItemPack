# Starts the offline test and saves a picture of the DayZ window at every stop of the
# mission's camera tour (see init.c). Pictures go to testmission\captures.
# The window is read directly (PrintWindow), so other windows on top of it do not matter,
# but it must not be minimised while this runs (2 to 5 minutes).
#   capture_tour.ps1                  the Jerrycan Hauler line-up (mission AFTest)
#   capture_tour.ps1 -Mission AFCape  the cape line-up
param([string]$Mission = 'AFTest')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class AFWin {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
}
'@
[AFWin]::SetProcessDPIAware() | Out-Null

$here = $PSScriptRoot
$out = Join-Path $here 'captures'
New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item (Join-Path $out '*.jpg') -ErrorAction SilentlyContinue

Get-Process DayZDiag_x64 -ErrorAction SilentlyContinue | Stop-Process -Force -Confirm:$false
Start-Sleep 2
$start = Get-Date
$dayz = 'C:\Program Files (x86)\Steam\steamapps\common\DayZ'
Start-Process (Join-Path $dayz 'DayZDiag_x64.exe') -WorkingDirectory $dayz -ArgumentList @(
    """-mission=$here\$Mission.ChernarusPlus""", """-mod=$(Split-Path $here -Parent)\@AFItemPack""", """-profiles=$here\profiles""",
    '-window', '-nosplash', '-noPause', '-scriptDebug=true')

function Save-Window($name) {
    $proc = Get-Process DayZDiag_x64 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if (-not $proc) { return $false }
    $h = $proc.MainWindowHandle
    $r = New-Object AFWin+RECT; [AFWin]::GetClientRect($h, [ref]$r) | Out-Null
    $w = $r.R - $r.L; $hgt = $r.B - $r.T
    if ($w -lt 100 -or $hgt -lt 100) { return $false }
    $bmp = New-Object System.Drawing.Bitmap $w, $hgt
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [AFWin]::PrintWindow($h, $hdc, 3) | Out-Null   # client area, full rendered content
    $g.ReleaseHdc($hdc)
    $g.Dispose()
    $bmp.Save((Join-Path $out "$name.jpg"), [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $bmp.Dispose()
    return $true
}

$seen = @{}; $front = $false; $done = $false
$deadline = (Get-Date).AddSeconds(360)
while ((Get-Date) -lt $deadline -and -not $done) {
    $log = Get-ChildItem (Join-Path $here 'profiles') -Filter 'script_*.log' -ErrorAction SilentlyContinue |
        Where-Object LastWriteTime -gt $start | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($log) {
        $fs = [IO.File]::Open($log.FullName, 'Open', 'Read', 'ReadWrite'); $sr = New-Object IO.StreamReader $fs
        $text = $sr.ReadToEnd(); $sr.Close(); $fs.Close()
        if (-not $front -and $text -match '\[AFTest\] mannequin') {
            $proc = Get-Process DayZDiag_x64 -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
            if ($proc) { $front = $true }
        }
        foreach ($m in [regex]::Matches($text, '\[AFTest\] SHOT (\S+)')) {
            $name = $m.Groups[1].Value
            if (-not $seen.ContainsKey($name)) {
                $seen[$name] = $true
                Start-Sleep -Milliseconds 1100
                if (Save-Window $name) { "captured $name" } else { "could not capture $name" }
            }
        }
        if ($text -match 'TOUR DONE') { $done = $true }
        if ($text -match 'ompile error|Can.t compile') { ($text -split "`n" | Select-String 'ompile|init\.c').Line; break }
    }
    if (-not (Get-Process DayZDiag_x64 -ErrorAction SilentlyContinue) -and ((Get-Date) - $start).TotalSeconds -gt 20) { 'DayZ exited'; break }
    Start-Sleep -Milliseconds 300
}
"tour finished: $done; pictures: $($seen.Count)"
