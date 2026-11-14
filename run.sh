#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Bitte zuerst die Installation aus README.md durchführen.' >&2
  exit 1
fi
export EOT_DATA_DIR="${EOT_DATA_DIR:-$PWD/data}"
export HF_HOME="${HF_HOME:-$EOT_DATA_DIR/models/hf-cache}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$PWD/.cache/matplotlib}"
case "${1:-serve}" in
  serve) exec .venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port "${PORT:-8765}" ;;
  prepare-models) exec .venv/bin/python -m eot_eval.cli prepare-models ;;
  doctor) exec .venv/bin/python -m eot_eval.cli doctor ;;
  test) exec .venv/bin/python -m pytest ;;
  *) exec .venv/bin/python -m eot_eval.cli "$@" ;;
esac
