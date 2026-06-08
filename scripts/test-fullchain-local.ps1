param(
    [switch]$SkipBuild,
    [switch]$KeepServices
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$AiDir = Join-Path $Root "ai-service"
$BackendDir = Join-Path $Root "backend-java"
$SmokeTest = Join-Path $Root "smoke_test.py"
$AiPython = Join-Path $AiDir ".venv\bin\python.exe"
$BackendJar = Join-Path $BackendDir "target\agent-knowledge-backend-0.0.1-SNAPSHOT.jar"
function Import-DotEnv {
    $envPath = Join-Path $Root ".env"
    if (-not (Test-Path $envPath)) {
        Copy-Item (Join-Path $Root ".env.example") $envPath
    }
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $name = $parts[0].Trim()
        $value = $parts[1].Trim().Trim('"').Trim("'")
        if ($name) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

function Test-HttpOk {
    param([string]$Url)
    try {
        Invoke-RestMethod -Uri $Url -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Wait-HttpOk {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpOk $Url) {
            Write-Host "READY $Name $Url"
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "$Name did not become healthy at $Url within $TimeoutSeconds seconds."
}

function Stop-StartedJob {
    param($Job)
    if ($Job) {
        Stop-Job $Job -ErrorAction SilentlyContinue
        Remove-Job $Job -Force -ErrorAction SilentlyContinue
    }
}

Import-DotEnv

$env:AI_RAG_USE_DATABASE = "true"
$env:MODEL_PROVIDER = "stub"
$env:LLM_PROVIDER = "stub"
$env:EMBEDDING_PROVIDER = "stub"
$env:RERANK_PROVIDER = "stub"

if (-not (Test-Path $AiPython)) {
    throw "AI virtualenv python not found: $AiPython"
}

if (-not $SkipBuild -or -not (Test-Path $BackendJar)) {
    Push-Location $BackendDir
    try {
        mvn package -DskipTests
    } finally {
        Pop-Location
    }
}

$aiAlreadyRunning = Test-HttpOk "http://127.0.0.1:8001/ai/health"
$backendAlreadyRunning = Test-HttpOk "http://127.0.0.1:8080/api/health"
$aiJob = $null
$backendJob = $null

try {
    if (-not $aiAlreadyRunning) {
        $aiJob = Start-Job -Name "agent-rag-ai-service" -ScriptBlock {
            param($AiDir, $AiPython)
            Set-Location $AiDir
            $env:AI_RAG_USE_DATABASE = "true"
            $env:MODEL_PROVIDER = "stub"
            $env:LLM_PROVIDER = "stub"
            $env:EMBEDDING_PROVIDER = "stub"
            $env:RERANK_PROVIDER = "stub"
            & $AiPython -m uvicorn app.main:app --host 127.0.0.1 --port 8001
        } -ArgumentList $AiDir, $AiPython
    }

    Wait-HttpOk "FastAPI" "http://127.0.0.1:8001/ai/health" 60

    if (-not $backendAlreadyRunning) {
        $dbUrl = $env:DB_URL
        $dbUsername = $env:DB_USERNAME
        $dbPassword = $env:DB_PASSWORD
        if (-not $dbUrl) {
            throw "DB_URL is required in .env for local full-chain testing."
        }
        $backendJob = Start-Job -Name "agent-rag-backend" -ScriptBlock {
            param($BackendDir, $BackendJar, $DbUrl, $DbUsername, $DbPassword)
            Set-Location $BackendDir
            & java -jar $BackendJar `
                --server.port=8080 `
                --app.ai-service.mock-enabled=false `
                --app.ai-service.base-url=http://127.0.0.1:8001 `
                --spring.datasource.url=$DbUrl `
                --spring.datasource.username=$DbUsername `
                --spring.datasource.password=$DbPassword
        } -ArgumentList $BackendDir, $BackendJar, $dbUrl, $dbUsername, $dbPassword
    }

    Wait-HttpOk "Spring Boot" "http://127.0.0.1:8080/api/health" 90

    Push-Location $Root
    try {
        & python $SmokeTest
    } finally {
        Pop-Location
    }
} catch {
    Write-Host "Full-chain test failed: $($_.Exception.Message)"
    if ($aiJob) {
        Write-Host "AI job output:"
        Receive-Job $aiJob -Keep -ErrorAction SilentlyContinue | Select-Object -Last 80
    }
    if ($backendJob) {
        Write-Host "Backend job output:"
        Receive-Job $backendJob -Keep -ErrorAction SilentlyContinue | Select-Object -Last 120
    }
    throw
} finally {
    if (-not $KeepServices) {
        Stop-StartedJob $backendJob
        Stop-StartedJob $aiJob
    }
}
