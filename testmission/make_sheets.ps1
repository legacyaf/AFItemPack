# Combines the four tour views of each mannequin (testmission\captures\mN_*.jpg) into one
# picture per mannequin, cropped to the character: front, back, its left, its right.
Add-Type -AssemblyName System.Drawing
$c = Join-Path $PSScriptRoot 'captures'
$first = [System.Drawing.Image]::FromFile((Join-Path $c 'm1_front.jpg')); $W = $first.Width; $H = $first.Height; $first.Dispose()
$cw = [int]($H * 0.50); $ch = [int]($H * 0.56); $x0 = [int](($W - $cw) / 2); $y0 = [int]($H * 0.16)
$tile = 480; $th = [int]($tile * $ch / $cw)
foreach ($n in 1..11) {
    if (-not (Test-Path (Join-Path $c "m${n}_front.jpg"))) { continue }
    $sheet = New-Object System.Drawing.Bitmap ($tile * 4), $th
    $g = [System.Drawing.Graphics]::FromImage($sheet); $g.InterpolationMode = 'HighQualityBicubic'
    $i = 0
    foreach ($v in 'front', 'back', 'left', 'right') {
        $img = [System.Drawing.Image]::FromFile((Join-Path $c "m${n}_$v.jpg"))
        $g.DrawImage($img, (New-Object System.Drawing.Rectangle ($i * $tile), 0, $tile, $th), (New-Object System.Drawing.Rectangle $x0, $y0, $cw, $ch), 'Pixel')
        $img.Dispose(); $i++
    }
    $g.Dispose(); $sheet.Save((Join-Path $c "sheet_m$n.jpg"), [System.Drawing.Imaging.ImageFormat]::Jpeg); $sheet.Dispose()
}
Get-ChildItem $c -Filter 'sheet_*.jpg' | Select-Object Name, Length
