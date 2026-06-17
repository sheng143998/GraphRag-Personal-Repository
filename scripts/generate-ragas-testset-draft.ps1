param(
    [string]$KnowledgeBaseId = "",

    [string]$ChunksJson = "",

    [Parameter(Mandatory = $true)]
    [string]$OutputJson,

    [Parameter(Mandatory = $true)]
    [string]$ReviewCsv,

    [int]$CasesPerDocument = 3,

    [int]$TopK = 5,

    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $repoRoot "ai-service\scripts\generate_ragas_testset_draft.py"

$argsList = @(
    $runner,
    "--output-json", $OutputJson,
    "--review-csv", $ReviewCsv,
    "--cases-per-document", $CasesPerDocument,
    "--top-k", $TopK
)

if ($KnowledgeBaseId) {
    $argsList += @("--knowledge-base-id", $KnowledgeBaseId)
} elseif ($ChunksJson) {
    $argsList += @("--chunks-json", $ChunksJson)
} else {
    throw "Either -KnowledgeBaseId or -ChunksJson is required."
}

& $Python @argsList
