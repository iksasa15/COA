#!/usr/bin/env bash
# مجلس CrewAI — Google Gemini (يتجاهل COA_LLM_PROVIDER في .env لهذا التشغيل فقط)
# ضع المفتاح في .env (GOOGLE_API_KEY أو COA_GEMINI_API_KEY) أو صدّرها قبل التشغيل:
#   export GOOGLE_API_KEY=AIza...
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f venv/bin/activate ]]; then
  # shellcheck disable=1091
  source venv/bin/activate
fi
export COA_LLM_PROVIDER=gemini
export COA_LLM_MODEL="${COA_LLM_MODEL:-gemini-2.0-flash}"
exec python main.py --council "$@"
