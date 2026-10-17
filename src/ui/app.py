"""
Interface Gráfica — Transcritor de Áudio e Vídeo.

Recursos:
- Arrastar e soltar (Drag and Drop) de arquivos em qualquer lugar da tela ou na zona dedicada.
- Botão discreto de seleção de arquivo ao lado da zona de drop.
- Transcrição com exibição de texto em tempo real (frase por frase).
- Botão para cancelar a transcrição a qualquer momento.
- Seletor discreto de modelo no rodapé com porcentagem real de download.
"""

import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

from src.audio_processor import (
    get_file_filter_string,
    get_media_info,
    is_supported_file,
    prepare_audio_for_transcription,
)
from src.exporter import export_txt
from src.model_manager import (
    MODELS_INFO,
    download_model_with_progress,
    get_model_status_label,
    is_model_downloaded,
)
from src.storage import load_config, save_config
from src.transcriber import Transcriber


class TranscritorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Janela principal do Transcritor."""

    ACCENT_COLOR = "#6366f1"
    ACCENT_HOVER = "#818cf8"
    BG_CARD_USER = ("#e0e7ff", "#1e1b4b")
    BG_CARD_BOT = ("#f1f5f9", "#1e293b")

    def __init__(self):
        super().__init__()
        # Inicializa o suporte a Drag & Drop nativo
        self.TkdndVersion = TkinterDnD._require(self)

        # Configurações do app
        self.config = load_config()
        self.transcriber = Transcriber()

        # Tema
        ctk.set_appearance_mode(self.config.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        # Configuração da janela
        self.title("Transcritor")
        self.geometry("960x700")
        self.minsize(820, 560)

        # Pasta de saída padrão
        default_output = self.config.get("output_directory")
        if not default_output:
            default_output = os.path.join(str(Path.home()), "Documentos", "Transcrições")
        self.output_dir = default_output
        os.makedirs(self.output_dir, exist_ok=True)

        # Modelo selecionado
        self.selected_model = self.config.get("default_model", "tiny")
        if not is_model_downloaded(self.selected_model):
            if is_model_downloaded("tiny"):
                self.selected_model = "tiny"

        self._is_processing = False
        self._current_cancel_event = threading.Event()

        self._build_ui()
        self._setup_drag_and_drop()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)  # Feed central expande
        self.grid_columnconfigure(0, weight=1)

        # ── 1. TOPO / CABEÇALHO ──
        self._build_header()

        # ── 2. CENTRO / FEED DE TRANSCRIÇÃO ──
        self._build_feed()

        # ── 3. RODAPÉ / ZONA DE ARRASTAR & MODELO ──
        self._build_footer()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=("gray90", "gray14"), corner_radius=0, height=52)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(1, weight=1)

        # Título simples
        ctk.CTkLabel(
            header,
            text="🎙️ Transcritor",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Pasta de Saída discreta na direita
        dir_frame = ctk.CTkFrame(header, fg_color="transparent")
        dir_frame.grid(row=0, column=2, padx=20, pady=8, sticky="e")

        self.lbl_output_dir = ctk.CTkLabel(
            dir_frame,
            text=f"📁 Salvar em: {Path(self.output_dir).name}/",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
        )
        self.lbl_output_dir.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            dir_frame,
            text="Alterar",
            width=65,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            command=self._choose_output_dir,
        ).pack(side="left")

    def _build_feed(self):
        """Feed rolável estilo chat/timeline."""
        self.feed_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=("gray95", "gray10"),
            corner_radius=0,
        )
        self.feed_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.feed_scroll.grid_columnconfigure(0, weight=1)

        # Estado inicial (boas-vindas simples)
        self.welcome_frame = ctk.CTkFrame(self.feed_scroll, fg_color="transparent")
        self.welcome_frame.pack(expand=True, fill="both", pady=120)

        ctk.CTkLabel(
            self.welcome_frame,
            text="🎙️",
            font=ctk.CTkFont(size=44),
        ).pack()

        ctk.CTkLabel(
            self.welcome_frame,
            text="Transcritor de Áudio e Vídeo",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(6, 4))

        ctk.CTkLabel(
            self.welcome_frame,
            text="Arraste e solte um arquivo aqui, ou clique no botão abaixo para começar.\nAs frases serão exibidas em tempo real conforme são reconhecidas.",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
            justify="center",
        ).pack()

    def _build_footer(self):
        """Rodapé com área de arrastar, botão discreto ao lado e seletor de modelo."""
        footer = ctk.CTkFrame(self, fg_color=("gray90", "gray14"), corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_columnconfigure(0, weight=1)

        # Linha 1: Drop Zone + Botão discreto ao lado
        input_row = ctk.CTkFrame(footer, fg_color="transparent")
        input_row.grid(row=0, column=0, padx=20, pady=(12, 6), sticky="ew")
        input_row.grid_columnconfigure(0, weight=1)

        # Zona de Arraste (Drop Zone clicável)
        self.drop_frame = ctk.CTkFrame(
            input_row,
            fg_color=("gray85", "gray18"),
            border_width=2,
            border_color=("gray70", "gray30"),
            corner_radius=8,
            height=46,
            cursor="hand2",
        )
        self.drop_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.drop_frame.grid_columnconfigure(0, weight=1)
        self.drop_frame.grid_rowconfigure(0, weight=1)

        self.lbl_drop = ctk.CTkLabel(
            self.drop_frame,
            text="📥  Arraste e solte o arquivo aqui (áudio ou vídeo)...",
            font=ctk.CTkFont(size=13),
            text_color=("gray35", "gray70"),
        )
        self.lbl_drop.place(relx=0.5, rely=0.5, anchor="center")

        # Clique na zona também abre o diálogo
        self.drop_frame.bind("<Button-1>", lambda e: self._on_select_file_clicked())
        self.lbl_drop.bind("<Button-1>", lambda e: self._on_select_file_clicked())

        # Botão discreto ao lado
        self.btn_select_file = ctk.CTkButton(
            input_row,
            text="📎  Selecionar",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=130,
            height=46,
            corner_radius=8,
            fg_color=self.ACCENT_COLOR,
            hover_color=self.ACCENT_HOVER,
            command=self._on_select_file_clicked,
        )
        self.btn_select_file.grid(row=0, column=1, sticky="e")

        # Linha 2: Barra inferior discreta (Seletor de modelo estilo ChatGPT)
        sub_bar = ctk.CTkFrame(footer, fg_color="transparent")
        sub_bar.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        sub_bar.grid_columnconfigure(2, weight=1)

        # Seletor discreto de modelo
        self.model_var = ctk.StringVar(value=get_model_status_label(self.selected_model))
        self.model_menu = ctk.CTkOptionMenu(
            sub_bar,
            variable=self.model_var,
            values=[get_model_status_label(name) for name in MODELS_INFO.keys()],
            width=180,
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=6,
            fg_color=("gray82", "gray22"),
            button_color=("gray75", "gray28"),
            button_hover_color=("gray68", "gray35"),
            text_color=("gray15", "gray90"),
            command=self._on_model_menu_changed,
        )
        self.model_menu.grid(row=0, column=0, sticky="w")

        # Botão Baixar Modelo (aparece somente se o modelo não foi baixado)
        self.btn_download_model = ctk.CTkButton(
            sub_bar,
            text="📥 Baixar Modelo",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6,
            fg_color="#10b981",
            hover_color="#059669",
            command=self._download_current_model,
        )
        self._update_download_btn_visibility()

        # Descrição curta do modelo selecionado
        info = MODELS_INFO.get(self.selected_model, {})
        self.lbl_model_desc = ctk.CTkLabel(
            sub_bar,
            text=info.get("desc", ""),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.lbl_model_desc.grid(row=0, column=3, sticky="e")

    # ── DRAG AND DROP ──

    def _setup_drag_and_drop(self):
        """Registra a janela inteira, o feed e a zona de drop para aceitar arrastar arquivos."""
        try:
            import urllib.parse  # garante importação

            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_file_dropped)

            self.feed_scroll.drop_target_register(DND_FILES)
            self.feed_scroll.dnd_bind("<<Drop>>", self._on_file_dropped)

            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind("<<Drop>>", self._on_file_dropped)
            self.drop_frame.dnd_bind("<<DropEnter>>", lambda e: self.drop_frame.configure(border_color=self.ACCENT_COLOR))
            self.drop_frame.dnd_bind("<<DropLeave>>", lambda e: self.drop_frame.configure(border_color=("gray70", "gray30")))
        except Exception as e:
            print("Aviso ao configurar Drag and Drop:", e)

    def _clean_dropped_path(self, raw_data: str) -> str:
        """Limpa e decodifica caminhos de arquivos arrastados do Linux/GNOME/KDE."""
        import urllib.parse
        path = raw_data.strip()
        # Se vier com quebras de linha (\r ou \n), pega a primeira linha
        lines = [line.strip() for line in path.splitlines() if line.strip()]
        if lines:
            path = lines[0]

        # Trata o formato de chaves do Tcl/Tk: {/caminho/com espaco/audio.ogg}
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]

        # Trata protocolos de URI comuns no Linux/Wayland (file:// e file://localhost)
        if path.startswith("file://localhost"):
            path = path[16:]
        elif path.startswith("file://"):
            path = path[7:]

        # Decodifica URL encoding (%20 para espaços, acentos, caracteres especiais)
        path = urllib.parse.unquote(path)

        # Remove aspas e chaves residuais
        path = path.strip("{}\"' \t\r\n")
        return path

    def _on_file_dropped(self, event):
        self.drop_frame.configure(border_color=("gray70", "gray30"))
        if self._is_processing:
            messagebox.showinfo("Aguarde", "Já existe uma transcrição em andamento!")
            return

        raw_data = getattr(event, "data", "")
        file_path = self._clean_dropped_path(raw_data)

        if not file_path:
            return

        if not os.path.exists(file_path):
            messagebox.showerror(
                "Arquivo não encontrado",
                f"Não foi possível localizar o arquivo arrastado:\n\n{file_path}\n\n(Dado original recebido: {raw_data})"
            )
            return

        if not is_supported_file(file_path):
            messagebox.showwarning(
                "Formato não suportado",
                f"O arquivo '{Path(file_path).name}' não é um formato de áudio ou vídeo compatível."
            )
            return

        self._start_transcription_flow(file_path)

    # ── MÉTODOS DE MODELO ──

    def _get_raw_model_name(self, display_name: str) -> str:
        return display_name.split(" ")[0].strip()

    def _on_model_menu_changed(self, choice: str):
        self.selected_model = self._get_raw_model_name(choice)
        info = MODELS_INFO.get(self.selected_model, {})
        self.lbl_model_desc.configure(text=info.get("desc", ""))
        self._update_download_btn_visibility()

    def _update_download_btn_visibility(self):
        if is_model_downloaded(self.selected_model):
            self.btn_download_model.grid_remove()
        else:
            self.btn_download_model.grid(row=0, column=1, padx=(8, 0), sticky="w")

    def _refresh_model_menu(self):
        self.model_menu.configure(values=[get_model_status_label(name) for name in MODELS_INFO.keys()])
        self.model_var.set(get_model_status_label(self.selected_model))
        self._update_download_btn_visibility()

    def _download_current_model(self):
        model_name = self.selected_model
        info = MODELS_INFO.get(model_name, {})
        size = info.get("size", "")

        self.btn_download_model.configure(state="disabled", text="Baixando...")

        # Card de download com %
        self._remove_welcome()
        card = ctk.CTkFrame(self.feed_scroll, fg_color=self.BG_CARD_BOT, corner_radius=12)
        card.pack(fill="x", padx=15, pady=8)

        lbl_status = ctk.CTkLabel(
            card,
            text=f"📥 Baixando modelo '{model_name}' ({size})... 0%",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_status.pack(anchor="w", padx=15, pady=(12, 6))

        prog_bar = ctk.CTkProgressBar(card, progress_color=self.ACCENT_COLOR)
        prog_bar.pack(fill="x", padx=15, pady=(0, 15))
        prog_bar.set(0)

        def _on_progress(pct: float, text: str):
            self.after(0, lambda: self._update_download_ui(prog_bar, lbl_status, model_name, pct, text))

        def _on_success():
            self.after(0, lambda: self._on_download_success(prog_bar, lbl_status, model_name))

        def _on_error(e):
            self.after(0, lambda: self._on_download_error(lbl_status, e))

        download_model_with_progress(
            model_name,
            on_progress=_on_progress,
            on_success=_on_success,
            on_error=_on_error,
        )

    def _update_download_ui(self, prog_bar, label, model_name, pct: float, text: str):
        val = max(0.0, min(1.0, pct / 100.0))
        prog_bar.set(val)
        label.configure(text=f"📥 Baixando modelo '{model_name}'... {text}")

    def _on_download_success(self, prog_bar, label, model_name):
        prog_bar.set(1.0)
        prog_bar.configure(progress_color="#10b981")
        label.configure(
            text=f"✅ Modelo '{model_name}' baixado com sucesso! (100%)",
            text_color="#10b981",
        )
        self.btn_download_model.configure(state="normal", text="📥 Baixar Modelo")
        self._refresh_model_menu()

    def _on_download_error(self, label, error):
        label.configure(text=f"❌ Erro ao baixar modelo: {error}", text_color="#ef4444")
        self.btn_download_model.configure(state="normal", text="📥 Tentar Novamente")

    # ── TRANSCRIÇÃO & FLUXO EM TEMPO REAL ──

    def _choose_output_dir(self):
        new_dir = filedialog.askdirectory(title="Escolha a pasta para salvar as transcrições", initialdir=self.output_dir)
        if new_dir:
            self.output_dir = new_dir
            self.config["output_directory"] = new_dir
            save_config(self.config)
            self.lbl_output_dir.configure(text=f"📁 Salvar em: {Path(self.output_dir).name}/")

    def _remove_welcome(self):
        if hasattr(self, "welcome_frame") and self.welcome_frame.winfo_exists():
            self.welcome_frame.destroy()

    def _on_select_file_clicked(self):
        if self._is_processing:
            messagebox.showinfo("Aguarde", "Já existe uma transcrição em andamento!")
            return

        file_types = get_file_filter_string()
        file_path = filedialog.askopenfilename(
            title="Selecionar Áudio ou Vídeo",
            filetypes=file_types,
        )
        if not file_path:
            return

        self._start_transcription_flow(file_path)

    def _cancel_current_transcription(self):
        """Cancela imediatamente o processamento atual."""
        self._current_cancel_event.set()
        self.transcriber.cancel()

    def _start_transcription_flow(self, file_path: str):
        self._remove_welcome()
        self._is_processing = True
        self._current_cancel_event.clear()

        self.btn_select_file.configure(state="disabled")
        self.lbl_drop.configure(text="⏳ Transcrição em andamento...")

        # 1. Card do Arquivo Enviado
        media_info = get_media_info(file_path)
        total_duration = media_info.get("duration", 0)

        user_card = ctk.CTkFrame(self.feed_scroll, fg_color=self.BG_CARD_USER, corner_radius=12)
        user_card.pack(fill="x", padx=40, pady=(10, 4), anchor="e")

        icon = "🎬" if media_info.get("format") in ("mp4", "mkv", "avi", "mov", "webm") else "🎵"
        duration_text = f" • ⏱️ {media_info['duration_formatted']}" if media_info.get("duration") else ""
        size_text = f" • 💾 {media_info['file_size_formatted']}" if media_info.get("file_size_formatted") else ""

        ctk.CTkLabel(
            user_card,
            text=f"{icon}  {media_info['file_name']}{duration_text}{size_text}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=15, pady=10)

        # 2. Card do Transcritor com Streaming ao Vivo
        bot_card = ctk.CTkFrame(self.feed_scroll, fg_color=self.BG_CARD_BOT, corner_radius=12)
        bot_card.pack(fill="x", padx=15, pady=(4, 15), anchor="w")

        # Cabeçalho do Card (Status + Botão Cancelar)
        header_card = ctk.CTkFrame(bot_card, fg_color="transparent")
        header_card.pack(fill="x", padx=15, pady=(10, 4))
        header_card.grid_columnconfigure(0, weight=1)

        status_label = ctk.CTkLabel(
            header_card,
            text=f"Iniciando transcrição ({self.selected_model})...",
            font=ctk.CTkFont(size=12),
        )
        status_label.grid(row=0, column=0, sticky="w")

        btn_cancel = ctk.CTkButton(
            header_card,
            text="⏹ Cancelar",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._cancel_current_transcription,
        )
        btn_cancel.grid(row=0, column=1, sticky="e")

        # Barra de Progresso
        prog_bar = ctk.CTkProgressBar(bot_card, progress_color=self.ACCENT_COLOR)
        prog_bar.pack(fill="x", padx=15, pady=(2, 8))
        prog_bar.set(0)

        # Caixa de Texto com Streaming em Tempo Real
        text_box = ctk.CTkTextbox(
            bot_card,
            font=ctk.CTkFont(family="Consolas", size=13),
            height=140,
            corner_radius=8,
            wrap="word",
        )
        text_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Lista de segmentos para salvar no final
        collected_segments = []

        def _on_live_segment(seg: dict):
            """Chamado frase por frase conforme o Whisper transcreve."""
            collected_segments.append(seg)
            text_line = f"[{seg['start']:.2f}s -> {seg['end']:.2f}s]  {seg['text'].strip()}\n"

            def _append():
                text_box.insert("end", text_line)
                text_box.see("end")

                if total_duration > 0:
                    pct = min(1.0, seg["end"] / total_duration)
                    prog_bar.set(pct)
                    status_label.configure(
                        text=f"Transcrevendo... {pct*100:.0f}%  (⏱️ {seg['end']:.1f}s / {total_duration:.1f}s)"
                    )

            self.after(0, _append)

        def _worker():
            try:
                # 1. Download do modelo se necessário
                if not is_model_downloaded(self.selected_model):
                    event_done = threading.Event()
                    error_holder = [None]

                    def _dl_prog(pct: float, text: str):
                        val = max(0.0, min(1.0, pct / 100.0))
                        self.after(0, lambda: prog_bar.set(val))
                        self.after(0, lambda: status_label.configure(
                            text=f"📥 Baixando modelo '{self.selected_model}'... {text}"
                        ))

                    def _dl_ok():
                        event_done.set()

                    def _dl_err(e):
                        error_holder[0] = e
                        event_done.set()

                    download_model_with_progress(
                        self.selected_model,
                        on_progress=_dl_prog,
                        on_success=_dl_ok,
                        on_error=_dl_err,
                    )
                    event_done.wait()

                    if error_holder[0]:
                        raise error_holder[0]

                    self.after(0, self._refresh_model_menu)

                if self._current_cancel_event.is_set():
                    self.after(0, lambda: self._on_transcription_cancelled(status_label, btn_cancel, prog_bar))
                    return

                # 2. Carrega o modelo na memória
                if self.transcriber.loaded_model != self.selected_model:
                    self.after(0, lambda: status_label.configure(
                        text=f"Carregando modelo '{self.selected_model}' na memória CPU..."
                    ))
                    self.after(0, lambda: prog_bar.configure(mode="indeterminate"))
                    self.after(0, prog_bar.start)
                    self.transcriber.load_model(self.selected_model, device="cpu")
                    self.after(0, prog_bar.stop)
                    self.after(0, lambda: prog_bar.configure(mode="determinate"))
                    self.after(0, lambda: prog_bar.set(0))

                if self._current_cancel_event.is_set():
                    self.after(0, lambda: self._on_transcription_cancelled(status_label, btn_cancel, prog_bar))
                    return

                # 3. Prepara o áudio
                self.after(0, lambda: status_label.configure(text="Extraindo áudio com FFmpeg..."))
                audio_path = prepare_audio_for_transcription(file_path)

                if self._current_cancel_event.is_set():
                    self.after(0, lambda: self._on_transcription_cancelled(status_label, btn_cancel, prog_bar))
                    return

                # 4. Transcrição com streaming de frases
                self.after(0, lambda: status_label.configure(text="Transcrevendo fala em tempo real..."))
                result = self.transcriber.transcribe(
                    audio_path,
                    language="auto",
                    on_segment=_on_live_segment,
                )

                if self._current_cancel_event.is_set():
                    self.after(0, lambda: self._on_transcription_cancelled(status_label, btn_cancel, prog_bar))
                    return

                # 5. Salva arquivo .txt automaticamente no disco
                stem = Path(file_path).stem
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                txt_filename = f"{stem}_{timestamp}.txt"
                txt_path = os.path.join(self.output_dir, txt_filename)

                segments = result.get("segments", collected_segments)
                export_txt(segments, txt_path, include_timestamps=True)

                self.after(0, lambda: self._on_transcription_finished(
                    bot_card, status_label, btn_cancel, prog_bar, text_box, result, txt_path
                ))

            except Exception as e:
                self.after(0, lambda: self._on_transcription_error(status_label, btn_cancel, prog_bar, e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_transcription_finished(self, card, status_label, btn_cancel, prog_bar, text_box, result, txt_path):
        prog_bar.set(1.0)
        prog_bar.configure(progress_color="#10b981")
        btn_cancel.grid_remove()

        full_text = text_box.get("1.0", "end").strip()
        if not full_text:
            text_box.insert("1.0", "(Nenhuma fala identificada no áudio)")
            full_text = "(Vazio)"

        status_label.configure(
            text=f"Transcrição Concluída  •  Idioma: {result.get('language', 'auto').upper()}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10b981",
        )

        # Rodapé do card com caminho salvo e botões
        footer_card = ctk.CTkFrame(card, fg_color="transparent")
        footer_card.pack(fill="x", padx=15, pady=(0, 12))

        lbl_saved = ctk.CTkLabel(
            footer_card,
            text=f"💾 Salvo em: {Path(txt_path).name}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        lbl_saved.pack(side="left")

        # Botão Copiar
        btn_copy = ctk.CTkButton(
            footer_card,
            text="📋 Copiar",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            command=lambda: self._copy_to_clipboard(full_text, btn_copy),
        )
        btn_copy.pack(side="right", padx=(6, 0))

        # Botão Abrir TXT
        btn_open = ctk.CTkButton(
            footer_card,
            text="📄 Abrir TXT",
            width=90,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            border_color=("gray60", "gray40"),
            text_color=("gray20", "gray80"),
            command=lambda: self._open_file(txt_path),
        )
        btn_open.pack(side="right", padx=(6, 0))

        self._reset_input_state()

    def _on_transcription_cancelled(self, status_label, btn_cancel, prog_bar):
        btn_cancel.grid_remove()
        prog_bar.set(1.0)
        prog_bar.configure(progress_color="#f59e0b")
        status_label.configure(
            text="⏹ Transcrição cancelada pelo usuário.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f59e0b",
        )
        self._reset_input_state()

    def _on_transcription_error(self, status_label, btn_cancel, prog_bar, error):
        btn_cancel.grid_remove()
        prog_bar.set(1.0)
        prog_bar.configure(progress_color="#ef4444")
        status_label.configure(
            text=f"Erro durante o processamento: {error}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ef4444",
        )
        self._reset_input_state()

    def _reset_input_state(self):
        self._is_processing = False
        self.btn_select_file.configure(state="normal")
        self.lbl_drop.configure(text="📥  Arraste e solte o arquivo aqui (áudio ou vídeo)...")

    def _copy_to_clipboard(self, text: str, button):
        self.clipboard_clear()
        self.clipboard_append(text)
        button.configure(text="✅ Copiado!")
        self.after(1500, lambda: button.configure(text="📋 Copiar"))

    def _open_file(self, file_path: str):
        try:
            subprocess.run(["xdg-open", file_path], check=False)
        except Exception:
            pass


def main():
    app = TranscritorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
