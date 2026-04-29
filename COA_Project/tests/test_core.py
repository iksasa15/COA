"""
Unit Tests for C.O.A
====================
Run with: pytest tests/ -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.threat_analyzer import ThreatAnalyzer, ThreatScorer
from core.solution_engine import SolutionEngine, CommandValidator
from utils.cache import SmartCache
import time


# ==================== Threat Scorer Tests ====================
class TestThreatScorer:
    def test_severity_critical(self):
        assert ThreatScorer.calculate_severity(85) == "CRITICAL"

    def test_severity_high(self):
        assert ThreatScorer.calculate_severity(65) == "HIGH"

    def test_severity_medium(self):
        assert ThreatScorer.calculate_severity(45) == "MEDIUM"

    def test_severity_low(self):
        assert ThreatScorer.calculate_severity(25) == "LOW"

    def test_severity_info(self):
        assert ThreatScorer.calculate_severity(10) == "INFO"

    def test_confidence_high_many_signals(self):
        signals = ['sig1', 'sig2', 'sig3', 'sig4']
        assert ThreatScorer.calculate_confidence(signals) == "HIGH"

    def test_confidence_medium_two_signals(self):
        assert ThreatScorer.calculate_confidence(['sig1', 'sig2']) == "MEDIUM"

    def test_confidence_low_one_signal(self):
        assert ThreatScorer.calculate_confidence(['sig1']) == "LOW"


# ==================== Threat Analyzer Tests ====================
class TestThreatAnalyzer:
    def test_trusted_ip_localhost(self):
        assert ThreatAnalyzer._is_trusted_ip("127.0.0.1") is True

    def test_trusted_ip_private(self):
        assert ThreatAnalyzer._is_trusted_ip("192.168.1.100") is True

    def test_untrusted_public_ip(self):
        assert ThreatAnalyzer._is_trusted_ip("8.8.8.8") is False

    def test_suspicious_path_temp(self):
        assert ThreatAnalyzer._is_suspicious_path("C:\\Temp\\malware.exe") is True

    def test_suspicious_path_appdata(self):
        assert ThreatAnalyzer._is_suspicious_path("C:\\Users\\X\\AppData\\Local\\Temp\\x.exe") is True

    def test_safe_path_program_files(self):
        assert ThreatAnalyzer._is_suspicious_path("C:\\Program Files\\app.exe") is False

    def test_trusted_process(self):
        assert ThreatAnalyzer._is_trusted_process("explorer.exe") is True

    def test_masquerading_detection(self):
        assert ThreatAnalyzer._is_masquerading("svch0st.exe") is True
        assert ThreatAnalyzer._is_masquerading("scvhost.exe") is True

    def test_legitimate_name_not_masquerading(self):
        assert ThreatAnalyzer._is_masquerading("svchost.exe") is False

    def test_analyze_suspicious_connection(self):
        conn = {
            "pid": 1234,
            "process_name": "suspicious.exe",
            "process_path": "C:\\Temp\\suspicious.exe",
            "remote_address": "8.8.8.8:4444",
            "status": "ESTABLISHED",
        }
        result = ThreatAnalyzer.analyze_connection(conn)
        assert result is not None
        assert result["severity"] in ["CRITICAL", "HIGH"]
        assert "suspicious_port" in result["signals"]

    def test_analyze_clean_connection(self):
        conn = {
            "pid": 100,
            "process_name": "chrome.exe",
            "process_path": "C:\\Program Files\\chrome\\chrome.exe",
            "remote_address": "192.168.1.1:443",
            "status": "ESTABLISHED",
        }
        result = ThreatAnalyzer.analyze_connection(conn)
        assert result is None  # Should not be flagged


# ==================== Solution Engine Tests ====================
class TestSolutionEngine:
    def test_dry_run_no_execution(self):
        engine = SolutionEngine(dry_run=True)
        result = engine.execute_command("taskkill /F /PID 1234", approved=True)
        assert result["dry_run"] is True
        assert "DRY RUN" in result["output"]

    def test_blocked_without_approval(self):
        engine = SolutionEngine(dry_run=False)
        result = engine.execute_command("taskkill /F /PID 1234", approved=False)
        assert result["success"] is False
        assert "SECURITY" in result["error"]

    def test_kill_command_generation(self):
        threat = {
            "recommended_action": "kill_process",
            "target_pid": 1234,
            "source": "bad.exe (PID: 1234)",
        }
        solution = SolutionEngine.generate_solution(threat)
        assert "1234" in solution["command"]
        assert solution["risk_level"] == "MEDIUM"
        assert solution["reversible"] is False

    def test_firewall_block_is_reversible(self):
        threat = {
            "recommended_action": "block_ip",
            "target_pid": 1234,
            "target_ip": "1.2.3.4",
            "source": "bad.exe",
        }
        solution = SolutionEngine.generate_solution(threat)
        assert solution["reversible"] is True
        assert solution["rollback_command"] is not None


# ==================== Command Validator Tests ====================
class TestCommandValidator:
    def test_safe_taskkill(self):
        is_safe, _ = CommandValidator.is_safe("taskkill /F /PID 1234")
        assert is_safe is True

    def test_blocks_format(self):
        is_safe, _ = CommandValidator.is_safe("format c:")
        assert is_safe is False

    def test_blocks_rm_rf(self):
        is_safe, _ = CommandValidator.is_safe("rm -rf /")
        assert is_safe is False

    def test_blocks_shutdown(self):
        is_safe, _ = CommandValidator.is_safe("shutdown /s /t 0")
        assert is_safe is False

    def test_blocks_fork_bomb(self):
        is_safe, _ = CommandValidator.is_safe(":(){:|:&};:")
        assert is_safe is False

    def test_empty_command_rejected(self):
        is_safe, _ = CommandValidator.is_safe("")
        assert is_safe is False


# ==================== Cache Tests ====================
class TestSmartCache:
    def test_basic_get_set(self):
        cache = SmartCache(default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        cache = SmartCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = SmartCache(default_ttl=1)
        cache.set("key", "value")
        time.sleep(1.1)
        assert cache.get("key") is None

    def test_hit_rate_tracking(self):
        cache = SmartCache()
        cache.set("k", "v")
        cache.get("k")  # hit
        cache.get("k")  # hit
        cache.get("x")  # miss

        stats = cache.stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1

    def test_cached_decorator(self):
        cache = SmartCache(default_ttl=10)
        call_count = {'n': 0}

        @cache.cached()
        def expensive_function(x):
            call_count['n'] += 1
            return x * 2

        # استدعاء أول
        assert expensive_function(5) == 10
        assert call_count['n'] == 1

        # استدعاء ثاني (من cache)
        assert expensive_function(5) == 10
        assert call_count['n'] == 1  # لم يزد


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
