"""Windows MCI WAV playback with software gain on a temporary copy."""
import ctypes, os, tempfile, wave

class Player:
    def __init__(self):
        self.dll=ctypes.windll.winmm;self.opened=False;self.state="stopped";self.source=None;self.gain=1.0;self.play_copy=None
    def _send(self, command):
        buf=ctypes.create_unicode_buffer(512); err=self.dll.mciSendStringW(command,buf,512,None)
        if err:
            message=ctypes.create_unicode_buffer(512)
            if not self.dll.mciGetErrorStringW(err,message,512):message.value=f"MCI {err}"
            raise RuntimeError(message.value)
        return buf.value
    def _scaled_path(self):
        if self.gain>=0.9999:return self.source
        fd,dst=tempfile.mkstemp(prefix=".jarvis-playback-",suffix=".wav",dir=os.path.dirname(self.source));os.close(fd)
        with wave.open(self.source,"rb") as src:
            if src.getcomptype()!="NONE":raise RuntimeError("O controle de volume aceita áudio WAV PCM não comprimido.")
            params=src.getparams();width=src.getsampwidth();raw=src.readframes(src.getnframes())
        if width==1:
            out=bytes(max(0,min(255,round((sample-128)*self.gain+128))) for sample in raw)
        elif width in (2,3,4):
            out=bytearray(len(raw));lo=-(1<<(width*8-1));hi=(1<<(width*8-1))-1
            for i in range(0,len(raw),width):
                value=int.from_bytes(raw[i:i+width],"little",signed=True)
                scaled=max(lo,min(hi,round(value*self.gain)))
                out[i:i+width]=scaled.to_bytes(width,"little",signed=True)
            out=bytes(out)
        else:raise RuntimeError(f"Largura PCM WAV não suportada para volume: {width} bytes.")
        try:
            with wave.open(dst,"wb") as target:target.setparams(params);target.writeframes(out)
        except Exception:
            try:os.unlink(dst)
            except OSError:pass
            raise
        self.play_copy=dst
        return dst
    def open(self,path,volume=1.0):
        self.stop()
        if os.name!="nt": raise RuntimeError("Reprodução MCI disponível apenas no Windows.")
        self.source=os.path.abspath(path);self.gain=max(0,min(1,float(volume)));escaped=self._scaled_path().replace('"','')
        self._send(f'open "{escaped}" type waveaudio alias jarvisvoice');self.opened=True
        self._send("set jarvisvoice time format milliseconds")
    def play(self): self._send("play jarvisvoice");self.state="playing"
    def pause(self): self._send("pause jarvisvoice");self.state="paused"
    def resume(self): self._send("resume jarvisvoice");self.state="playing"
    def stop(self):
        if getattr(self,"opened",False):
            self._send("close jarvisvoice");self.opened=False
        self.state="stopped"
        if self.play_copy:
            try:os.unlink(self.play_copy)
            except OSError:pass
            self.play_copy=None
    def position(self):
        try:return int(self._send("status jarvisvoice position"))/1000
        except (ValueError,RuntimeError):return 0
    def length(self):
        try:return int(self._send("status jarvisvoice length"))/1000
        except (ValueError,RuntimeError):return 0
    def volume(self,value):
        value=max(0,min(1,float(value)))
        if abs(value-self.gain)<0.005:return
        old_position=self.position() if self.opened else 0;was_playing=self.state=="playing";source=self.source
        self.gain=value
        if self.opened and source:
            self.stop();self.open(source,value);self.seek(old_position)
            if was_playing:self.play()
    def seek(self,seconds):self._send(f"seek jarvisvoice to {int(max(0,float(seconds))*1000)}")
