"""Passive OT/ICS analyzer tests."""

from ics_analyzer import analyze_ot_ics


def test_analyze_ot_ics_empty():
    r = analyze_ot_ics({"network_connections": []})
    assert r["passive_by_default"] is True
    assert r["ics_protocol_hits"] == []
    assert r["production_continuity_score"] == 100


def test_analyze_ot_ics_modbus_hit():
    system_data = {
        "network_connections": [
            {
                "process_name": "python",
                "pid": 1,
                "local_address": "192.168.1.10:49152",
                "remote_address": "192.168.1.99:502",
                "status": "ESTABLISHED",
                "protocol": "tcp",
            }
        ]
    }
    r = analyze_ot_ics(system_data)
    assert len(r["ics_protocol_hits"]) >= 1
    assert 502 in r["ics_ports_observed"]
    assert r["distinct_ics_protocols"] >= 1


def test_analyze_ot_ics_multi_protocol_triggers_playbooks():
    system_data = {
        "network_connections": [
            {
                "process_name": "some_engine",
                "pid": 2,
                "local_address": "10.0.0.5:45000",
                "remote_address": "10.0.0.20:502",
                "status": "ESTABLISHED",
                "protocol": "tcp",
            },
            {
                "process_name": "some_engine",
                "pid": 2,
                "local_address": "10.0.0.5:45001",
                "remote_address": "10.0.0.21:102",
                "status": "ESTABLISHED",
                "protocol": "tcp",
            },
            {
                "process_name": "some_engine",
                "pid": 2,
                "local_address": "10.0.0.5:45002",
                "remote_address": "10.0.0.22:4840",
                "status": "ESTABLISHED",
                "protocol": "tcp",
            },
        ]
    }
    r = analyze_ot_ics(system_data)
    assert r["distinct_ics_protocols"] >= 3
    ids = {p["id"] for p in r["ot_playbooks_triggered"]}
    assert "ot_pipedream_like" in ids
