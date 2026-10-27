"""JARVIS Voice Studio and reusable JARVIS TTS interface."""
import sys
from pathlib import Path

_vendor = str(Path(__file__).resolve().parents[1] / "vendor")
if Path(_vendor).is_dir() and _vendor not in sys.path:
    sys.path.insert(0, _vendor)

from .synthesis import generate

def falar(texto, voz="jarvis", velocidade=1.0, output_path="jarvis.wav", *, provider="local", api_key="", local_voice="", model="gpt-4o-mini-tts", cloud_voice="onyx"):
    """Synthesize speech into a WAV file; returns its duration in seconds."""
    return generate(texto, output_path, provider=provider, local_voice=local_voice,
        speed=velocidade, api_key=api_key, model=model, voice=cloud_voice)
