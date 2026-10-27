$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $project
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js 20+ não encontrado. Instale Node.js e tente novamente.' }
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
$port = 3000
$portLine = Select-String -Path '.env' -Pattern '^\s*PORT\s*=\s*(\d+)' -AllMatches | Select-Object -First 1
if ($portLine -and $portLine.Matches.Count -gt 0) { $port = [int]$portLine.Matches[0].Groups[1].Value }
$url = "http://127.0.0.1:$port"
$running = $false
try { $null = Invoke-RestMethod "$url/api/health" -TimeoutSec 2; $running = $true } catch {}
if ($running) { Start-Process $url; Write-Host "JARVIS já estava ativo em $url"; exit 0 }
$node = (Get-Command node).Source
Start-Job -ArgumentList $url -ScriptBlock { param($target); Start-Sleep -Seconds 2; Start-Process $target } | Out-Null
Write-Host 'JARVIS local iniciando. Pressione Ctrl+C para encerrar.'
& $node 'server.js'
