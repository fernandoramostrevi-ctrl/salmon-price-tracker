#!/usr/bin/env bash
# Script llamado por cron. Activa el virtualenv y ejecuta el tracker.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

cd "$SCRIPT_DIR"

# Activar virtualenv
source "${VENV_DIR}/bin/activate"

# Ejecutar el tracker
python -m tracker.main
