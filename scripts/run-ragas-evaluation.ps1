param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$Metrics = "IDBasedContextPrecision,IDBasedContextRecall",

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $repoRoot "ai-service\scripts\run_ragas_evaluation.py"

& $Python $runner --input $InputPath --output $OutputPath --metrics $Metrics
