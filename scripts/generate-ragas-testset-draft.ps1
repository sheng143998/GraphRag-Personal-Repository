param(
    [string]$KnowledgeBaseId = "",

    [string]$ChunksJson = "",

    [Parameter(Mandatory = $true)]
    [string]$OutputJson,

    [Parameter(Mandatory = $true)]
    [string]$ReviewCsv,

    [string]$ExperimentId = "",

    [int]$CasesPerDocument = 3,

    [int]$TopK = 5,

    [ValidateSet("rule", "llm", "ragas", "auto")]
    [string]$GeneratorMode = "rule",

    [string]$QuestionTypes = "fact,reasoning,multi_context,troubleshooting",

    [int]$RagasTestsetSize = 0,

    [switch]$NoFallback,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $repoRoot "ai-service\scripts\generate_ragas_testset_draft.py"

if ($KnowledgeBaseId -and $ChunksJson) {
    throw "Only one of -KnowledgeBaseId or -ChunksJson can be provided."
}

$argsList = @(
    $runner,
    "--output-json", $OutputJson,
    "--review-csv", $ReviewCsv,
    "--cases-per-document", $CasesPerDocument,
    "--top-k", $TopK,
    "--generator-mode", $GeneratorMode,
    "--question-types", $QuestionTypes
)

if ($RagasTestsetSize -gt 0) {
    $argsList += @("--ragas-testset-size", $RagasTestsetSize)
}

if ($NoFallback) {
    $argsList += "--no-fallback"
}

if ($ExperimentId) {
    $argsList += @("--experiment-id", $ExperimentId)
}

if ($KnowledgeBaseId) {
    $argsList += @("--knowledge-base-id", $KnowledgeBaseId)
} elseif ($ChunksJson) {
    $argsList += @("--chunks-json", $ChunksJson)
} else {
    throw "Either -KnowledgeBaseId or -ChunksJson is required."
}

& $Python @argsList
