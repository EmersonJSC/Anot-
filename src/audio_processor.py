"""
Processador de áudio e vídeo.

Responsável por validar arquivos, extrair áudio de vídeos
e obter metadados de mídia usando FFmpeg.
"""

import os
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Optional


# Formatos suportados
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".opus"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".ts"}
ALL_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS


def get_supported_extensions() -> set[str]:
    """Retorna todas as extensões de arquivo suportadas."""
    return ALL_EXTENSIONS


def get_file_filter_string() -> str:
    """Retorna string de filtro para diálogos de seleção de arquivo."""
    all_exts = " ".join(f"*{ext}" for ext in sorted(ALL_EXTENSIONS))
    audio_exts = " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS))
    video_exts = " ".join(f"*{ext}" for ext in sorted(VIDEO_EXTENSIONS))
    return [
        ("Todos os formatos suportados", all_exts),
        ("Arquivos de áudio", audio_exts),
        ("Arquivos de vídeo", video_exts),
        ("Todos os arquivos", "*.*"),
    ]


def is_supported_file(file_path: str) -> bool:
    """Verifica se o arquivo tem uma extensão suportada."""
    ext = Path(file_path).suffix.lower()
    return ext in ALL_EXTENSIONS


def is_video_file(file_path: str) -> bool:
    """Verifica se o arquivo é um vídeo."""
    ext = Path(file_path).suffix.lower()
    return ext in VIDEO_EXTENSIONS


def is_audio_file(file_path: str) -> bool:
    """Verifica se o arquivo é áudio."""
    ext = Path(file_path).suffix.lower()
    return ext in AUDIO_EXTENSIONS


def _find_ffmpeg() -> Optional[str]:
    """Encontra o executável do FFmpeg no sistema."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "ffmpeg"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _find_ffprobe() -> Optional[str]:
    """Encontra o executável do FFprobe no sistema."""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "ffprobe"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def check_ffmpeg_available() -> bool:
    """Verifica se o FFmpeg está instalado e disponível."""
    return _find_ffmpeg() is not None


def get_media_info(file_path: str) -> dict:
    """
    Obtém informações de mídia do arquivo usando ffprobe.

    Retorna:
        dict com keys: duration, format, codec, sample_rate, channels, file_size
    """
    info = {
        "duration": 0.0,
        "duration_formatted": "00:00",
        "format": "",
        "codec": "",
        "sample_rate": 0,
        "channels": 0,
        "file_size": 0,
        "file_size_formatted": "",
        "file_name": Path(file_path).name,
    }

    # Tamanho do arquivo
    try:
        file_size = os.path.getsize(file_path)
        info["file_size"] = file_size
        info["file_size_formatted"] = _format_file_size(file_size)
    except OSError:
        pass

    # Formato pela extensão
    info["format"] = Path(file_path).suffix.lower().lstrip(".")

    # Tentar obter metadados via ffprobe
    ffprobe = _find_ffprobe()
    if ffprobe is None:
        return info

    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            # Duração
            if "format" in data and "duration" in data["format"]:
                duration = float(data["format"]["duration"])
                info["duration"] = duration
                info["duration_formatted"] = _format_duration(duration)

            # Info do stream de áudio
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    info["codec"] = stream.get("codec_name", "")
                    info["sample_rate"] = int(stream.get("sample_rate", 0))
                    info["channels"] = int(stream.get("channels", 0))
                    break

    except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, KeyError):
        pass

    return info


def extract_audio_from_video(
    video_path: str,
    output_dir: Optional[str] = None,
) -> Optional[str]:
    """
    Extrai a faixa de áudio de um arquivo de vídeo.

    Args:
        video_path: Caminho do arquivo de vídeo.
        output_dir: Diretório de saída. Se None, usa temp.

    Returns:
        Caminho do arquivo WAV extraído, ou None em caso de erro.
    """
    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(
            "FFmpeg não encontrado. Instale com: sudo apt install ffmpeg"
        )

    if output_dir is None:
        output_dir = tempfile.gettempdir()

    # Nome do arquivo de saída
    stem = Path(video_path).stem
    output_path = os.path.join(output_dir, f"{stem}_audio.wav")

    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-i", video_path,
                "-vn",                    # Sem vídeo
                "-acodec", "pcm_s16le",   # WAV PCM 16-bit
                "-ar", "16000",           # 16kHz (ideal para Whisper)
                "-ac", "1",               # Mono
                "-y",                     # Sobrescrever sem perguntar
                output_path,
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min máximo
        )

        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            return None

    except subprocess.TimeoutExpired:
        return None


def prepare_audio_for_transcription(file_path: str) -> str:
    """
    Prepara um arquivo de mídia para transcrição.

    Se for vídeo, extrai o áudio.
    Se for áudio, retorna o caminho original (faster-whisper lida nativamente).

    Returns:
        Caminho do arquivo de áudio pronto para transcrição.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    if not is_supported_file(file_path):
        raise ValueError(
            f"Formato não suportado: {Path(file_path).suffix}. "
            f"Formatos aceitos: {', '.join(sorted(ALL_EXTENSIONS))}"
        )

    if is_video_file(file_path):
        audio_path = extract_audio_from_video(file_path)
        if audio_path is None:
            raise RuntimeError(
                f"Falha ao extrair áudio do vídeo: {file_path}. "
                "Verifique se o FFmpeg está instalado."
            )
        return audio_path

    # Arquivo de áudio — faster-whisper aceita diretamente
    return file_path


def _format_duration(seconds: float) -> str:
    """Formata duração em segundos para HH:MM:SS ou MM:SS."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo em formato legível."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
