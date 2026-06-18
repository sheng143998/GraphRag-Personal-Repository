param(
    [Parameter(Mandatory = $true)]
    [string]$DraftJson,

    [Parameter(Mandatory = $true)]
    [string]$ReviewCsv,

    [Parameter(Mandatory = $true)]
    [string]$ExperimentId,

    [Parameter(Mandatory = $true)]
    [string]$OutputJson,

    [switch]$ActiveOnly,

    [switch]$ExcludeRejected,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $repoRoot "ai-service\scripts\finalize_ragas_testset_review.py"

$argsList = @(
    $runner,
    "--draft-json", $DraftJson,
    "--review-csv", $ReviewCsv,
    "--experiment-id", $ExperimentId,
    "--output-json", $OutputJson
)

if ($ActiveOnly) {
    $argsList += "--active-only"
}

if ($ExcludeRejected) {
    $argsList += "--exclude-rejected"
}

& $Python @argsList
