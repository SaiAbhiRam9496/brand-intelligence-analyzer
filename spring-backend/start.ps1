# ============================================================
# start.ps1
# Startup script for the Spring Boot backend
# - Kills any existing process on port 8080 before starting
# Run with: powershell -ExecutionPolicy Bypass -File start.ps1
# ============================================================

$PORT = 8080

Write-Host "[Startup] Checking for existing process on port $PORT..."

$existingPid = (netstat -ano | Select-String ":$PORT " | Select-String "LISTENING" | ForEach-Object {
    ($_ -split "\s+")[-1]
} | Select-Object -First 1)

if ($existingPid) {
    Write-Host "[Startup] Found existing process PID $existingPid on port $PORT. Terminating..."
    Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "[Startup] Process terminated."
} else {
    Write-Host "[Startup] No existing process on port $PORT."
}

Write-Host "[Startup] Starting Spring Boot backend on port $PORT..."
mvn spring-boot:run
