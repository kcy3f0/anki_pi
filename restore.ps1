# Windows Restore Script for Anki Pi
# Run this script with PowerShell.

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $PSScriptRoot = Get-Location
}
Set-Location $PSScriptRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       Anki Pi 資料庫還原腳本                     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

if (-not (Test-Path "backups") -or (Get-ChildItem "backups\*.db").Count -eq 0) {
    Write-Error "找不到任何可用的資料庫備份檔案！還原中止。"
    Exit
}

# 1. List backup files
Write-Host "目前可用的備份檔案清單：" -ForegroundColor Yellow
$backups = Get-ChildItem "backups\*.db" | Sort-Object LastWriteTime -Descending

for ($i = 0; $i -lt $backups.Count; $i++) {
    $idx = $i + 1
    $time = $backups[$i].LastWriteTime.ToString("yyyy/MM/dd HH:mm:ss")
    $size = [Math]::Round($backups[$i].Length / 1KB, 2)
    Write-Host "  [$idx] $($backups[$i].Name) ($time) - $size KB"
}

Write-Host ""
$choice = Read-Host "請輸入欲還原的備份編號 (或按 Enter 取消)"

if ([string]::IsNullOrEmpty($choice)) {
    Write-Host "操作取消。" -ForegroundColor Yellow
    Exit
}

$choiceIdx = [int]$choice - 1

if ($choiceIdx -lt 0 -or $choiceIdx -ge $backups.Count) {
    Write-Error "輸入無效的編號，還原中止。"
    Exit
}

$targetBackup = $backups[$choiceIdx]
Write-Host ""
Write-Host "確定要將資料庫還原至 $($targetBackup.Name) 嗎？" -ForegroundColor Warning
Write-Host "⚠️ 注意：這將會覆蓋您目前的 flashcards.db！" -ForegroundColor Warning
$confirm = Read-Host "確認還原請輸入 'y'，輸入其他字元取消"

if ($confirm.ToLower() -eq 'y') {
    # Backup current first, just in case
    if (Test-Path "flashcards.db") {
        $backupTemp = "backups\flashcards_temp_before_restore.db"
        Copy-Item "flashcards.db" $backupTemp
        Write-Host "已將目前的資料庫備份為 $backupTemp 以防萬一。" -ForegroundColor Gray
    }
    
    # Perform restore
    Copy-Item $targetBackup.FullName "flashcards.db" -Force
    Write-Host "資料庫還原完成！" -ForegroundColor Green
} else {
    Write-Host "操作已取消。" -ForegroundColor Yellow
}
