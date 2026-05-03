"""
C.O.A - Council of Agents
=========================
Central Configuration File
"""

import os
from pathlib import Path

# ==================== Project Paths ====================
BASE_DIR = Path(__file__).resolve().parent.parent

# Load secrets and overrides from COA_Project/.env (before other env reads below)
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ==================== LLM Configuration ====================
# COA_LLM_PROVIDER: ollama (default, local) | gemini (Google Gemini API).
# Put secrets in COA_Project/.env — see .env.example
_raw_llm_provider = (os.environ.get("COA_LLM_PROVIDER", "ollama") or "ollama").strip().lower()
# السحابي = Gemini فقط (أسماء قديمة openai/external تُعامل كـ gemini لتفادي الرجوع لـ ollama بالخطأ).
if _raw_llm_provider in ("gemini", "google", "openai", "external", "api", "cloud"):
    LLM_PROVIDER = "gemini"
else:
    LLM_PROVIDER = "ollama"

LLM_MODEL = os.environ.get("COA_LLM_MODEL", "llama3.1").strip() or "llama3.1"
# مفتاح Gemini: أي من المتغيرات التالية (CrewAI يقرأ GOOGLE_API_KEY أيضاً داخلياً).
LLM_GEMINI_API_KEY = (
    (os.environ.get("COA_GEMINI_API_KEY") or "").strip()
    or (os.environ.get("COA_LLM_API_KEY") or "").strip()
    or (os.environ.get("GOOGLE_API_KEY") or "").strip()
    or (os.environ.get("GEMINI_API_KEY") or "").strip()
)
LLM_TEMPERATURE = float(os.environ.get("COA_LLM_TEMPERATURE", "0.3") or "0.3")

if LLM_PROVIDER == "ollama":
    _base = os.environ.get("COA_LLM_BASE_URL", "http://localhost:11434").strip().rstrip("/")
    LLM_BASE_URL = _base or "http://localhost:11434"
else:
    # Gemini: عادةً فارغ (مفتاح AI Studio). يُترك للتوسعات لاحقاً (Vertex إلخ).
    _base = (os.environ.get("COA_LLM_BASE_URL") or "").strip().rstrip("/")
    LLM_BASE_URL = _base


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        v = int(os.environ.get(name, str(default)) or str(default))
        return max(lo, min(hi, v))
    except ValueError:
        return default


# CrewAI council: full step logs (huge JSON in terminal). Default off for readable CLI.
_COUNCIL_VERBOSE = os.environ.get("COA_COUNCIL_VERBOSE", "").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Council speed: smaller snapshot + fewer agent iterations = faster PHASE 2.9 (see .env.example)
COUNCIL_SNAPSHOT_MAX_CONN = _int_env("COA_COUNCIL_MAX_CONN", 18, 5, 120)
COUNCIL_SNAPSHOT_MAX_PROC = _int_env("COA_COUNCIL_MAX_PROC", 22, 8, 120)
COUNCIL_RAW_JSON_MAX = _int_env("COA_COUNCIL_RAW_JSON_MAX", 48_000, 6_000, 250_000)
COUNCIL_THREATS_JSON_MAX = _int_env("COA_COUNCIL_THREATS_JSON_MAX", 32_000, 4_000, 150_000)
# Fewer iterations = faster council (each task may still invoke the LLM multiple times internally).
COUNCIL_MAX_ITER = _int_env("COA_COUNCIL_MAX_ITER", 2, 1, 15)
# Hard cap on completion length per LLM call (Ollama/OpenAI-compatible); main lever for wall-clock time.
COUNCIL_MAX_OUTPUT_TOKENS = _int_env("COA_COUNCIL_MAX_OUTPUT_TOKENS", 2048, 256, 8192)
COUNCIL_LLM_TIMEOUT_SEC = float(
    os.environ.get("COA_COUNCIL_LLM_TIMEOUT", "300") or "300"
)
if COUNCIL_LLM_TIMEOUT_SEC < 30:
    COUNCIL_LLM_TIMEOUT_SEC = 30.0
if COUNCIL_LLM_TIMEOUT_SEC > 1200:
    COUNCIL_LLM_TIMEOUT_SEC = 1200.0

# ==================== Agent Configuration ====================
# memory=False: CrewAI "Unified Memory" needs OpenAI/Chroma embedder keys without extra setup.
AGENT_CONFIG = {
    "verbose": _COUNCIL_VERBOSE,
    "allow_delegation": False,
    "max_iter": COUNCIL_MAX_ITER,
    "max_tokens": COUNCIL_MAX_OUTPUT_TOKENS,
    "memory": False,
}

# ==================== Security Rules ====================
# قوائم بيضاء للعمليات الموثوقة
TRUSTED_PROCESSES = [
    "explorer.exe", "svchost.exe", "System", "Registry",
    "csrss.exe", "winlogon.exe", "services.exe", "lsass.exe",
    "chrome.exe", "firefox.exe", "msedge.exe",
]

# مجلدات مشبوهة (يجب فحص أي عملية تعمل منها)
SUSPICIOUS_PATHS = [
    "temp", "tmp", "appdata\\local\\temp",
    "downloads", "public", "programdata\\temp",
]

# منافذ مشبوهة معروفة
SUSPICIOUS_PORTS = [
    4444, 5555, 6666, 1337, 31337,  # منافذ Metasploit/hacking شائعة
    8080, 9090,  # بروكسيات مشبوهة أحياناً
]

# عناوين IP موثوقة (local networks)
TRUSTED_IP_RANGES = [
    "127.", "192.168.", "10.", "172.16.", "172.17.",
    "172.18.", "172.19.", "172.20.", "172.21.",
]

# ==================== Report Settings ====================
REPORT_FILENAME = "COA_Audit_Report.txt"
REPORT_PATH = REPORTS_DIR / REPORT_FILENAME

# ==================== UI Settings ====================
UI_COLORS = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "danger": "red",
    "info": "blue",
    "accent": "magenta",
}

# ==================== Human-in-the-Loop ====================
REQUIRE_CONFIRMATION = True  # صمام الأمان - لا تغيّره إلا إذا كنت تعرف ماذا تفعل
AUTO_EXECUTE_SAFE_COMMANDS = False  # منع التنفيذ التلقائي حتى للأوامر الآمنة
