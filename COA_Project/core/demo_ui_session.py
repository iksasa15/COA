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
مع مسار تحت /var/tmp — يطابق C2 شائع. اتصال ثانٍ PID 99444 إلى 203.0.113.50:5555 (مرحلة إسقاط).
عملية svch0st_cloned (88122) انتحال اسم؛ pool_update_svc (99333) نمط استهلاك موارد مرتفع مع مسار tmp.

[Defense Analyst] يُوصى بعزل العقدة عن الشبكة الإنتاجية، أخذ صورة ذاكرة للعمليتين،
ومراجعة جدول الاتصالات للأقران على نفس VLAN. راقب نطاق 192.168.20.0/24 للحركات الجانبية.

[Incident Lead] خطوات فورية: (1) احتفاظ بالأدلة (2) تدوين وقت الاكتشاف (3) تنسيق مع SOC
قبل أي إجراء حجب واسع قد يؤثر على OT المجاور. افتح تذكرة P1 مع مالك الأصول.

[ICS Liaison] جدول OT في الجلسة يعرض ارتباطات بروتوكولات صناعية من حزمة العرض — راجع
لوحة OT/ICS للتفاصيل الكاملة.

[Forensics] جمع netstat/ss، جدول العمليات، ولقطات DNS — الحفاظ على سلسلة العهدة.

[SOAR] يمكن ربط قوالب الاستجابة: عزل المضيف، حظر عنوان C2 مؤقتاً، إشعار فريق OT إن وُجدت بوابة مشتركة.

[Comms] مسودة إعلان داخلي: «نشاط مشبوه تحت التحقيق على عقدة مخبرية — لا تأثير على الإنتاج».
""".strip()


def _demo_system_data() -> Dict[str, Any]:
    """
    Expanded lab snapshot: many benign rows + several distinct suspicious PIDs so
    ThreatAnalyzer yields multiple threats without duplicate network+process for the same PID.
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
                "pid": 99444,
                "process_name": "stage_dropper",
                "process_path": "/var/tmp/stage_dropper",
                "local_address": "192.168.20.15:55999",
                "remote_address": "203.0.113.50:5555",
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
            {
                "pid": 4401,
                "process_name": "docker-proxy",
                "process_path": "/usr/bin/docker-proxy",
                "local_address": "0.0.0.0:32768",
                "remote_address": "172.17.0.2:443",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
            {
                "pid": 5502,
                "process_name": "postgres",
                "process_path": "/usr/lib/postgresql/15/bin/postgres",
                "local_address": "127.0.0.1:5432",
                "remote_address": "127.0.0.1:52411",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
            {
                "pid": 6603,
                "process_name": "redis-server",
                "process_path": "/usr/bin/redis-server",
                "local_address": "127.0.0.1:6379",
                "remote_address": "N/A",
                "status": "LISTEN",
                "protocol": "TCP",
            },
            {
                "pid": 7704,
                "process_name": "curl",
                "process_path": "/usr/bin/curl",
                "local_address": "192.168.20.15:53210",
                "remote_address": "151.101.1.140:443",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
            {
                "pid": 8805,
                "process_name": "java",
                "process_path": "/usr/lib/jvm/java-17-openjdk/bin/java",
                "local_address": "192.168.20.15:8080",
                "remote_address": "192.168.20.5:52400",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
        ],
        # 88110 and 99444 are connection-only PIDs (omit from processes to avoid duplicate network+process threats).
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
                "pid": 99333,
                "name": "pool_update_svc",
                "path": "/tmp/pool_update_svc",
                "cpu_percent": 88.0,
                "memory_percent": 2.1,
                "user": "labuser",
                "threads": 6,
                "status": "running",
                "started_at": "2024-06-01 10:22:00",
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
            {
                "pid": 4401,
                "name": "docker-proxy",
                "path": "/usr/bin/docker-proxy",
                "cpu_percent": 0.2,
                "memory_percent": 0.1,
                "user": "root",
                "threads": 4,
                "status": "running",
                "started_at": "2024-06-01 09:12:00",
            },
            {
                "pid": 5502,
                "name": "postgres",
                "path": "/usr/lib/postgresql/15/bin/postgres",
                "cpu_percent": 1.1,
                "memory_percent": 4.2,
                "user": "postgres",
                "threads": 9,
                "status": "running",
                "started_at": "2024-06-01 08:30:00",
            },
            {
                "pid": 6603,
                "name": "redis-server",
                "path": "/usr/bin/redis-server",
                "cpu_percent": 0.8,
                "memory_percent": 0.5,
                "user": "redis",
                "threads": 4,
                "status": "running",
                "started_at": "2024-06-01 08:31:00",
            },
            {
                "pid": 7704,
                "name": "curl",
                "path": "/usr/bin/curl",
                "cpu_percent": 0.0,
                "memory_percent": 0.1,
                "user": "labuser",
                "threads": 1,
                "status": "running",
                "started_at": "2024-06-01 10:25:00",
            },
            {
                "pid": 8805,
                "name": "java",
                "path": "/usr/lib/jvm/java-17-openjdk/bin/java",
                "cpu_percent": 12.0,
                "memory_percent": 14.0,
                "user": "labuser",
                "threads": 42,
                "status": "running",
                "started_at": "2024-06-01 09:50:00",
            },
            {
                "pid": 9011,
                "name": "python3",
                "path": "/usr/bin/python3",
                "cpu_percent": 2.4,
                "memory_percent": 1.2,
                "user": "labuser",
                "threads": 3,
                "status": "running",
                "started_at": "2024-06-01 09:55:00",
            },
            {
                "pid": 9022,
                "name": "tailscaled",
                "path": "/usr/sbin/tailscaled",
                "cpu_percent": 0.3,
                "memory_percent": 0.4,
                "user": "root",
                "threads": 10,
                "status": "running",
                "started_at": "2024-06-01 08:10:00",
            },
        ],
        "collection_duration": 0.38,
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
    reporter.log_event("IOC", "Lab IOCs: 198.51.100.77:4444, 203.0.113.50:5555 — للتدريب فقط")
    reporter.log_event("CORRELATION", "PID 88110 و 99444 اتصالات خارجية؛ 88122 و 99333 عمليات مشبوهة من /var/tmp و /tmp")
    reporter.log_event("HEALTH", "وكلاء المجلس: تقرير ثابت مرفق — لا استدعاء Ollama في جلسة التحميل الوهمي")

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
