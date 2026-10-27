# JARVIS Voice Studio

Windows desktop app that turns typed text into real WAV files. The default "JARVIS — Official Voice" is synthesized locally by Piper using the Brazilian Portuguese male model pt_BR-faber-medium. Synthesis through the OpenAI API is also available as an option.

> The app UI and the voice are in Brazilian Portuguese; button labels are quoted below in Portuguese with an English gloss.

## Requirements

- Windows 10 or 11.
- Python 3.10 or later with Tcl/Tk (the standard Python distribution for Windows includes Tkinter).
- Internet access and an OpenAI API key with available access and quota, for OpenAI mode only.

The Piper runtime comes from the `piper-tts` package (`pip install -r requirements.txt`) and the `pt_BR-faber-medium.onnx` model must be downloaded into `models/` (see the JARVIS README). After that, local synthesis needs neither internet nor a SAPI voice. The app loads the model in the background on startup and keeps it in memory to reduce the wait when generating. FFmpeg is not required.

## Install and run

1. Install Python 3.10+ from the official installer, including Tcl/Tk.
2. Run `pip install -r requirements.txt` and download the `.onnx` model into `models/`.
3. Double-click `run.bat`, or run `python -m jarvis_voice_studio` in this folder.
4. Leave the `local` engine selected and click **Testar voz** (test voice) or **Gerar áudio** (generate audio). This produces real audio offline; the text never leaves the computer.

## Engines and privacy

- **Local / Piper Faber:** a male neural model in Brazilian Portuguese, run on your computer. The speed control acts on synthesis. The text stays local. "JARVIS — Official Voice" is the configured profile that uses this model at a moderate speed; the voice model was pre-trained by third parties and was not created from scratch, cloned, or trained to imitate an actor. The model does not accept independent personality instructions.
- **OpenAI (optional):** requires an API key and access/quota on the service. `gpt-4o-mini-tts` uses instructions to guide the speech; `onyx` is the initial option. The text and connection-test requests are sent to OpenAI; confirm the in-app warning before each generation/short test. Costs may apply, and the service's limits and privacy policy apply.
- The speech endpoint accepts up to 4,096 characters per request. The app splits longer text at sentence/space boundaries and concatenates compatible WAVs; a segment change may produce a noticeable pause.
- Output is WAV. Local audio is not automatically converted to MP3.
- The player volume is applied to a temporary copy so the exported original WAV is not altered.
- The key is stored in the Windows Credential Manager. Preferences and history live in `%APPDATA%\JarvisVoiceStudio`; WAV files are stored in `%APPDATA%\JarvisVoiceStudio\audio`. History may contain typed text, so delete items if you don't want to keep it on this computer.
- The Faber voice is an existing model under a CC0 license, with a GPL-3.0 Piper runtime. Notices and provenance are in `models/VOICE-LICENSE.md` and in the `piper-tts` package distribution.

## Set up OpenAI

1. Open **Configurações** (settings) in the app and choose `openai`.
2. Paste an OpenAI API key into the protected field. Click **Testar conexão** (test connection) to validate authentication through the models endpoint; the test does not generate audio.
3. Pick a model and an available voice from the list and save. For cloud generation or a short test, select `openai` on the main screen and accept the text-sending warning.
4. To delete the key, leave the field empty and save. It is never written to the preferences JSON or to logs.

`config.example.json` documents the options without containing credentials. Current preferences are written to AppData.

## Reuse in the JARVIS assistant

With the package's parent folder on `PYTHONPATH`:

```python
from jarvis_voice_studio import falar

segundos = falar("Certamente, senhor.", voz="jarvis", velocidade=1.0,
                 output_path="resposta.wav")
```

The module returns the duration in seconds and creates a WAV. The call above uses the local Piper Faber neural voice. The caller may pass `provider="openai"`, `api_key=...`, `model=...`, and `cloud_voice=...` if it chooses the cloud; retrieve credentials from the Credential Manager in the host process and inform the user that the text will be sent. To synchronize playback in another process, use the generated WAV and the assistant's own player; the studio UI is independent.

## Windows executable

The project does not yet include a packaged executable. One can be built with PyInstaller on a Windows environment (with Tk/Tcl and PowerShell installed):

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --name "JARVIS Voice Studio" --add-data "models;models" entrypoint.py
```

The model and runtime make the distribution larger (hundreds of MB).

## Checks

Code checks can be run with `python -m compileall jarvis_voice_studio`. See `TESTING.md` for the real synthesis test and known limits. Local synthesis is self-contained once the model is downloaded; only the cloud alternative requires a key.
