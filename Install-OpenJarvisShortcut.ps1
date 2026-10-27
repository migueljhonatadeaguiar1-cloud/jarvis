param([switch]$InstallOnStartup)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$listener = Join-Path $project 'Listen-For-OpenJarvis.ps1'
if (-not (Test-Path $listener)) { throw 'Listen-For-OpenJarvis.ps1 não está junto deste instalador.' }
$shell = New-Object -ComObject WScript.Shell
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path $powershell)) { throw 'Windows PowerShell não foi encontrado em System32.' }
function New-VoiceShortcut([string]$destination) {
    $shortcut = $shell.CreateShortcut($destination)
    $shortcut.TargetPath = $powershell
    $shortcut.Arguments = "-NoProfile -WindowStyle Hidden -File `"$listener`""
    $shortcut.WorkingDirectory = $project
    $shortcut.Description = 'Escuta local “open JARVIS” e variantes para abrir o JARVIS.'
    $shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,167"
    $shortcut.Save()
}
$projectShortcut = Join-Path $project 'Atalho-Open-JARVIS.lnk'
New-VoiceShortcut $projectShortcut
Remove-Item -LiteralPath (Join-Path $project 'Atalho-JARVIS-Palmas.lnk') -Force -ErrorAction SilentlyContinue
Write-Host "Atalho criado: $projectShortcut"
if ($InstallOnStartup) {
    $startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
    $null = New-Item -ItemType Directory -Path $startup -Force
    $startupShortcut = Join-Path $startup 'JARVIS por voz.lnk'
    New-VoiceShortcut $startupShortcut
    Write-Host "Inicialização com o Windows ativada: $startupShortcut"
}
Write-Host 'Escuta local do Windows; frases incluem “open JARVIS”, “open Chaves”, “abrir JARVIS” e variantes.'
Write-Host 'Para encerrar a escuta: .\Stop-OpenJarvisListener.ps1'
if ($InstallOnStartup) { Write-Host 'Para remover a inicialização automática, apague o atalho JARVIS por voz da pasta Inicializar.' }
