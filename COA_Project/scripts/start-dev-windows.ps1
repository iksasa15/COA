# C.O.A — تشغيل الواجهة + الـ API على ويندوز (نافذتين للوج)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "Creating .venv ..." -ForegroundColor Yellow
    python -m venv (Join-Path $Root ".venv")
}
& $Py -m pip install -q "flask>=3" "flask-cors>=4" "psutil>=5.9" "PyYAML>=6" "python-dotenv>=1" "pydantic>=2.5" "requests>=2.31" "pywin32>=306" 2>$null

$Web = Join-Path $Root "web"
if (Test-Path (Join-Path $Web "package.json")) {
    Push-Location $Web
    npm install --silent
    Pop-Location
}

$env:PYTHONUTF8 = "1"
$apiCmd = "Set-Location '$Root'; `$env:PYTHONUTF8='1'; & '$Py' web_api.py"
$uiCmd = "Set-Location '$Web'; npm run dev"

Start-Process powershell -ArgumentList @("-NoExit", "-Command", $apiCmd) -WorkingDirectory $Root
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $uiCmd) -WorkingDirectory $Web

Write-Host "Opened 2 windows: API http://127.0.0.1:5050  |  UI http://localhost:5173" -ForegroundColor Green
