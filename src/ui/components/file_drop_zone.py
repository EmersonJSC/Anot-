"""
Componente de zona de seleção de arquivo.
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import Callable, Optional

from src.audio_processor import get_file_filter_string, get_media_info, is_supported_file


class FileDropZone(ctk.CTkFrame):
    """Zona visual para seleção de arquivo com informações."""

    def __init__(self, parent, on_file_selected: Optional[Callable[[str], None]] = None):
        super().__init__(
            parent,
            height=140,
            corner_radius=12,
            border_width=2,
            border_color=("gray70", "gray35"),
            fg_color=("gray92", "gray17"),
        )
        self.on_file_selected = on_file_selected
        self._file_path = None
        self._file_info = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_empty_state()

        # Clicar na zona abre o diálogo
        self.bind("<Button-1>", lambda e: self.browse_file())

    def _build_empty_state(self):
        """Constrói o estado vazio (nenhum arquivo selecionado)."""
        self._clear()

        self._empty_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._empty_frame.grid(row=0, column=0, sticky="nsew")
        self._empty_frame.grid_columnconfigure(0, weight=1)
        self._empty_frame.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self._empty_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            container,
            text="📁",
            font=ctk.CTkFont(size=36),
        ).pack()

        ctk.CTkLabel(
            container,
            text="Clique para selecionar um arquivo",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        ).pack(pady=(5, 0))

        ctk.CTkLabel(
            container,
            text="Áudio: MP3, WAV, FLAC, M4A, OGG  •  Vídeo: MP4, MKV, AVI, MOV",
            font=ctk.CTkFont(size=11),
            text_color=("gray55", "gray50"),
        ).pack(pady=(2, 0))

        # Bind clicks no frame interno também
        for widget in [self._empty_frame, container]:
            widget.bind("<Button-1>", lambda e: self.browse_file())
            for child in widget.winfo_children():
                child.bind("<Button-1>", lambda e: self.browse_file())

    def _build_file_state(self):
        """Constrói o estado com arquivo selecionado."""
        self._clear()

        self.configure(
            border_color=("#6366f1", "#6366f1"),
            fg_color=("gray92", "gray17"),
        )

        self._file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._file_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)
        self._file_frame.grid_columnconfigure(1, weight=1)

        # Ícone
        ext = self._file_info.get("format", "")
        icon = "🎵" if ext in ("mp3", "wav", "flac", "m4a", "ogg", "aac", "wma") else "🎬"

        ctk.CTkLabel(
            self._file_frame,
            text=icon,
            font=ctk.CTkFont(size=36),
        ).grid(row=0, column=0, rowspan=3, padx=(5, 15), pady=5)

        # Nome do arquivo
        ctk.CTkLabel(
            self._file_frame,
            text=self._file_info.get("file_name", ""),
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        # Detalhes
        details_parts = []
        if self._file_info.get("duration_formatted"):
            details_parts.append(f"⏱ {self._file_info['duration_formatted']}")
        if self._file_info.get("file_size_formatted"):
            details_parts.append(f"💾 {self._file_info['file_size_formatted']}")
        if self._file_info.get("format"):
            details_parts.append(f"📄 {self._file_info['format'].upper()}")

        if details_parts:
            ctk.CTkLabel(
                self._file_frame,
                text="  •  ".join(details_parts),
                font=ctk.CTkFont(size=12),
                text_color=("gray40", "gray60"),
                anchor="w",
            ).grid(row=1, column=1, sticky="w")

        # Botão trocar arquivo
        btn_frame = ctk.CTkFrame(self._file_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, rowspan=3, padx=(10, 5))

        ctk.CTkButton(
            btn_frame,
            text="Trocar",
            width=80,
            height=30,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self.browse_file,
        ).pack()

    def _clear(self):
        """Remove todos os widgets filhos."""
        for widget in self.winfo_children():
            widget.destroy()

    def browse_file(self):
        """Abre diálogo de seleção de arquivo."""
        file_types = get_file_filter_string()
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo de áudio ou vídeo",
            filetypes=file_types,
        )
        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path: str):
        """Define o arquivo selecionado."""
        if not is_supported_file(file_path):
            return

        self._file_path = file_path
        self._file_info = get_media_info(file_path)
        self._build_file_state()

        if self.on_file_selected:
            self.on_file_selected(file_path)

    def get_file_path(self) -> Optional[str]:
        """Retorna o caminho do arquivo selecionado."""
        return self._file_path

    def get_file_info(self) -> Optional[dict]:
        """Retorna as informações do arquivo selecionado."""
        return self._file_info

    def reset(self):
        """Reseta para o estado vazio."""
        self._file_path = None
        self._file_info = None
        self.configure(
            border_color=("gray70", "gray35"),
        )
        self._build_empty_state()
