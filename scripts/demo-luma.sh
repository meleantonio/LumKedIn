#!/usr/bin/env bash
# One-command demo launcher. Point KYM_MEMBERS at your (private, gitignored) CSV.
# Usage: KYM_MEMBERS=data/private/<event>.csv KYM_DATASET=<dataset> scripts/demo-luma.sh [--backend tfidf]
set -euo pipefail
cd "$(dirname "$0")/.."
: "${KYM_MEMBERS:?set KYM_MEMBERS to your private members CSV (e.g. data/private/<event>.csv)}"
[ -f "$KYM_MEMBERS" ] || { echo "Members file not found: $KYM_MEMBERS" >&2; exit 1; }
export KYM_MEMBERS
export KYM_DATASET="${KYM_DATASET:-luma-eveur09a}"
export KYM_COMMUNITY="${KYM_COMMUNITY:-Grok Bot London hackathon}"
[ "${1:-}" = "--backend" ] && export KYM_BACKEND="${2:-tfidf}"
[ -n "${COGNEE_API_KEY:-}" ] && echo "Cognee key: present" || echo "Cognee key: not set (TF-IDF fallback)"
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
exec "$PY" -m streamlit run app.py --server.headless true --server.port "${PORT:-8501}"
