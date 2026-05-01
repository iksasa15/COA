from core.mitre_deep_analysis import (
    build_kill_chain_phases,
    build_mitre_deep_bundle,
    build_navigator_layer,
)


def test_kill_chain_orders_tactics():
    threats = [
        {
            "signals": ["suspicious_port"],
            "details": "x",
            "source": "p",
            "confidence": "HIGH",
        },
        {
            "signals": ["runs_from_temp"],
            "details": "y",
            "source": "q",
            "confidence": "MEDIUM",
        },
    ]
    phases = build_kill_chain_phases(threats)
    ta_ids = [p["ta_id"] for p in phases]
    assert ta_ids.index("TA0005") < ta_ids.index("TA0011")  # evasion before C2


def test_navigator_layer_shape():
    layer = build_navigator_layer(
        "lab-1",
        [{"technique_id": "T1071", "name": "App Protocol", "tactic": "C2", "heat": 2}],
    )
    assert layer["domain"] == "enterprise-attack"
    assert layer["techniques"][0]["techniqueID"] == "T1071"


def test_bundle_clean():
    b = build_mitre_deep_bundle(
        {"threats": []},
        {"mitre_heatmap": [], "playbooks_triggered": [], "attribution": {}},
        {"network_connections": []},
        {"hostname": "h"},
    )
    assert "navigator_layer" in b
    assert "ascii_report" in b
