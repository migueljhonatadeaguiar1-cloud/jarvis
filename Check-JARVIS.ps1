$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw 'Node.js não encontrado.' }
if ([int]((& node --version).TrimStart('v').Split('.')[0]) -lt 20) { throw 'Node.js 20 ou superior é necessário.' }
& node --check (Join-Path $project 'server.js')
if ($LASTEXITCODE -ne 0) { throw 'Sintaxe do backend inválida.' }
& node --check (Join-Path $project 'public\app.js')
if ($LASTEXITCODE -ne 0) { throw 'Sintaxe do frontend inválida.' }
Write-Host 'Sintaxe JavaScript: OK'
$port = 3000
if (Test-Path (Join-Path $project '.env')) { $portLine = Select-String -Path (Join-Path $project '.env') -Pattern '^\s*PORT\s*=\s*(\d+)' -AllMatches | Select-Object -First 1; if ($portLine -and $portLine.Matches.Count -gt 0) { $port = [int]$portLine.Matches[0].Groups[1].Value } }
try {
  $health = Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 3
  if (-not $health.ok) { throw 'Health check retornou falha.' }
  Write-Host "Backend local: OK; agente=$($health.localAgent); M-Search+ fontes=$($health.searchPlusAvailable)"
} catch { Write-Host 'Backend HTTP: não está iniciado; sintaxe validada. Inicie Start-JARVIS.ps1 para validar rotas.' }
