"""
Synthetic scan bundle for UI demos — no host collection, no council LLM.

Used by POST /api/demo/seed-session so the React app can populate sessionStorage
and /api/last/* endpoints without running SystemDataCollector.
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
    """Minimal shape compatible with ThreatAnalyzer, DefenseContext, MITRE deep, OT fixture."""
    return {
        "system_info": {
            "hostname": "coa-ui-demo",
            "platform": "Demo",
            "platform_release": "seed",
            "architecture": "n/a",
            "processor": "synthetic",
        },
        "network_connections": [
            {
                "pid": 424242,
                "process_name": "svch0st_demo",
                "process_path": "/var/tmp/coa_demo_agent",
                "local_address": "192.168.50.10:52341",
                "remote_address": "198.51.100.77:4444",
                "status": "ESTABLISHED",
                "protocol": "TCP",
            },
        ],
        "processes": [
            {
                "pid": 424242,
                "name": "svch0st_demo",
                "path": "/var/tmp/coa_demo_agent",
                "cpu_percent": 5.0,
                "memory_percent": 4.0,
                "user": "demo",
                "threads": 3,
                "status": "running",
                "started_at": "2020-01-01 00:00:00",
            },
        ],
        "collection_duration": 0.0,
    }


def build_demo_ui_seed_bundle() -> Tuple[Dict[str, Any], Dict[str, Any], ReportGenerator]:
    """
    Returns:
      - payload: same keys as POST /api/scan success body (for JSON + client mirroring)
      - last_block: dict to assign to web_api._last
      - reporter: with events populated
    """
    reporter = ReportGenerator()
    reporter.log_event("SYSTEM", "UI demo seed — synthetic bundle (no live host collection)")

    system_data = _demo_system_data()
    reporter.log_event(
        "DATA",
        f"Synthetic demo: {len(system_data['network_connections'])} connections, "
        f"{len(system_data['processes'])} processes",
    )

    reporter.log_event("ANALYSIS", "Threat analysis on synthetic demo data…")
    analysis = ThreatAnalyzer.full_analysis(system_data)
    for t in analysis.get("threats", []):
        reporter.log_threat(t)

    reporter.log_event("DEFENSE_CONTEXT", "Defense Context Analyzer (Agent #5) on demo data…")
    defense_context = DefenseContextAnalyzer.analyze(system_data, analysis)

    reporter.log_event("OT_ICS", "Presentation OT/ICS fixture for UI demo…")
    ot_ics = load_presentation_demo_ot_ics()
    ot_ics["presentation_demo"] = True
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
    reporter.log_event("COUNCIL", "Skipped in UI demo seed (use full scan for CrewAI council)")

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
    payload = {
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
