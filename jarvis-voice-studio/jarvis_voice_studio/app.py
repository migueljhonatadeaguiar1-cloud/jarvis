import os, queue, shutil, threading, tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from . import credentials, history, settings
from .player import Player
from .synthesis import generate, preload_local_voice, test_connection

BG="#0c0d10"; PANEL="#14161b"; PANEL2="#1b1e24"; RED="#f04452"; WHITE="#e8e9ed"; MUTED="#969ba7"

def fmt(seconds): return f"{int(seconds)//60:02d}:{int(seconds)%60:02d}"

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("JARVIS Voice Studio");self.geometry("1180x790");self.minsize(920,650);self.configure(bg=BG)
        self.cfg=settings.read_settings();self.player=Player();self.current=None;self.duration=0;self.generating=False
        self._style();self._build();self._refresh_history();self._tick()
        if self.provider_var.get()=="local":self.status.config(text="Preparando a voz neural em segundo plano…",fg=MUTED)
        self._preload_results=queue.Queue()
        self.after(100,self._poll_preload)
        threading.Thread(target=self._preload_voice,daemon=True).start()
        self.protocol("WM_DELETE_WINDOW",self._close)

    def _style(self):
        st=ttk.Style(self);st.theme_use("clam");st.configure("Treeview",background=PANEL,foreground=WHITE,fieldbackground=PANEL,rowheight=27,borderwidth=0)
        st.configure("Treeview.Heading",background=PANEL2,foreground=WHITE,borderwidth=0);st.map("Treeview",background=[("selected", "#54252b")])
        st.configure("TCombobox",fieldbackground=PANEL2,background=PANEL2,foreground=WHITE);st.configure("Horizontal.TScale",background=PANEL)

    def _button(self,parent,text,command,primary=False):
        b=tk.Button(parent,text=text,command=command,bg=RED if primary else PANEL2,fg="white",activebackground="#ff6873",activeforeground="white",relief="flat",bd=0,padx=15,pady=10,font=("Segoe UI",10,"bold" if primary else "normal"),cursor="hand2");return b
    def _label(self,parent,text,**kw):return tk.Label(parent,text=text,bg=kw.pop("bg",PANEL),fg=kw.pop("fg",WHITE),font=kw.pop("font",("Segoe UI",10)),**kw)
    def _build(self):
        head=tk.Frame(self,bg=BG);head.pack(fill="x",padx=27,pady=(22,15))
        self._label(head,"◉",fg=RED,font=("Segoe UI",24,"bold")).pack(side="left",padx=(0,11))
        title=tk.Frame(head,bg=BG);title.pack(side="left");self._label(title,"JARVIS VOICE STUDIO",bg=BG,font=("Segoe UI",16,"bold")).pack(anchor="w");self._label(title,"ESTÚDIO DE SÍNTESE DE VOZ",bg=BG,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w")
        self._button(head,"⚙  Configurações",self._settings).pack(side="right")
        body=tk.Frame(self,bg=BG);body.pack(fill="both",expand=True,padx=27,pady=(0,20));body.columnconfigure(0,weight=1);body.columnconfigure(1,minsize=270);body.rowconfigure(0,weight=1)
        left=tk.Frame(body,bg=PANEL);left.grid(row=0,column=0,sticky="nsew",padx=(0,14));left.rowconfigure(2,weight=1);left.columnconfigure(0,weight=1)
        bar=tk.Frame(left,bg=PANEL);bar.grid(row=0,column=0,sticky="ew",padx=19,pady=(17,10));self._label(bar,"TEXTO PARA NARRAÇÃO",font=("Segoe UI",9,"bold")).pack(side="left");self._label(bar,"PORTUGUÊS BRASILEIRO",fg=RED,font=("Segoe UI",8,"bold")).pack(side="right")
        self.text=tk.Text(left,bg="#101216",fg=WHITE,insertbackground=RED,relief="flat",wrap="word",font=("Segoe UI",12),padx=15,pady=13,undo=True);self.text.grid(row=2,column=0,sticky="nsew",padx=18);self.text.bind("<KeyRelease>",self._count)
        self.text.insert("1.0","Certamente, senhor. Todos os sistemas estão operacionais. Como posso ajudar?")
        foot=tk.Frame(left,bg=PANEL);foot.grid(row=3,column=0,sticky="ew",padx=18,pady=(9,16));self.count=self._label(foot,"0 caracteres  ·  ~0 s",fg=MUTED);self.count.pack(side="left");self._button(foot,"Colar",self._paste).pack(side="right",padx=(8,0));self._button(foot,"Limpar",lambda:self.text.delete("1.0","end")).pack(side="right")
        right=tk.Frame(body,bg=PANEL);right.grid(row=0,column=1,sticky="nsew");right.columnconfigure(0,weight=1)
        self._label(right,"VOZ",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=17,pady=(17,7))
        self.voice_var=tk.StringVar(value="JARVIS — Official Voice · Faber (pt-BR)");self.voice_combo=ttk.Combobox(right,textvariable=self.voice_var,state="readonly",values=["JARVIS — Official Voice · Faber (pt-BR)"]);self.voice_combo.pack(fill="x",padx=17)
        self.voice_status=self._label(right,"Voz neural masculina · Faber · funciona offline",fg=MUTED,font=("Segoe UI",8));self.voice_status.pack(anchor="w",padx=18,pady=(5,12))
        self._label(right,"IDIOMA",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=17,pady=(0,6))
        self.locale_var=tk.StringVar(value=self.cfg.get("locale","pt-BR"));self.locale_combo=ttk.Combobox(right,textvariable=self.locale_var,state="readonly",values=["pt-BR","en-US","es-ES","fr-FR","de-DE","it-IT"]);self.locale_combo.pack(fill="x",padx=17,pady=(0,12))
        self._label(right,"MECANISMO",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=17,pady=(2,7))
        self.provider_var=tk.StringVar(value=self.cfg["provider"]);self.provider=ttk.Combobox(right,textvariable=self.provider_var,state="readonly",values=["local","openai"]);self.provider.pack(fill="x",padx=17);self.provider.bind("<<ComboboxSelected>>",self._provider_change)
        self.provider_hint=self._label(right,"Local · Piper neural (offline)",fg=MUTED,font=("Segoe UI",8));self.provider_hint.pack(anchor="w",padx=18,pady=(4,12))
        self._label(right,"VELOCIDADE",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=17,pady=(2,1))
        self.speed=tk.DoubleVar(value=self.cfg["speed"]);row=tk.Frame(right,bg=PANEL);row.pack(fill="x",padx=12);self.speed_scale=ttk.Scale(row,from_=0.75,to=1.25,variable=self.speed,command=lambda _:self.speed_lbl.config(text=f"{self.speed.get():.2f}×"));self.speed_scale.pack(side="left",fill="x",expand=True);self.speed_lbl=self._label(row,f"{self.speed.get():.2f}×",width=5,anchor="e");self.speed_lbl.pack(side="right")
        self._label(right,"VOLUME",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=17,pady=(8,1));self.vol=tk.DoubleVar(value=self.cfg["volume"]);self.vol_scale=ttk.Scale(right,from_=0,to=1,variable=self.vol,command=self._volume);self.vol_scale.pack(fill="x",padx=17)
        self._button(right,"Restaurar padrão JARVIS",self._defaults).pack(fill="x",padx=17,pady=(9,14))
        self._button(right,"▶  Testar voz",self._preview).pack(fill="x",padx=17,pady=(0,9));self._button(right,"◉  GERAR ÁUDIO",self._generate,True).pack(fill="x",padx=17,pady=(0,14))
        self.status=self._label(right,"Pronto para gerar",fg=MUTED,font=("Segoe UI",8),wraplength=225);self.status.pack(anchor="w",padx=18,pady=(0,10))
        playback=tk.Frame(right,bg=PANEL2);playback.pack(fill="x",padx=12,pady=(0,12));self._label(playback,"REPRODUÇÃO",bg=PANEL2,fg=MUTED,font=("Segoe UI",8,"bold")).pack(anchor="w",padx=10,pady=(9,0))
        self._button(playback,"▶",self._play).pack(side="left",padx=(9,4),pady=6);self._button(playback,"Ⅱ",self._pause).pack(side="left",padx=4,pady=6);self._button(playback,"■",self._stop).pack(side="left",padx=4,pady=6);self._button(playback,"↓ WAV",self._export).pack(side="right",padx=8,pady=6)
        self.seek=tk.DoubleVar(value=0);ttk.Scale(playback,from_=0,to=100,variable=self.seek,command=self._seek).pack(fill="x",padx=10);self.time_lbl=self._label(playback,"00:00 / 00:00",bg=PANEL2,fg=MUTED,font=("Segoe UI",8));self.time_lbl.pack(anchor="e",padx=10,pady=(0,7))
        hist=tk.Frame(right,bg=PANEL);hist.pack(fill="both",expand=True,padx=12,pady=(0,12));self._label(hist,"HISTÓRICO RECENTE",font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(5,7));self.tree=ttk.Treeview(hist,columns=("date","duration"),show="tree headings",height=5);self.tree.heading("#0",text="Arquivo");self.tree.heading("date",text="Data");self.tree.heading("duration",text="Duração");self.tree.column("#0",width=120);self.tree.column("date",width=80);self.tree.column("duration",width=55);self.tree.pack(fill="both",expand=True);self.tree.bind("<Double-1>",lambda _:self._history_play())
        ops=tk.Frame(hist,bg=PANEL);ops.pack(fill="x",pady=7);self._button(ops,"Reproduzir",self._history_play).pack(side="left",padx=(0,4));self._button(ops,"Renomear",self._rename).pack(side="left",padx=4);self._button(ops,"Excluir",self._delete).pack(side="right")
        self._count();self._provider_change()

    def _count(self,*_):
        n=len(self.text.get("1.0","end-1c"));self.count.config(text=f"{n:,} caracteres  ·  ~{fmt(n/14)} min" if n>80 else f"{n:,} caracteres  ·  ~{max(1,round(n/14))} s")
    def _preload_voice(self):
        try:
            preload_local_voice()
            self._preload_results.put((True,"Voz local carregada · próxima geração pronta"))
        except Exception as e:self._preload_results.put((False,f"Voz será carregada ao gerar · {e}"))
    def _poll_preload(self):
        try:
            ok,msg=self._preload_results.get_nowait()
            if not self.generating and self.status.cget("text").startswith("Preparando a voz"):
                self.status.config(text=msg,fg="#7ed6a3" if ok else MUTED)
        except queue.Empty:pass
        if self.winfo_exists():self.after(150,self._poll_preload)
    def _paste(self):
        try:self.text.insert("insert",self.clipboard_get())
        except tk.TclError:messagebox.showinfo("Área de transferência","Não há texto disponível para colar.")
    def _provider_change(self,*_):
        cloud=self.provider_var.get()=="openai";self.provider_hint.config(text="Nuvem · texto enviado à OpenAI" if cloud else "Local · Piper neural (offline)");self.voice_status.config(text="Voz integrada OpenAI · instruções de estilo JARVIS" if cloud else "Voz neural masculina · Faber · funciona offline")
        if cloud:
            choices=["onyx","echo","alloy","ash","ballad","coral","fable","nova","sage","shimmer","verse","marin","cedar"]
            self.voice_combo.configure(values=choices);self.voice_var.set(self.cfg.get("cloud_voice","onyx"))
        else:
            self.voice_combo.configure(values=["JARVIS — Official Voice · Faber (pt-BR)"]);self.voice_var.set("JARVIS — Official Voice · Faber (pt-BR)")
        self.locale_combo.configure(values=["pt-BR","en-US","es-ES","fr-FR","de-DE","it-IT"] if cloud else ["pt-BR"])
        if not cloud:self.locale_var.set("pt-BR")
    def _selected_voice(self):
        return ""
    def _defaults(self):
        self.speed.set(1.0);self.vol.set(.85);self.locale_var.set("pt-BR");self.speed_lbl.config(text="1.00×");self.voice_var.set("JARVIS — Official Voice · Faber (pt-BR)");self._provider_change();self.status.config(text="Padrões JARVIS restaurados",fg=MUTED)
    def _save_cfg(self):
        self.cfg.update(provider=self.provider_var.get(),locale=self.locale_var.get(),speed=round(self.speed.get(),2),volume=round(self.vol.get(),2),local_voice="")
        if self.provider_var.get()=="openai":self.cfg["cloud_voice"]=self.voice_var.get()
        settings.write_settings(self.cfg)
    def _generate(self):
        text=self.text.get("1.0","end-1c").strip()
        if not text:messagebox.showinfo("Texto vazio","Digite ou cole um texto antes de gerar.");return
        cloud=self.provider_var.get()=="openai";key=credentials.load() if cloud else ""
        if cloud and not key:messagebox.showwarning("Chave necessária","Configure a chave OpenAI nas Configurações.");self._settings();return
        if cloud and not messagebox.askyesno("Envio para provedor externo",f"Este texto ( {len(text):,} caracteres ) será enviado à OpenAI para gerar o áudio. O uso pode ter custos e está sujeito aos limites e à política de privacidade do provedor. Continuar?"):return
        self._save_cfg();settings.AUDIO_DIR.mkdir(parents=True,exist_ok=True);path=settings.AUDIO_DIR/(datetime.now().strftime("jarvis_%Y%m%d_%H%M%S")+".wav");self.generating=True;self.status.config(text="Gerando áudio…",fg=RED)
        local_voice=self._selected_voice();speed=self.speed.get();model=self.cfg.get("model","gpt-4o-mini-tts");cloud_voice=self.voice_var.get() if cloud else self.cfg.get("cloud_voice","onyx");locale=self.locale_var.get()
        def work():
            try:
                dur=generate(text,path,provider="openai" if cloud else "local",local_voice=local_voice,speed=speed,api_key=key,model=model,voice=cloud_voice,locale=locale);item=history.add(text,path,dur,"OpenAI" if cloud else "Piper local · Faber");self.after(0,lambda:self._done(item))
            except Exception as e:self.after(0,lambda:self._fail(str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _done(self,item):
        self.generating=False;self.current=item;self.duration=item["duration"];self._refresh_history();self.status.config(text=f"Áudio gerado · {fmt(self.duration)}",fg="#7ed6a3");self._open_play(item["path"])
    def _fail(self,msg):self.generating=False;self.status.config(text="A geração falhou",fg=RED);messagebox.showerror("Falha ao gerar áudio",msg)
    def _preview(self):
        text="Certamente, senhor. Verificando os sistemas agora. Tudo pronto.";cloud=self.provider_var.get()=="openai";key=credentials.load() if cloud else ""
        if cloud and not key:messagebox.showinfo("Configuração necessária","Adicione uma chave nas Configurações.");return
        if cloud and not messagebox.askyesno("Teste em nuvem","O texto de teste será enviado à OpenAI. Continuar?"):return
        path=settings.AUDIO_DIR/"voice_preview.wav";settings.AUDIO_DIR.mkdir(parents=True,exist_ok=True);self.status.config(text="Gerando teste curto…",fg=RED)
        local_voice=self._selected_voice();speed=self.speed.get();model=self.cfg.get("model","gpt-4o-mini-tts");cloud_voice=self.voice_var.get() if cloud else self.cfg.get("cloud_voice","onyx");locale=self.locale_var.get()
        def work():
            try:generate(text,path,provider="openai" if cloud else "local",local_voice=local_voice,speed=speed,api_key=key,model=model,voice=cloud_voice,locale=locale);self.after(0,lambda:(self.status.config(text="Teste pronto",fg="#7ed6a3"),self._open_play(str(path))))
            except Exception as e:self.after(0,lambda:self._fail(str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _open_play(self,path):
        try:self.player.open(path,self.vol.get());self.player.play();self.duration=self.player.length();self._tick()
        except Exception as e:messagebox.showerror("Reprodução indisponível",str(e))
    def _play(self):
        if self.player.opened:
            try:self.player.resume();return
            except Exception:pass
        if self.current:self._open_play(self.current["path"])
        else:messagebox.showinfo("Sem áudio","Gere um áudio primeiro ou selecione um item do histórico.")
    def _pause(self):
        try:self.player.pause()
        except Exception:pass
    def _stop(self):
        try:self.player.stop()
        except Exception:pass
        self.time_lbl.config(text="00:00 / "+fmt(self.duration))
    def _volume(self,*_):
        if hasattr(self,"vol"):self.player.volume(self.vol.get())
    def _seek(self,val):
        if self.player.opened and self.duration>0:
            try:self.player.seek(float(val)*self.duration/100)
            except Exception:pass
    def _tick(self):
        if self.player.opened:
            pos=self.player.position();self.duration=max(self.duration,self.player.length());self.time_lbl.config(text=f"{fmt(pos)} / {fmt(self.duration)}");self.seek.set(pos/self.duration*100 if self.duration else 0)
        self.after(500,self._tick)
    def _export(self):
        if not self.current:messagebox.showinfo("Sem áudio","Gere um áudio antes de exportar.");return
        dst=filedialog.asksaveasfilename(defaultextension=".wav",initialfile=self.current["name"],filetypes=[("Áudio WAV","*.wav")])
        if dst:
            try:shutil.copy2(self.current["path"],dst);self.status.config(text="WAV exportado",fg="#7ed6a3")
            except OSError as e:messagebox.showerror("Falha ao exportar",str(e))
    def _refresh_history(self):
        if not hasattr(self,"tree"):return
        self.items=history.all_items()
        for i in self.tree.get_children():self.tree.delete(i)
        for item in self.items:self.tree.insert("","end",iid=item["id"],text=item["name"],values=(item["date"][:10],fmt(item["duration"])))
    def _selected_item(self):
        sel=self.tree.selection();return next((i for i in self.items if sel and i["id"]==sel[0]),None)
    def _history_play(self):
        item=self._selected_item()
        if not item:return
        if not Path(item["path"]).exists():messagebox.showerror("Arquivo indisponível","O áudio local deste item não foi encontrado.");return
        self.current=item;self.duration=item["duration"];self._open_play(item["path"]);self.status.config(text=item["text"][:100],fg=MUTED)
    def _rename(self):
        item=self._selected_item()
        if not item:return
        name=simpledialog.askstring("Renomear áudio","Novo nome (sem extensão):",initialvalue=Path(item["name"]).stem,parent=self)
        if name and name.strip():item["name"]=Path(name.strip()).stem+".wav";history.save(self.items);self._refresh_history()
    def _delete(self):
        item=self._selected_item()
        if not item:return
        if not messagebox.askyesno("Excluir do histórico","Excluir este item e o arquivo local de áudio?"):return
        try:Path(item["path"]).unlink(missing_ok=True)
        except OSError:pass
        history.save([i for i in self.items if i["id"]!=item["id"]]);self._refresh_history()
    def _settings(self):
        win=tk.Toplevel(self);win.title("Configurações · JARVIS Voice Studio");win.configure(bg=BG);win.resizable(False,False);win.transient(self);win.grab_set()
        box=tk.Frame(win,bg=PANEL,padx=22,pady=20);box.pack(fill="both",expand=True,padx=14,pady=14)
        self._label(box,"PROVEDOR DE VOZ",font=("Segoe UI",9,"bold")).pack(anchor="w");prov=tk.StringVar(value=self.provider_var.get());ttk.Combobox(box,textvariable=prov,state="readonly",values=["local","openai"],width=45).pack(fill="x",pady=(5,14))
        self._label(box,"Chave API OpenAI (armazenada no Gerenciador de Credenciais do Windows)",font=("Segoe UI",9)).pack(anchor="w");secret=tk.StringVar(value=credentials.load());entry=tk.Entry(box,textvariable=secret,show="●",bg=PANEL2,fg=WHITE,insertbackground=WHITE,relief="flat",width=53);entry.pack(fill="x",pady=(5,4))
        self._label(box,"Texto enviado à OpenAI pode incorrer em custos e segue a política de privacidade do provedor.",fg=MUTED,font=("Segoe UI",8),wraplength=400,justify="left").pack(anchor="w",pady=(0,12))
        self._label(box,"MODELO E VOZ",font=("Segoe UI",9,"bold")).pack(anchor="w");row=tk.Frame(box,bg=PANEL);row.pack(fill="x",pady=5);model=tk.StringVar(value=self.cfg.get("model","gpt-4o-mini-tts"));ttk.Combobox(row,textvariable=model,state="readonly",values=["gpt-4o-mini-tts","tts-1","tts-1-hd"],width=25).pack(side="left");cloud_voice=tk.StringVar(value=self.cfg.get("cloud_voice","onyx"));ttk.Combobox(row,textvariable=cloud_voice,state="readonly",values=["onyx","echo","alloy","ash","ballad","coral","fable","nova","sage","shimmer","verse","marin","cedar"],width=17).pack(side="right")
        status=self._label(box,"",fg=MUTED);status.pack(anchor="w",pady=(8,0))
        def test():
            try:
                if test_connection(secret.get().strip()):status.config(text="Conexão autenticada com sucesso.",fg="#7ed6a3")
            except Exception as e:status.config(text=str(e),fg=RED)
        def save():
            try:
                value=secret.get().strip()
                if value:credentials.save(value)
                else:credentials.delete()
                self.cfg.update(provider=prov.get(),model=model.get(),cloud_voice=cloud_voice.get());settings.write_settings(self.cfg);self.provider_var.set(prov.get());self._provider_change();win.destroy()
            except Exception as e:messagebox.showerror("Não foi possível salvar a chave",str(e),parent=win)
        controls=tk.Frame(box,bg=PANEL);controls.pack(fill="x",pady=(14,0));self._button(controls,"Testar conexão",test).pack(side="left");self._button(controls,"Salvar",save,True).pack(side="right")
    def _close(self):
        self._save_cfg()
        try:self.player.stop()
        except Exception:pass
        self.destroy()

def main():App().mainloop()
