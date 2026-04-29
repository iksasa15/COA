"""
C.O.A - Council of Agents
=========================
Central Configuration File
"""

import os
from pathlib import Path

# ==================== Project Paths ====================
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ==================== LLM Configuration ====================
# Local LLM settings (Ollama)
LLM_PROVIDER = "ollama"
LLM_MODEL = "llama3.1"  # غيّرها حسب النموذج المثبت لديك
LLM_BASE_URL = "http://localhost:11434"
LLM_TEMPERATURE = 0.3  # دقة أعلى للتحليل الأمني

# ==================== Agent Configuration ====================
AGENT_CONFIG = {
    "verbose": True,
    "allow_delegation": False,
    "max_iter": 5,
    "memory": True,
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
