"""
Agent #5 — Defense Context Analyzer
===================================
Adds a strategic layer on top of Threat Hunter output using:
- Local YAML APT profiles (open-source summaries)
- Defense playbooks
- MITRE heatmap cells for UI

Deterministic engine in ``core.defense_context_engine`` (no cloud).
"""

from typing import Any, Dict

from core.defense_context_engine import format_defense_context_report, run_defense_context_analysis


class DefenseContextAnalyzer:
    """محلل السياق الدفاعي — الوكيل الخامس"""

    ROLE = "Defense Context Analyzer"
    GOAL = (
        "Enrich threat findings with regional APT heuristics, strategic intent, "
        "and playbook triggers using only local profiles."
    )

    @staticmethod
    def analyze(system_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run matching engine (Threat Hunter output must be in ``analysis``)."""
        return run_defense_context_analysis(system_data, analysis)

    @staticmethod
    def format_report(defense_context: Dict[str, Any]) -> str:
        return format_defense_context_report(defense_context)
