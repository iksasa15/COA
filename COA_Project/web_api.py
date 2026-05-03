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
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from agents.council import diagnose_ollama
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


def _cli_ui_allowed() -> bool:
    """Run CLI from /api/dev/run-cli when COA_ALLOW_CLI_RUN=1 or COA_ALLOW_DEV_TESTS=1."""
    flag = os.environ.get("COA_ALLOW_CLI_RUN", "").strip().lower() in ("1", "true", "yes")
    return flag or _dev_tests_allowed()


def _cli_run_specs() -> dict[str, dict[str, object]]:
    """Whitelist for POST /api/dev/run-cli — argv + cwd + background + optional timeout (sync only)."""
    root = str(PROJECT_ROOT)
    web = str(PROJECT_ROOT / "web")
    py = sys.executable
    return {
        "main": {"argv": [py, "main.py"], "cwd": root, "background": True},
        "main_council": {"argv": [py, "main.py", "--council"], "cwd": root, "background": True},
        "main_vt": {"argv": [py, "main.py", "--vt"], "cwd": root, "background": True},
        "main_yara": {"argv": [py, "main.py", "--yara"], "cwd": root, "background": True},
        "main_dry_run": {"argv": [py, "main.py", "--dry-run"], "cwd": root, "background": True},
        "main_reports": {
            "argv": [py, "main.py", "--html", "--json", "--markdown", "--csv"],
            "cwd": root,
            "background": True,
        },
        "main_all": {"argv": [py, "main.py", "--all"], "cwd": root, "background": True},
        "council_test": {"argv": [py, "-m", "agents.council"], "cwd": root, "background": False, "timeout": 300},
        "gui": {"argv": [py, "gui.py"], "cwd": root, "background": True},
        "helpdesk_api": {"argv": [py, "helpdesk_api.py"], "cwd": root, "background": True},
        "helpdesk_main": {"argv": [py, "main.py", "--helpdesk"], "cwd": root, "background": True},
        "npm_run_dev": {"argv": [], "cwd": web, "background": True},  # argv filled after which("npm")
    }


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

    @app.get("/api/health/ollama")
    def health_ollama():
        """Ollama reachability + model check (no CrewAI load)."""
        return jsonify(_json_safe(diagnose_ollama()))

    @app.get("/api/health/council-agents")
    def health_council_agents():
        """
        Verify Ollama + CrewAI can construct an agent (no full scan / no crew kickoff).
        """
        d = diagnose_ollama()
        if not d.get("model_available"):
            return jsonify(
                _json_safe(
                    {
                        "ok": False,
                        "ollama": d,
                        "crewai_agents_ready": False,
                        "error": d.get("error") or "Ollama or model not ready",
                    }
                )
            )
        try:
            from crewai import Agent, LLM

            from config.settings import LLM_BASE_URL, LLM_MODEL, LLM_TEMPERATURE

            llm = LLM(
                model=LLM_MODEL,
                provider="ollama",
                base_url=LLM_BASE_URL,
                temperature=LLM_TEMPERATURE,
            )
            _ = Agent(
                role="COA connectivity probe",
                goal="No task will run; this only validates wiring.",
                backstory="Ephemeral probe agent.",
                llm=llm,
                memory=False,
                verbose=False,
                allow_delegation=False,
                max_iter=1,
            )
            return jsonify(
                _json_safe(
                    {
                        "ok": True,
                        "ollama": d,
                        "crewai_agents_ready": True,
                        "message": "Ollama OK and CrewAI Agent+LLM wiring works (council path should run).",
                    }
                )
            )
        except Exception as e:
            logger.warning("council-agents health failed: %s", e)
            return jsonify(
                _json_safe(
                    {
                        "ok": False,
                        "ollama": d,
                        "crewai_agents_ready": False,
                        "error": str(e),
                    }
                )
            )

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
        use_council = bool(body.get("use_council", False))

        reporter = ReportGenerator()
        reporter.log_event("SYSTEM", "React UI scan started")
        council_result = None

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

            council_result = None
            if use_council:
                from agents.council import run_council_on_scan

                reporter.log_event("COUNCIL", "Running CrewAI multi-agent council (Ollama)…")
                council_result = run_council_on_scan(system_data, analysis)
                if council_result.get("ok"):
                    reporter.log_event("COUNCIL", "Council finished")
                else:
                    reporter.log_event("COUNCIL", (council_result.get("error") or "failed")[:800])

            _last = {
                "system_data": system_data,
                "analysis": analysis,
                "classification": classification,
                "summary": summary,
                "defense_context": defense_context,
                "mitre_deep": mitre_deep,
                "ot_ics": ot_ics,
                "dry_run": dry_run,
                "council": council_result,
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
                "council": council_result,
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

    @app.get("/api/dev/cli-run-enabled")
    def dev_cli_run_enabled():
        """COA_ALLOW_CLI_RUN=1 or COA_ALLOW_DEV_TESTS=1."""
        return jsonify(
            {
                "ok": True,
                "enabled": _cli_ui_allowed(),
                "via_dev_tests": _dev_tests_allowed(),
                "via_cli_flag": os.environ.get("COA_ALLOW_CLI_RUN", "").strip().lower()
                in ("1", "true", "yes"),
            }
        )

    @app.post("/api/dev/run-cli")
    def dev_run_cli():
        """
        Run a fixed CLI command (whitelist only). Long jobs run in background; output -> reports/ui_cli_*.log
        Enable with: COA_ALLOW_CLI_RUN=1 or COA_ALLOW_DEV_TESTS=1
        """
        if not _cli_ui_allowed():
            return (
                jsonify(
                    {
                        "ok": False,
                        "enabled": False,
                        "error": (
                            "Disabled. Restart API with one of: "
                            "COA_ALLOW_CLI_RUN=1 python web_api.py  OR  "
                            "COA_ALLOW_DEV_TESTS=1 python web_api.py"
                        ),
                    }
                ),
                403,
            )

        body = request.get_json(silent=True) or {}
        action = str(body.get("action") or "").strip()
        specs = _cli_run_specs()
        if action not in specs:
            return jsonify({"ok": False, "enabled": True, "error": f"Unknown action: {action!r}"}), 400

        spec = specs[action]
        argv: list[str] = list(spec["argv"])  # type: ignore[arg-type]
        cwd: str = str(spec["cwd"])
        background = bool(spec["background"])

        if action == "npm_run_dev":
            npm = shutil.which("npm") or (shutil.which("npm.cmd") if os.name == "nt" else None)
            if not npm:
                return jsonify({"ok": False, "enabled": True, "error": "npm not found in PATH"}), 400
            argv = [npm, "run", "dev"]

        env = {**os.environ, "PYTHONUTF8": "1"}
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = REPORTS_DIR / f"ui_cli_{action}_{ts}.log"

        if background:
            try:
                logf = open(log_path, "w", encoding="utf-8")
            except OSError as e:
                return jsonify({"ok": False, "enabled": True, "error": f"Cannot open log file: {e}"}), 500
            try:
                proc = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    stdout=logf,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env=env,
                )
            except Exception as e:
                logf.close()
                logger.error(f"CLI run spawn failed action={action}: {e}")
                return jsonify({"ok": False, "enabled": True, "error": str(e)}), 500
            logf.close()
            logger.info("CLI run started (background)", action=action, pid=proc.pid, log=str(log_path))
            return jsonify(
                {
                    "ok": True,
                    "enabled": True,
                    "background": True,
                    "action": action,
                    "pid": proc.pid,
                    "log": str(log_path),
                    "command": argv,
                }
            )

        timeout = int(spec.get("timeout") or 120)
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
            logger.info("CLI run finished (sync)", action=action, exit_code=proc.returncode)
            return jsonify(
                {
                    "ok": True,
                    "enabled": True,
                    "background": False,
                    "action": action,
                    "exit_code": proc.returncode,
                    "command": argv,
                    "output": out[-200000:] if len(out) > 200000 else out,
                }
            )
        except subprocess.TimeoutExpired:
            return jsonify({"ok": False, "enabled": True, "error": f"Timed out after {timeout}s"}), 500
        except Exception as e:
            logger.error(f"CLI run failed action={action}: {e}")
            return jsonify({"ok": False, "enabled": True, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  C.O.A Web API (React dashboard backend)")
    print("=" * 60)
    print("  API:  http://127.0.0.1:5050")
    print("  UI:   cd web && npm install && npm run dev")
    print("        -> http://localhost:5173")
    if _dev_tests_allowed():
        print("  Dev:  COA_ALLOW_DEV_TESTS=1 → POST /api/dev/run-tests")
    if _cli_ui_allowed():
        print("  CLI UI: COA_ALLOW_CLI_RUN=1 or COA_ALLOW_DEV_TESTS=1 → POST /api/dev/run-cli")
    print("=" * 60 + "\n")
    create_app().run(host="127.0.0.1", port=5050, debug=False, threaded=True)
