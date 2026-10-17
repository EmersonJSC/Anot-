"""
Componente de barra de progresso customizada.
"""

import customtkinter as ctk
from typing import Optional


class TranscriptionProgress(ctk.CTkFrame):
    """Barra de progresso com status e percentual para transcrição."""

    ACCENT_COLOR = "#6366f1"

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        # Status text
        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            anchor="w",
        )
        self._status_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        # Percentual
        self._percent_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e",
        )
        self._percent_label.grid(row=0, column=1, sticky="e", pady=(0, 4))

        # Barra de progresso
        self._progress_bar = ctk.CTkProgressBar(
            self,
            height=8,
            corner_radius=4,
            progress_color=self.ACCENT_COLOR,
        )
        self._progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._progress_bar.set(0)

    def set_progress(self, value: float, status: Optional[str] = None):
        """
        Atualiza o progresso.

        Args:
            value: Progresso entre 0.0 e 1.0
            status: Texto de status opcional
        """
        value = max(0.0, min(1.0, value))
        self._progress_bar.set(value)
        self._percent_label.configure(text=f"{value:.0%}")

        if status:
            self._status_label.configure(text=status)

    def set_status(self, text: str):
        """Atualiza apenas o texto de status."""
        self._status_label.configure(text=text)

    def set_indeterminate(self, status: str = "Processando..."):
        """Modo indeterminado (carregando modelo, etc)."""
        self._progress_bar.configure(mode="indeterminate")
        self._progress_bar.start()
        self._status_label.configure(text=status)
        self._percent_label.configure(text="")

    def set_determinate(self):
        """Volta ao modo determinado."""
        self._progress_bar.stop()
        self._progress_bar.configure(mode="determinate")
        self._progress_bar.set(0)

    def set_complete(self, status: str = "Transcrição concluída!"):
        """Marca como completo."""
        self.set_determinate()
        self._progress_bar.set(1.0)
        self._status_label.configure(text=f"✅ {status}")
        self._percent_label.configure(text="100%")
        self._progress_bar.configure(progress_color="#22c55e")  # verde

    def set_error(self, message: str = "Erro na transcrição"):
        """Marca como erro."""
        self.set_determinate()
        self._progress_bar.set(1.0)
        self._status_label.configure(text=f"❌ {message}")
        self._percent_label.configure(text="")
        self._progress_bar.configure(progress_color="#ef4444")  # vermelho

    def reset(self):
        """Reseta a barra para o estado inicial."""
        self.set_determinate()
        self._progress_bar.set(0)
        self._progress_bar.configure(progress_color=self.ACCENT_COLOR)
        self._status_label.configure(text="")
        self._percent_label.configure(text="")

    def show(self):
        """Mostra a barra."""
        self.grid()

    def hide(self):
        """Esconde a barra."""
        self.grid_remove()
