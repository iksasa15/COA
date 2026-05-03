"""
C.O.A - Council of Agents v3.0
==============================
Main Entry Point with ALL enhancements

New in v3.0:
- VirusTotal integration (--vt)
- YARA rules engine (--yara)
- 4th agent: Incident Reporter (always on)
- React Web UI (--gui starts API for `web/`)
- Helpdesk bot mode (--helpdesk)

Usage:
    python main.py                    # Normal CLI scan
    python main.py --gui              # Start API for React UI (see on-screen steps)
    python main.py --helpdesk         # Launch helpdesk bot
    python main.py --vt               # Enable VirusTotal enrichment
    python main.py --yara             # Enable YARA scanning
    python main.py --all              # Enable EVERYTHING
"""

import os
import sys
import argparse
import json
import traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from utils.admin_check import require_admin
from utils.ui_manager import UIManager
from utils.report_generator import ReportGenerator
from utils.html_report import HTMLReportGenerator
from utils.logger import logger
from utils.cache import global_cache
from core.data_collector import SystemDataCollector
from core.threat_analyzer import ThreatAnalyzer
from core.solution_engine import SolutionEngine
from agents.defense_context_analyzer import DefenseContextAnalyzer
from agents.ics_specialist import ICSSpecialistAgent
from core.mitre_deep_analysis import build_mitre_deep_bundle
from agents.incident_reporter import IncidentReporter
from ics_analyzer import analyze_ot_ics
from config.settings import REPORTS_DIR


def _council_llm_label() -> str:
    return "Ollama"


def parse_arguments():
    """تحليل CLI arguments"""
    parser = argparse.ArgumentParser(
        description="C.O.A v3.0 — Advanced AI Security Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  python main.py --gui                # Web API for React dashboard (web/)
  python main.py --helpdesk           # Interactive chatbot
  python main.py                      # CLI scan (default)

CLI Options:
  python main.py --dry-run            # Safe simulation
  python main.py --council            # CrewAI council (3 agents; Ollama local per .env)
  python main.py --vt                 # VirusTotal enrichment
  python main.py --yara               # YARA rules scan
  python main.py --html --json        # Multiple report formats
  python main.py --all                # Enable everything
        """
    )

    # Main modes
    parser.add_argument('--gui', action='store_true', help='Start Web API for React UI (see terminal hints)')
    parser.add_argument('--helpdesk', action='store_true', help='Launch helpdesk bot')

    # CLI options
    parser.add_argument('--dry-run', action='store_true', help='Simulate without executing')
    parser.add_argument('--vt', action='store_true', help='Enable VirusTotal enrichment')
    parser.add_argument('--yara', action='store_true', help='Enable YARA rules scanning')
    parser.add_argument('--html', action='store_true', help='Generate HTML report')
    parser.add_argument('--json', action='store_true', help='Generate JSON report')
    parser.add_argument('--markdown', action='store_true', help='Generate Markdown report')
    parser.add_argument('--csv', action='store_true', help='Generate CSV report')
    parser.add_argument('--all', action='store_true', help='Enable all features')
    parser.add_argument(
        '--council',
        action='store_true',
        help='After scan, run CrewAI council (Eye/Brain/Strategist); Ollama from .env',
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-admin-check', action='store_true', help='Skip admin check')

    return parser.parse_args()


def launch_gui():
    """تشغيل واجهة الويب (React) — يشغّل خادم الـ API حتى تستخدم `npm run dev` داخل web/"""
    ui = UIManager()
    ui.display_banner()
    ui.section_header("React dashboard", "🖥️")
    ui.info("API:  http://127.0.0.1:5050")
    ui.info("Open a second terminal, then:")
    ui.info("  cd web && npm install && npm run dev")
    ui.info("Browser:  http://localhost:5173")
    ui.info("Legacy Tkinter UI:  python gui.py")
    ui.divider()
    from web_api import create_app

    create_app().run(host="127.0.0.1", port=5050, debug=False, threaded=True)


def launch_helpdesk():
    """تشغيل Helpdesk Bot"""
    from helpdesk.bot import HelpdeskBot, UserMessage

    ui = UIManager()
    ui.display_banner()
    ui.section_header("💬 Helpdesk Bot Mode", "🤖")
    ui.info("Talk to me like you would to an IT support agent!")
    ui.info("Type 'quit' to exit\n")

    bot = HelpdeskBot()
    user_id = "cli_user"

    while True:
        try:
            text = input("\n👤 You: ").strip()
            if not text or text.lower() in ['quit', 'exit', 'bye']:
                ui.success("Goodbye! 👋")
                break

            msg = UserMessage(text=text, user_id=user_id)
            response = bot.handle_message(msg)
            print(f"\n🤖 Bot: {response.text}")

        except KeyboardInterrupt:
            ui.success("\nGoodbye! 👋")
            break


def save_json_report(system_info, analysis_result, events, output_path):
    """حفظ تقرير JSON"""
    report_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "3.0",
            "generator": "C.O.A",
        },
        "system_info": system_info,
        "analysis": analysis_result,
        "events": events,
        "cache_stats": global_cache.stats(),
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    return str(output_path)


def cli_scan(args):
    """الفحص الرئيسي في وضع CLI"""
    ui = UIManager()
    ui.display_banner()

    # تفعيل --all
    if args.all:
        args.vt = True
        args.yara = True
        args.html = True
        args.json = True
        args.markdown = True
        args.csv = True

    logger.info(
        "C.O.A v3.0 scan started",
        dry_run=args.dry_run,
        vt=args.vt,
        yara=args.yara,
    )

    # عرض الوضع
    modes = []
    if args.dry_run: modes.append("🧪 Dry-run")
    if args.vt: modes.append("🔍 VirusTotal")
    if args.yara: modes.append("📋 YARA")

    if modes:
        ui.info(f"Enabled: {' | '.join(modes)}")
    if args.council:
        ui.info(f"Enabled: 🤖 CrewAI council ({_council_llm_label()} multi-agent)")

    # التحقق من Admin
    if not args.no_admin_check:
        require_admin()
        if os.name == "nt":
            ui.success("Administrator privileges confirmed")
        else:
            ui.success("Running with current user privileges (use sudo for deeper system access)")

    reporter = ReportGenerator()
    reporter.log_event("SYSTEM", f"C.O.A v3.0 scan initiated")
    solution_engine = SolutionEngine(dry_run=args.dry_run)

    # Scan summary: only ✓ when council ran and produced a report (not merely --council passed).
    council_ok = False

    try:
        # ============ PHASE 1: Data Collection ============
        ui.divider()
        ui.section_header("PHASE 1: Data Collection (The Eye)", "👁️")
        ui.loading_animation("Collecting system data in parallel...", 1.0)

        system_data = SystemDataCollector.collect_all()
        sys_info = system_data["system_info"]
        conn_count = len(system_data["network_connections"])
        proc_count = len(system_data["processes"])
        duration = system_data.get("collection_duration", 0)

        ui.success(f"Collected {conn_count} connections + {proc_count} processes in {duration:.2f}s")
        reporter.log_event("DATA_COLLECTION", f"Collected in {duration:.2f}s")

        # ============ PHASE 2: Threat Analysis ============
        ui.divider()
        ui.section_header("PHASE 2: Threat Analysis (The Brain)", "🧠")
        ui.loading_animation("Analyzing with scoring engine...", 1.5)

        analysis_result = ThreatAnalyzer.full_analysis(system_data)

        # ============ PHASE 2.5: VirusTotal Enrichment ============
        if args.vt:
            ui.divider()
            ui.section_header("PHASE 2.5: VirusTotal Enrichment", "🔍")
            try:
                from integrations.virustotal import VirusTotalEnricher
                enricher = VirusTotalEnricher()

                if enricher.client.enabled:
                    ui.loading_animation("Checking threats against VirusTotal...", 1.0)
                    enriched = enricher.enrich_all(analysis_result.get('threats', []))
                    analysis_result['threats'] = enriched
                    ui.success("VirusTotal enrichment complete")
                else:
                    ui.warning("VirusTotal disabled - no API key configured")
                    ui.info("Get free key at: https://www.virustotal.com/gui/join-us")
                    ui.info("Set: export VIRUSTOTAL_API_KEY='your_key'")
            except Exception as e:
                ui.warning(f"VirusTotal enrichment failed: {e}")

        # ============ PHASE 2.7: YARA Scanning ============
        if args.yara:
            ui.divider()
            ui.section_header("PHASE 2.7: YARA Rules Scan", "📋")
            try:
                from integrations.yara_engine import YARAEngine
                yara = YARAEngine()
                ui.info("YARA engine loaded")

                suspicious_processes = [
                    p for p in system_data.get('processes', [])
                    if p.get('path') != 'N/A'
                ][:10]  # فحص أول 10 فقط لتجنب البطء

                yara_matches = 0
                for proc in suspicious_processes:
                    matches = yara.scan_file(proc['path'])
                    if matches:
                        yara_matches += len(matches)
                        for match in matches:
                            ui.danger(f"YARA: {match['rule_name']} in {proc['name']}")
                            analysis_result['threats'].append({
                                'severity': 'HIGH',
                                'confidence': 'HIGH',
                                'score': 75,
                                'type': f"YARA: {match['rule_name']}",
                                'source': f"{proc['name']} (PID: {proc['pid']})",
                                'details': f"Matched YARA rule: {match['rule_name']}",
                                'signals': match.get('tags', ['yara_match']),
                                'recommended_action': 'investigate',
                                'target_pid': proc['pid'],
                            })
                ui.success(f"YARA scan complete: {yara_matches} matches in {len(suspicious_processes)} processes")

            except Exception as e:
                ui.warning(f"YARA scan failed: {e}")

        # إعادة حساب الإحصائيات بعد الإثراء
        threats = analysis_result.get('threats', [])
        analysis_result['total_threats'] = len(threats)
        analysis_result['critical'] = sum(1 for t in threats if t.get('severity') == 'CRITICAL')
        analysis_result['high'] = sum(1 for t in threats if t.get('severity') == 'HIGH')

        if threats:
            ui.danger(f"⚠️ Detected {len(threats)} threats")
            ui.display_threats_table(threats)
            for t in threats:
                reporter.log_threat(t)
        else:
            ui.success("🎉 No threats detected!")

        # ============ PHASE 2.8: Defense Context Analyzer (Agent #5) ============
        ui.divider()
        ui.section_header("PHASE 2.8: Defense Context Analyzer", "🎯")
        ui.loading_animation("Correlating with regional APT heuristics & playbooks...", 0.8)
        defense_context = DefenseContextAnalyzer.analyze(system_data, analysis_result)
        ui.info(DefenseContextAnalyzer.format_report(defense_context).strip().replace("\n", "\n  "))
        ot_ics = analyze_ot_ics(system_data)
        ot_ics["ics_specialist"] = ICSSpecialistAgent.assess(ot_ics)
        ui.section_header("OT/ICS — Passive view (Agent #6)", "🏭")
        ui.info(
            (ot_ics.get("ics_specialist") or {})
            .get("ascii_report", "")
            .strip()
            .replace("\n", "\n  ")[:4000]
        )
        mitre_deep = build_mitre_deep_bundle(
            analysis_result,
            defense_context,
            system_data,
            sys_info,
            ot_ics,
        )
        ui.section_header("MITRE ATT&CK — Deep analysis (summary)", "📚")
        ui.info(mitre_deep.get("ascii_report", "").strip().replace("\n", "\n  ")[:6000])

        # ============ PHASE 2.9: CrewAI council (optional multi-agent) ============
        if args.council:
            ui.divider()
            ui.section_header(
                f"PHASE 2.9: Multi-Agent Council (CrewAI + {_council_llm_label()})",
                "🤖",
            )
            try:
                from agents.council import OllamaConnectionError, run_council_on_scan

                out = UIManager.run_with_council_progress(
                    "Council: Eye→Brain→Strategist",
                    lambda: run_council_on_scan(system_data, analysis_result),
                )
                if out.get("ok") and out.get("report"):
                    council_ok = True
                    reporter.log_event("COUNCIL", f"CrewAI council completed ({_council_llm_label()})")
                    text = str(out["report"])
                    ui.info(text.strip().replace("\n", "\n  ")[:12000])
                    if len(text) > 12000:
                        ui.info("… [council output truncated in terminal; full text in logs]")
                    logger.info(
                        f"Council report length={len(text)}",
                        report_chars=len(text),
                    )
                else:
                    err = out.get("error") or "Unknown council error"
                    reporter.log_event("COUNCIL", f"Council skipped or failed: {err[:500]}")
                    ui.warning(f"Council not run: {err[:2000]}")
            except OllamaConnectionError as e:
                reporter.log_event("COUNCIL", str(e)[:500])
                ui.warning(str(e))
            except Exception as e:
                reporter.log_event("COUNCIL", f"Error: {e}")
                ui.warning(f"Council error: {e}")

        # ============ PHASE 3-4: Solutions + Approval ============
        if threats:
            ui.divider()
            ui.section_header("PHASE 3: Solution Planning (The Strategist)", "🎯")
            solutions = SolutionEngine.generate_all_solutions(threats)

            ui.divider()
            ui.section_header("PHASE 4: Human Approval Required", "🔒")

            if args.dry_run:
                ui.warning("Dry-run mode - commands will be simulated only")

            approved_count = 0
            for i, solution in enumerate(solutions, 1):
                if not solution.get("command"):
                    continue

                ui.divider()
                ui.info(f"Threat {i}/{len(solutions)} - Score: {solution['threat'].get('score', 0)}")

                approved = ui.ask_confirmation(
                    solution["command"],
                    solution["description"],
                )

                if approved:
                    result = solution_engine.execute_command(solution["command"], approved=True)
                    if result["success"]:
                        ui.success("✅ Command succeeded" + (" [DRY RUN]" if result.get('dry_run') else ""))
                        approved_count += 1
                    reporter.log_action(solution["command"], approved=True, result=result)
                else:
                    reporter.log_action(solution["command"], approved=False)

        # ============ PHASE 5: Report Generation (4th Agent!) ============
        ui.divider()
        ui.section_header("PHASE 5: Incident Reporting (The Reporter)", "📄")

        reporter_agent = IncidentReporter()

        # TXT (default)
        txt_path = reporter.generate(sys_info, analysis_result)
        ui.success(f"TXT: {txt_path}")

        # HTML
        if args.html:
            html_path = REPORTS_DIR / "COA_Report.html"
            HTMLReportGenerator.generate(sys_info, analysis_result, reporter.events, html_path)
            ui.success(f"HTML: {html_path}")

        # JSON
        if args.json:
            json_path = REPORTS_DIR / "COA_Report.json"
            save_json_report(sys_info, analysis_result, reporter.events, json_path)
            ui.success(f"JSON: {json_path}")

        # Markdown (from 4th agent)
        if args.markdown:
            md_path = REPORTS_DIR / "COA_Report.md"
            reporter_agent.generate_markdown_report(sys_info, analysis_result, reporter.events, md_path)
            ui.success(f"Markdown: {md_path}")

        # CSV (from 4th agent)
        if args.csv:
            csv_path = REPORTS_DIR / "COA_Report.csv"
            reporter_agent.generate_csv_report(analysis_result, csv_path)
            ui.success(f"CSV: {csv_path}")

        # ============ Summary ============
        ui.divider()
        cache_stats = global_cache.stats()
        ui.display_summary({
            "Total Connections": conn_count,
            "Total Processes": proc_count,
            "Threats Detected": len(threats),
            "Critical": analysis_result.get("critical", 0),
            "High": analysis_result.get("high", 0),
            "Cache Hit Rate": cache_stats['hit_rate'],
            "Collection Time": f"{duration:.2f}s",
            "VirusTotal": "✓" if args.vt else "✗",
            "YARA": "✓" if args.yara else "✗",
            f"CrewAI+{_council_llm_label()}": "✓" if (args.council and council_ok) else "✗",
        })

        ui.divider()
        ui.success("🎉 C.O.A v3.0 scan completed successfully!")
        logger.info("Scan completed successfully")

    except KeyboardInterrupt:
        ui.warning("\nScan interrupted by user")
        sys.exit(0)
    except Exception as e:
        ui.danger(f"Error: {str(e)}")
        logger.critical(f"Unhandled exception: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


def main():
    """نقطة الدخول الرئيسية - توجه للوضع المناسب"""
    args = parse_arguments()

    # وضع GUI
    if args.gui:
        launch_gui()
        return

    # وضع Helpdesk
    if args.helpdesk:
        launch_helpdesk()
        return

    # وضع CLI الافتراضي
    cli_scan(args)


if __name__ == "__main__":
    main()
