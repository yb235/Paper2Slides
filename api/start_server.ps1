# PowerShell script to start the Paper2Slides backend server
# This handles PowerShell's stderr interpretation issue

$pythonExe = "..\\.venv\Scripts\python.exe"
$serverScript = "server.py"

Write-Host "Starting Paper2Slides API server..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Run with proper error handling - redirect stderr to stdout
& $pythonExe $serverScript 2>&1 | ForEach-Object {
    Write-Host $_
}
