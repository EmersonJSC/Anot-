"""
View de histórico de transcrições.

Exibe lista de transcrições anteriores com preview e re-exportação.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional

from src.storage import load_history, delete_from_history, clear_history
from src.exporter import (
    export_txt, export_srt, export_json,
    get_formatted_text, get_default_output_path,
)


class HistoryView(ctk.CTkFrame):
    """Tela de histórico de transcrições."""

    ACCENT_COLOR = "#6366f1"

    def __init__(self, parent, config: dict):
        super().__init__(parent, fg_color="transparent")
        self.config = config
        self._selected_record = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="Histórico",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        # Botão limpar
        self._clear_btn = ctk.CTkButton(
            header,
            text="🗑️  Limpar tudo",
            width=120,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("#ef4444", "#ef4444"),
            text_color=("#ef4444", "#ef4444"),
            hover_color=("gray90", "gray20"),
            command=self._clear_all,
        )
        self._clear_btn.pack(side="right")

        # Botão atualizar
        self._refresh_btn = ctk.CTkButton(
            header,
            text="🔄 Atualizar",
            width=100,
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self.refresh,
        )
        self._refresh_btn.pack(side="right", padx=8)

        # ── Conteúdo (dividido: lista + preview) ──
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        # Lista de itens
        self._list_frame = ctk.CTkScrollableFrame(
            content,
            corner_radius=10,
            fg_color=("gray92", "gray17"),
            label_text="  Transcrições",
            label_font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._list_frame.grid_columnconfigure(0, weight=1)

        # Preview
        preview_frame = ctk.CTkFrame(content, corner_radius=10, fg_color=("gray92", "gray17"))
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)

        # Header do preview
        self._preview_header = ctk.CTkFrame(preview_frame, fg_color="transparent")
        self._preview_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 5))

        self._preview_title = ctk.CTkLabel(
            self._preview_header,
            text="Selecione uma transcrição",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self._preview_title.pack(side="left", fill="x", expand=True)

        # Botões de export no preview
        self._export_frame = ctk.CTkFrame(self._preview_header, fg_color="transparent")
        self._export_frame.pack(side="right")

        for text, fmt in [("TXT", "txt"), ("SRT", "srt"), ("JSON", "json")]:
            ctk.CTkButton(
                self._export_frame,
                text=f"💾 {text}",
                width=65,
                height=26,
                corner_radius=5,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                border_width=1,
                border_color=("gray60", "gray40"),
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                command=lambda f=fmt: self._export_selected(f),
            ).pack(side="left", padx=2)

        # Texto do preview
        self._preview_text = ctk.CTkTextbox(
            preview_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=0,
            fg_color="transparent",
            wrap="word",
        )
        self._preview_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Carregar histórico
        self.refresh()

    def refresh(self):
        """Recarrega a lista de transcrições do histórico."""
        # Limpar lista atual
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        history = load_history()

        if not history:
            ctk.CTkLabel(
                self._list_frame,
                text="Nenhuma transcrição no histórico.",
                font=ctk.CTkFont(size=13),
                text_color="gray",
            ).grid(row=0, column=0, pady=30)
            return

        for i, record in enumerate(history):
            self._create_history_item(record, i)

    def _create_history_item(self, record: dict, index: int):
        """Cria um item na lista de histórico."""
        item = ctk.CTkFrame(
            self._list_frame,
            corner_radius=8,
            fg_color=("gray88", "gray22"),
            cursor="hand2",
        )
        item.grid(row=index, column=0, sticky="ew", pady=3, padx=5)
        item.grid_columnconfigure(0, weight=1)

        # Nome do arquivo
        ctk.CTkLabel(
            item,
            text=record.get("file_name", "Sem nome"),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))

        # Detalhes
        details_parts = []
        if record.get("created_at_formatted"):
            details_parts.append(f"📅 {record['created_at_formatted']}")
        if record.get("model"):
            details_parts.append(f"🧠 {record['model']}")
        if record.get("duration_formatted"):
            details_parts.append(f"⏱ {record['duration_formatted']}")

        ctk.CTkLabel(
            item,
            text="  •  ".join(details_parts),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 4))

        # Preview curto
        preview = record.get("text_preview", "")[:80]
        if preview:
            ctk.CTkLabel(
                item,
                text=preview,
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray55"),
                anchor="w",
            ).grid(row=2, column=0, sticky="w", padx=10, pady=(0, 8))

        # Botão deletar
        del_btn = ctk.CTkButton(
            item,
            text="✕",
            width=28,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("gray50", "gray50"),
            hover_color=("#fee2e2", "#3b1111"),
            command=lambda r=record: self._delete_item(r),
        )
        del_btn.grid(row=0, column=1, rowspan=3, padx=5, pady=5)

        # Bind click
        for widget in [item] + list(item.winfo_children()):
            if not isinstance(widget, ctk.CTkButton):
                widget.bind("<Button-1>", lambda e, r=record: self._select_item(r))

    def _select_item(self, record: dict):
        """Seleciona um item do histórico e mostra preview."""
        self._selected_record = record

        self._preview_title.configure(
            text=f"📄 {record.get('file_name', 'Sem nome')}"
        )

        self._preview_text.configure(state="normal")
        self._preview_text.delete("1.0", "end")

        # Info header
        info_lines = []
        if record.get("created_at_formatted"):
            info_lines.append(f"Data: {record['created_at_formatted']}")
        if record.get("model"):
            info_lines.append(f"Modelo: {record['model']}")
        if record.get("language"):
            info_lines.append(f"Idioma: {record['language']}")
        if record.get("duration_formatted"):
            info_lines.append(f"Duração: {record['duration_formatted']}")
        if record.get("segments_count"):
            info_lines.append(f"Segmentos: {record['segments_count']}")

        if info_lines:
            self._preview_text.insert("end", " | ".join(info_lines) + "\n")
            self._preview_text.insert("end", "─" * 50 + "\n\n")

        # Texto completo
        full_text = record.get("full_text", "Texto não disponível.")
        self._preview_text.insert("end", full_text)
        self._preview_text.configure(state="disabled")

    def _delete_item(self, record: dict):
        """Remove um item do histórico."""
        record_id = record.get("id")
        if record_id:
            delete_from_history(record_id)
            if self._selected_record and self._selected_record.get("id") == record_id:
                self._selected_record = None
                self._preview_text.configure(state="normal")
                self._preview_text.delete("1.0", "end")
                self._preview_title.configure(text="Selecione uma transcrição")
                self._preview_text.configure(state="disabled")
            self.refresh()

    def _clear_all(self):
        """Limpa todo o histórico."""
        confirm = messagebox.askyesno(
            "Confirmar",
            "Deseja limpar todo o histórico de transcrições?\n\nEsta ação não pode ser desfeita.",
        )
        if confirm:
            clear_history()
            self._selected_record = None
            self._preview_text.configure(state="normal")
            self._preview_text.delete("1.0", "end")
            self._preview_title.configure(text="Selecione uma transcrição")
            self._preview_text.configure(state="disabled")
            self.refresh()

    def _export_selected(self, format_type: str):
        """Exporta a transcrição selecionada."""
        if not self._selected_record:
            return

        segments = self._selected_record.get("segments", [])
        if not segments:
            # Fallback: criar segmento único com texto completo
            full_text = self._selected_record.get("full_text", "")
            if full_text:
                segments = [{"start": 0, "end": 0, "text": full_text}]
            else:
                return

        file_name = self._selected_record.get("file_name", "transcricao")
        ext_map = {"txt": ".txt", "srt": ".srt", "json": ".json"}
        ext = ext_map.get(format_type, ".txt")

        save_path = filedialog.asksaveasfilename(
            title=f"Salvar como {format_type.upper()}",
            defaultextension=ext,
            initialfile=f"{file_name}_transcricao{ext}",
            filetypes=[(f"Arquivo {ext.upper()}", f"*{ext}")],
        )

        if not save_path:
            return

        try:
            if format_type == "txt":
                export_txt(segments, save_path)
            elif format_type == "srt":
                export_srt(segments, save_path)
            elif format_type == "json":
                export_json(segments, save_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {e}")
