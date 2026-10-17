"""
Exportador de transcrições.

Suporta exportação em TXT (texto puro), SRT (legendas) e JSON (estruturado).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def export_txt(
    segments: list[dict],
    output_path: str,
    include_timestamps: bool = True,
) -> str:
    """
    Exporta transcrição como arquivo de texto puro.

    Args:
        segments: Lista de segmentos com keys: start, end, text
        output_path: Caminho do arquivo de saída (.txt)
        include_timestamps: Se True, inclui timestamps por segmento

    Returns:
        Caminho do arquivo criado.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            if include_timestamps:
                start = _format_timestamp_simple(segment["start"])
                end = _format_timestamp_simple(segment["end"])
                f.write(f"[{start} → {end}] {segment['text'].strip()}\n")
            else:
                f.write(f"{segment['text'].strip()}\n")

    return output_path


def export_srt(
    segments: list[dict],
    output_path: str,
) -> str:
    """
    Exporta transcrição como arquivo de legendas SRT.

    Args:
        segments: Lista de segmentos com keys: start, end, text
        output_path: Caminho do arquivo de saída (.srt)

    Returns:
        Caminho do arquivo criado.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = _format_timestamp_srt(segment["start"])
            end = _format_timestamp_srt(segment["end"])
            text = segment["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n")
            f.write("\n")

    return output_path


def export_json(
    segments: list[dict],
    output_path: str,
    metadata: Optional[dict] = None,
) -> str:
    """
    Exporta transcrição como arquivo JSON estruturado.

    Args:
        segments: Lista de segmentos com keys: start, end, text
        output_path: Caminho do arquivo de saída (.json)
        metadata: Metadados opcionais (arquivo, modelo, idioma, etc.)

    Returns:
        Caminho do arquivo criado.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Texto completo concatenado
    full_text = " ".join(seg["text"].strip() for seg in segments)

    data = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "total_segments": len(segments),
            "total_duration": segments[-1]["end"] if segments else 0,
            **(metadata or {}),
        },
        "full_text": full_text,
        "segments": [
            {
                "index": i,
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "duration": round(seg["end"] - seg["start"], 3),
                "text": seg["text"].strip(),
            }
            for i, seg in enumerate(segments, start=1)
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return output_path


def get_full_text(segments: list[dict]) -> str:
    """Retorna o texto completo da transcrição concatenado."""
    return " ".join(seg["text"].strip() for seg in segments)


def get_formatted_text(segments: list[dict], include_timestamps: bool = True) -> str:
    """Retorna o texto formatado da transcrição como string."""
    lines = []
    for segment in segments:
        if include_timestamps:
            start = _format_timestamp_simple(segment["start"])
            end = _format_timestamp_simple(segment["end"])
            lines.append(f"[{start} → {end}] {segment['text'].strip()}")
        else:
            lines.append(segment["text"].strip())
    return "\n".join(lines)


def get_default_output_path(
    input_file: str,
    extension: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Gera um caminho de saída padrão baseado no arquivo de entrada.

    Args:
        input_file: Caminho do arquivo de entrada.
        extension: Extensão do arquivo de saída (ex: ".txt", ".srt", ".json")
        output_dir: Diretório de saída. Se None, usa o mesmo dir do input.

    Returns:
        Caminho do arquivo de saída.
    """
    input_path = Path(input_file)

    if output_dir is None:
        output_dir = str(input_path.parent)

    if not extension.startswith("."):
        extension = f".{extension}"

    stem = input_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{stem}_transcricao_{timestamp}{extension}"

    return os.path.join(output_dir, filename)


def _format_timestamp_simple(seconds: float) -> str:
    """Formata timestamp para exibição simples: MM:SS.ms ou HH:MM:SS.ms"""
    total_seconds = int(seconds)
    milliseconds = int((seconds - total_seconds) * 100)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:02d}"
    return f"{minutes:02d}:{secs:02d}.{milliseconds:02d}"


def _format_timestamp_srt(seconds: float) -> str:
    """Formata timestamp no padrão SRT: HH:MM:SS,mmm"""
    total_seconds = int(seconds)
    milliseconds = int((seconds - total_seconds) * 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
