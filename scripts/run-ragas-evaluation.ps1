param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$Metrics = "IDBasedContextPrecision,IDBasedContextRecall",

    [string]$BackfillBackendUrl = "",

    [string]$RagasVersion = "",

    [string]$JudgeModel = "",

    [string]$ReportUri = "",

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $repoRoot "ai-service\scripts\run_ragas_evaluation.py"

$arguments = @("--input", $InputPath, "--output", $OutputPath, "--metrics", $Metrics)
if ($BackfillBackendUrl) {
    $arguments += @("--backfill-backend-url", $BackfillBackendUrl)
}
if ($RagasVersion) {
    $arguments += @("--ragas-version", $RagasVersion)
}
if ($JudgeModel) {
    $arguments += @("--judge-model", $JudgeModel)
}
if ($ReportUri) {
    $arguments += @("--report-uri", $ReportUri)
}

& $Python $runner @arguments
