param([switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$localData = $env:LOCALAPPDATA
if (-not $localData) { $localData = Join-Path $HOME 'AppData\Local' }
$stateDir = Join-Path $localData 'JARVIS'
$stopFile = Join-Path $stateDir 'stop-open-jarvis-listener.flag'
$logFile = Join-Path $stateDir 'open-jarvis-listener.log'
$null = New-Item -ItemType Directory -Path $stateDir -Force
Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue

$mutex = [Threading.Mutex]::new($false, 'Local\JARVIS-Open-Voice-Listener')
if (-not $mutex.WaitOne(0)) { exit 0 }
$engine = $null
try {
    Add-Type -AssemblyName System.Speech
    # InstalledRecognizers pode lançar uma NullReferenceException em alguns
    # Windows sem o mecanismo de reconhecimento instalado/configurado.
    $recognizers = @()
    try {
        $installed = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
        if ($null -ne $installed) { $recognizers = @($installed) }
    } catch {
        Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format s) O Windows não conseguiu enumerar reconhecedores: $($_.Exception.Message)"
    }
    if ($recognizers.Count -eq 0 -or $null -eq $recognizers[0]) {
        $message = 'O Windows não disponibilizou um reconhecedor de fala neste computador. Instale o recurso de Reconhecimento de fala para Português (Brasil) ou Inglês (Estados Unidos) em Configurações > Hora e idioma > Idioma e região > Opções de idioma. Se o recurso já estiver instalado, reinicie o Windows e tente novamente. A ativação por voz não iniciou.'
        if (-not $ValidateOnly) { Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show($message, 'JARVIS — ativação por voz', 'OK', 'Information') | Out-Null }
        return
    }
    $recognizer = $recognizers | Where-Object { $_.Culture.Name -eq 'pt-BR' } | Select-Object -First 1
    if (-not $recognizer) { $recognizer = $recognizers | Where-Object { $_.Culture.Name -eq 'en-US' } | Select-Object -First 1 }
    if (-not $recognizer) { $recognizer = $recognizers | Select-Object -First 1 }
    if ($ValidateOnly) { Write-Host "Reconhecedor disponível: $($recognizer.Description) [$($recognizer.Culture.Name)]"; exit 0 }

    $engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($recognizer)
    $phrases = @('open jarvis','open chaves','open chave','open jervis','abrir jarvis','abrir chaves','abrir chave','abrir jervis','open jars')
    $choices = [System.Speech.Recognition.Choices]::new()
    foreach ($phrase in ($phrases | Select-Object -Unique)) { $choices.Add($phrase) }
    $builder = [System.Speech.Recognition.GrammarBuilder]::new()
    $builder.Culture = $recognizer.Culture
    $builder.Append($choices)
    $grammar = [System.Speech.Recognition.Grammar]::new($builder)
    $engine.LoadGrammar($grammar)
    $engine.SetInputToDefaultAudioDevice()
    $engine.add_SpeechRecognized({
        param($sender, $eventArgs)
        if ($eventArgs.Result.Confidence -lt 0.62) { return }
        $port = 3000
        $envFile = Join-Path $project '.env'
        if (Test-Path $envFile) {
            $line = Select-String -Path $envFile -Pattern '^\s*PORT\s*=\s*(\d+)' | Select-Object -First 1
            if ($line -and $line.Matches.Count) { $port = [int]$line.Matches[0].Groups[1].Value }
        }
        $url = "http://127.0.0.1:$port"
        $ready = $false
        try { $null = Invoke-RestMethod "$url/api/health" -TimeoutSec 2; $ready = $true } catch {}
        if (-not $ready) {
            $node = Get-Command node -ErrorAction SilentlyContinue
            if (-not $node) { Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format s) Node.js não encontrado."; return }
            if (-not (Test-Path $envFile)) { Copy-Item (Join-Path $project '.env.example') $envFile }
            Start-Process -FilePath $node.Source -ArgumentList @('server.js') -WorkingDirectory $project -WindowStyle Hidden
            for ($attempt=0; $attempt -lt 40; $attempt++) { Start-Sleep -Milliseconds 500; try { $null=Invoke-RestMethod "$url/api/health" -TimeoutSec 2; $ready=$true; break } catch {} }
        }
        if ($ready) { Start-Process $url } else { Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format s) Backend local não respondeu." }
    }.GetNewClosure())
    Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format s) Escuta ativa; reconhecedor $($recognizer.Culture.Name)."
    $engine.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
    while (-not (Test-Path $stopFile)) { Start-Sleep -Milliseconds 400 }
} catch {
    Add-Content -LiteralPath $logFile -Value "$(Get-Date -Format s) $($_.Exception.Message)"
    if (-not $ValidateOnly) { try { Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'JARVIS — ativação por voz', 'OK', 'Error') | Out-Null } catch {} }
    throw
} finally {
    if ($engine) { try { $engine.RecognizeAsyncCancel(); $engine.Dispose() } catch {} }
    if (Test-Path $stopFile) { Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue }
    $mutex.ReleaseMutex(); $mutex.Dispose()
}
