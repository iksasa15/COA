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


def _demo_system_data() -> Dict[str, Any]:
    """
    Synthetic host shaped like a real collector snapshot: two distinct PIDs so
    ThreatAnalyzer yields one network threat and one process threat (no duplicate row
    for the same executable).
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
        ],
        # One process row only (88110 appears only on the connection — avoids duplicate
        # Network + Process threat for the same PID).
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

    council_result = None
    reporter.log_event("COUNCIL", "Council not run for this session")

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
