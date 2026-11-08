# Launch Frontend Vite Server
Write-Host "Starting AI Tutor Frontend UI on http://localhost:5173..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\..\frontend"
npm run dev
