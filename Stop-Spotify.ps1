$ErrorActionPreference = 'Stop'
$spotify = Get-Process -Name Spotify -ErrorAction SilentlyContinue
if (-not $spotify) {
    Write-Output 'O Spotify já estava fechado.'
    exit 0
}

# The user explicitly asked JARVIS to close Spotify after the startup briefing.
# Stop only processes named Spotify; do not touch browser or system audio sessions.
$ids = @($spotify | ForEach-Object { $_.Id })
foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }

$deadline = (Get-Date).AddSeconds(5)
do {
    Start-Sleep -Milliseconds 200
    $remaining = Get-Process -Name Spotify -ErrorAction SilentlyContinue
} while ($remaining -and (Get-Date) -lt $deadline)

if (Get-Process -Name Spotify -ErrorAction SilentlyContinue) {
    Write-Error 'O Spotify ainda está em execução.'
    exit 1
}
Write-Output 'Spotify encerrado; a reprodução foi interrompida.'
exit 0
