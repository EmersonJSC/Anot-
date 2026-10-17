"""
View de configurações do aplicativo.

Gerencia tema, modelo padrão, idioma, diretório de saída e info do sistema.
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Optional

from src.transcriber import (
    AVAILABLE_MODELS, AVAILABLE_LANGUAGES,
    get_device_info, get_recommended_model,
)
from src.storage import load_config, save_config, APP_DATA_DIR


class SettingsView(ctk.CTkFrame):
    """Tela de configurações."""

    ACCENT_COLOR = "#6366f1"

    def __init__(self, parent, config: dict, on_config_changed: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.config = config
        self.on_config_changed = on_config_changed

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        row = 0

        # ── Título ──
        ctk.CTkLabel(
            self,
            text="Configurações",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        # ── Aparência ──
        appearance_frame = self._create_section("🎨  Aparência", row)
        row += 1

        # Tema
        theme_row = ctk.CTkFrame(appearance_frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            theme_row,
            text="Tema:",
            font=ctk.CTkFont(size=13),
            width=150,
            anchor="w",
        ).pack(side="left")

        current_theme = self.config.get("theme", "dark")
        self._theme_var = ctk.StringVar(value=current_theme)

        theme_menu = ctk.CTkSegmentedButton(
            theme_row,
            values=["dark", "light", "system"],
            variable=self._theme_var,
            font=ctk.CTkFont(size=12),
            selected_color=self.ACCENT_COLOR,
            selected_hover_color="#818cf8",
            command=self._on_theme_changed,
        )
        theme_menu.pack(side="left")

        # ── Transcrição ──
        transcription_frame = self._create_section("🧠  Transcrição (Padrões)", row)
        row += 1

        # Modelo padrão
        model_row = ctk.CTkFrame(transcription_frame, fg_color="transparent")
        model_row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            model_row,
            text="Modelo padrão:",
            font=ctk.CTkFont(size=13),
            width=150,
            anchor="w",
        ).pack(side="left")

        default_model = self.config.get("default_model", "small")
        self._model_var = ctk.StringVar(value=default_model)

        ctk.CTkOptionMenu(
            model_row,
            variable=self._model_var,
            values=list(AVAILABLE_MODELS.keys()),
            width=180,
            height=30,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            command=lambda _: self._save_setting("default_model", self._model_var.get()),
        ).pack(side="left")

        recommended = get_recommended_model()
        ctk.CTkLabel(
            model_row,
            text=f"  (Recomendado: {recommended})",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(side="left", padx=10)

        # Idioma padrão
        lang_row = ctk.CTkFrame(transcription_frame, fg_color="transparent")
        lang_row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            lang_row,
            text="Idioma padrão:",
            font=ctk.CTkFont(size=13),
            width=150,
            anchor="w",
        ).pack(side="left")

        default_lang = self.config.get("default_language", "auto")
        default_lang_display = AVAILABLE_LANGUAGES.get(default_lang, "Automático (detectar)")
        self._lang_var = ctk.StringVar(value=default_lang_display)

        ctk.CTkOptionMenu(
            lang_row,
            variable=self._lang_var,
            values=list(AVAILABLE_LANGUAGES.values()),
            width=200,
            height=30,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            command=lambda _: self._save_language_setting(),
        ).pack(side="left")

        # Dispositivo padrão
        device_row = ctk.CTkFrame(transcription_frame, fg_color="transparent")
        device_row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            device_row,
            text="Dispositivo padrão:",
            font=ctk.CTkFont(size=13),
            width=150,
            anchor="w",
        ).pack(side="left")

        default_device = self.config.get("default_device", "auto")
        self._device_var = ctk.StringVar(value=default_device)

        ctk.CTkOptionMenu(
            device_row,
            variable=self._device_var,
            values=["auto", "cpu", "cuda"],
            width=180,
            height=30,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            command=lambda _: self._save_setting("default_device", self._device_var.get()),
        ).pack(side="left")

        # Timestamps
        ts_row = ctk.CTkFrame(transcription_frame, fg_color="transparent")
        ts_row.pack(fill="x", pady=5)

        ctk.CTkLabel(
            ts_row,
            text="Incluir timestamps:",
            font=ctk.CTkFont(size=13),
            width=150,
            anchor="w",
        ).pack(side="left")

        self._timestamps_var = ctk.BooleanVar(
            value=self.config.get("include_timestamps", True)
        )
        ctk.CTkSwitch(
            ts_row,
            text="",
            variable=self._timestamps_var,
            progress_color=self.ACCENT_COLOR,
            command=lambda: self._save_setting("include_timestamps", self._timestamps_var.get()),
        ).pack(side="left")

        # ── Saída ──
        output_frame = self._create_section("📁  Diretório de Saída", row)
        row += 1

        dir_row = ctk.CTkFrame(output_frame, fg_color="transparent")
        dir_row.pack(fill="x", pady=5)
        dir_row.grid_columnconfigure(0, weight=1)

        current_dir = self.config.get("output_directory", "")
        self._dir_var = ctk.StringVar(value=current_dir or "(Mesmo diretório do arquivo)")

        dir_entry = ctk.CTkEntry(
            dir_row,
            textvariable=self._dir_var,
            height=32,
            corner_radius=6,
            state="disabled",
            font=ctk.CTkFont(size=12),
        )
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(
            dir_row,
            text="📂 Escolher",
            width=100,
            height=32,
            corner_radius=6,
            fg_color=self.ACCENT_COLOR,
            hover_color="#818cf8",
            font=ctk.CTkFont(size=12),
            command=self._select_output_dir,
        ).pack(side="left")

        # ── Informações do Sistema ──
        sys_frame = self._create_section("💻  Informações do Sistema", row)
        row += 1

        device_info = get_device_info()

        sys_info = [
            ("Dispositivo:", device_info.get("device", "cpu").upper()),
            ("GPU:", device_info.get("gpu_name", "Não detectada")),
            ("VRAM:", device_info.get("vram", "N/A")),
            ("Tipo de cálculo:", device_info.get("compute_type", "int8")),
            ("Dados do app:", APP_DATA_DIR),
        ]

        for label, value in sys_info:
            info_row = ctk.CTkFrame(sys_frame, fg_color="transparent")
            info_row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                info_row,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=150,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                info_row,
                text=value,
                font=ctk.CTkFont(size=12),
                text_color=("gray30", "gray70"),
                anchor="w",
            ).pack(side="left")

    def _create_section(self, title: str, row: int) -> ctk.CTkFrame:
        """Cria uma seção com título e conteúdo."""
        frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray92", "gray17"))
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))

        # Título da seção
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(12, 5))

        # Container de conteúdo
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 12))

        return content

    def _on_theme_changed(self, value: str):
        """Callback quando o tema muda."""
        ctk.set_appearance_mode(value)
        self._save_setting("theme", value)

    def _save_setting(self, key: str, value):
        """Salva uma configuração individual."""
        self.config[key] = value
        save_config(self.config)
        if self.on_config_changed:
            self.on_config_changed(key, value)

    def _save_language_setting(self):
        """Salva a configuração de idioma (converte display→code)."""
        display = self._lang_var.get()
        for code, name in AVAILABLE_LANGUAGES.items():
            if name == display:
                self._save_setting("default_language", code)
                return

    def _select_output_dir(self):
        """Abre diálogo para selecionar diretório de saída."""
        directory = filedialog.askdirectory(title="Selecionar diretório de saída")
        if directory:
            self._dir_var.set(directory)
            self._save_setting("output_directory", directory)
