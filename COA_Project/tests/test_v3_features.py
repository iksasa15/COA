"""
Unit Tests for v3.0 New Components
==================================
- VirusTotal integration
- YARA engine
- Incident Reporter
- Helpdesk API
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.incident_reporter import IncidentReporter
from helpdesk_api import COAHelpdesk
from core.virustotal import VirusTotalClient


# ==================== Incident Reporter Tests ====================
class TestIncidentReporter:
    def test_clean_system_classification(self):
        analysis = {'threats': [], 'critical': 0, 'high': 0, 'medium': 0}
        result = IncidentReporter.classify_incident(analysis)
        assert result['severity'] == 'NONE'
        assert result['priority'] == 5

    def test_critical_incident(self):
        analysis = {
            'threats': [{'severity': 'CRITICAL', 'signals': ['suspicious_port']}],
            'critical': 1, 'high': 0, 'medium': 0,
        }
        result = IncidentReporter.classify_incident(analysis)
        assert result['severity'] == 'CRITICAL'
        assert result['priority'] == 1

    def test_category_cryptominer(self):
        analysis = {
            'threats': [
                {'severity': 'HIGH', 'signals': ['high_cpu_low_memory', 'runs_from_temp']}
            ],
            'critical': 0, 'high': 1, 'medium': 0,
        }
        result = IncidentReporter.classify_incident(analysis)
        assert 'Cryptominer' in result['category']

    def test_mitre_mapping(self):
        threats = [
            {'signals': ['suspicious_port', 'runs_from_temp']},
            {'signals': ['high_cpu_low_memory']},
        ]
        ttps = IncidentReporter.mitre_mapping(threats)
        assert len(ttps) >= 2
        assert any('Command and Control' in t['tactic'] for t in ttps)

    def test_recommendations_clean(self):
        classification = {'severity': 'NONE', 'priority': 5}
        recs = IncidentReporter.recommendations([], classification)
        assert len(recs) > 0
        assert any('monitoring' in r.lower() for r in recs)

    def test_recommendations_critical(self):
        classification = {'severity': 'CRITICAL', 'priority': 1}
        threats = [{'signals': ['suspicious_port']}]
        recs = IncidentReporter.recommendations(threats, classification)
        assert any('Isolate' in r for r in recs)

    def test_executive_summary_clean(self):
        sys_info = {'hostname': 'TEST-PC'}
        analysis = {'threats': []}
        classification = {'severity': 'NONE', 'priority': 5}
        summary = IncidentReporter.executive_summary(sys_info, analysis, classification)
        assert 'No security threats' in summary
        assert 'TEST-PC' in summary

    def test_executive_summary_critical(self):
        sys_info = {'hostname': 'TEST-PC'}
        analysis = {
            'threats': [{'severity': 'CRITICAL'}],
            'critical': 1, 'high': 0,
        }
        classification = {'severity': 'CRITICAL', 'priority': 1, 'category': 'Test'}
        summary = IncidentReporter.executive_summary(sys_info, analysis, classification)
        assert 'CRITICAL' in summary
        assert 'Isolate' in summary


# ==================== Helpdesk API Tests ====================
class TestHelpdeskAPI:
    def test_initialization(self):
        helpdesk = COAHelpdesk(dry_run_default=True)
        assert helpdesk.dry_run_default is True
        assert helpdesk.scan_history == []

    def test_scan_system_returns_dict(self):
        helpdesk = COAHelpdesk()
        result = helpdesk.scan_system(user_id='test_user')
        assert isinstance(result, dict)
        assert 'scan_id' in result
        assert 'status' in result
        assert 'bot_response' in result

    def test_scan_includes_user_id(self):
        helpdesk = COAHelpdesk()
        result = helpdesk.scan_system(user_id='john_123')
        assert result.get('user_id') == 'john_123'

    def test_health_status(self):
        helpdesk = COAHelpdesk()
        health = helpdesk.get_health_status()
        assert 'status' in health
        assert 'timestamp' in health

    def test_bot_response_language(self):
        """Bot response should be user-friendly (not technical)"""
        helpdesk = COAHelpdesk()

        # محاكاة حادث critical
        classification = {'severity': 'CRITICAL', 'priority': 1, 'category': 'Test'}
        analysis = {'threats': [{'severity': 'CRITICAL'}], 'critical': 1}
        response = helpdesk._generate_bot_response(classification, analysis)

        # يجب أن يكون الرد ودوداً
        assert '🚨' in response or 'critical' in response.lower()
        assert 'IT support' in response or 'Disconnect' in response

    def test_invalid_scan_id(self):
        helpdesk = COAHelpdesk()
        result = helpdesk.get_remediation_plan(scan_id='nonexistent')
        assert result['status'] == 'error'


# ==================== VirusTotal Client Tests ====================
class TestVirusTotalClient:
    def test_disabled_without_key(self):
        client = VirusTotalClient(api_key=None)
        assert client.enabled is False

    def test_enabled_with_key(self):
        client = VirusTotalClient(api_key='fake_test_key')
        assert client.enabled is True

    def test_hash_computation(self):
        import tempfile
        # إنشاء ملف مؤقت
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test content")
            temp_path = f.name

        hash_value = VirusTotalClient.compute_file_hash(temp_path)
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 length

        import os
        os.unlink(temp_path)

    def test_check_file_without_key(self):
        client = VirusTotalClient(api_key=None)
        result = client.check_file('/tmp/nonexistent')
        assert 'error' in result
        assert result['found'] is False

    def test_confidence_calculation(self):
        # High confidence cases
        assert VirusTotalClient._calculate_vt_confidence(15, 70) == 'VERY_HIGH'
        assert VirusTotalClient._calculate_vt_confidence(7, 70) == 'HIGH'
        assert VirusTotalClient._calculate_vt_confidence(3, 70) == 'MEDIUM'
        assert VirusTotalClient._calculate_vt_confidence(1, 70) == 'LOW'
        assert VirusTotalClient._calculate_vt_confidence(0, 0) == 'UNKNOWN'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
