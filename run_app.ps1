$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\streamlit.exe")) {
    Write-Error "Streamlit executable not found in .\venv\Scripts\streamlit.exe"
}

Write-Host "Starting EduBridge AI..."
Write-Host "Open http://localhost:8501 in your browser after the server starts."

.\venv\Scripts\streamlit.exe run app.py --server.headless=true
