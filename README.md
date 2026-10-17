# 🎙️ Transcritor Local

**Transcritor de áudio e vídeo para texto — 100% offline, no estilo "Chat Silencioso".**

Aplicação desktop nativa com interface simples e moderna: você não digita conversas, apenas envia arquivos de áudio ou vídeo. O app processa localmente, salva o arquivo de texto no disco e exibe a transcrição na hora na tela.

---

## ✨ Funcionalidades

- 💬 **Conceito "Chat Silencioso"** — Interface limpa e minimalista: solte o áudio/vídeo, o app transcreve, salva o arquivo de texto e abre o resultado na tela.
- 🔒 **100% Offline** — Nenhum dado sai da sua máquina. Zero conexão com a internet após o download do modelo.
- 📁 **Salvamento Automático** — Salva automaticamente o arquivo `.txt` no diretório de saída definido.
- 🎵 **Áudio e Vídeo** — Suporte a múltiplos formatos: MP3, WAV, FLAC, M4A, OGG, MP4, MKV, AVI, MOV, WebM.
- 🧠 **Modelos Locais** — Utiliza modelos Whisper (OpenAI) otimizados via `faster-whisper` (CTranslate2).
- 🖥️ **Interface Gráfica Nativa** — Construída com CustomTkinter, visual moderno com Dark Mode.
- ⚡ **Otimizado para CPU & GPU** — Roda com eficiência em processadores comuns via quantização INT8.

---

## 🧠 Modelos Disponíveis

O projeto utiliza os modelos Whisper via **faster-whisper**, uma implementação otimizada com CTranslate2 que oferece até **4x mais velocidade** e **metade do uso de memória** comparado ao Whisper original.

| Modelo | Parâmetros | Disco | VRAM (GPU)¹ | RAM (CPU)¹ | Velocidade | Precisão | Melhor Para |
|--------|-----------|-------|------------|-----------|-----------|----------|-------------|
| `tiny` | 39M | ~75 MB | < 500 MB | ~1 GB | ⚡⚡⚡⚡⚡ | ⭐⭐ | Testes rápidos, rascunhos |
| `base` | 74M | ~142 MB | < 500 MB | ~1 GB | ⚡⚡⚡⚡ | ⭐⭐⭐ | Áudios claros, uso diário básico |
| `small` | 244M | ~466 MB | ~1 GB | ~2 GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | **Recomendado para a maioria** |
| `medium` | 769M | ~1.5 GB | ~3 GB | ~5 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Profissional, entrevistas |
| `large-v3` | 1.55B | ~3.0 GB | ~5 GB | ~10 GB | ⚡ | ⭐⭐⭐⭐⭐ | Máxima precisão, idiomas raros |
| `large-v3-turbo` | 809M | ~1.6 GB | ~3.5 GB | ~6 GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | **Melhor custo-benefício** |

> ¹ Valores aproximados com quantização INT8 via faster-whisper.

### 🎯 Qual modelo escolher?

| Seu PC tem... | Modelo recomendado |
|---------------|-------------------|
| Apenas CPU, pouca RAM (< 4 GB) | `tiny` ou `base` |
| CPU com 8 GB+ de RAM | `small` |
| GPU NVIDIA com 4 GB VRAM | `small` ou `medium` |
| GPU NVIDIA com 6-8 GB VRAM | `large-v3-turbo` ⭐ |
| GPU NVIDIA com 10 GB+ VRAM | `large-v3` |

---

## 📋 Requisitos do Sistema

### Mínimos
- **OS:** Linux, Windows 10+, macOS
- **Python:** 3.9+
- **RAM:** 4 GB
- **Disco:** 500 MB livres (para o modelo `small`)

### Recomendados
- **RAM:** 8 GB+
- **GPU:** NVIDIA com suporte CUDA (GTX 1060 ou superior)
- **VRAM:** 4 GB+ (para modelos `medium` e maiores)
- **Disco:** 5 GB livres (para vários modelos)

### Dependências do Sistema
- **FFmpeg** — Para processamento de formatos de áudio e vídeo
- **CUDA Toolkit** (opcional) — Para aceleração via GPU NVIDIA

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd transcritor-local
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Instale o FFmpeg (se necessário)

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# macOS
brew install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

### 5. Execute a aplicação

```bash
python main.py
```

---

## 🎮 Como Usar

1. **Abra a aplicação** executando `python main.py`
2. **Selecione o modelo** adequado ao seu hardware (veja a tabela acima)
3. **Escolha o arquivo** de áudio ou vídeo para transcrever
4. **Selecione o idioma** ou deixe em "Automático" para detecção automática
5. **Clique em "Transcrever"** e aguarde o processamento
6. **Visualize e exporte** o texto transcrito no formato desejado

---

## 📁 Estrutura do Projeto

```
transcritor-local/
├── main.py                  # Ponto de entrada da aplicação
├── requirements.txt         # Dependências Python
├── README.md                # Este arquivo
├── PROJETO.md               # Documento detalhado do projeto
├── src/
│   ├── __init__.py
│   ├── transcriber.py       # Motor de transcrição (faster-whisper)
│   ├── audio_processor.py   # Processamento/conversão de áudio
│   ├── exporter.py          # Exportação (TXT, SRT, JSON)
│   └── ui/
│       ├── __init__.py
│       └── app.py           # Interface gráfica
├── models/                  # Modelos baixados (cache local)
└── output/                  # Arquivos transcritos
```

---

## 🛠️ Tecnologias

| Tecnologia | Propósito |
|-----------|----------|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Motor de transcrição (Whisper + CTranslate2) |
| [Gradio](https://gradio.app/) ou [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface gráfica |
| [FFmpeg](https://ffmpeg.org/) | Processamento de mídia |
| Python 3.9+ | Linguagem principal |

---

## 📜 Licença

Este projeto é de uso pessoal/interno. Veja o arquivo `LICENSE` para detalhes.

---

## 🤝 Contribuição

Contribuições são bem-vindas! Abra uma issue ou envie um pull request.

---

> **Nota:** Os modelos Whisper são baixados automaticamente no primeiro uso e ficam em cache local. Após o download inicial, nenhuma conexão com a internet é necessária.
