# 📦 CACHE — Referência Técnica Estável

> Referência de arquitetura, APIs e convenções. Muda raramente.
> Criado em: 2026-10-17

---

## Arquitetura & Fluxo ("Chat Silencioso")

```
[ Usuário seleciona/arrasta Áudio ou Vídeo ]
                     │
                     ▼
       ┌───────────────────────────┐
       │     "Chat Silencioso"     │
       │    (Interface Nativa)     │
       └─────────────┬─────────────┘
                     │ (Processamento Local)
                     ▼
       ┌───────────────────────────┐
       │       faster-whisper      │
       │    (Inference Local CPU)  │
       └─────────────┬─────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Salva em disco   │    │ Abre e exibe no  │
│ (.txt / .srt)    │    │ feed da tela     │
└──────────────────┘    └──────────────────┘
```

---

## APIs dos Módulos Backend

### `src/transcriber.py`
```python
# Constantes
AVAILABLE_MODELS: dict[str, dict]  # tiny,base,small,medium,large-v3,large-v3-turbo
AVAILABLE_LANGUAGES: dict[str, str]  # código→nome ("pt"→"Português")

# Funções
detect_device() -> str  # "cuda" ou "cpu"
get_device_info() -> dict  # device, gpu_name, vram, compute_type
get_recommended_model() -> str

# Classe
class Transcriber:
    is_transcribing: bool  # property
    loaded_model: str | None  # property
    load_model(model_name, device="auto", on_status=None)
    transcribe(file_path, language="auto", on_progress, on_status, on_segment) -> dict
    # retorno: {segments: [{start,end,text}], language, duration, info}
    transcribe_async(file_path, language, on_progress, on_status, on_segment, on_complete, on_error)
    cancel()
```

### `src/audio_processor.py`
```python
AUDIO_EXTENSIONS: set  # .wav,.mp3,.flac,.m4a,.aac,.ogg,.wma,.opus
VIDEO_EXTENSIONS: set  # .mp4,.mkv,.avi,.mov,.webm,.flv,.wmv,.ts
ALL_EXTENSIONS: set

get_supported_extensions() -> set
get_file_filter_string() -> list[tuple]  # para filedialog
is_supported_file(path) -> bool
is_video_file(path) -> bool
is_audio_file(path) -> bool
check_ffmpeg_available() -> bool
get_media_info(path) -> dict  # duration, format, codec, file_size, etc.
prepare_audio_for_transcription(path) -> str  # extrai áudio se vídeo
```

### `src/exporter.py`
```python
export_txt(segments, output_path, include_timestamps=True) -> str
export_srt(segments, output_path) -> str
export_json(segments, output_path, metadata=None) -> str
get_full_text(segments) -> str
get_formatted_text(segments, include_timestamps=True) -> str
get_default_output_path(input_file, extension, output_dir=None) -> str
```

### `src/storage.py`
```python
APP_DATA_DIR = "~/.transcritor-local/"
DEFAULT_CONFIG: dict  # theme, default_model, default_language, etc.

load_config() -> dict
save_config(config: dict)
update_config(key, value)
load_history() -> list[dict]
add_to_history(file_name, file_path, model, language, duration, segments, full_text) -> dict
delete_from_history(record_id)
clear_history()
get_history_record(record_id) -> dict | None
get_models_cache_dir() -> str
```

---

## Convenções de UI (CustomTkinter)

### Padrão de View
```python
class MinhaView(ctk.CTkFrame):
    def __init__(self, parent, app_reference):
        super().__init__(parent, fg_color="transparent")
        self.app = app_reference  # acesso ao Transcriber, Storage, etc.
        self._build_ui()
```

### Layout
- **Sidebar**: coluna 0, largura fixa 200px, `corner_radius=0`
- **Content**: coluna 1, `weight=1` (expande)
- **Grid**: usar `grid_rowconfigure/columnconfigure` com `weight=1`
- **Sticky**: `"nsew"` para expandir em todas direções

### Tema/Cores
- Modo padrão: `"dark"`
- Color theme: `"blue"`
- Cor destaque customizada: `#6366f1` (indigo/roxo)
- Fontes: `CTkFont(family="Segoe UI"/"Helvetica", size=N, weight="bold")`

### Threading
- Transcrição roda via `transcribe_async()` (thread separada)
- Atualizar UI da thread: usar `self.after(0, lambda: ...)` ou `self.after(ms, fn)`

---

## Estrutura de Diretórios

```
Transcritor local/
├── main.py
├── requirements.txt
├── README.md
├── PROJETO.md
├── RAM.md              ← este doc (memória de trabalho)
├── CACHE.md            ← este doc (referência estável)
├── src/
│   ├── __init__.py
│   ├── transcriber.py
│   ├── audio_processor.py
│   ├── exporter.py
│   ├── storage.py
│   └── ui/
│       ├── __init__.py
│       ├── app.py
│       ├── views/
│       │   ├── __init__.py
│       │   ├── transcribe_view.py
│       │   ├── history_view.py
│       │   └── settings_view.py
│       └── components/
│           ├── __init__.py
│           ├── sidebar.py
│           ├── file_drop_zone.py
│           └── progress_bar.py
├── models/             # cache local de modelos whisper
└── output/             # transcrições exportadas
```

---

## Dependências

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| `customtkinter` | >=5.2.0 | Interface gráfica nativa |
| `faster-whisper` | >=1.0.0 | Motor de transcrição (inclui CTranslate2) |
| `ffmpeg` (sistema) | qualquer | Processamento de mídia (opcional p/ áudio puro) |

---

## Config Padrão (`~/.transcritor-local/config.json`)
```json
{
  "theme": "dark",
  "default_model": "small",
  "default_language": "auto",
  "default_device": "auto",
  "output_directory": "",
  "include_timestamps": true,
  "window_width": 1100,
  "window_height": 700
}
```
