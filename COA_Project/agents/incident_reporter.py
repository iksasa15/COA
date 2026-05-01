"""
Incident Reporter Agent (Agent #4)
===================================
Synthesizes findings into professional incident reports with:
- Executive summaries
- MITRE ATT&CK mapping
- Actionable recommendations
- Priority classification
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from agents.defense_context_analyzer import DefenseContextAnalyzer
from utils.logger import logger


class IncidentReporter:
    """الوكيل الرابع: كاتب التقارير الاحترافية"""

    @staticmethod
    def classify_incident(analysis: Dict) -> Dict:
        """تصنيف الحادث"""
        threats = analysis.get('threats', [])

        if not threats:
            return {
                'severity': 'NONE',
                'category': 'Clean System',
                'priority': 5,
            }

        critical = analysis.get('critical', 0)
        high = analysis.get('high', 0)

        # اكتشاف الفئة الأساسية
        signal_counts = {}
        for threat in threats:
            for signal in threat.get('signals', []):
                signal_counts[signal] = signal_counts.get(signal, 0) + 1

        top_signal = max(signal_counts.items(), key=lambda x: x[1])[0] if signal_counts else 'unknown'

        category_map = {
            'high_cpu_low_memory': 'Suspected Cryptominer',
            'suspicious_port': 'Suspected C2 Communication',
            'external_connection_from_temp': 'Suspected Data Exfiltration',
            'masquerading_name': 'Process Masquerading',
            'runs_from_temp': 'Suspicious Execution',
            'no_digital_signature': 'Unsigned Process',
        }
        category = category_map.get(top_signal, 'General Security Concern')

        if critical > 0:
            priority, severity = 1, 'CRITICAL'
        elif high >= 2:
            priority, severity = 2, 'HIGH'
        elif high >= 1:
            priority, severity = 3, 'HIGH'
        else:
            priority, severity = 4, 'MEDIUM'

        return {
            'severity': severity,
            'category': category,
            'priority': priority,
            'top_signal': top_signal,
        }

    @staticmethod
    def executive_summary(system_info, analysis, classification, defense_context=None):
        """ملخص تنفيذي لأصحاب القرار"""
        threats = analysis.get('threats', [])
        hostname = system_info.get('hostname', 'Unknown')

        if not threats:
            return (
                f"Security scan of {hostname} completed successfully. "
                f"No security threats were detected. The system appears clean "
                f"and operating normally."
            )

        severity = classification['severity']
        priority = classification['priority']
        category = classification['category']

        summary = (
            f"Scan of {hostname} detected {len(threats)} security issue(s). "
            f"Classification: {severity} severity, {category}, priority P{priority}/5.\n\n"
        )

        if analysis.get('critical', 0) > 0:
            summary += (
                f"⚠️ CRITICAL: {analysis['critical']} critical threat(s) requiring "
                f"immediate action.\n"
            )
        if analysis.get('high', 0) > 0:
            summary += f"{analysis['high']} high-severity threat(s) needing prompt review.\n"

        summary += "\n**Recommendation:** "
        if priority <= 2:
            summary += (
                "Isolate system immediately. Approve remediation actions. "
                "Consider escalating to security team."
            )
        else:
            summary += "Review findings and approve appropriate remediation."

        if defense_context:
            att = defense_context.get('attribution') or {}
            summary += (
                f"\n\n**Defense context (heuristic):** {att.get('likely_actor', 'N/A')} "
                f"— confidence {att.get('confidence_percent', 0)}%. "
                f"{att.get('reasoning', '')}"
            )

        return summary

    @staticmethod
    def mitre_mapping(threats):
        """ربط بإطار MITRE ATT&CK"""
        mitre_map = {
            'suspicious_port': {
                'tactic': 'Command and Control',
                'technique': 'T1071',
                'name': 'Application Layer Protocol',
            },
            'runs_from_temp': {
                'tactic': 'Defense Evasion',
                'technique': 'T1036',
                'name': 'Masquerading',
            },
            'external_connection_from_temp': {
                'tactic': 'Exfiltration',
                'technique': 'T1041',
                'name': 'Exfiltration Over C2 Channel',
            },
            'masquerading_name': {
                'tactic': 'Defense Evasion',
                'technique': 'T1036.005',
                'name': 'Match Legitimate Name',
            },
            'high_cpu_low_memory': {
                'tactic': 'Impact',
                'technique': 'T1496',
                'name': 'Resource Hijacking',
            },
            'no_digital_signature': {
                'tactic': 'Defense Evasion',
                'technique': 'T1553',
                'name': 'Subvert Trust Controls',
            },
        }

        seen = set()
        ttps = []
        for threat in threats:
            for signal in threat.get('signals', []):
                if signal in mitre_map and signal not in seen:
                    seen.add(signal)
                    ttps.append(mitre_map[signal])
        return ttps

    @staticmethod
    def recommendations(threats, classification):
        """توصيات مخصصة"""
        if not threats:
            return [
                "Continue regular security monitoring",
                "Keep OS and software updated",
                "Run periodic security scans",
            ]

        recs = []
        signals = set()
        for t in threats:
            signals.update(t.get('signals', []))

        if 'suspicious_port' in signals or 'external_connection_from_temp' in signals:
            recs.append("⚠️ Isolate affected systems from network immediately")

        if 'runs_from_temp' in signals or 'masquerading_name' in signals:
            recs.append("🔍 Investigate temp directories for additional artifacts")

        if 'high_cpu_low_memory' in signals:
            recs.append("💰 Check for cryptomining activity")

        if classification['priority'] <= 2:
            recs.extend([
                "📞 Notify incident response team",
                "📝 Preserve evidence for forensic analysis",
                "🔐 Rotate credentials for affected accounts",
            ])

        recs.extend([
            "🛡️ Update endpoint security solutions",
            "📊 Monitor network traffic for 48+ hours",
            "📚 Document findings for future reference",
        ])
        return recs

    @classmethod
    def generate_full_report(cls, system_info, analysis, events, output_path, defense_context=None):
        """توليد التقرير الكامل"""
        logger.info("Generating incident report")

        classification = cls.classify_incident(analysis)
        threats = analysis.get('threats', [])
        ttps = cls.mitre_mapping(threats)
        recs = cls.recommendations(threats, classification)

        lines = []
        lines.append("=" * 75)
        lines.append("          SECURITY INCIDENT REPORT")
        lines.append("          C.O.A — Council of Agents")
        lines.append("=" * 75)
        lines.append("")
        lines.append(f"Report ID:    COA-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        lines.append(f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Host:         {system_info.get('hostname', 'Unknown')}")
        lines.append(f"Severity:     {classification['severity']}")
        lines.append(f"Category:     {classification['category']}")
        lines.append(f"Priority:     P{classification['priority']}")
        lines.append("")

        # Executive Summary
        lines.append("=" * 75)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("=" * 75)
        lines.append(cls.executive_summary(system_info, analysis, classification, defense_context))
        lines.append("")

        # System
        lines.append("=" * 75)
        lines.append("AFFECTED SYSTEM")
        lines.append("=" * 75)
        for key, value in system_info.items():
            if key != 'scan_time':
                lines.append(f"  {key:20s}: {value}")
        lines.append("")

        # Threats
        if threats:
            lines.append("=" * 75)
            lines.append("TECHNICAL FINDINGS")
            lines.append("=" * 75)
            for i, threat in enumerate(threats, 1):
                lines.append(f"--- Finding #{i} ---")
                lines.append(f"  Severity:   {threat.get('severity')}")
                lines.append(f"  Confidence: {threat.get('confidence')}")
                lines.append(f"  Score:      {threat.get('score')}/100")
                lines.append(f"  Source:     {threat.get('source')}")
                lines.append(f"  Details:    {threat.get('details')}")
                signals = threat.get('signals', [])
                if signals:
                    lines.append(f"  Indicators ({len(signals)}):")
                    for signal in signals:
                        lines.append(f"    • {signal}")
                lines.append("")

        # MITRE
        if ttps:
            lines.append("=" * 75)
            lines.append("MITRE ATT&CK MAPPING")
            lines.append("=" * 75)
            for ttp in ttps:
                lines.append(f"• {ttp['technique']} — {ttp['name']}")
                lines.append(f"  Tactic: {ttp['tactic']}")
                lines.append("")

        if defense_context:
            lines.append("=" * 75)
            lines.append("DEFENSE CONTEXT (Agent #5 — heuristic)")
            lines.append("=" * 75)
            lines.append(DefenseContextAnalyzer.format_report(defense_context))
            lines.append("")

        # Recommendations
        lines.append("=" * 75)
        lines.append("RECOMMENDED ACTIONS")
        lines.append("=" * 75)
        for i, rec in enumerate(recs, 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

        # Events
        lines.append("=" * 75)
        lines.append("EVENT TIMELINE")
        lines.append("=" * 75)
        for event in events:
            lines.append(f"  [{event.get('timestamp')}] {event.get('type')}")
            lines.append(f"      {event.get('details')}")
        lines.append("")

        lines.append("=" * 75)
        lines.append("  Report by C.O.A Agent #4 — All analysis done locally 🔒")
        lines.append("=" * 75)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return str(output_path)
