"""Presentation demo OT bundle (judges UI)."""

from ics_analyzer.demo_fixture import load_presentation_demo_ot_ics


def test_demo_fixture_loads():
    d = load_presentation_demo_ot_ics()
    assert d.get("presentation_demo") is True
    assert len(d.get("ics_protocol_hits") or []) >= 1
    assert "known_ports_reference" in d
