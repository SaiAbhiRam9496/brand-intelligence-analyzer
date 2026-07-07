# ============================================================
# start.ps1
# Startup script for the python-engine FastAPI server
# - Kills any existing process on port 8000 before starting
# - Sets PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION to bypass TF/Protobuf conflict
# - Uses a fixed port 8000
# Run with: powershell -ExecutionPolicy Bypass -File start.ps1
# ============================================================

$PORT = 8000

Write-Host "[Startup] Checking for existing process on port $PORT..."

$existingPid = (netstat -ano | Select-String ":$PORT " | Select-String "LISTENING" | ForEach-Object {
    ($_ -split "\s+")[-1]
} | Select-Object -First 1)

if ($existingPid) {
    Write-Host "[Startup] Found existing process PID $existingPid on port $PORT. Terminating..."
    Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    Write-Host "[Startup] Process terminated."
} else {
    Write-Host "[Startup] No existing process on port $PORT."
}

# Set environment variable to bypass Protobuf/TensorFlow conflict
$env:PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION = "python"

Write-Host "[Startup] Starting python-engine on port $PORT..."
python -m uvicorn main:app --host 127.0.0.1 --port $PORT
