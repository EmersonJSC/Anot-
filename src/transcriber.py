"""
Motor de transcrição.

Encapsula o faster-whisper para transcrição de áudio/vídeo
com suporte a GPU (CUDA) e CPU, múltiplos modelos e idiomas.
"""

import os
import threading
from typing import Callable, Optional

from src.audio_processor import prepare_audio_for_transcription, get_media_info


# Modelos disponíveis com informações
AVAILABLE_MODELS = {
    "tiny": {
        "name": "Tiny",
        "params": "39M",
        "size": "~75 MB",
        "vram": "< 500 MB",
        "speed": "Muito rápido",
        "quality": "Básica",
        "description": "Testes rápidos, rascunhos",
    },
    "base": {
        "name": "Base",
        "params": "74M",
        "size": "~142 MB",
        "vram": "< 500 MB",
        "speed": "Rápido",
        "quality": "Razoável",
        "description": "Áudios claros, uso básico",
    },
    "small": {
        "name": "Small",
        "params": "244M",
        "size": "~466 MB",
        "vram": "~1 GB",
        "speed": "Moderado",
        "quality": "Boa",
        "description": "Recomendado para a maioria",
    },
    "medium": {
        "name": "Medium",
        "params": "769M",
        "size": "~1.5 GB",
        "vram": "~3 GB",
        "speed": "Lento",
        "quality": "Muito boa",
        "description": "Profissional, entrevistas",
    },
    "large-v3": {
        "name": "Large V3",
        "params": "1.55B",
        "size": "~3 GB",
        "vram": "~5 GB",
        "speed": "Muito lento",
        "quality": "Máxima",
        "description": "Máxima precisão",
    },
    "large-v3-turbo": {
        "name": "Large V3 Turbo",
        "params": "809M",
        "size": "~1.6 GB",
        "vram": "~3.5 GB",
        "speed": "Rápido",
        "quality": "Excelente",
        "description": "Melhor custo-benefício",
    },
}

# Idiomas suportados (subset dos mais comuns)
AVAILABLE_LANGUAGES = {
    "auto": "Automático (detectar)",
    "pt": "Português",
    "en": "Inglês",
    "es": "Espanhol",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
    "ja": "Japonês",
    "ko": "Coreano",
    "zh": "Chinês",
    "ru": "Russo",
    "ar": "Árabe",
    "nl": "Holandês",
    "pl": "Polonês",
    "sv": "Sueco",
    "tr": "Turco",
}


def detect_device() -> str:
    """
    Detecta o melhor dispositivo disponível (CUDA ou CPU).

    Returns:
        "cuda" se GPU NVIDIA disponível, senão "cpu".
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    # Tentar via ctranslate2 diretamente
    try:
        import ctranslate2
        if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
            return "cuda"
    except (ImportError, RuntimeError):
        pass

    return "cpu"


def get_device_info() -> dict:
    """
    Retorna informações sobre o dispositivo disponível.

    Returns:
        dict com keys: device, gpu_name, vram, cpu_name
    """
    info = {
        "device": "cpu",
        "gpu_name": "Não detectada",
        "vram": "N/A",
        "compute_type": "int8",
    }

    try:
        import torch
        if torch.cuda.is_available():
            info["device"] = "cuda"
            info["gpu_name"] = torch.cuda.get_device_name(0)
            vram_bytes = torch.cuda.get_device_properties(0).total_mem
            info["vram"] = f"{vram_bytes / (1024**3):.1f} GB"
            info["compute_type"] = "float16"
    except ImportError:
        pass

    return info


def get_recommended_model() -> str:
    """
    Recomenda o melhor modelo baseado no hardware disponível.

    Returns:
        Nome do modelo recomendado.
    """
    device_info = get_device_info()

    if device_info["device"] == "cuda":
        try:
            import torch
            vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            if vram >= 8:
                return "large-v3-turbo"
            elif vram >= 4:
                return "medium"
            else:
                return "small"
        except ImportError:
            return "small"

    # CPU: ser conservador
    return "small"


class Transcriber:
    """Motor de transcrição baseado em faster-whisper."""

    def __init__(self):
        self._model = None
        self._model_name = None
        self._device = None
        self._is_transcribing = False
        self._cancel_flag = threading.Event()

    @property
    def is_transcribing(self) -> bool:
        return self._is_transcribing

    @property
    def loaded_model(self) -> Optional[str]:
        return self._model_name

    def load_model(
        self,
        model_name: str = "small",
        device: str = "auto",
        on_status: Optional[Callable[[str], None]] = None,
    ):
        """
        Carrega um modelo Whisper.

        Args:
            model_name: Nome do modelo (tiny, base, small, medium, large-v3, large-v3-turbo)
            device: Dispositivo (auto, cpu, cuda)
            on_status: Callback para atualização de status
        """
        from faster_whisper import WhisperModel

        if device == "auto":
            device = detect_device()

        compute_type = "float16" if device == "cuda" else "int8"

        if on_status:
            on_status(f"Carregando modelo '{model_name}' em {device.upper()}...")

        self._model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
        )
        self._model_name = model_name
        self._device = device

        if on_status:
            on_status(f"Modelo '{model_name}' carregado com sucesso!")

    def transcribe(
        self,
        file_path: str,
        language: str = "auto",
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_segment: Optional[Callable[[dict], None]] = None,
    ) -> dict:
        """
        Transcreve um arquivo de áudio ou vídeo.

        Args:
            file_path: Caminho do arquivo.
            language: Código do idioma ou "auto".
            on_progress: Callback(percentual, mensagem) para progresso.
            on_status: Callback(mensagem) para status.
            on_segment: Callback(segmento) para cada segmento transcrito.

        Returns:
            dict com keys: segments, language, duration, info
        """
        if self._model is None:
            raise RuntimeError("Modelo não carregado. Chame load_model() primeiro.")

        self._is_transcribing = True
        self._cancel_flag.clear()

        try:
            # Preparar arquivo (extrair áudio se for vídeo)
            if on_status:
                on_status("Preparando arquivo...")

            audio_path = prepare_audio_for_transcription(file_path)

            # Obter duração para cálculo de progresso
            media_info = get_media_info(file_path)
            total_duration = media_info.get("duration", 0)

            if on_status:
                on_status("Transcrevendo...")

            # Configurar parâmetros
            transcribe_kwargs = {
                "beam_size": 5,
                "vad_filter": True,
            }

            if language != "auto":
                transcribe_kwargs["language"] = language

            # Executar transcrição
            raw_segments, info = self._model.transcribe(
                audio_path,
                **transcribe_kwargs,
            )

            # Processar segmentos
            segments = []
            for segment in raw_segments:
                if self._cancel_flag.is_set():
                    if on_status:
                        on_status("Transcrição cancelada.")
                    break

                seg_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
                segments.append(seg_dict)

                if on_segment:
                    on_segment(seg_dict)

                # Calcular progresso
                if on_progress and total_duration > 0:
                    progress = min(segment.end / total_duration, 1.0)
                    on_progress(
                        progress,
                        f"Transcrevendo... {progress:.0%}",
                    )

            if on_progress:
                on_progress(1.0, "Transcrição concluída!")

            if on_status:
                on_status("Transcrição concluída!")

            detected_lang = getattr(info, "language", language)

            return {
                "segments": segments,
                "language": detected_lang,
                "duration": total_duration,
                "info": {
                    "model": self._model_name,
                    "device": self._device,
                    "language_detected": detected_lang,
                    "language_probability": getattr(info, "language_probability", 0),
                    "total_segments": len(segments),
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                },
            }

        finally:
            self._is_transcribing = False

    def cancel(self):
        """Cancela a transcrição em andamento."""
        self._cancel_flag.set()

    def transcribe_async(
        self,
        file_path: str,
        language: str = "auto",
        on_progress: Optional[Callable[[float, str], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_segment: Optional[Callable[[dict], None]] = None,
        on_complete: Optional[Callable[[dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Transcreve em thread separada (não bloqueia a UI).

        Args:
            Mesmos de transcribe() + on_complete e on_error callbacks.
        """

        def _run():
            try:
                result = self.transcribe(
                    file_path=file_path,
                    language=language,
                    on_progress=on_progress,
                    on_status=on_status,
                    on_segment=on_segment,
                )
                if on_complete:
                    on_complete(result)
            except Exception as e:
                if on_error:
                    on_error(e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
