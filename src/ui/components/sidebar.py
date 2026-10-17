"""
Componente de sidebar (barra lateral de navegação).
"""

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    """Barra lateral com navegação entre telas."""

    # Cor de destaque (indigo)
    ACCENT_COLOR = "#6366f1"
    ACCENT_HOVER = "#818cf8"

    def __init__(self, parent, on_navigate=None):
        super().__init__(parent, width=220, corner_radius=0)
        self.on_navigate = on_navigate
        self._active_button = None
        self._buttons = {}

        self.grid_rowconfigure(6, weight=1)  # espaço flexível antes do rodapé
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        # ── Logo / Título ──
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(25, 5), sticky="ew")

        ctk.CTkLabel(
            logo_frame,
            text="🎙️",
            font=ctk.CTkFont(size=32),
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="anotô",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Local & Offline",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="w")

        # ── Separador ──
        separator = ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray30"))
        separator.grid(row=1, column=0, padx=15, pady=(15, 10), sticky="ew")

        # ── Navegação ──
        nav_label = ctk.CTkLabel(
            self,
            text="NAVEGAÇÃO",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray",
        )
        nav_label.grid(row=2, column=0, padx=25, pady=(5, 5), sticky="w")

        # Botões de navegação
        nav_items = [
            ("transcribe", "📝  Transcrever", 3),
            ("history", "📋  Histórico", 4),
            ("settings", "⚙️  Configurações", 5),
        ]

        for name, text, row in nav_items:
            btn = ctk.CTkButton(
                self,
                text=text,
                font=ctk.CTkFont(size=14),
                height=40,
                anchor="w",
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda n=name: self._on_click(n),
            )
            btn.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
            self._buttons[name] = btn

        # ── Rodapé ──
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=7, column=0, padx=15, pady=(0, 15), sticky="sew")

        ctk.CTkLabel(
            footer_frame,
            text="v1.0.0",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=5)

        ctk.CTkLabel(
            footer_frame,
            text="100% Offline 🔒",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w", padx=5)

    def _on_click(self, name: str):
        """Callback interno ao clicar num botão."""
        self.set_active(name)
        if self.on_navigate:
            self.on_navigate(name)

    def set_active(self, name: str):
        """Define o botão ativo visualmente."""
        # Resetar todos
        for btn_name, btn in self._buttons.items():
            btn.configure(
                fg_color="transparent",
                text_color=("gray10", "gray90"),
            )

        # Destacar o ativo
        if name in self._buttons:
            self._buttons[name].configure(
                fg_color=self.ACCENT_COLOR,
                text_color="white",
            )
            self._active_button = name
