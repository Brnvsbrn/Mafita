$ErrorActionPreference = "Stop"

$envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
if (Test-Path $envPath) {
  Get-Content $envPath | ForEach-Object {
    if ($_ -and -not $_.StartsWith("#") -and $_.Contains("=")) {
      $parts = $_.Split("=", 2)
      if (-not [Environment]::GetEnvironmentVariable($parts[0])) {
        [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
      }
    }
  }
}

if (-not $env:CENCORI_API_KEY) {
  Write-Output "SKIP: CENCORI_API_KEY is not set."
  exit 0
}

$body = @{
  model = "gemini-2.5-flash"
  messages = @(
    @{ role = "user"; content = "Say Bank0 Cencori curl smoke test passed in one short sentence." }
  )
} | ConvertTo-Json -Depth 10

curl.exe https://api.cencori.com/v1/chat/completions `
  -H "Authorization: Bearer $env:CENCORI_API_KEY" `
  -H "Content-Type: application/json" `
  -d $body
