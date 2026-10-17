#!/usr/bin/env bash
# Iniciar o Transcritor Local no ambiente virtual

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py
else
    python3 main.py
fi
