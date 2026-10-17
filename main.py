#!/usr/bin/env python3
"""
Transcritor Local — Ponto de entrada.

Transcritor de áudio e vídeo para texto, 100% offline.
Utiliza faster-whisper (CTranslate2) com interface CustomTkinter.
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Inicializa e executa a aplicação."""
    from src.ui.app import TranscritorApp

    app = TranscritorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
