$ErrorActionPreference = 'Stop'
$localData = $env:LOCALAPPDATA
if (-not $localData) { $localData = Join-Path $HOME 'AppData\Local' }
$stopDir = Join-Path $localData 'JARVIS'
$null = New-Item -ItemType Directory -Path $stopDir -Force
Set-Content -LiteralPath (Join-Path $stopDir 'stop-open-jarvis-listener.flag') -Value 'stop' -NoNewline -Encoding ascii
Write-Host 'Pedido enviado. A escuta por voz será encerrada.'
