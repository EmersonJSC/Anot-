"""
Gerenciador de modelos locais do Whisper.

Verifica se os modelos estão em cache local e permite baixá-los sob demanda
diretamente pela interface, com progresso em porcentagem (%).
"""

import threading
from typing import Callable, Optional
import huggingface_hub
from faster_whisper.utils import _MODELS, download_model
from tqdm.auto import tqdm

MODELS_INFO = {
    "tiny": {
        "label": "Tiny",
        "size": "~75 MB",
        "desc": "Ultra rápido • PC básico",
    },
    "base": {
        "label": "Base",
        "size": "~142 MB",
        "desc": "Rápido • Uso comum",
    },
    "small": {
        "label": "Small",
        "size": "~466 MB",
        "desc": "Equilibrado • Recomendado",
    },
    "medium": {
        "label": "Medium",
        "size": "~1.5 GB",
        "desc": "Alta precisão",
    },
    "large-v3": {
        "label": "Large v3",
        "size": "~3.0 GB",
        "desc": "Máxima precisão",
    },
}


def is_model_downloaded(model_name: str) -> bool:
    """Verifica se o modelo já está salvo localmente no disco."""
    try:
        download_model(model_name, local_files_only=True)
        return True
    except Exception:
        return False


def get_model_status_label(model_name: str) -> str:
    """Retorna o texto de status formatado para o seletor da UI."""
    info = MODELS_INFO.get(model_name, {})
    size = info.get("size", "")
    if is_model_downloaded(model_name):
        return f"{model_name} • ✅ Baixado"
    else:
        return f"{model_name} • 📥 {size}"


def download_model_with_progress(
    model_name: str,
    on_progress: Optional[Callable[[float, str], None]] = None,
    on_success: Optional[Callable[[], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
):
    """
    Baixa o modelo em background e reporta porcentagem de 0% a 100%.
    """
    def _run():
        try:
            repo_id = _MODELS.get(model_name, model_name)
            allow_patterns = [
                "config.json",
                "preprocessor_config.json",
                "model.bin",
                "tokenizer.json",
                "vocabulary.*",
            ]

            class UIProgressTqdm(tqdm):
                def update(self, n=1):
                    super().update(n)
                    if self.total and self.total > 100_000 and on_progress:
                        pct = (self.n / self.total) * 100
                        mb_done = self.n / (1024 * 1024)
                        mb_total = self.total / (1024 * 1024)
                        text = f"{pct:.0f}% ({mb_done:.1f} MB / {mb_total:.1f} MB)"
                        on_progress(pct, text)

            huggingface_hub.snapshot_download(
                repo_id,
                allow_patterns=allow_patterns,
                tqdm_class=UIProgressTqdm,
            )

            if on_progress:
                on_progress(100.0, "100% (Concluído)")
            if on_success:
                on_success()

        except Exception as e:
            if on_error:
                on_error(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread
