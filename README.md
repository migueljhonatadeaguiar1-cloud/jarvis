# jarvis
Local personal assistant prototype for Windows 11: 3D web UI, chat and Portuguese voice, multiple AI providers, restricted local actions, optional Google Calendar/Gmail and M-Search+ integration.

# JARVIS (protótipo)

Assistente pessoal **local** inspirado no J.A.R.V.I.S., para Windows 11: interface web com esfera 3D animada, chat, voz em português, ações locais restritas e integrações opcionais (Hermes Agent, Google Agenda/Gmail, Spotify e o buscador [M-Search+](../msearch-plus)).

> ⚠️ **Protótipo.** Foi feito e testado em um único computador Windows. Espere arestas, e leia a seção [Segurança](#segurança) antes de conectar contas ou agentes.

## Recursos

- **Chat e voz:** texto e reconhecimento de fala do navegador (`pt-BR`); resposta falada pelo Voice Studio (Piper local ou OpenAI, opcional).
- **Esfera Three.js** que reage aos estados: inativo, escutando, processando, executando e falando.
- **Vários provedores de IA:** Hermes Agent, NVIDIA NIM, Groq, OpenRouter, DeepSeek, Gemini e OpenAI. Chaves ficam só no backend.
- **Ações locais controladas:** abrir VS Code, Word, Explorador, Calculadora e Bloco de Notas; criar projeto Python e `.docx`; abrir aplicativos que você cadastrar.
- **Briefing de abertura** com manchetes (Google News Brasil e BBC News Brasil por RSS).
- **Google Agenda e Gmail** (somente leitura no Gmail), sempre com confirmação por ação.
- **Pesquisa local** pelo M-Search+ e pesquisa web para perguntas factuais, com links das fontes.
- **Ativação por voz** (“open JARVIS”) via reconhecedor local do Windows.

## Requisitos

- Windows 11 (as ações locais e os scripts `.ps1` são específicos do Windows)
- Node.js 20+ (o backend não tem dependências npm)
- Python 3.10+ (Voice Studio e M-Search+)
- Opcional: Hermes Agent, conta Google Cloud (OAuth), Spotify desktop

## Instalação

```powershell
# 1. Clone os dois projetos lado a lado
git clone https://github.com/SEU-USUARIO/jarvis.git
git clone https://github.com/SEU-USUARIO/msearch-plus.git

# 2. Configure o JARVIS
cd jarvis
Copy-Item .env.example .env      # edite o .env e preencha as chaves que for usar

# 3. Dependências de voz e do buscador
py -3 -m pip install -r jarvis-voice-studio\requirements.txt
py -3 -m pip install -r ..\msearch-plus\requirements.txt

# 4. Modelo de voz (veja abaixo) e inicie
.\Start-JARVIS.ps1
```

O `Start-JARVIS.ps1` cria o `.env` se faltar, sobe o backend e abre `http://127.0.0.1:3000`. Alternativa: `node server.js`.

### Modelo de voz (Piper, pt-BR)

O modelo neural **não está no repositório** (63 MB). Baixe `pt_BR-faber-medium.onnx` em
[rhasspy/piper-voices › pt/pt_BR/faber/medium](https://huggingface.co/rhasspy/piper-voices/tree/main/pt/pt_BR/faber/medium)
e salve em `jarvis-voice-studio/models/` (o `.onnx.json` já está lá). SHA-256 esperado do `.onnx`:
`858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7`.

## Configuração (`.env`)

O `.env` fica ao lado de `server.js` e **nunca deve ser publicado** (já está no `.gitignore`). Veja todas as variáveis em [`.env.example`](.env.example).

| Variável | Para quê |
|---|---|
| `JARVIS_PROVIDER` | Provedor ativo (`hermes`, `nvidia`, `groq`, `openrouter`, `deepseek`, `gemini`, `openai`) |
| `<PROVEDOR>_API_KEY` / `<PROVEDOR>_MODEL` | Chave e modelo de cada provedor |
| `HERMES_API_SERVER_KEY`, `HERMES_API_BASE_URL`, `HERMES_MODEL` | Gateway local do Hermes |
| `HERMES_SHORTCUT_PATH` | Atalho do Hermes Desktop (padrão: `Desktop\Hermes.lnk`) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | OAuth do Google (o token é gravado pelo fluxo de conexão) |
| `PORT` | Porta local (padrão 3000) |
| `SEARCH_PLUS_DIR` | Pasta do M-Search+ (padrão: `../msearch-plus`) |
| `JARVIS_VOICE_STUDIO_DIR` | Pasta do Voice Studio (padrão: `./jarvis-voice-studio`) |
| `JARVIS_PYTHON` | Caminho do Python, se `python` não resolver |

Estado de saúde sem expor chaves: `http://127.0.0.1:3000/api/health`.

## Hermes Agent (opcional)

O Hermes CLI local é o agente preferencial; sem ele, o JARVIS avisa e usa um provedor configurado como contingência. Tarefas de automação que exigem Hermes reportam falha em vez de fingir execução.

Para usar o gateway OpenAI-compatível (`http://127.0.0.1:8642/v1`):

1. Configure o provedor no próprio Hermes (`hermes model`).
2. No `.env` do Hermes, defina `API_SERVER_ENABLED=true`, `API_SERVER_HOST=127.0.0.1`, `API_SERVER_PORT=8642` e uma `API_SERVER_KEY` forte (diferente da chave do provedor).
3. Rode `hermes gateway` e deixe a janela aberta.
4. No JARVIS: **CONFIGURAR APIs → Hermes Agent (local)**, informe a `API_SERVER_KEY` e use **TESTAR GATEWAY HERMES**.

## Google Agenda e Gmail (opcional)

1. No Google Cloud, crie um cliente OAuth do tipo **Aplicativo da Web** e habilite as APIs **Calendar** e **Gmail**.
2. Origem JavaScript autorizada: `http://127.0.0.1:3000`.
3. URI de redirecionamento: `http://127.0.0.1:3000/oauth/google/callback`.
4. Informe Client ID e Secret em **CONECTORES E APIs** e clique em **CONECTAR CONTA GOOGLE**. Em modo de teste, adicione sua conta como usuário de teste.

Escopos: `calendar.events.owned` (consultar/criar/alterar eventos) e `gmail.readonly` (listar as 8 mensagens mais recentes e ler uma selecionada). O JARVIS **não envia, arquiva nem apaga e-mails**. Nada é lido no início: cada consulta exige confirmação específica, também validada no backend.

## Voz (JARVIS Voice Studio)

Pasta [`jarvis-voice-studio/`](jarvis-voice-studio): app Tkinter + ponte local usada pelo backend.

- **Local (padrão):** Piper com o modelo Faber pt-BR, 100% offline; o texto não sai do computador.
- **OpenAI (opcional):** `gpt-4o-mini-tts`; pede confirmação antes de cada envio e pode gerar custos. A chave fica no **Gerenciador de Credenciais do Windows**, nunca em JSON, argumentos de processo ou logs.
- Preferências e histórico em `%APPDATA%\JarvisVoiceStudio`.
- Abra-o em **CONECTORES E APIs → ABRIR VOICE STUDIO** ou rode `jarvis-voice-studio\run.bat`.
- Uso em Python: `from jarvis_voice_studio import falar` (veja o código em `jarvis_voice_studio/`).

O que foi testado e o que não foi está em [`jarvis-voice-studio/TESTES.md`](jarvis-voice-studio/TESTES.md).

## Segurança

- O backend escuta **somente em `127.0.0.1`**. Não exponha a porta na rede.
- Chaves e tokens ficam no `.env` local e **nunca são devolvidos ao navegador**.
- No modo direto, o navegador só aciona **ferramentas estruturadas**; não há shell livre, comandos administrativos, exclusão ou sobrescrita de documentos. Arquivos Word novos recebem nome exclusivo em `Documents\JARVIS`.
- Aplicativos extras são cadastrados por você (nome + caminho do `.exe`) e guardados em `%LOCALAPPDATA%\JARVIS\apps.json`. Terminais e interpretadores (`cmd`, `powershell`, `python`, `node`…) são bloqueados.
- **Atenção com o Hermes:** quando ele é o provedor, mensagens comuns podem acionar os *toolsets* ativos **dentro do Hermes** (terminal, arquivos etc.). O JARVIS não consegue limitá-los; restrinja-os na configuração do Hermes.
- Nunca faça commit de `.env`, `apps.json` ou tokens. Se uma chave vazar, revogue-a no provedor.

## Briefing de abertura e Spotify

Ao abrir a página, o JARVIS lê manchetes públicas e pode abrir o Spotify desktop com uma faixa fixa, ajustando só a sessão de áudio dele a 45% (`Set-SpotifyVolume.ps1`) e encerrando-o ao fim do briefing (`Stop-Spotify.ps1`). É um comportamento pessoal do protótipo: edite ou remova em `server.js` e `public/app.js` se não quiser. Navegadores podem bloquear áudio sem clique; use **OUVIR BRIEFING**.

## Ativação por voz

```powershell
.\Install-OpenJarvisShortcut.ps1                  # cria o atalho
.\Install-OpenJarvisShortcut.ps1 -InstallOnStartup # opcional: inicia com o Windows
.\Stop-OpenJarvisListener.ps1                      # encerra a escuta
```

Depois de iniciar o atalho, diga “open JARVIS” ou “abrir JARVIS”. Usa o reconhecedor local do Windows (sem enviar áudio a serviços externos); exige um recurso de fala instalado em *Configurações → Hora e idioma → Idioma e região* e acesso ao microfone.

## Solução de problemas

- **Voz local indisponível:** confirme que o `.onnx` está em `jarvis-voice-studio/models/` e que `piper-tts` foi instalado.
- **Voice Studio ou M-Search+ não encontrados:** ajuste `JARVIS_VOICE_STUDIO_DIR` / `SEARCH_PLUS_DIR` e, se preciso, `JARVIS_PYTHON`.
- **Porta ocupada:** defina `PORT=3001` no `.env`.
- **VS Code não abre:** verifique `code --version` no PowerShell.
- **Erro de API:** confira chave, modelo, cota e provedor selecionado.
- **Verificação rápida:** `.\Check-JARVIS.ps1` valida Node e a sintaxe do servidor e do frontend.

## Estrutura

```text
jarvis/
├─ server.js               backend local: provedores, OAuth, ferramentas autorizadas
├─ public/                 interface (HTML/CSS/JS), esfera Three.js, chat
├─ jarvis-voice-studio/    síntese de voz (Piper local / OpenAI opcional) e ponte
├─ *.ps1                   iniciar, verificar, atalho de voz, Spotify
├─ .env.example            nomes das variáveis, sem credenciais
└─ TODO.md
```

O buscador fica em um repositório separado: [msearch-plus](../msearch-plus).

## Limitações

- Somente Windows para as ações locais; sem escuta contínua no navegador.
- Three.js e OrbitControls carregam por CDN: sem internet, a esfera não renderiza (chat e automação continuam).
- Rotação de múltiplas chaves por provedor não foi portada: há uma chave por provedor.
- Geração de voz via OpenAI não foi validada com chave real.

## Licenças de terceiros

- Voz Faber (pt-BR): conjunto CC0, modelo MIT, via [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices). Veja `jarvis-voice-studio/models/VOICE-LICENSE.md`.
- Runtime `piper-tts`: **GPL-3.0**. Considere isso ao escolher a licença do projeto.
- Defina a licença do JARVIS antes de publicar (adicione um `LICENSE`).
