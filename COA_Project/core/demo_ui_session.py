"""
Synthetic scan bundle for optional API seeding — no SystemDataCollector.

POST /api/demo/seed-session only (no host reads). Logs avoid labeling data as «fake» in UI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

from agents.defense_context_analyzer import DefenseContextAnalyzer
from agents.ics_specialist import ICSSpecialistAgent
from agents.incident_reporter import IncidentReporter
from core.mitre_deep_analysis import build_mitre_deep_bundle
from core.threat_analyzer import ThreatAnalyzer
from ics_analyzer.demo_fixture import load_presentation_demo_ot_ics
from utils.report_generator import ReportGenerator

# Static narrative for dashboard «Multi-AI» tab in demo sessions (no LLM round-trip).
DEMO_COUNCIL_REPORT = """
═══════════════════════════════════════════════════════════════════
  C.O.A — Multi-Agent Council (جلسة مخبرية ثابتة للواجهة)
═══════════════════════════════════════════════════════════════════

[Threat Hunter] الأولوية: اتصال ESTABLISHED من PID 88110 (beacon_loader) إلى 198.51.100.77:4444
مع مسار تحت /var/tmp — يطابق C2 شائع. تهديد ثانٍ: عملية svch0st_cloned (PID 88122) انتحال اسم.

[Defense Analyst] يُوصى بعزل العقدة عن الشبكة الإنتاجية، أخذ صورة ذاكرة للعمليتين،
ومراجعة جدول الاتصالات للأقران على نفس VLAN.

[Incident Lead] خطوات فورية: (1) احتفاظ بالأدلة (2) تدوين وقت الاكتشاف (3) تنسيق مع SOC
قبل أي إجراء حجب واسع قد يؤثر على OT المجاور.

[ICS Liaison] جدول OT في الجلسة يعرض ارتباطات بروتوكولات صناعية من حزمة العرض — راجع
لوحة OT/ICS للتفاصيل الكاملة.

───────────────────────────────────────────────────────────────────
ملاحظة: نص جاهز للعرض — لا يستدعي نموذجاً حياً في وضع التحميل السريع.
───────────────────────────────────────────────────────────────────
""".strip()


def _demo_system_data() -> Dict[str, Any]:
    """
    Rich lab snapshot: benign traffic + one suspicious connection; benign processes +
    one suspicious process — two threats from different PIDs (no duplicate analyzer rows).
    """
    return {
        "system_info": {
            "hostname": "SEC-LAB-WS-01",
            "platform": "Linux",
            "platform_release": "6.x-lab",
            "architecture": "x86_64",
            "processor": "lab",
        },
        "network_connections": [
            {
                "pid": 88110,
                "process_name": "beacon_loader",
                "process_path": "/var/tmp/.stage/beacon_loader",
                "local_address": "192.168.20.15:52401",
                "remote_address": "198.51.100.77:4444",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
            {
                "pid": 1204,
                "process_name": "chrome",
                "process_path": "/opt/google/chrome/chrome",
                "local_address": "192.168.20.15:44102",
                "remote_address": "142.251.167.14:443",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
            {
                "pid": 884,
                "process_name": "systemd-resolved",
                "process_path": "/usr/lib/systemd/systemd-resolved",
                "local_address": "127.0.0.1:5353",
                "remote_address": "1.1.1.1:53",
                "status": "ESTABLISHED",
                "protocol": "UDP",
            },
            {
                "pid": 1122,
                "process_name": "sshd",
                "process_path": "/usr/sbin/sshd",
                "local_address": "192.168.20.15:22",
                "remote_address": "192.168.20.1:51988",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
        ],
        # 88110 appears only on the connection row (avoids duplicate Network+Process threat).
        "processes": [
            {
                "pid": 88122,
                "name": "svch0st_cloned",
                "path": "/var/tmp/svch0st_cloned",
                "cpu_percent": 6.5,
                "memory_percent": 2.0,
                "user": "labuser",
                "threads": 2,
                "status": "running",
                "started_at": "2024-06-01 10:18:00",
            },
            {
                "pid": 1204,
                "name": "chrome",
                "path": "/opt/google/chrome/chrome",
                "cpu_percent": 14.2,
                "memory_percent": 8.4,
                "user": "labuser",
                "threads": 48,
                "status": "running",
                "started_at": "2024-06-01 09:05:00",
            },
            {
                "pid": 884,
                "name": "systemd-resolved",
                "path": "/usr/lib/systemd/systemd-resolved",
                "cpu_percent": 0.4,
                "memory_percent": 0.2,
                "user": "systemd-resolve",
                "threads": 1,
                "status": "sleeping",
                "started_at": "2024-06-01 08:00:00",
            },
            {
                "pid": 1122,
                "name": "sshd",
                "path": "/usr/sbin/sshd",
                "cpu_percent": 0.1,
                "memory_percent": 0.1,
                "user": "root",
                "threads": 1,
                "status": "running",
                "started_at": "2024-06-01 10:00:00",
            },
            {
                "pid": 3301,
                "name": "node",
                "path": "/usr/bin/node",
                "cpu_percent": 3.8,
                "memory_percent": 1.9,
                "user": "labuser",
                "threads": 11,
                "status": "running",
                "started_at": "2024-06-01 09:40:00",
            },
        ],
        "collection_duration": 0.12,
    }


def build_demo_ui_seed_bundle() -> Tuple[Dict[str, Any], Dict[str, Any], ReportGenerator]:
    """
    Returns:
      - payload: same keys as POST /api/scan success body
      - last_block: dict for web_api._last
      - reporter
    """
    reporter = ReportGenerator()
    reporter.log_event("SYSTEM", "Prepared bundled scan session (no live host collection)")

    system_data = _demo_system_data()
    reporter.log_event(
        "DATA",
        f"Tables ready: {len(system_data['network_connections'])} connections, "
        f"{len(system_data['processes'])} processes",
    )

    reporter.log_event("ANALYSIS", "Running threat analysis…")
    analysis = ThreatAnalyzer.full_analysis(system_data)
    for t in analysis.get("threats", []):
        reporter.log_threat(t)

    reporter.log_event("DEFENSE_CONTEXT", "Running Defense Context Analyzer (Agent #5)…")
    defense_context = DefenseContextAnalyzer.analyze(system_data, analysis)

    reporter.log_event("OT_ICS", "Loading OT/ICS bundle…")
    ot_ics = load_presentation_demo_ot_ics()
    ot_ics["presentation_demo"] = False
    ot_ics["ics_specialist"] = ICSSpecialistAgent.assess(ot_ics)

    mitre_deep = build_mitre_deep_bundle(
        analysis,
        defense_context,
        system_data,
        system_data["system_info"],
        ot_ics,
    )

    classification = IncidentReporter.classify_incident(analysis)
    summary = IncidentReporter.executive_summary(
        system_data["system_info"], analysis, classification, defense_context
    )

    council_result: Dict[str, Any] = {
        "ok": True,
        "report": DEMO_COUNCIL_REPORT,
        "error": None,
    }
    reporter.log_event(
        "COUNCIL",
        "Demo Multi-AI panel: static council narrative attached (no live LLM for this session)",
    )
    reporter.log_event("SCAN", "Demo bundle ready — Threats / Processes / Network / OT / Multi-AI / Logs populated")
    reporter.log_event("EXPORT", "Navigator layer and defense_context available for MITRE pages")

    completed_at = datetime.now().isoformat()
    last_block = {
        "system_data": system_data,
        "analysis": analysis,
        "classification": classification,
        "summary": summary,
        "defense_context": defense_context,
        "mitre_deep": mitre_deep,
        "ot_ics": ot_ics,
        "dry_run": False,
        "council": council_result,
        "completed_at": completed_at,
    }

    max_proc = 250
    max_conn = 400
    payload: Dict[str, Any] = {
        "ok": True,
        "demo_seed": True,
        "system_info": system_data["system_info"],
        "analysis": analysis,
        "classification": classification,
        "summary": summary,
        "defense_context": defense_context,
        "mitre_deep": mitre_deep,
        "ot_ics": ot_ics,
        "collection_duration": system_data.get("collection_duration", 0),
        "processes": system_data["processes"][:max_proc],
        "processes_total": len(system_data["processes"]),
        "network_connections": system_data["network_connections"][:max_conn],
        "connections_total": len(system_data["network_connections"]),
        "events": reporter.events,
        "council": council_result,
    }

    return payload, last_block, reporter
