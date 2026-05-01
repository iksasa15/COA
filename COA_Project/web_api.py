"""
C.O.A Web API — backend for the React dashboard
================================================
Run:  python web_api.py

Then in another terminal:
  cd web && npm install && npm run dev
Open http://localhost:5173
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from agents.defense_context_analyzer import DefenseContextAnalyzer
from agents.ics_specialist import ICSSpecialistAgent
from agents.incident_reporter import IncidentReporter
from config.settings import REPORTS_DIR
from core.data_collector import SystemDataCollector
from core.mitre_deep_analysis import build_mitre_deep_bundle
from ics_analyzer import analyze_ot_ics
from core.threat_analyzer import ThreatAnalyzer
from utils.html_report import HTMLReportGenerator
from utils.logger import logger
from utils.report_generator import ReportGenerator

# Last completed scan (for report downloads)
_last: dict | None = None
_last_reporter: ReportGenerator | None = None

MAX_PROCESSES_RESPONSE = 250
MAX_CONNECTIONS_RESPONSE = 400


def _json_safe(obj):
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return json.loads(json.dumps(obj, default=str))


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://127.0.0.1:5173", "http://localhost:5173"]}},
        supports_credentials=True,
    )

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True, "service": "C.O.A Web API", "time": datetime.now().isoformat()})

    @app.post("/api/scan")
    def scan():
        global _last, _last_reporter
        body = request.get_json(silent=True) or {}
        dry_run = bool(body.get("dry_run", False))

        reporter = ReportGenerator()
        reporter.log_event("SYSTEM", "React UI scan started")

        try:
            reporter.log_event("DATA", "Collecting system data…")
            system_data = SystemDataCollector.collect_all()

            reporter.log_event(
                "DATA",
                f"Collected {len(system_data['network_connections'])} connections, "
                f"{len(system_data['processes'])} processes",
            )

            reporter.log_event("ANALYSIS", "Running threat analysis…")
            analysis = ThreatAnalyzer.full_analysis(system_data)

            for t in analysis.get("threats", []):
                reporter.log_threat(t)

            reporter.log_event("DEFENSE_CONTEXT", "Running Defense Context Analyzer (Agent #5)…")
            defense_context = DefenseContextAnalyzer.analyze(system_data, analysis)
            reporter.log_event("OT_ICS", "Passive OT/ICS correlation (ports/processes only)…")
            ot_ics = analyze_ot_ics(system_data)
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

            _last = {
                "system_data": system_data,
                "analysis": analysis,
                "classification": classification,
                "summary": summary,
                "defense_context": defense_context,
                "mitre_deep": mitre_deep,
                "ot_ics": ot_ics,
                "dry_run": dry_run,
                "completed_at": datetime.now().isoformat(),
            }
            _last_reporter = reporter

            payload = {
                "ok": True,
                "system_info": system_data["system_info"],
                "analysis": analysis,
                "classification": classification,
                "summary": summary,
                "defense_context": defense_context,
                "mitre_deep": mitre_deep,
                "ot_ics": ot_ics,
                "collection_duration": system_data.get("collection_duration", 0),
                "processes": system_data["processes"][:MAX_PROCESSES_RESPONSE],
                "processes_total": len(system_data["processes"]),
                "network_connections": system_data["network_connections"][:MAX_CONNECTIONS_RESPONSE],
                "connections_total": len(system_data["network_connections"]),
                "events": reporter.events,
            }
            return jsonify(_json_safe(payload))
        except Exception as e:
            logger.error(f"Scan failed: {e}\n{traceback.format_exc()}")
            reporter.log_event("ERROR", str(e))
            return (
                jsonify({"ok": False, "error": str(e), "events": reporter.events}),
                500,
            )

    def _require_last():
        if not _last or not _last_reporter:
            return None, (jsonify({"ok": False, "error": "Run a scan first"}), 400)
        return (_last, _last_reporter), None

    @app.get("/api/reports/txt")
    def report_txt():
        err = _require_last()
        if err[1]:
            return err[1]
        (data, rep) = err[0]
        try:
            path = rep.generate(data["system_data"]["system_info"], data["analysis"])
            return send_file(path, as_attachment=True, download_name=Path(path).name)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get("/api/reports/html")
    def report_html():
        err = _require_last()
        if err[1]:
            return err[1]
        (data, rep) = err[0]
        try:
            out = REPORTS_DIR / "COA_Report.html"
            path = HTMLReportGenerator.generate(
                data["system_data"]["system_info"],
                data["analysis"],
                rep.events,
                out,
            )
            return send_file(path, as_attachment=True, download_name=Path(path).name)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get("/api/reports/incident")
    def report_incident():
        err = _require_last()
        if err[1]:
            return err[1]
        (data, rep) = err[0]
        try:
            out = REPORTS_DIR / "COA_Incident_Report.txt"
            path = IncidentReporter.generate_full_report(
                data["system_data"]["system_info"],
                data["analysis"],
                rep.events,
                out,
                defense_context=data.get("defense_context"),
                mitre_deep=data.get("mitre_deep"),
            )
            return send_file(path, as_attachment=True, download_name=Path(path).name)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @app.get("/api/reports/mitre-navigator.json")
    def mitre_navigator_json():
        err = _require_last()
        if err[1]:
            return err[1]
        (data, _) = err[0]
        layer = (data.get("mitre_deep") or {}).get("navigator_layer")
        if not layer:
            return jsonify({"ok": False, "error": "Run a scan first; no Navigator layer available"}), 400
        return jsonify(_json_safe(layer))

    return app


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  C.O.A Web API (React dashboard backend)")
    print("=" * 60)
    print("  API:  http://127.0.0.1:5050")
    print("  UI:   cd web && npm install && npm run dev")
    print("        → http://localhost:5173")
    print("=" * 60 + "\n")
    create_app().run(host="127.0.0.1", port=5050, debug=False, threaded=True)
