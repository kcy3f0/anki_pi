param (
    [switch]$NonInteractive = $false
)

# Windows Installation Script for Anki Pi
# Run this script with PowerShell.

$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ([string]::IsNullOrEmpty($PSScriptRoot)) {
    $PSScriptRoot = Get-Location
}
Set-Location $PSScriptRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       Anki Pi Installation Script (Windows)       " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Error "Python executable not found. Please install Python and make sure to check 'Add Python to PATH'."
    Exit
}
$pyVersion = python --version
Write-Host "Detected Python: $pyVersion" -ForegroundColor Green

# 2. Create Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
    if (Test-Path "venv") {
        Write-Host "Virtual environment created successfully." -ForegroundColor Green
    } else {
        Write-Error "Failed to create virtual environment!"
        Exit
    }
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

# 3. Upgrade pip and Install requirements
Write-Host "Upgrading pip and installing requirements..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip -q
& ".\venv\Scripts\pip.exe" install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "Requirements installed successfully!" -ForegroundColor Green
} else {
    Write-Error "Failed to install packages."
    Exit
}

# 4. Generate .env Configuration
if (-not (Test-Path ".env")) {
    Write-Host "Setting up environment configuration (.env)..." -ForegroundColor Yellow
    
    # Generate random key
    $bytes = New-Object Byte[] 24
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    $secretKey = [System.Convert]::ToBase64String($bytes)
    
    $discordWebhook = ""
    if ($NonInteractive) {
        Write-Host "Non-interactive mode, skipping Discord Webhook URL prompt." -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Do you want to configure Discord Webhook Notification?" -ForegroundColor Cyan
        Write-Host "If yes, paste the Discord Webhook URL below. Otherwise, press Enter to skip."
        $discordWebhook = Read-Host "Discord Webhook URL (Optional)"
    }
    
    $envContent = @"
SECRET_KEY=$secretKey
DATABASE_PATH=flashcards.db
DISCORD_WEBHOOK_URL=$discordWebhook
"@
    $envContent | Out-File -FilePath ".env" -Encoding utf8
    Write-Host ".env configuration created." -ForegroundColor Green
} else {
    Write-Host ".env configuration already exists." -ForegroundColor Green
}

# 5. Create Desktop Shortcut
Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
try {
    $desktop = [System.Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop "Anki Pi.lnk"
    
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = "cmd.exe"
    # Safely construct cmd.exe arguments with single quotes
    $Shortcut.Arguments = '/c cd /d "' + $PSScriptRoot + '" && .\venv\Scripts\python.exe app.py'
    $Shortcut.WorkingDirectory = $PSScriptRoot
    $Shortcut.Description = "Start Anki Pi Server"
    $Shortcut.Save()
    
    Write-Host "Shortcut created successfully on Desktop (Anki Pi.lnk)!" -ForegroundColor Green
} catch {
    Write-Warning "Failed to create desktop shortcut. You can still run the app by executing 'python app.py' directly."
}

Write-Host "==================================================" -ForegroundColor Green
Write-Host "  Anki Pi Installation Completed!                 " -ForegroundColor Green
Write-Host "  1. Double click 'Anki Pi' shortcut on Desktop.  " -ForegroundColor Green
Write-Host "  2. Open browser at: http://127.0.0.1:10000       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
