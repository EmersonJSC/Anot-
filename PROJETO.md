# 📄 Documento do Projeto — Transcritor Local

**Versão:** 1.0  
**Data:** Outubro 2026  
**Status:** Em Desenvolvimento  

---

## 1. Visão Geral

O **Transcritor Local** é uma aplicação desktop que converte arquivos de áudio e vídeo em texto utilizando modelos de inteligência artificial executados inteiramente na máquina do usuário, **sem necessidade de conexão com a internet**.

### 1.1 Objetivo e Conceito: O "Chat Silencioso"

O objetivo é uma ferramenta extremamente direta, limpa e descomplicada:
- **Conceito "Chat Silencioso":** A interface funciona no estilo de um chat minimalista. Não há digitação de conversas ou comandos complexos. O usuário apenas entrega (arrasta/seleciona) um arquivo de áudio ou vídeo.
- **Processamento Local:** O modelo escolhido processa o arquivo offline.
- **Entrega Dupla:**
  1. **Salva automaticamente** o arquivo de texto (.txt ou .srt) no disco (em uma pasta designada).
  2. **Abre e exibe** o texto transcrito imediatamente na interface para leitura instantânea e cópia rápida.

### 1.2 Público-Alvo

- Profissionais que lidam com transcrição (jornalistas, pesquisadores, advogados)
- Estudantes que precisam transcrever aulas e palestras
- Criadores de conteúdo que necessitam de legendas
- Qualquer pessoa que valorize privacidade e não queira enviar áudios para serviços em nuvem

### 1.3 Princípios Fundamentais

| Princípio | Descrição |
|-----------|-----------|
| **Chat Silencioso** | Interface limpa: recebe mídia, processa e devolve o texto formatado. |
| **Privacidade Total** | Zero dados enviados pela internet. Tudo roda localmente na CPU/GPU. |
| **Offline First** | Funciona 100% offline após o download inicial do modelo. |
| **Simplicidade Máxima** | Sem telas ou menus desnecessários. Modelo + Arquivo = Texto entregue. |
| **Persistência Direta** | Transcreveu? Já salva o arquivo no disco e mostra na tela. |

---

## 2. Arquitetura Técnica

### 2.1 Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────┐
│                    Interface Gráfica                      │
│              (Gradio / CustomTkinter)                     │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Seleção de  │  │  Configuração│  │  Visualização  │  │
│  │   Arquivos    │  │  do Modelo   │  │  de Resultados │  │
│  └──────┬───────┘  └──────┬───────┘  └───────▲────────┘  │
│         │                 │                   │           │
├─────────┼─────────────────┼───────────────────┼──────────┤
│         ▼                 ▼                   │           │
│  ┌──────────────────────────────────────┐     │           │
│  │        Processador de Áudio          │     │           │
│  │           (FFmpeg / PyAV)            │     │           │
│  └──────────────┬───────────────────────┘     │           │
│                 │                              │           │
│                 ▼                              │           │
│  ┌──────────────────────────────────────┐     │           │
│  │       Motor de Transcrição           │     │           │
│  │         (faster-whisper)             │─────┘           │
│  │      CTranslate2 + Whisper           │                 │
│  └──────────────┬───────────────────────┘                 │
│                 │                                          │
│                 ▼                                          │
│  ┌──────────────────────────────────────┐                 │
│  │           Exportador                  │                 │
│  │       (TXT / SRT / JSON)             │                 │
│  └──────────────────────────────────────┘                 │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **Motor de IA** | faster-whisper (CTranslate2) | 4x mais rápido que Whisper original, metade da VRAM |
| **Modelos** | Whisper (tiny → large-v3) | Estado da arte em STT, multilíngue, gratuito |
| **Interface** | Gradio ou CustomTkinter | Interface moderna, fácil de desenvolver |
| **Áudio** | FFmpeg / PyAV | Suporte universal a formatos de mídia |
| **Linguagem** | Python 3.9+ | Ecossistema rico para ML e interfaces |

### 2.3 Por que faster-whisper?

Após pesquisa das alternativas disponíveis, **faster-whisper** foi escolhido como motor principal pelos seguintes motivos:

| Critério | Whisper (original) | faster-whisper | whisper.cpp |
|----------|-------------------|---------------|-------------|
| Velocidade | 1x (base) | **4-5x** | 3-4x |
| Uso de VRAM | Alto | **~50% menor** | Mínimo |
| Precisão | Referência | **Idêntica** | Idêntica |
| Ecossistema Python | Nativo | **Nativo** | Requer bindings |
| GPU NVIDIA | ✅ | **✅ Otimizado** | ⚠️ Parcial |
| CPU | ✅ | **✅ INT8** | ✅ GGML |
| Facilidade de uso | Alta | **Alta** | Média |

**Alternativas consideradas:**
- **whisper.cpp** — Excelente para Apple Silicon e dispositivos embarcados, mas o ecossistema Python é limitado.
- **WhisperX** — Adiciona diarização (identificação de falantes), mas adiciona complexidade e dependências.
- **NVIDIA Parakeet** — Ótima performance, mas focado em inglês e requer hardware NVIDIA.

---

## 3. Modelos e Hardware

### 3.1 Tabela de Modelos

| Modelo | Params | Disco | VRAM (INT8) | RAM (CPU) | Vel. Relativa | WER (pt-BR)* |
|--------|--------|-------|------------|-----------|---------------|-------------|
| `tiny` | 39M | 75 MB | < 500 MB | ~1 GB | ~32x | Alto |
| `base` | 74M | 142 MB | < 500 MB | ~1 GB | ~16x | Médio-Alto |
| `small` | 244M | 466 MB | ~1 GB | ~2 GB | ~6x | Médio |
| `medium` | 769M | 1.5 GB | ~3 GB | ~5 GB | ~2x | Baixo |
| `large-v3` | 1.55B | 3.0 GB | ~5 GB | ~10 GB | ~1x | Muito Baixo |
| `large-v3-turbo` | 809M | 1.6 GB | ~3.5 GB | ~6 GB | ~8x | Baixo |

> *WER = Word Error Rate (taxa de erro por palavra). Menor = melhor.

### 3.2 Perfis de Hardware Recomendados

#### 🖥️ PC Básico (sem GPU dedicada)
- **CPU:** Qualquer processador moderno (Intel i3+ / AMD Ryzen 3+)
- **RAM:** 4-8 GB
- **Modelo:** `tiny` ou `base`
- **Expectativa:** Transcrição ~4-8x mais lenta que tempo real
- **Uso:** Rascunhos rápidos, áudios curtos e claros

#### 💻 Notebook/PC Intermediário
- **CPU:** Intel i5+ / AMD Ryzen 5+
- **RAM:** 8-16 GB
- **Modelo:** `small` (CPU) ou `medium` (se GPU disponível)
- **Expectativa:** Transcrição ~2-4x velocidade real (CPU), mais rápido com GPU
- **Uso:** Uso diário, boa precisão para português

#### 🎮 PC Gamer / Workstation (GPU NVIDIA)
- **GPU:** GTX 1060+ / RTX série (4+ GB VRAM)
- **RAM:** 16 GB+
- **Modelo:** `large-v3-turbo` ou `large-v3`
- **Expectativa:** Transcrição ~8-12x velocidade real
- **Uso:** Máxima precisão, grandes volumes, múltiplos idiomas

---

## 4. Funcionalidades Detalhadas

### 4.1 MVP (Versão 1.0)

- [ ] **Seleção de arquivos** — Navegação por diálogos do sistema
- [ ] **Seleção de modelo** — Dropdown com modelos disponíveis
- [ ] **Detecção de hardware** — Auto-detectar GPU/CPU e sugerir modelo
- [ ] **Transcrição básica** — Converter áudio/vídeo para texto
- [ ] **Barra de progresso** — Feedback visual durante transcrição
- [ ] **Visualização do texto** — Exibir resultado com timestamps
- [ ] **Exportação TXT** — Salvar transcrição em texto puro
- [ ] **Exportação SRT** — Salvar como arquivo de legendas
- [ ] **Seleção de idioma** — Escolher idioma ou detecção automática

### 4.2 Versão 2.0 (Futuro)

- [ ] **Processamento em lote** — Transcrever múltiplos arquivos
- [ ] **Exportação JSON** — Formato estruturado com metadados
- [ ] **Gravação direta** — Gravar áudio do microfone e transcrever
- [ ] **Diarização** — Identificar diferentes falantes (via WhisperX/Pyannote)
- [ ] **Editor de texto** — Editar transcrição na interface
- [ ] **Atalhos de teclado** — Controlar reprodução durante edição
- [ ] **Tradução** — Traduzir áudio para inglês automaticamente
- [ ] **Temas** — Modo claro e escuro

---

## 5. Formatos Suportados

### 5.1 Entrada (Áudio)
| Formato | Extensão | Suporte |
|---------|----------|---------|
| WAV | `.wav` | ✅ Nativo |
| MP3 | `.mp3` | ✅ Via FFmpeg |
| FLAC | `.flac` | ✅ Via FFmpeg |
| AAC/M4A | `.m4a`, `.aac` | ✅ Via FFmpeg |
| OGG/Vorbis | `.ogg` | ✅ Via FFmpeg |
| WMA | `.wma` | ✅ Via FFmpeg |

### 5.2 Entrada (Vídeo)
| Formato | Extensão | Suporte |
|---------|----------|---------|
| MP4 | `.mp4` | ✅ Extrai áudio via FFmpeg |
| MKV | `.mkv` | ✅ Extrai áudio via FFmpeg |
| AVI | `.avi` | ✅ Extrai áudio via FFmpeg |
| MOV | `.mov` | ✅ Extrai áudio via FFmpeg |
| WebM | `.webm` | ✅ Extrai áudio via FFmpeg |

### 5.3 Saída
| Formato | Extensão | Descrição |
|---------|----------|-----------|
| Texto Puro | `.txt` | Transcrição sem formatação |
| Legendas SRT | `.srt` | Formato padrão de legendas com timestamps |
| JSON | `.json` | Dados estruturados com metadados e timestamps |

---

## 6. Interface do Usuário (O "Chat Silencioso")

A interface é focada na objetividade. Não há menus complexos ou telas confusas:
- **Topo / Barra de Ferramentas:**
  - **Seletor e Gerenciador de Modelos:** Mostra os modelos e o status de cada um (ex: `tiny ✅ (Baixado)`, `small 📥 (Baixar 466 MB)`). O usuário pode baixar modelos novos com **1 clique**, sem abrir terminal e sem que o app venha pesado de fábrica.
  - **Pasta de Destino:** Onde os arquivos `.txt` serão salvos automaticamente.
- **Área Central (Feed do Chat):** Exibe as transcrições como balões ou cartões de mensagem. Cada áudio/vídeo enviado gera um bloco com:
  - Nome do arquivo e duração.
  - Texto transcrito em tempo real ou ao finalizar.
  - Botão de copiar texto e atalho para abrir o arquivo `.txt` gerado no disco.
- **Rodapé (Entrada do Chat Silencioso):** Um campo de entrada intuitivo onde o usuário clica ou arrasta os arquivos de áudio/vídeo diretamente.

### 6.1 Layout Conceitual da Interface

```
┌───────────────────────────────────────────────────────────────┐
│ 🎙️ Transcritor Local — Chat Silencioso                  ─ □ ✕ │
├───────────────────────────────────────────────────────────────┤
│ 🧠 Modelo: [ small (Recomendado) ▾ ]    📁 Destino: [ ~/Transcrições ▾ ]
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 👤 Você enviou: entrevista_reuniao.mp3 (04:15)          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ 🤖 Transcrição concluída:                               │  │
│  │                                                         │  │
│  │ "Bom dia a todos. Vamos iniciar a reunião de alinhamento│  │
│  │ do projeto do transcritor local. O ponto principal é... │  │
│  │ garantir que tudo funcione sem conexão de rede..."      │  │
│  │                                                         │  │
│  │ [📋 Copiar Texto]  [📄 Abrir Arquivo Salvo (.txt)]      │  │
│  │ 💾 Salvo em: ~/Transcrições/entrevista_reuniao.txt       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│ 📎 [ Arraste seu áudio ou vídeo aqui, ou clique para anexar ] │
└───────────────────────────────────────────────────────────────┘
```

---

## 7. Fluxo de Processamento

```
Usuário seleciona arquivo
         │
         ▼
┌──────────────────┐
│ Verificar formato │
│ do arquivo        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ É vídeo?         │─Sim─▶ Extrair áudio    │
│                  │     │ (FFmpeg)          │
└────────┬─────────┘     └────────┬─────────┘
         │ Não                     │
         ▼                         ▼
┌──────────────────┐
│ Converter para    │
│ formato otimizado │
│ (16kHz, mono)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Carregar modelo   │
│ faster-whisper    │
│ (cache local)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Transcrever       │
│ (segmento a       │
│  segmento)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Exibir resultado  │
│ com timestamps    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Exportar          │
│ (TXT/SRT/JSON)    │
└──────────────────┘
```

---

## 8. Dependências Python

```
faster-whisper>=1.0.0      # Motor de transcrição
gradio>=4.0.0               # Interface gráfica (Opção A)
# customtkinter>=5.0.0      # Interface gráfica (Opção B)
ffmpeg-python>=0.2.0        # Integração FFmpeg
```

---

## 9. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Hardware insuficiente | Transcrição lenta ou falha | Detecção automática + sugestão de modelo |
| Modelo não baixado | Sem funcionar offline | Download guiado no primeiro uso |
| Áudio com ruído | Baixa precisão | Recomendação de modelos maiores |
| Formato não suportado | Erro na importação | Validação prévia + mensagem clara |
| CUDA não disponível | Sem aceleração GPU | Fallback automático para CPU |

---

## 10. Cronograma Estimado

| Fase | Tarefas | Duração |
|------|---------|---------|
| **Fase 1** | Documentação + Setup do projeto | ✅ Concluído |
| **Fase 2** | Motor de transcrição (faster-whisper) | 1-2 dias |
| **Fase 3** | Interface gráfica básica | 1-2 dias |
| **Fase 4** | Exportação (TXT, SRT) | 1 dia |
| **Fase 5** | Testes e refinamento | 1-2 dias |
| **Fase 6** | Funcionalidades extras (v2.0) | Contínuo |

---

## 11. Referências

- [OpenAI Whisper](https://github.com/openai/whisper) — Modelo original
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — Implementação otimizada
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — Port em C/C++
- [WhisperX](https://github.com/m-bain/whisperX) — Whisper com diarização
- [Gradio](https://gradio.app/) — Framework de interface
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Tkinter moderno
