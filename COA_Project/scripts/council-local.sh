#!/usr/bin/env bash
# مجلس CrewAI — Ollama محلي (يتجاهل COA_LLM_PROVIDER في .env لهذا التشغيل فقط)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f venv/bin/activate ]]; then
  # shellcheck disable=1091
  source venv/bin/activate
fi
export COA_LLM_PROVIDER=ollama
export COA_LLM_MODEL="${COA_LLM_MODEL:-llama3.1}"
export COA_LLM_BASE_URL="${COA_LLM_BASE_URL:-http://localhost:11434}"
exec python main.py --council "$@"
