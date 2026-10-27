# JARVIS (prototype)

**Local** personal assistant inspired by J.A.R.V.I.S., for Windows 11: a web interface with an animated 3D sphere, chat, Portuguese voice, restricted local actions, and optional integrations (Hermes Agent, Google Calendar/Gmail, Spotify, and the [M-Search+](../msearch-plus) search engine).

> ⚠️ **Prototype.** Built and tested on a single Windows computer. Expect rough edges, and read the [Security](#security) section before connecting accounts or agents.
>
> 🇧🇷 The assistant itself (UI labels, speech recognition, voice, voice commands) is in **Brazilian Portuguese**. UI labels are quoted below in Portuguese, with an English gloss where helpful.

## Features

- **Chat and voice:** text input and browser speech recognition (`pt-BR`); spoken replies through Voice Studio (local Piper, or OpenAI as an option).
- **Three.js sphere** that reacts to states: idle, listening, processing, executing, and speaking.
- **Multiple AI providers:** Hermes Agent, NVIDIA NIM, Groq, OpenRouter, DeepSeek, Gemini, and OpenAI. Keys stay on the backend only.
- **Controlled local actions:** open VS Code, Word, File Explorer, Calculator, and Notepad; create a Python project and `.docx` files; open applications you register yourself.
- **Opening briefing** with headlines (Google News Brasil and BBC News Brasil via RSS).
- **Google Calendar and Gmail** (Gmail is read-only), always with per-action confirmation.
- **Local search** through M-Search+, plus web search for factual questions, with source links.
- **Voice activation** ("open JARVIS") through the local Windows speech recognizer.

## Requirements

- Windows 11 (local actions and the `.ps1` scripts are Windows-specific)
- Node.js 20+ (the backend has no npm dependencies)
- Python 3.10+ (Voice Studio and M-Search+)
- Optional: Hermes Agent, a Google Cloud account (OAuth), Spotify desktop

## Installation

```powershell
# 1. Clone both projects side by side
git clone https://github.com/YOUR-USERNAME/jarvis.git
git clone https://github.com/YOUR-USERNAME/msearch-plus.git

# 2. Configure JARVIS
cd jarvis
Copy-Item .env.example .env      # edit .env and fill in the keys you plan to use

# 3. Voice and search dependencies
py -3 -m pip install -r jarvis-voice-studio\requirements.txt
py -3 -m pip install -r ..\msearch-plus\requirements.txt

# 4. Download the voice model (see below), then start
.\Start-JARVIS.ps1
```

`Start-JARVIS.ps1` creates `.env` if it is missing, starts the backend, and opens `http://127.0.0.1:3000`. Alternative: `node server.js`.

### Voice model (Piper, pt-BR)

The neural model is **not in the repository** (63 MB). Download `pt_BR-faber-medium.onnx` from
[rhasspy/piper-voices › pt/pt_BR/faber/medium](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/faber/medium)
and save it to `jarvis-voice-studio/models/` (the `.onnx.json` is already there). Expected SHA-256 of the `.onnx`:
`858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7`.

## Configuration (`.env`)

`.env` lives next to `server.js` and **must never be published** (it is already in `.gitignore`). See every variable in [`.env.example`](.env.example).

| Variable | Purpose |
|---|---|
| `JARVIS_PROVIDER` | Active provider (`hermes`, `nvidia`, `groq`, `openrouter`, `deepseek`, `gemini`, `openai`) |
| `<PROVIDER>_API_KEY` / `<PROVIDER>_MODEL` | Key and model for each provider |
| `HERMES_API_SERVER_KEY`, `HERMES_API_BASE_URL`, `HERMES_MODEL` | Local Hermes gateway |
| `HERMES_SHORTCUT_PATH` | Hermes Desktop shortcut (default: `Desktop\Hermes.lnk`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth (the token is written by the connect flow) |
| `PORT` | Local port (default 3000) |
| `SEARCH_PLUS_DIR` | M-Search+ folder (default: `../msearch-plus`) |
| `JARVIS_VOICE_STUDIO_DIR` | Voice Studio folder (default: `./jarvis-voice-studio`) |
| `JARVIS_PYTHON` | Path to Python, if `python` does not resolve |

Health status without exposing keys: `http://127.0.0.1:3000/api/health`.

## Hermes Agent (optional)

The local Hermes CLI is the preferred agent; without it, JARVIS warns you and falls back to a configured provider. Automation tasks that require Hermes report a failure instead of pretending to run.

To use the OpenAI-compatible gateway (`http://127.0.0.1:8642/v1`):

1. Configure the provider in Hermes itself (`hermes model`).
2. In Hermes' own `.env`, set `API_SERVER_ENABLED=true`, `API_SERVER_HOST=127.0.0.1`, `API_SERVER_PORT=8642`, and a strong `API_SERVER_KEY` (different from your provider key).
3. Run `hermes gateway` and leave the window open.
4. In JARVIS: **CONFIGURAR APIs → Hermes Agent (local)** (configure APIs), enter the `API_SERVER_KEY`, and use **TESTAR GATEWAY HERMES** (test Hermes gateway).

## Google Calendar and Gmail (optional)

1. In Google Cloud, create an OAuth client of type **Web application** and enable the **Calendar** and **Gmail** APIs.
2. Authorized JavaScript origin: `http://127.0.0.1:3000`.
3. Authorized redirect URI: `http://127.0.0.1:3000/oauth/google/callback`.
4. Enter the Client ID and Secret under **CONECTORES E APIs** (connectors and APIs) and click **CONECTAR CONTA GOOGLE** (connect Google account). In testing mode, add your account as a test user.

Scopes: `calendar.events.owned` (read/create/change events) and `gmail.readonly` (list the 8 most recent messages and read a selected one). JARVIS **does not send, archive, or delete email**. Nothing is read at startup: each query requires its own confirmation, also validated on the backend.

## Voice (JARVIS Voice Studio)

Folder [`jarvis-voice-studio/`](jarvis-voice-studio): a Tkinter app plus a local bridge used by the backend.

- **Local (default):** Piper with the Faber pt-BR model, 100% offline; text never leaves the computer.
- **OpenAI (optional):** `gpt-4o-mini-tts`; asks for confirmation before each request and may incur costs. The key is stored in the **Windows Credential Manager**, never in JSON, process arguments, or logs.
- Preferences and history in `%APPDATA%\JarvisVoiceStudio`.
- Open it from **CONECTORES E APIs → ABRIR VOICE STUDIO** or run `jarvis-voice-studio\run.bat`.
- Python usage: `from jarvis_voice_studio import falar` (see the code in `jarvis_voice_studio/`).

What was tested, and what was not, is documented in [`jarvis-voice-studio/TESTING.md`](jarvis-voice-studio/TESTING.md).

## Security

- The backend listens **only on `127.0.0.1`**. Do not expose the port to the network.
- Keys and tokens stay in the local `.env` and are **never returned to the browser**.
- In direct mode, the browser can only trigger **structured tools**; there is no free-form shell, no administrative commands, and no deleting or overwriting documents. New Word files get a unique name in `Documents\JARVIS`.
- Extra applications are registered by you (name + path to the `.exe`) and stored in `%LOCALAPPDATA%\JARVIS\apps.json`. Terminals and interpreters (`cmd`, `powershell`, `python`, `node`, …) are blocked.
- **Heads-up about Hermes:** when it is the provider, ordinary messages may trigger the active *toolsets* **inside Hermes** (terminal, files, etc.). JARVIS cannot limit them; restrict them in Hermes' own configuration.
- Never commit `.env`, `apps.json`, or tokens. If a key leaks, revoke it with the provider.

## Opening briefing and Spotify

When the page opens, JARVIS reads public headlines and can open the Spotify desktop app with a fixed track, setting only its own audio session to 45% (`Set-SpotifyVolume.ps1`) and closing it when the briefing ends (`Stop-Spotify.ps1`). This is a personal behavior of the prototype: edit or remove it in `server.js` and `public/app.js` if you don't want it. Browsers may block audio without a click; use **OUVIR BRIEFING** (listen to briefing).

## Voice activation

```powershell
.\Install-OpenJarvisShortcut.ps1                   # creates the shortcut
.\Install-OpenJarvisShortcut.ps1 -InstallOnStartup # optional: start with Windows
.\Stop-OpenJarvisListener.ps1                      # stops listening
```

After starting the shortcut, say "open JARVIS" or "abrir JARVIS". It uses the local Windows speech recognizer (no audio is sent to external services); it requires an installed speech resource under *Settings → Time & language → Language & region* and microphone access.

## Troubleshooting

- **Local voice unavailable:** confirm the `.onnx` is in `jarvis-voice-studio/models/` and that `piper-tts` is installed.
- **Voice Studio or M-Search+ not found:** set `JARVIS_VOICE_STUDIO_DIR` / `SEARCH_PLUS_DIR` and, if needed, `JARVIS_PYTHON`.
- **Port in use:** set `PORT=3001` in `.env`.
- **VS Code won't open:** check `code --version` in PowerShell.
- **API error:** check the key, model, quota, and selected provider.
- **Quick check:** `.\Check-JARVIS.ps1` validates Node and the server/frontend syntax.

## Structure

```text
jarvis/
├─ server.js               local backend: providers, OAuth, authorized tools
├─ public/                 interface (HTML/CSS/JS), Three.js sphere, chat
├─ jarvis-voice-studio/    speech synthesis (local Piper / optional OpenAI) and bridge
├─ *.ps1                   start, check, voice shortcut, Spotify
├─ .env.example            variable names, no credentials
└─ TODO.md
```

The search engine lives in a separate repository: [msearch-plus](../msearch-plus).

## Limitations

- Local actions are Windows-only; there is no continuous listening in the browser.
- Three.js and OrbitControls load from a CDN: offline, the sphere does not render (chat and automation keep working).
- Multi-key rotation per provider was not ported: there is one key per provider.
- OpenAI voice generation has not been validated with a real key.

## Third-party licenses

- Faber voice (pt-BR): dataset CC0, model MIT, via [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices). See `jarvis-voice-studio/models/VOICE-LICENSE.md`.
- `piper-tts` runtime: **GPL-3.0**. Keep this in mind when choosing the project's license.
- Choose a license for JARVIS before publishing (add a `LICENSE` file).
