"""
View principal de transcrição.

Contém seleção de arquivo, configurações, transcrição e resultado.
"""

import customtkinter as ctk
from tkinter import filedialog
from typing import Optional

from src.ui.components.file_drop_zone import FileDropZone
from src.ui.components.progress_bar import TranscriptionProgress
from src.transcriber import AVAILABLE_MODELS, AVAILABLE_LANGUAGES, Transcriber
from src.exporter import (
    export_txt, export_srt, export_json,
    get_formatted_text, get_default_output_path,
)


class TranscribeView(ctk.CTkFrame):
    """Tela principal de transcrição."""

    ACCENT_COLOR = "#6366f1"

    def __init__(self, parent, transcriber: Transcriber, config: dict):
        super().__init__(parent, fg_color="transparent")
        self.transcriber = transcriber
        self.config = config
        self._current_result = None
        self._current_file = None

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        row = 0

        # ── Título ──
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(
            title_frame,
            text="Transcrever",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        row += 1

        # ── Zona de Arquivo ──
        self._file_zone = FileDropZone(self, on_file_selected=self._on_file_selected)
        self._file_zone.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        row += 1

        # ── Configurações ──
        config_frame = ctk.CTkFrame(self, fg_color=("gray92", "gray17"), corner_radius=10)
        config_frame.grid(row=row, column=0, sticky="ew", pady=(0, 15))
        config_frame.grid_columnconfigure((0, 1, 2), weight=1)
        row += 1

        # Modelo
        model_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        model_frame.grid(row=0, column=0, padx=15, pady=12, sticky="ew")

        ctk.CTkLabel(
            model_frame,
            text="🧠 Modelo",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        model_names = list(AVAILABLE_MODELS.keys())
        default_model = self.config.get("default_model", "small")
        self._model_var = ctk.StringVar(value=default_model)

        self._model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self._model_var,
            values=model_names,
            width=160,
            height=32,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            button_hover_color="#818cf8",
        )
        self._model_menu.pack(anchor="w", pady=(5, 0))

        # Info do modelo
        self._model_info_label = ctk.CTkLabel(
            model_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._model_info_label.pack(anchor="w", pady=(3, 0))
        self._update_model_info()
        self._model_var.trace_add("write", lambda *_: self._update_model_info())

        # Idioma
        lang_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=1, padx=15, pady=12, sticky="ew")

        ctk.CTkLabel(
            lang_frame,
            text="🌍 Idioma",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        lang_display = list(AVAILABLE_LANGUAGES.values())
        default_lang = self.config.get("default_language", "auto")
        default_lang_display = AVAILABLE_LANGUAGES.get(default_lang, "Automático (detectar)")
        self._lang_var = ctk.StringVar(value=default_lang_display)

        self._lang_menu = ctk.CTkOptionMenu(
            lang_frame,
            variable=self._lang_var,
            values=lang_display,
            width=160,
            height=32,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            button_hover_color="#818cf8",
        )
        self._lang_menu.pack(anchor="w", pady=(5, 0))

        # Dispositivo
        device_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        device_frame.grid(row=0, column=2, padx=15, pady=12, sticky="ew")

        ctk.CTkLabel(
            device_frame,
            text="💻 Dispositivo",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        self._device_var = ctk.StringVar(value="auto")

        self._device_menu = ctk.CTkOptionMenu(
            device_frame,
            variable=self._device_var,
            values=["auto", "cpu", "cuda"],
            width=160,
            height=32,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            button_color=self.ACCENT_COLOR,
            button_hover_color="#818cf8",
        )
        self._device_menu.pack(anchor="w", pady=(5, 0))

        # ── Botão Transcrever ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        btn_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._transcribe_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Transcrever",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=48,
            corner_radius=10,
            fg_color=self.ACCENT_COLOR,
            hover_color="#818cf8",
            command=self._start_transcription,
        )
        self._transcribe_btn.grid(row=0, column=0, sticky="ew")

        self._cancel_btn = ctk.CTkButton(
            btn_frame,
            text="⏹  Cancelar",
            font=ctk.CTkFont(size=14),
            height=48,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._cancel_transcription,
        )
        # Cancel button is hidden initially

        # ── Progresso ──
        self._progress = TranscriptionProgress(self)
        self._progress.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        # ── Resultado ──
        self._result_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._result_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 0))
        self._result_frame.grid_columnconfigure(0, weight=1)
        self._result_frame.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(row, weight=1)
        row += 1

        # Header do resultado
        result_header = ctk.CTkFrame(self._result_frame, fg_color="transparent")
        result_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        ctk.CTkLabel(
            result_header,
            text="📄 Resultado",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        # Botões de exportação
        export_frame = ctk.CTkFrame(result_header, fg_color="transparent")
        export_frame.pack(side="right")

        self._copy_btn = ctk.CTkButton(
            export_frame, text="📋 Copiar", width=80, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=self._copy_to_clipboard,
        )
        self._copy_btn.pack(side="left", padx=3)

        self._txt_btn = ctk.CTkButton(
            export_frame, text="💾 TXT", width=70, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=lambda: self._export("txt"),
        )
        self._txt_btn.pack(side="left", padx=3)

        self._srt_btn = ctk.CTkButton(
            export_frame, text="💾 SRT", width=70, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=lambda: self._export("srt"),
        )
        self._srt_btn.pack(side="left", padx=3)

        self._json_btn = ctk.CTkButton(
            export_frame, text="💾 JSON", width=75, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=lambda: self._export("json"),
        )
        self._json_btn.pack(side="left", padx=3)

        # Texto do resultado
        self._result_text = ctk.CTkTextbox(
            self._result_frame,
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=10,
            fg_color=("gray92", "gray17"),
            wrap="word",
        )
        self._result_text.grid(row=1, column=0, sticky="nsew")
        self._result_text.insert("1.0", "O resultado da transcrição aparecerá aqui...")
        self._result_text.configure(state="disabled")

        # Esconder botões de exportação até ter resultado
        self._set_export_buttons_state(False)

    def _update_model_info(self):
        """Atualiza a info do modelo selecionado."""
        model_name = self._model_var.get()
        info = AVAILABLE_MODELS.get(model_name, {})
        desc = info.get("description", "")
        size = info.get("size", "")
        vram = info.get("vram", "")
        self._model_info_label.configure(text=f"{desc} • {size} • VRAM: {vram}")

    def _get_selected_language_code(self) -> str:
        """Converte display name para código do idioma."""
        display = self._lang_var.get()
        for code, name in AVAILABLE_LANGUAGES.items():
            if name == display:
                return code
        return "auto"

    def _on_file_selected(self, file_path: str):
        """Callback quando um arquivo é selecionado."""
        self._current_file = file_path

    def _start_transcription(self):
        """Inicia a transcrição."""
        file_path = self._file_zone.get_file_path()
        if not file_path:
            self._show_message("⚠️ Selecione um arquivo primeiro!")
            return

        model_name = self._model_var.get()
        language = self._get_selected_language_code()
        device = self._device_var.get()

        # UI: modo transcrevendo
        self._transcribe_btn.grid_remove()
        self._cancel_btn.grid(row=0, column=0, sticky="ew")
        self._progress.show()
        self._progress.reset()
        self._set_export_buttons_state(False)
        self._result_text.configure(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.configure(state="disabled")

        # Carregar modelo (se diferente do carregado)
        if self.transcriber.loaded_model != model_name:
            self._progress.set_indeterminate(f"Carregando modelo '{model_name}'...")

            def _load_and_transcribe():
                try:
                    self.transcriber.load_model(
                        model_name=model_name,
                        device=device,
                        on_status=lambda s: self.after(0, lambda: self._progress.set_status(s)),
                    )
                    self.after(0, lambda: self._run_transcription(file_path, language))
                except Exception as e:
                    self.after(0, lambda: self._on_error(e))

            import threading
            threading.Thread(target=_load_and_transcribe, daemon=True).start()
        else:
            self._run_transcription(file_path, language)

    def _run_transcription(self, file_path: str, language: str):
        """Executa a transcrição (modelo já carregado)."""
        self._progress.set_determinate()
        self._progress.set_progress(0, "Iniciando transcrição...")

        self.transcriber.transcribe_async(
            file_path=file_path,
            language=language,
            on_progress=lambda p, msg: self.after(
                0, lambda: self._progress.set_progress(p, msg)
            ),
            on_status=lambda s: self.after(
                0, lambda: self._progress.set_status(s)
            ),
            on_segment=lambda seg: self.after(
                0, lambda s=seg: self._append_segment(s)
            ),
            on_complete=lambda result: self.after(
                0, lambda: self._on_complete(result)
            ),
            on_error=lambda e: self.after(
                0, lambda: self._on_error(e)
            ),
        )

    def _cancel_transcription(self):
        """Cancela a transcrição."""
        self.transcriber.cancel()
        self._restore_ui()
        self._progress.set_error("Transcrição cancelada pelo usuário")

    def _append_segment(self, segment: dict):
        """Adiciona um segmento ao texto de resultado."""
        self._result_text.configure(state="normal")
        start = f"{segment['start']:.2f}"
        end = f"{segment['end']:.2f}"
        text = segment["text"].strip()
        self._result_text.insert("end", f"[{start}s → {end}s] {text}\n")
        self._result_text.see("end")
        self._result_text.configure(state="disabled")

    def _on_complete(self, result: dict):
        """Callback quando a transcrição termina."""
        self._current_result = result
        self._restore_ui()
        self._progress.set_complete()
        self._set_export_buttons_state(True)

        # Salvar no histórico
        try:
            from src.storage import add_to_history
            from src.exporter import get_full_text
            segments = result.get("segments", [])
            full_text = get_full_text(segments)
            add_to_history(
                file_name=result["info"]["file_name"],
                file_path=result["info"]["file_path"],
                model=result["info"]["model"],
                language=result.get("language", "auto"),
                duration=result.get("duration", 0),
                segments=segments,
                full_text=full_text,
            )
        except Exception:
            pass  # não interromper fluxo por erro no histórico

    def _on_error(self, error: Exception):
        """Callback de erro."""
        self._restore_ui()
        self._progress.set_error(str(error))

    def _restore_ui(self):
        """Restaura a UI ao estado normal."""
        self._cancel_btn.grid_remove()
        self._transcribe_btn.grid(row=0, column=0, sticky="ew")

    def _set_export_buttons_state(self, enabled: bool):
        """Habilita/desabilita botões de exportação."""
        state = "normal" if enabled else "disabled"
        for btn in [self._copy_btn, self._txt_btn, self._srt_btn, self._json_btn]:
            btn.configure(state=state)

    def _copy_to_clipboard(self):
        """Copia o texto para a área de transferência."""
        if self._current_result:
            segments = self._current_result.get("segments", [])
            text = get_formatted_text(segments, include_timestamps=False)
            self.clipboard_clear()
            self.clipboard_append(text)
            self._copy_btn.configure(text="✅ Copiado!")
            self.after(2000, lambda: self._copy_btn.configure(text="📋 Copiar"))

    def _export(self, format_type: str):
        """Exporta a transcrição no formato especificado."""
        if not self._current_result:
            return

        segments = self._current_result.get("segments", [])
        file_path = self._current_result.get("info", {}).get("file_path", "output")

        ext_map = {"txt": ".txt", "srt": ".srt", "json": ".json"}
        ext = ext_map.get(format_type, ".txt")

        default_path = get_default_output_path(file_path, ext)

        save_path = filedialog.asksaveasfilename(
            title=f"Salvar como {ext.upper()}",
            defaultextension=ext,
            initialfile=default_path.split("/")[-1] if "/" in default_path else default_path.split("\\")[-1],
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
                metadata = self._current_result.get("info", {})
                export_json(segments, save_path, metadata)

            self._show_message(f"✅ Exportado: {save_path}")
        except Exception as e:
            self._show_message(f"❌ Erro ao exportar: {e}")

    def _show_message(self, message: str):
        """Exibe uma mensagem temporária no status do progresso."""
        self._progress.show()
        self._progress.set_status(message)
