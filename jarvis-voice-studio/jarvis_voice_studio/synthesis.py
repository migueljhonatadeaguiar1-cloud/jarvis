"""Real speech synthesis backends: bundled Piper local neural voice and OpenAI cloud TTS."""
import json, tempfile, urllib.error, urllib.request, wave, contextlib
from pathlib import Path
import threading

MAX_CHARS = 4096
STYLE = "Speak in natural Brazilian Portuguese. Adult masculine voice, medium-low register, calm, polished, clear articulation, measured pace, restrained expression, professional and warm. Do not sound theatrical."
PIPER_MODEL = Path(__file__).resolve().parents[1] / "models" / "pt_BR-faber-medium.onnx"
_PIPER_LOCK = threading.Lock()
_PIPER_INSTANCE = None

# Portuguese text normalization for TTS
import re

_ORDINAL_PT = {
    "1º": "primeiro", "1ª": "primeira", "1°": "primeiro",
    "2º": "segundo", "2ª": "segunda", "2°": "segundo",
    "3º": "terceiro", "3ª": "terceira", "3°": "terceiro",
    "4º": "quarto", "4ª": "quarta", "4°": "quarto",
    "5º": "quinto", "5ª": "quinta", "5°": "quinto",
    "6º": "sexto", "6ª": "sexta", "6°": "sexto",
    "7º": "sétimo", "7ª": "sétima", "7°": "sétimo",
    "8º": "oitavo", "8ª": "oitava", "8°": "oitavo",
    "9º": "nono", "9ª": "nona", "9°": "nono",
    "10º": "décimo", "10ª": "décima", "10°": "décimo",
    "11º": "décimo primeiro", "11ª": "décima primeira", "11°": "décimo primeiro",
    "12º": "décimo segundo", "12ª": "décima segunda", "12°": "décimo segundo",
    "13º": "décimo terceiro", "13ª": "décima terceira", "13°": "décimo terceiro",
    "14º": "décimo quarto", "14ª": "décima quarta", "14°": "décimo quarto",
    "15º": "décimo quinto", "15ª": "décima quinta", "15°": "décimo quinto",
    "16º": "décimo sexto", "16ª": "décima sexta", "16°": "décimo sexto",
    "17º": "décimo sétimo", "17ª": "décima sétima", "17°": "décimo sétimo",
    "18º": "décimo oitavo", "18ª": "décima oitava", "18°": "décimo oitavo",
    "19º": "décimo nono", "19ª": "décima nona", "19°": "décimo nono",
    "20º": "vigésimo", "20ª": "vigésima", "20°": "vigésimo",
}

def normalize_pt_br(text: str) -> str:
    """Normalize Portuguese text for better TTS pronunciation."""
    # Ordinal numbers: 2º -> segundo, 1ª -> primeira, etc.
    def replace_ordinal(m):
        num = m.group(1)
        suffix = m.group(2)
        key = f"{num}{suffix}"
        return _ORDINAL_PT.get(key, m.group(0))
    text = re.sub(r"(?<!\w)(\d{1,2})(º|ª|°)(?!\w)", replace_ordinal, text)
    # Common abbreviations
    text = re.sub(r"\betc\.\b", "etcétera", text, flags=re.IGNORECASE)
    text = re.sub(r"\bp\.?ex\.?\b", "por exemplo", text, flags=re.IGNORECASE)
    text = re.sub(r"\be\.?g\.?\b", "por exemplo", text, flags=re.IGNORECASE)
    text = re.sub(r"\bi\.?e\.?\b", "isto é", text, flags=re.IGNORECASE)
    # Currency and units
    text = re.sub(r"(\d+)\s*%", r"\1 por cento", text)
    text = re.sub(r"R\$\s*(\d+(?:[.,]\d+)?)", r"\1 reais", text)
    text = re.sub(r"\b(\d+)\s*kg\b", r"\1 quilos", text)
    text = re.sub(r"\b(\d+)\s*km\b", r"\1 quilômetros", text)
    return text


def split_text(text, limit=MAX_CHARS):
    text=text.strip(); chunks=[]
    while len(text)>limit:
        cut=max(text.rfind("\n",0,limit+1),text.rfind(". ",0,limit+1),text.rfind("! ",0,limit+1),text.rfind("? ",0,limit+1),text.rfind("; ",0,limit+1),text.rfind(" ",0,limit+1))
        if cut < limit//2: cut=limit
        chunks.append(text[:cut].strip()); text=text[cut:].strip()
    if text: chunks.append(text)
    return chunks

def _piper_voice():
    global _PIPER_INSTANCE
    if _PIPER_INSTANCE is not None:return _PIPER_INSTANCE
    with _PIPER_LOCK:
        if _PIPER_INSTANCE is not None:return _PIPER_INSTANCE
        return _load_piper_voice()

def _load_piper_voice():
    global _PIPER_INSTANCE
    try:
        from piper import PiperVoice
    except ImportError as e:
        raise RuntimeError("O mecanismo Piper não está instalado. Execute run.bat ou instale requirements.txt.") from e
    if not PIPER_MODEL.is_file() or not Path(str(PIPER_MODEL)+".json").is_file():
        raise RuntimeError("O modelo local da voz JARVIS não foi encontrado na pasta models.")
    try:
        _PIPER_INSTANCE=PiperVoice.load(str(PIPER_MODEL))
        return _PIPER_INSTANCE
    except Exception as e:raise RuntimeError(f"Não foi possível carregar o modelo neural local: {e}") from None

def preload_local_voice():
    """Load the neural model in the background when the desktop app starts."""
    return _piper_voice()

def _piper(text,path,speed,volume=1.0):
    try:
        from piper.config import SynthesisConfig
    except ImportError as e:raise RuntimeError("Instale o mecanismo local Piper a partir de requirements.txt.") from e
    voice=_piper_voice();parts=split_text(text,1600)
    syn=SynthesisConfig(volume=max(0,min(1,float(volume))),length_scale=max(.25,min(4,1/max(.25,float(speed)))),noise_scale=.667,noise_w_scale=.8,normalize_audio=True)
    if len(parts)==1:
        with wave.open(str(path),"wb") as out:voice.synthesize_wav(parts[0],out,syn_config=syn)
        return
    with tempfile.TemporaryDirectory() as td:
        files=[]
        try:
            for i,part in enumerate(parts):
                p=Path(td)/f"{i}.wav"
                with wave.open(str(p),"wb") as out:voice.synthesize_wav(part,out,syn_config=syn)
                files.append(p)
            _concat_wav(files,path)
        except Exception:Path(path).unlink(missing_ok=True);raise

def _cloud_chunk(text, path, api_key, model, voice, speed, style, locale="pt-BR"):
    payload={"model":model,"voice":voice,"input":text,"response_format":"wav","speed":max(.25,min(4,speed))}
    if model.startswith("gpt-4o-mini-tts"):
        language={"pt-BR":"natural Brazilian Portuguese", "en-US":"natural US English", "es-ES":"natural European Spanish", "fr-FR":"natural French", "de-DE":"natural German", "it-IT":"natural Italian"}.get(locale,"natural Brazilian Portuguese")
        payload["instructions"]=(style or STYLE).replace("natural Brazilian Portuguese",language)
    req=urllib.request.Request("https://api.openai.com/v1/audio/speech",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+api_key,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=180) as r: Path(path).write_bytes(r.read())
    except urllib.error.HTTPError as e:
        body=e.read(1000).decode("utf-8","replace").lower()
        if e.code in (401,403): msg="Autenticação recusada. Confira a chave e o acesso ao modelo."
        elif e.code==429: msg="Limite ou cota do provedor atingido. Confira uso e faturamento da conta."
        elif e.code>=500: msg="O serviço de voz está indisponível. Tente novamente mais tarde."
        else: msg=f"Provedor recusou a solicitação (HTTP {e.code}). Confira o modelo e os parâmetros."
        raise RuntimeError(msg) from None
    except (urllib.error.URLError,TimeoutError): raise RuntimeError("Falha de conexão com o provedor de voz. Verifique a internet e tente novamente.") from None

def duration(path):
    with contextlib.closing(wave.open(str(path),"rb")) as w:return w.getnframes()/float(w.getframerate())

def generate(text,path,provider="local",local_voice="",speed=1.0,api_key="",model="gpt-4o-mini-tts",voice="onyx",style=STYLE,locale="pt-BR"):
    if locale and locale.startswith("pt"):
        text = normalize_pt_br(text)
    parts=split_text(text)
    if provider=="local":
        _piper(text,path,speed)
    else:
        if not api_key: raise RuntimeError("Configure uma chave de API nas Configurações para usar o provedor em nuvem.")
        if len(parts)==1:_cloud_chunk(parts[0],path,api_key,model,voice,speed,style,locale)
        else:
            import tempfile
            temp=[]
            try:
                with tempfile.TemporaryDirectory() as td:
                    for i,part in enumerate(parts):
                        p=Path(td)/f"{i}.wav";_cloud_chunk(part,p,api_key,model,voice,speed,style,locale);temp.append(p)
                    _concat_wav(temp,path)
            except Exception:
                Path(path).unlink(missing_ok=True);raise
    return duration(path)

def _concat_wav(files,out):
    with wave.open(str(files[0]),"rb") as first: params=first.getparams()
    with wave.open(str(out),"wb") as dst:
        dst.setparams(params)
        for f in files:
            with wave.open(str(f),"rb") as src:
                if src.getparams()[:4] != params[:4]: raise RuntimeError("O provedor retornou segmentos de áudio incompatíveis.")
                dst.writeframes(src.readframes(src.getnframes()))

def test_connection(api_key):
    req=urllib.request.Request("https://api.openai.com/v1/models",headers={"Authorization":"Bearer "+api_key})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:return r.status==200
    except urllib.error.HTTPError as e:
        if e.code in (401,403): raise RuntimeError("Autenticação recusada. Verifique a chave.") from None
        if e.code==429: raise RuntimeError("Limite de requisições atingido durante o teste.") from None
        raise RuntimeError(f"O provedor respondeu com HTTP {e.code}.") from None
    except (urllib.error.URLError,TimeoutError):raise RuntimeError("Não foi possível conectar. Confira a internet.") from None
