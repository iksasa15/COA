"""
Council of Agents — CrewAI + Ollama (محلي فقط)
==============================================
الوكلاء الثلاثة يشتركون في LLM واحد عبر Ollama:
  COA_LLM_BASE_URL (افتراضي http://localhost:11434) + COA_LLM_MODEL (مثل llama3.1)
"""

import json
import requests
from typing import Any, Dict

from utils.logger import logger
from config.settings import (
    AGENT_CONFIG,
    COUNCIL_LLM_TIMEOUT_SEC,
    COUNCIL_MAX_OUTPUT_TOKENS,
    COUNCIL_RAW_JSON_MAX,
    COUNCIL_SNAPSHOT_MAX_CONN,
    COUNCIL_SNAPSHOT_MAX_PROC,
    COUNCIL_THREATS_JSON_MAX,
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_TEMPERATURE,
)


class OllamaConnectionError(Exception):
    """خطأ مخصص لمشاكل الاتصال بـ Ollama"""
    pass


def check_ollama_running(base_url: str = LLM_BASE_URL) -> bool:
    """
    التحقق إذا كان Ollama يعمل
    Returns: True/False
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


def check_model_available(model_name: str, base_url: str = LLM_BASE_URL) -> bool:
    """
    التحقق إذا كان النموذج مثبتاً في Ollama
    Returns: True/False
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        if response.status_code != 200:
            return False

        data = response.json()
        installed_models = [m.get('name', '').split(':')[0] for m in data.get('models', [])]
        model_base = model_name.split(':')[0]

        return model_base in installed_models
    except Exception:
        return False


def diagnose_ollama() -> dict:
    """
    تشخيص شامل لـ Ollama - يساعد على معرفة المشكلة
    Returns: dict بتفاصيل التشخيص
    """
    diagnosis = {
        'ollama_running': False,
        'model_available': False,
        'model_name': LLM_MODEL,
        'base_url': LLM_BASE_URL,
        'error': None,
        'suggestion': None,
    }

    # فحص 1: هل Ollama يعمل؟
    if not check_ollama_running():
        diagnosis['error'] = 'Ollama is not running'
        diagnosis['suggestion'] = (
            'Start Ollama by running: ollama serve\n'
            'Or download Ollama from: https://ollama.com/download'
        )
        return diagnosis

    diagnosis['ollama_running'] = True

    # فحص 2: هل النموذج متوفر؟
    if not check_model_available(LLM_MODEL):
        diagnosis['error'] = f"Model '{LLM_MODEL}' not found"
        diagnosis['suggestion'] = (
            f'Download the model by running: ollama pull {LLM_MODEL}\n'
            f'Or change LLM_MODEL in config/settings.py to an installed model'
        )
        return diagnosis

    diagnosis['model_available'] = True
    return diagnosis


def diagnose_llm() -> dict:
    """
    جاهزية مجلس CrewAI — Ollama محلي فقط.

    يعيد على الأقل: provider, model_name, model_available, error, suggestion،
    و ollama_running, base_url.
    """
    d = diagnose_ollama()
    d["provider"] = "ollama"
    return d


# ==================== Lazy Imports for CrewAI ====================
# نستخدم lazy imports لأن CrewAI ثقيل ولتجنب أخطاء عند فحص النظام فقط

def _get_crewai():
    """استيراد CrewAI فقط عند الحاجة"""
    try:
        from crewai import Agent, Crew, LLM, Process, Task

        return Agent, Task, Crew, Process, LLM
    except ImportError as e:
        raise ImportError(
            f"CrewAI not installed: {e}\n"
            f"Install with: pip install crewai"
        )


class CouncilOfAgents:
    """
    مجلس الوكلاء الكامل — يدير الوكلاء الثلاثة عبر LLM محلي

    Architecture:
        ┌──────────────────────────────────────────┐
        │  Ollama (http://localhost:11434)         │
        │  └── llama3.1 model                      │
        └─────────────┬────────────────────────────┘
                      │
            ┌─────────┼─────────┐
            ▼         ▼         ▼
        ┌───────┐ ┌───────┐ ┌───────┐
        │Agent 1│ │Agent 2│ │Agent 3│
        │(Eye)  │ │(Brain)│ │(Plan) │
        └───────┘ └───────┘ └───────┘
            │         │         │
            └─────────┼─────────┘
                      ▼
              CrewAI orchestrator
    """

    def __init__(self, auto_diagnose: bool = True):
        """
        تهيئة المجلس

        Args:
            auto_diagnose: إذا True، يقوم بتشخيص Ollama قبل البدء
        """
        # تشخيص Ollama قبل تحميل CrewAI
        if auto_diagnose:
            diagnosis = diagnose_llm()
            if not diagnosis.get("model_available"):
                error_msg = (
                    f"\n{'='*60}\n"
                    f"❌ LLM / Council Setup Issue ({diagnosis.get('provider', 'ollama')})\n"
                    f"{'='*60}\n"
                    f"Error:      {diagnosis.get('error')}\n"
                    f"Model:      {diagnosis.get('model_name')}\n"
                    f"URL:        {diagnosis.get('base_url')}\n\n"
                    f"💡 How to fix:\n{diagnosis.get('suggestion')}\n"
                    f"{'='*60}\n"
                )
                logger.error(error_msg)
                raise OllamaConnectionError(error_msg)

            logger.info(
                f"✓ Ollama is running with {diagnosis['model_name']}",
                base_url=diagnosis.get("base_url"),
            )

        # الآن نحمّل CrewAI ونبني الوكلاء
        Agent, Task, Crew, Process, LLM = _get_crewai()

        self.Agent = Agent
        self.Task = Task
        self.Crew = Crew
        self.Process = Process

        self.llm = self._initialize_llm(LLM)

        # بناء الوكلاء الثلاثة
        self.data_collector = self._create_data_collector()
        self.threat_hunter = self._create_threat_hunter()
        self.solution_advisor = self._create_solution_advisor()

        logger.info("Council of Agents initialized successfully")

    def _initialize_llm(self, LLMClass):
        """تهيئة CrewAI LLM — Ollama محلي فقط."""
        try:
            common = dict(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                max_tokens=COUNCIL_MAX_OUTPUT_TOKENS,
                timeout=COUNCIL_LLM_TIMEOUT_SEC,
            )
            llm = LLMClass(
                provider="ollama",
                base_url=LLM_BASE_URL,
                **common,
            )
            log_url = LLM_BASE_URL

            logger.info(
                f"LLM initialized: provider=ollama model={LLM_MODEL} @ {log_url} "
                f"(max_tokens={COUNCIL_MAX_OUTPUT_TOKENS} timeout={COUNCIL_LLM_TIMEOUT_SEC}s)",
                model=LLM_MODEL,
                provider="ollama",
                base_url=log_url,
                max_tokens=COUNCIL_MAX_OUTPUT_TOKENS,
            )
            return llm
        except Exception as e:
            hint = (
                f"Make sure:\n"
                f"  1. Ollama is running: ollama serve\n"
                f"  2. Model is installed: ollama pull {LLM_MODEL}"
            )
            raise OllamaConnectionError(
                f"Failed to initialize LLM (provider=ollama):\n"
                f"  Model: {LLM_MODEL}\n"
                f"  Error: {e}\n\n"
                f"{hint}"
            )

    # ==================== Agent 1: The Eye ====================
    def _create_data_collector(self):
        """الوكيل الأول: جامع البيانات"""
        return self.Agent(
            role="System Data Collector",
            goal=(
                "Gather comprehensive raw data from the system including "
                "network connections, running processes, and system metrics. "
                "Format everything into clean, structured JSON."
            ),
            backstory=(
                "You are 'The Eye' of the council — a meticulous data collector "
                "with years of experience in system forensics. Your job is NOT "
                "to analyze or judge; only to observe and report faithfully. "
                "You never miss a detail and always produce clean, structured output."
            ),
            llm=self.llm,
            **AGENT_CONFIG,
        )

    # ==================== Agent 2: The Brain ====================
    def _create_threat_hunter(self):
        """الوكيل الثاني: صائد التهديدات"""
        return self.Agent(
            role="Cybersecurity Threat Hunter",
            goal=(
                "Analyze system data to identify suspicious patterns, anomalies, "
                "and potential security threats. Classify each threat by severity "
                "(CRITICAL, HIGH, MEDIUM, LOW) with clear reasoning."
            ),
            backstory=(
                "You are 'The Brain' — an elite threat hunter trained on thousands "
                "of malware samples and attack patterns. You think like an attacker "
                "to defend like a pro. You focus on: unusual network connections, "
                "processes running from temp folders, suspicious ports, and "
                "behavioral anomalies. You are precise and never cry wolf."
            ),
            llm=self.llm,
            **AGENT_CONFIG,
        )

    # ==================== Agent 3: The Strategist ====================
    def _create_solution_advisor(self):
        """الوكيل الثالث: مستشار الحلول"""
        return self.Agent(
            role="Security Solution Strategist",
            goal=(
                "For each identified threat, generate precise, safe remediation "
                "commands. Always prefer reversible actions. Mark risk level for "
                "each command. NEVER approve auto-execution — human must decide."
            ),
            backstory=(
                "You are 'The Strategist' — a senior security architect who has "
                "remediated thousands of incidents. You know that a wrong command "
                "can cause more damage than the threat itself. You craft surgical "
                "fixes: taskkill, firewall rules, registry cleanups — all with "
                "clear explanations so the human operator can make informed decisions."
            ),
            llm=self.llm,
            **AGENT_CONFIG,
        )

    # ==================== Tasks ====================
    def create_collection_task(self, raw_data: str):
        return self.Task(
            description=(
                f"Review the following raw system data and structure it:\n\n"
                f"{raw_data}\n\n"
                "Output a concise structured summary highlighting key observations. "
                "Be brief: prioritize anomalies and high-signal items; avoid repeating every benign row."
            ),
            agent=self.data_collector,
            expected_output="Short structured summary (roughly under 1200 words).",
        )

    def create_analysis_task(self, threats_data: str):
        return self.Task(
            description=(
                f"Analyze these detected threats and enrich each with explanations:\n\n"
                f"{threats_data}\n\n"
                "For each threat, briefly explain WHY it's suspicious and the potential impact. "
                "If the list is long, summarize clusters first, then detail only CRITICAL/HIGH."
            ),
            agent=self.threat_hunter,
            expected_output="Concise enriched analysis (prioritize severity).",
        )

    def create_solution_task(self, analyzed_threats: str):
        return self.Task(
            description=(
                f"For each analyzed threat, provide remediation:\n\n"
                f"{analyzed_threats}\n\n"
                "Include: exact command, risk level, reversibility, one-line explanation per item. "
                "Keep the plan compact. REMEMBER: Human decides — never auto-execute."
            ),
            agent=self.solution_advisor,
            expected_output="Compact actionable remediation plan.",
        )

    # ==================== Orchestration ====================
    def run_council(self, raw_data: str, threats_data: str) -> str:
        """
        تشغيل المجلس الكامل - الوكلاء الثلاثة يعملون بالتسلسل
        """
        logger.info("Starting Council of Agents collaboration")

        task1 = self.create_collection_task(raw_data)
        task2 = self.create_analysis_task(threats_data)
        task3 = self.create_solution_task(threats_data)

        crew = self.Crew(
            agents=[
                self.data_collector,
                self.threat_hunter,
                self.solution_advisor,
            ],
            tasks=[task1, task2, task3],
            process=self.Process.sequential,
            verbose=AGENT_CONFIG.get("verbose", False),
        )

        try:
            result = crew.kickoff()
            logger.info("Council collaboration completed")
            return str(result)
        except Exception:
            # Single user-facing + COA log in run_council_on_scan (avoid duplicate ERROR lines).
            raise


def summarize_for_council(
    system_data: Dict[str, Any],
    max_conns: int | None = None,
    max_procs: int | None = None,
) -> str:
    """Trim scan payload so CrewAI + Ollama stay within practical context limits (tunable via .env)."""
    mc = COUNCIL_SNAPSHOT_MAX_CONN if max_conns is None else max_conns
    mp = COUNCIL_SNAPSHOT_MAX_PROC if max_procs is None else max_procs
    snap = {
        "system_info": system_data.get("system_info"),
        "network_connections": (system_data.get("network_connections") or [])[:mc],
        "processes": (system_data.get("processes") or [])[:mp],
        "truncation": {
            "connections_shown": min(mc, len(system_data.get("network_connections") or [])),
            "connections_total": len(system_data.get("network_connections") or []),
            "processes_shown": min(mp, len(system_data.get("processes") or [])),
            "processes_total": len(system_data.get("processes") or []),
        },
    }
    raw = json.dumps(snap, indent=2, default=str)
    if len(raw) > COUNCIL_RAW_JSON_MAX:
        return raw[:COUNCIL_RAW_JSON_MAX] + "\n…[truncated]"
    return raw


def _shorten_council_api_error(message: str) -> str:
    """اقتصاص رسائل أخطاء طويلة من CrewAI/Ollama للعرض في الطرفية."""
    if len(message) > 1400:
        return message[:1400] + "\n…[truncated]"
    return message


def run_council_on_scan(system_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the 3-agent CrewAI pipeline on top of an existing scan (LLM must be configured).

    Returns:
        {"ok": bool, "report": str | None, "error": str | None}
    """
    try:
        raw = summarize_for_council(system_data)
        threats_list = analysis.get("threats") or []
        threats_json = json.dumps(threats_list, indent=2, default=str)
        if len(threats_json) > COUNCIL_THREATS_JSON_MAX:
            threats_json = threats_json[:COUNCIL_THREATS_JSON_MAX] + "\n…[truncated]"
        council = CouncilOfAgents()
        report = council.run_council(raw, threats_json)
        return {"ok": True, "report": str(report), "error": None}
    except OllamaConnectionError as e:
        return {"ok": False, "report": None, "error": _shorten_council_api_error(str(e))}
    except ImportError as e:
        return {
            "ok": False,
            "report": None,
            "error": f"Missing dependency: {e}. Install: pip install crewai langchain-community",
        }
    except Exception as e:
        err = _shorten_council_api_error(str(e))
        logger.error(f"Council scan failed: {err}")
        return {"ok": False, "report": None, "error": err}


# ==================== Standalone Test ====================
def test_connection():
    """
    اختبار سريع للتأكد من أن كل شيء جاهز
    شغّل هذا قبل استخدام النظام:
        python -m agents.council
    """
    print("\n" + "=" * 60)
    print("  C.O.A — Connection Test")
    print("=" * 60 + "\n")

    print("[1] Checking LLM (provider=ollama)...")
    diagnosis = diagnose_llm()

    if diagnosis.get("ollama_running"):
        print(f"    ✓ Ollama is running at {diagnosis.get('base_url')}")
    else:
        print(f"    ❌ {diagnosis.get('error')}")
        print(f"    💡 {diagnosis.get('suggestion')}")
        return False
    print(f"\n[2] Checking model '{diagnosis.get('model_name')}'...")

    if diagnosis.get("model_available"):
        print("    ✓ Model / credentials ready")
    else:
        print(f"    ❌ {diagnosis.get('error')}")
        print(f"    💡 {diagnosis.get('suggestion')}")
        return False

    print("\n[3] Initializing Council of Agents...")
    try:
        council = CouncilOfAgents()
        print("    ✓ All 3 agents created successfully")
        print(f"    ✓ Agent 1: {council.data_collector.role}")
        print(f"    ✓ Agent 2: {council.threat_hunter.role}")
        print(f"    ✓ Agent 3: {council.solution_advisor.role}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("  ✅ Everything is ready!")
    print("=" * 60)
    print("\nYou can now run:")
    print("  python main.py       # Full scan")
    print("  python gui.py        # Graphical interface")
    print("  python helpdesk_api.py  # REST API")
    print()
    return True


if __name__ == "__main__":
    test_connection()
