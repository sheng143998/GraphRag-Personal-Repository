$ErrorActionPreference = "Stop"

$confirmation = Read-Host "This will remove local PostgreSQL and Redis volumes. Type RESET to continue"
if ($confirmation -ne "RESET") {
    Write-Host "Cancelled."
    exit 0
}

docker compose down -v
docker compose up -d postgres redis
