# Alice Search Test Script
# Quick testing for Alice search functionality

param(
    [string]$Action = "help"
)

$BaseUrl = "http://localhost:8000"

function Show-Help {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "Alice Search Test Script" -ForegroundColor Yellow
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\test.ps1 [action]" -ForegroundColor Green
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  start       - Start Alice server"
    Write-Host "  test        - Run full test suite"
    Write-Host "  search      - Test search endpoint"
    Write-Host "  health      - Check health status"
    Write-Host "  stop        - Stop Alice server"
    Write-Host "  help        - Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\test.ps1 start"
    Write-Host "  .\test.ps1 test"
    Write-Host "  .\test.ps1 search"
    Write-Host ""
}

function Start-Alice {
    Write-Host ""
    Write-Host "🚀 Starting Alice AI Assistant..." -ForegroundColor Green
    Write-Host ""
    
    $AlicePath = "c:\Users\mahaj\OneDrive\Documents\Projects\Alice"
    
    if (Test-Path $AlicePath) {
        Set-Location $AlicePath
        Write-Host "📂 Working directory: $AlicePath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Starting server with uvicorn..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    } else {
        Write-Host "❌ Error: Alice directory not found" -ForegroundColor Red
    }
}

function Test-Health {
    Write-Host ""
    Write-Host "🏥 Checking Alice Health..." -ForegroundColor Green
    Write-Host ""
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get
        Write-Host "✅ Server is running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Response:" -ForegroundColor Cyan
        $response | ConvertTo-Json -Depth 3 | Write-Host
        Write-Host ""
    } catch {
        Write-Host "❌ Server is not running!" -ForegroundColor Red
        Write-Host "Start it with: .\test.ps1 start" -ForegroundColor Yellow
        Write-Host ""
    }
}

function Test-Search {
    Write-Host ""
    Write-Host "🔍 Testing Search Endpoint..." -ForegroundColor Green
    Write-Host ""
    
    $body = @{
        query = "What is the weather in Jalandhar today?"
        required_results = 3
        user_id = "test_user"
    } | ConvertTo-Json
    
    try {
        Write-Host "📤 Sending search request..." -ForegroundColor Cyan
        Write-Host "Query: What is the weather in Jalandhar today?" -ForegroundColor Yellow
        Write-Host ""
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/search/execute" `
                                      -Method Post `
                                      -Body $body `
                                      -ContentType "application/json" `
                                      -TimeoutSec 120
        
        Write-Host "✅ Search completed!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Results:" -ForegroundColor Cyan
        Write-Host "  Success: $($response.success)" -ForegroundColor White
        Write-Host "  Total Results: $($response.total_results)" -ForegroundColor White
        Write-Host "  Processing Time: $($response.processing_time)s" -ForegroundColor White
        Write-Host ""
        
        if ($response.results) {
            Write-Host "📊 Top Results:" -ForegroundColor Yellow
            $i = 1
            foreach ($result in $response.results) {
                Write-Host ""
                Write-Host "  $i. $($result.title)" -ForegroundColor Cyan
                Write-Host "     URL: $($result.url)" -ForegroundColor Gray
                Write-Host "     Method: $($result.method)" -ForegroundColor Gray
                Write-Host "     Quality: $($result.quality_score)" -ForegroundColor Gray
                Write-Host "     Content: $($result.content.Substring(0, [Math]::Min(150, $result.content.Length)))..." -ForegroundColor White
                $i++
            }
        }
        Write-Host ""
        
    } catch {
        Write-Host "❌ Search failed!" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host ""
    }
}

function Run-FullTest {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "Running Full Test Suite" -ForegroundColor Yellow
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $AlicePath = "c:\Users\mahaj\OneDrive\Documents\Projects\Alice"
    
    if (Test-Path $AlicePath) {
        Set-Location $AlicePath
        python test_search.py
    } else {
        Write-Host "❌ Error: Alice directory not found" -ForegroundColor Red
    }
}

function Stop-Alice {
    Write-Host ""
    Write-Host "🛑 Stopping Alice..." -ForegroundColor Yellow
    Write-Host ""
    
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*main:app*"
    }
    
    if ($processes) {
        $processes | ForEach-Object {
            Write-Host "Stopping process $($_.Id)..." -ForegroundColor Cyan
            Stop-Process -Id $_.Id -Force
        }
        Write-Host "✅ Alice stopped" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Alice is not running" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Main execution
switch ($Action.ToLower()) {
    "start" { Start-Alice }
    "test" { Run-FullTest }
    "search" { Test-Search }
    "health" { Test-Health }
    "stop" { Stop-Alice }
    "help" { Show-Help }
    default { Show-Help }
}
