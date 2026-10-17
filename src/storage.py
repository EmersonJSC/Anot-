"""
Persistência de dados.

Gerencia configurações do aplicativo e histórico de transcrições
usando arquivos JSON no diretório de dados do usuário.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# Diretório de dados da aplicação
APP_DATA_DIR = os.path.join(Path.home(), ".transcritor-local")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
HISTORY_FILE = os.path.join(APP_DATA_DIR, "history.json")


# Configurações padrão
DEFAULT_CONFIG = {
    "theme": "dark",
    "default_model": "small",
    "default_language": "auto",
    "default_device": "auto",
    "output_directory": "",
    "include_timestamps": True,
    "window_width": 1100,
    "window_height": 700,
}


def _ensure_data_dir():
    """Garante que o diretório de dados existe."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)


def load_config() -> dict:
    """
    Carrega as configurações do aplicativo.
    Retorna as configurações padrão se o arquivo não existir.
    """
    _ensure_data_dir()

    config = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass

    return config


def save_config(config: dict):
    """Salva as configurações do aplicativo."""
    _ensure_data_dir()

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Erro ao salvar configurações: {e}")


def update_config(key: str, value):
    """Atualiza uma configuração específica."""
    config = load_config()
    config[key] = value
    save_config(config)


def load_history() -> list[dict]:
    """
    Carrega o histórico de transcrições.

    Returns:
        Lista de dicts com info das transcrições anteriores.
    """
    _ensure_data_dir()

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history: list[dict]):
    """Salva o histórico de transcrições."""
    _ensure_data_dir()

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Erro ao salvar histórico: {e}")


def add_to_history(
    file_name: str,
    file_path: str,
    model: str,
    language: str,
    duration: float,
    segments: list[dict],
    full_text: str,
) -> dict:
    """
    Adiciona uma transcrição ao histórico.

    Returns:
        O registro adicionado.
    """
    history = load_history()

    record = {
        "id": str(uuid.uuid4())[:8],
        "file_name": file_name,
        "file_path": file_path,
        "model": model,
        "language": language,
        "duration": round(duration, 2),
        "duration_formatted": _format_duration(duration),
        "segments_count": len(segments),
        "text_preview": full_text[:200] + "..." if len(full_text) > 200 else full_text,
        "full_text": full_text,
        "segments": segments,
        "created_at": datetime.now().isoformat(),
        "created_at_formatted": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    # Adiciona no início (mais recente primeiro)
    history.insert(0, record)

    # Limita a 100 registros
    history = history[:100]

    save_history(history)
    return record


def delete_from_history(record_id: str):
    """Remove uma transcrição do histórico pelo ID."""
    history = load_history()
    history = [h for h in history if h.get("id") != record_id]
    save_history(history)


def clear_history():
    """Limpa todo o histórico de transcrições."""
    save_history([])


def get_history_record(record_id: str) -> Optional[dict]:
    """Busca um registro específico no histórico pelo ID."""
    history = load_history()
    for record in history:
        if record.get("id") == record_id:
            return record
    return None


def get_models_cache_dir() -> str:
    """Retorna o diretório de cache dos modelos."""
    cache_dir = os.path.join(APP_DATA_DIR, "models")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _format_duration(seconds: float) -> str:
    """Formata duração em segundos para formato legível."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
