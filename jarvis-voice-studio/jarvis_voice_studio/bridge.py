"""Small local bridge for the JARVIS web backend; secrets stay in Credential Manager."""
import json
import os
import sys
from pathlib import Path

from . import credentials, settings
from .synthesis import generate, _piper_voice


def _settings():
    cfg = settings.read_settings()
    provider = cfg.get("provider", "local")
    if provider not in ("local", "openai"):
        raise ValueError("Provedor de voz inválido nas configurações do Voice Studio.")
    return cfg, provider


def handle(request):
    cfg, provider = _settings()
    if request.get("mode") == "status":
        try:
            api_configured = bool(credentials.load()) if provider == "openai" else False
        except OSError:
            api_configured = False
        if provider == "local":
            try:
                _piper_voice()  # Load the local model once in the persistent bridge worker.
            except Exception as exc:
                return {"ok": True, "provider": provider, "ready": False, "warmupError": str(exc), "model": cfg.get("model", "gpt-4o-mini-tts"),
                        "cloudVoice": cfg.get("cloud_voice", "onyx"), "apiConfigured": api_configured,
                        "localVoice": cfg.get("local_voice", "")}
        return {"ok": True, "provider": provider, "ready": True, "model": cfg.get("model", "gpt-4o-mini-tts"),
                "cloudVoice": cfg.get("cloud_voice", "onyx"), "apiConfigured": api_configured,
                "localVoice": cfg.get("local_voice", "")}

    text = request.get("text")
    if not isinstance(text, str) or not text.strip() or len(text) > 4000:
        raise ValueError("Texto de voz inválido ou maior que 4000 caracteres.")
    output = Path(request.get("output", "")).resolve()
    temp_root = Path(__import__("tempfile").gettempdir()).resolve()
    try:
        output.relative_to(temp_root)
    except ValueError:
        raise ValueError("O arquivo temporário de áudio está fora da pasta permitida.") from None
    if output.suffix.lower() != ".wav" or not output.parent.is_dir():
        raise ValueError("Destino temporário de áudio inválido.")
    if provider == "openai" and request.get("cloudConsent") is not True:
        raise PermissionError("O texto só será enviado à OpenAI após sua confirmação explícita.")
    api_key = credentials.load() if provider == "openai" else ""
    duration = generate(text.strip(), output, provider=provider,
                        local_voice=cfg.get("local_voice", ""),
                        speed=float(cfg.get("speed", 1.0)), api_key=api_key,
                        model=cfg.get("model", "gpt-4o-mini-tts"),
                        voice=cfg.get("cloud_voice", "onyx"), locale=cfg.get("locale", "pt-BR"))
    if not output.is_file() or output.stat().st_size <= 44:
        raise RuntimeError("O Voice Studio não produziu um WAV válido.")
    return {"ok": True, "duration": duration, "provider": provider}


def main():
    if "--worker" in sys.argv:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
        for line in sys.stdin:
            try:
                request = json.loads(line)
                result = handle(request)
                print(json.dumps(result, ensure_ascii=False), flush=True)
            except Exception as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), flush=True)
        return
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
            sys.stdout.reconfigure(encoding="utf-8")
        request = json.load(sys.stdin)
        result = handle(request)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
