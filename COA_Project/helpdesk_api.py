"""
IT Helpdesk Bot Integration API
================================
Exposes C.O.A as a service that IT Helpdesk Bots can call.

Two modes:
1. REST API (Flask) - for web-based bots
2. Python SDK - for direct integration

Usage:
    # Start REST API server
    python -m helpdesk_api

    # Or import directly
    from helpdesk_api import COAHelpdesk
    bot = COAHelpdesk()
    result = bot.scan_system(user_id="john")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from core.data_collector import SystemDataCollector
from core.threat_analyzer import ThreatAnalyzer
from core.solution_engine import SolutionEngine
from agents.incident_reporter import IncidentReporter
from utils.logger import logger


class COAHelpdesk:
    """
    واجهة برمجية للدمج مع أي IT Helpdesk Bot
    يحوّل C.O.A إلى خدمة قابلة للاستدعاء
    """

    def __init__(self, dry_run_default: bool = True):
        """
        Args:
            dry_run_default: افتراضياً في وضع المحاكاة (آمن للـ bots)
        """
        self.dry_run_default = dry_run_default
        self.scan_history: List[Dict] = []
        logger.info("COA Helpdesk API initialized")

    def scan_system(
        self,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        quick_mode: bool = False,
    ) -> Dict:
        """
        فحص سريع للنظام - مناسب لردود الـ bot
        Returns: JSON-friendly dict

        Example integration with Helpdesk Bot:
            result = bot.scan_system(user_id="employee_123")
            if result['severity'] != 'NONE':
                send_alert_to_user(result['summary'])
        """
        start_time = datetime.now()
        scan_id = request_id or f"COA-{start_time.strftime('%Y%m%d%H%M%S')}"

        logger.info(f"Helpdesk scan requested by {user_id}", scan_id=scan_id)

        try:
            # جمع البيانات
            system_data = SystemDataCollector.collect_all()

            # تحليل
            analysis = ThreatAnalyzer.full_analysis(system_data)

            # تصنيف للـ Helpdesk
            classification = IncidentReporter.classify_incident(analysis)

            # توليد ردّ مبسط للـ bot
            summary = IncidentReporter.executive_summary(
                system_data["system_info"], analysis, classification
            )

            response = {
                "scan_id": scan_id,
                "user_id": user_id,
                "timestamp": start_time.isoformat(),
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "status": "success",
                "severity": classification["severity"],
                "category": classification["category"],
                "priority": classification["priority"],
                "threat_count": analysis["total_threats"],
                "critical_count": analysis["critical"],
                "high_count": analysis["high"],
                "summary": summary,
                "needs_action": classification["priority"] <= 3,
                "bot_response": self._generate_bot_response(classification, analysis),
            }

            # حفظ في التاريخ
            self.scan_history.append(response)

            return response

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return {
                "scan_id": scan_id,
                "user_id": user_id,
                "status": "error",
                "error": str(e),
                "bot_response": "I encountered an error while scanning. Please try again or contact IT support.",
            }

    def _generate_bot_response(self, classification: Dict, analysis: Dict) -> str:
        """
        توليد رد ودّي للمستخدم عبر الـ bot
        يستخدم لغة بسيطة غير تقنية
        """
        threats = analysis.get("threats", [])

        if not threats:
            return (
                "✅ Good news! I've scanned your system and everything looks clean. "
                "No security issues detected. Your device appears to be safe."
            )

        priority = classification["priority"]
        severity = classification["severity"]

        if priority == 1:
            return (
                f"🚨 I found {len(threats)} critical security issue(s) on your system. "
                f"This requires immediate attention. I strongly recommend you:\n"
                f"1. Disconnect from the internet\n"
                f"2. Contact IT support immediately\n"
                f"3. Don't access sensitive systems until this is resolved\n\n"
                f"Category: {classification['category']}"
            )
        elif priority == 2:
            return (
                f"⚠️ I detected {len(threats)} security concern(s) on your system. "
                f"This is {severity} severity. I recommend you:\n"
                f"1. Close any suspicious applications\n"
                f"2. Review the detailed report\n"
                f"3. Consider running a full antivirus scan\n\n"
                f"Would you like me to walk you through the remediation steps?"
            )
        elif priority == 3:
            return (
                f"🔍 I noticed {len(threats)} potentially suspicious activity on your system. "
                f"It's {severity} severity and worth investigating. "
                f"Would you like me to explain what I found?"
            )
        else:
            return (
                f"ℹ️ I found {len(threats)} item(s) worth monitoring. These are low-priority "
                f"but I'll keep watching. Would you like more details?"
            )

    def get_remediation_plan(
        self,
        scan_id: str,
        auto_approve_safe: bool = False,
    ) -> Dict:
        """
        الحصول على خطة حل للحادث
        Returns: خطوات مرتبة + أوامر
        """
        # البحث عن الفحص
        scan = next((s for s in self.scan_history if s.get("scan_id") == scan_id), None)
        if not scan:
            return {"status": "error", "error": "Scan ID not found"}

        # الحصول على آخر analysis
        try:
            system_data = SystemDataCollector.collect_all()
            analysis = ThreatAnalyzer.full_analysis(system_data)

            solutions = SolutionEngine.generate_all_solutions(analysis["threats"])

            steps = []
            for i, sol in enumerate(solutions, 1):
                steps.append({
                    "step": i,
                    "action": sol["description"],
                    "command": sol["command"],
                    "risk_level": sol["risk_level"],
                    "reversible": sol["reversible"],
                    "requires_approval": True,  # دائماً للأمان
                    "estimated_impact": sol.get("estimated_impact", ""),
                })

            return {
                "scan_id": scan_id,
                "status": "success",
                "total_steps": len(steps),
                "steps": steps,
                "bot_message": self._format_remediation_message(steps),
            }

        except Exception as e:
            logger.error(f"Remediation plan failed: {e}")
            return {"status": "error", "error": str(e)}

    def _format_remediation_message(self, steps: List[Dict]) -> str:
        """تنسيق خطة الحل لرسالة bot"""
        if not steps:
            return "No remediation needed - system is clean."

        lines = [f"I've prepared {len(steps)} remediation step(s) for you:\n"]
        for step in steps:
            icon = "🔴" if step["risk_level"] == "MEDIUM" else "🟢"
            reversible = "✅ reversible" if step["reversible"] else "⚠️ not reversible"
            lines.append(
                f"{icon} Step {step['step']}: {step['action']}\n"
                f"   Risk: {step['risk_level']} | {reversible}"
            )

        lines.append(
            "\nEach step requires your explicit approval. "
            "Would you like me to proceed with step 1?"
        )
        return "\n".join(lines)

    def execute_step(
        self,
        scan_id: str,
        step_number: int,
        user_approved: bool,
        dry_run: Optional[bool] = None,
    ) -> Dict:
        """
        تنفيذ خطوة محددة بعد موافقة المستخدم
        """
        if not user_approved:
            return {
                "status": "rejected",
                "message": "Step not executed - user did not approve",
            }

        plan = self.get_remediation_plan(scan_id)
        if plan["status"] != "success":
            return plan

        steps = plan.get("steps", [])
        if step_number < 1 or step_number > len(steps):
            return {
                "status": "error",
                "error": f"Invalid step number. Valid range: 1-{len(steps)}",
            }

        step = steps[step_number - 1]

        # استخدم dry_run المحدد أو الافتراضي
        use_dry_run = dry_run if dry_run is not None else self.dry_run_default
        engine = SolutionEngine(dry_run=use_dry_run)

        result = engine.execute_command(step["command"], approved=True)

        return {
            "status": "success" if result["success"] else "failed",
            "step": step_number,
            "command": step["command"],
            "dry_run": use_dry_run,
            "output": result.get("output", ""),
            "error": result.get("error", ""),
            "bot_message": (
                f"{'✅' if result['success'] else '❌'} "
                f"Step {step_number}: "
                f"{'simulated successfully' if use_dry_run else ('completed' if result['success'] else 'failed')}"
            ),
        }

    def get_health_status(self) -> Dict:
        """صحة النظام - لـ monitoring checks"""
        try:
            data = SystemDataCollector.get_system_info()
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "scans_completed": len(self.scan_history),
                "system_info": data,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# ==================== Example: REST API Server ====================
def create_flask_app():
    """
    إنشاء Flask API server (اختياري)
    يتطلب: pip install flask
    """
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask not installed. Run: pip install flask")
        return None

    app = Flask(__name__)
    helpdesk = COAHelpdesk(dry_run_default=True)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify(helpdesk.get_health_status())

    @app.route('/scan', methods=['POST'])
    def scan():
        data = request.get_json() or {}
        result = helpdesk.scan_system(
            user_id=data.get('user_id'),
            request_id=data.get('request_id'),
        )
        return jsonify(result)

    @app.route('/remediation/<scan_id>', methods=['GET'])
    def get_remediation(scan_id):
        return jsonify(helpdesk.get_remediation_plan(scan_id))

    @app.route('/execute', methods=['POST'])
    def execute_step():
        data = request.get_json() or {}
        result = helpdesk.execute_step(
            scan_id=data.get('scan_id'),
            step_number=data.get('step'),
            user_approved=data.get('approved', False),
            dry_run=data.get('dry_run'),
        )
        return jsonify(result)

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            "service": "C.O.A Helpdesk API",
            "version": "1.0",
            "endpoints": [
                "GET  /health",
                "POST /scan",
                "GET  /remediation/<scan_id>",
                "POST /execute",
            ],
        })

    return app


if __name__ == "__main__":
    # تشغيل API server
    app = create_flask_app()
    if app:
        print("\n" + "=" * 60)
        print("  C.O.A Helpdesk API Server")
        print("=" * 60)
        print("  Running on: http://localhost:5000")
        print("  Endpoints:")
        print("    GET  /              - API info")
        print("    GET  /health        - Health check")
        print("    POST /scan          - Start security scan")
        print("    GET  /remediation/:id - Get fix plan")
        print("    POST /execute       - Execute step")
        print("=" * 60 + "\n")
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        # عرض مثال للاستخدام المباشر
        print("Running in SDK mode (no Flask)")
        helpdesk = COAHelpdesk()

        print("\n🔍 Running scan...")
        result = helpdesk.scan_system(user_id="demo_user")
        print(f"\nBot response:\n{result.get('bot_response', 'N/A')}")
