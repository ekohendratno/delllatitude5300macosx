Write-Host "=== Step 1: Write HFS image to partition 2 ==="
$hfsFile = "$env:TEMP\macos_hfs\5.hfs"
$ddExe = "C:\delllatitude5300macosx\gibMacOS\Scripts\ddrelease64.exe"
$efiSrc = "C:\delllatitude5300macosx\EFI"

if (-not (Test-Path $hfsFile)) {
    Write-Host "ERROR: HFS file not found at $hfsFile"
    Read-Host "Press Enter to exit"
    exit 1
}

$size = [math]::Round((Get-Item $hfsFile).Length / 1GB, 2)
Write-Host "HFS image: $hfsFile ($size GB)"
Write-Host "Target: \\.\Harddisk1\Partition2"
Write-Host ""

Write-Host "Running dd (this will take several minutes)..."
& $ddExe "if=$hfsFile" "of=\\.\Harddisk1\Partition2" bs=8M --progress
Write-Host "dd exit code: $LASTEXITCODE"

Write-Host ""
Write-Host "=== Step 2: Copy EFI folder to E: ==="
$efiTarget = "E:\EFI"
if (Test-Path $efiTarget) {
    Remove-Item -Path $efiTarget -Recurse -Force
}
Copy-Item -Path $efiSrc -Destination $efiTarget -Recurse -Force
Write-Host "EFI copied to E:\EFI"

Write-Host ""
Write-Host "=== DONE! USB installer is ready ==="
Write-Host "You can now:"
Write-Host "  1. Safely eject the USB (Eject from system tray)"
Write-Host "  2. Reboot and press F12/F2 to boot from USB"
Write-Host "  3. Select 'Install macOS Ventura' from OpenCore"
Read-Host "Press Enter to exit"