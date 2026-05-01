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
import os
import subprocess
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
from ics_analyzer.demo_fixture import load_presentation_demo_ot_ics
from core.threat_analyzer import ThreatAnalyzer
from utils.html_report import HTMLReportGenerator
from utils.logger import logger
from utils.report_generator import ReportGenerator

# Last completed scan (for report downloads)
_last: dict | None = None
_last_reporter: ReportGenerator | None = None

MAX_PROCESSES_RESPONSE = 250
MAX_CONNECTIONS_RESPONSE = 400

PROJECT_ROOT = Path(__file__).resolve().parent


def _dev_tests_allowed() -> bool:
    """Run pytest from UI only when explicitly enabled (local dev / demos)."""
    return os.environ.get("COA_ALLOW_DEV_TESTS", "").strip().lower() in ("1", "true", "yes")


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

    @app.get("/api/demo/ot-ics-fixture")
    def demo_ot_ics_fixture():
        """Simulated OT/ICS payload for judge UI demo (read-only, no host scan)."""
        demo = load_presentation_demo_ot_ics()
        demo["ics_specialist"] = ICSSpecialistAgent.assess(demo)
        return jsonify(_json_safe(demo))

    @app.post("/api/scan")
    def scan():
        global _last, _last_reporter
        body = request.get_json(silent=True) or {}
        dry_run = bool(body.get("dry_run", False))
        presentation_demo = bool(body.get("presentation_demo", False))

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
            if presentation_demo:
                reporter.log_event("OT_ICS", "Presentation demo — loading simulated OT/ICS bundle for judges UI…")
                ot_ics = load_presentation_demo_ot_ics()
            else:
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

    @app.get("/api/dev/tests-enabled")
    def dev_tests_enabled():
        """Whether POST /api/dev/run-tests is allowed (requires COA_ALLOW_DEV_TESTS=1)."""
        return jsonify({"ok": True, "enabled": _dev_tests_allowed()})

    @app.post("/api/dev/run-tests")
    def dev_run_tests():
        """
        Run pytest on tests/ (fixed argv only — no shell injection).
        Enable with: COA_ALLOW_DEV_TESTS=1 python web_api.py
        """
        if not _dev_tests_allowed():
            return (
                jsonify(
                    {
                        "ok": False,
                        "enabled": False,
                        "error": "Disabled. Start API with COA_ALLOW_DEV_TESTS=1 to enable UI test runs.",
                    }
                ),
                403,
            )
        tests_dir = PROJECT_ROOT / "tests"
        if not tests_dir.is_dir():
            return jsonify({"ok": False, "error": "tests/ directory not found"}), 400

        body = request.get_json(silent=True) or {}
        scope = str(body.get("scope") or "all").strip().lower()
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(tests_dir),
            "-q",
            "--tb=line",
            "--no-header",
        ]
        if scope == "quick":
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(tests_dir / "test_core.py"),
                str(tests_dir / "test_defense_context.py"),
                str(tests_dir / "test_ics_analyzer.py"),
                str(tests_dir / "test_mitre_deep.py"),
                str(tests_dir / "test_v3_features.py"),
                "-q",
                "--tb=line",
                "--no-header",
            ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=180,
                env={**os.environ, "PYTHONUTF8": "1"},
            )
            out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
            logger.info("Dev pytest finished", exit_code=proc.returncode, scope=scope)
            return jsonify(
                {
                    "ok": True,
                    "enabled": True,
                    "exit_code": proc.returncode,
                    "scope": scope,
                    "command": cmd,
                    "output": out[-200000:] if len(out) > 200000 else out,
                }
            )
        except subprocess.TimeoutExpired:
            return jsonify({"ok": False, "enabled": True, "error": "pytest timed out (180s)"}), 500
        except Exception as e:
            logger.error(f"pytest run failed: {e}")
            return jsonify({"ok": False, "enabled": True, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  C.O.A Web API (React dashboard backend)")
    print("=" * 60)
    print("  API:  http://127.0.0.1:5050")
    print("  UI:   cd web && npm install && npm run dev")
    print("        → http://localhost:5173")
    if _dev_tests_allowed():
        print("  Dev:  UI pytest — COA_ALLOW_DEV_TESTS=1 → POST /api/dev/run-tests")
    print("=" * 60 + "\n")
    create_app().run(host="127.0.0.1", port=5050, debug=False, threaded=True)
