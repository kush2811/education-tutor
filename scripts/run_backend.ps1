# Launch Backend Server
Write-Host "Starting AI Tutor Backend Service on http://127.0.0.1:8000..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\..\backend"
& ".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
