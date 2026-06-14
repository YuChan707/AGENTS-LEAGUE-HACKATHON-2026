# Dev server — reload watches only backend/ so data_processor, data_ingestor, etc. don't trigger restarts.
# Run from the project root: ./start-dev.ps1

Set-Location $PSScriptRoot

& "$PSScriptRoot\backend\venv\Scripts\python.exe" -m uvicorn backend.main:app `
  --host 0.0.0.0 `
  --port 8000 `
  --reload `
  --reload-dir backend
