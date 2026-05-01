"""Tests for Defense Context Analyzer (Agent #5) engine."""

from core.defense_context_engine import run_defense_context_analysis


def test_defense_context_empty_clean():
    system_data = {"network_connections": [], "processes": []}
    analysis = {
        "threats": [],
        "total_threats": 0,
        "critical": 0,
        "high": 0,
    }
    dc = run_defense_context_analysis(system_data, analysis)
    assert dc["agent"] == "Defense Context Analyzer"
    assert dc["attribution"]["confidence_percent"] <= 40
    assert isinstance(dc["mitre_heatmap"], list)


def test_defense_context_with_signals():
    system_data = {
        "network_connections": [
            {"remote_address": "10.0.0.5:4444", "process_name": "curl", "process_path": "/tmp/x", "pid": 1},
        ],
        "processes": [],
    }
    analysis = {
        "threats": [
            {
                "severity": "HIGH",
                "confidence": "HIGH",
                "score": 70,
                "signals": ["suspicious_port", "external_connection_from_temp"],
                "details": "powershell encoded suspicious_port",
                "source": "proc",
            }
        ],
        "total_threats": 1,
        "critical": 0,
        "high": 1,
    }
    dc = run_defense_context_analysis(system_data, analysis)
    assert dc["mitre_heatmap"]
    assert any(c["heat"] >= 2 for c in dc["mitre_heatmap"])
