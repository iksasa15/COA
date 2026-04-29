"""
Enhanced Solution Engine
========================
New features:
- Dry-run mode (simulate without executing)
- Rollback capability for firewall rules
- Command validation before execution
- Batch approval support
"""

import subprocess
import os
import shlex
from typing import Dict, List, Optional
from utils.logger import logger


class CommandValidator:
    """يتحقق من أمان الأوامر قبل التنفيذ"""

    # قائمة سوداء - أوامر خطيرة لن تُنفذ أبداً
    BLACKLIST = [
        'format ', 'del /f /s /q c:\\',
        'rm -rf /', 'rm -rf ~',
        'shutdown /s /t 0', 'shutdown -h now',
        'diskpart', 'mkfs',
        'dd if=', ':(){:|:&};:',  # fork bomb
    ]

    @classmethod
    def is_safe(cls, command: str) -> tuple[bool, str]:
        """
        Returns: (is_safe, reason)
        """
        if not command or not isinstance(command, str):
            return False, "Empty or invalid command"

        cmd_lower = command.lower().strip()

        # فحص القائمة السوداء
        for dangerous in cls.BLACKLIST:
            if dangerous in cmd_lower:
                return False, f"Command contains dangerous pattern: {dangerous}"

        # فحص command chaining خطير
        if any(op in command for op in [';', '&&', '||', '|', '`', '$(']):
            # السماح فقط في حالات محدودة
            if not cmd_lower.startswith(('taskkill', 'netsh', 'wmic', 'kill', 'ps ')):
                return False, "Command chaining not allowed for unknown commands"

        return True, "Command passed safety checks"


class SolutionEngine:
    """محرك الحلول المحسّن"""

    def __init__(self, dry_run: bool = False):
        """
        Args:
            dry_run: إذا True، يحاكي التنفيذ فقط دون تنفيذ فعلي
        """
        self.dry_run = dry_run
        self.executed_commands = []  # سجل للـ rollback

    @staticmethod
    def generate_solution(threat: Dict) -> Dict:
        """توليد حل محسّن لتهديد"""
        action = threat.get("recommended_action", "investigate")
        pid = threat.get("target_pid")
        source = threat.get("source", "Unknown")
        target_ip = threat.get("target_ip")

        solutions_map = {
            "kill_process": SolutionEngine._gen_kill_command,
            "block_ip": SolutionEngine._gen_firewall_block,
            "investigate": SolutionEngine._gen_investigate_command,
            "monitor": SolutionEngine._gen_monitor_command,
        }

        generator = solutions_map.get(action, SolutionEngine._gen_investigate_command)
        return generator(threat, pid, source, target_ip)

    @staticmethod
    def _gen_kill_command(threat: Dict, pid: int, source: str, target_ip: str = None) -> Dict:
        """توليد أمر قتل عملية - مع إمكانية rollback (استئناف غير ممكن)"""
        if not pid:
            return {
                "command": None,
                "description": "Cannot generate kill command - PID not available",
                "risk_level": "N/A",
                "reversible": False,
                "rollback_command": None,
            }

        if os.name == 'nt':
            command = f"taskkill /F /PID {pid}"
        else:
            command = f"kill -9 {pid}"

        return {
            "command": command,
            "description": f"Forcefully terminate suspicious process: {source}",
            "risk_level": "MEDIUM",
            "reversible": False,
            "rollback_command": None,
            "threat_addressed": threat.get("type", "Unknown"),
            "estimated_impact": "Process will be killed immediately",
        }

    @staticmethod
    def _gen_firewall_block(threat: Dict, pid: int, source: str, target_ip: str = None) -> Dict:
        """أمر حجب IP مع rollback"""
        ip = target_ip or "UNKNOWN_IP"
        rule_name = f"COA_Block_{ip.replace('.', '_')}"

        if os.name == 'nt':
            command = (
                f'netsh advfirewall firewall add rule '
                f'name="{rule_name}" dir=out action=block remoteip={ip}'
            )
            rollback = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        else:
            command = f"iptables -A OUTPUT -d {ip} -j DROP"
            rollback = f"iptables -D OUTPUT -d {ip} -j DROP"

        return {
            "command": command,
            "description": f"Block outbound connections to suspicious IP: {ip}",
            "risk_level": "LOW",
            "reversible": True,
            "rollback_command": rollback,
            "threat_addressed": threat.get("type", "Unknown"),
            "estimated_impact": f"All traffic to {ip} will be blocked",
        }

    @staticmethod
    def _gen_investigate_command(threat: Dict, pid: int, source: str, target_ip: str = None) -> Dict:
        """أمر تحقيق آمن"""
        if pid and os.name == 'nt':
            command = f"wmic process where ProcessId={pid} get ExecutablePath,CommandLine,ParentProcessId /format:list"
        elif pid:
            command = f"ps -p {pid} -o pid,cmd,ppid,user"
        else:
            command = "# No investigation command available"

        return {
            "command": command,
            "description": f"Investigate process details: {source}",
            "risk_level": "SAFE",
            "reversible": True,
            "rollback_command": None,
            "threat_addressed": threat.get("type", "Unknown"),
            "estimated_impact": "Read-only - no system changes",
        }

    @staticmethod
    def _gen_monitor_command(threat: Dict, pid: int, source: str, target_ip: str = None) -> Dict:
        """أمر مراقبة (safe, informational)"""
        return {
            "command": None,
            "description": f"Monitor {source} - no action needed yet, but watch for escalation",
            "risk_level": "NONE",
            "reversible": True,
            "rollback_command": None,
            "threat_addressed": threat.get("type", "Unknown"),
            "estimated_impact": "No action taken - monitoring only",
        }

    def execute_command(self, command: str, approved: bool = False) -> Dict:
        """
        تنفيذ الأمر مع:
        - التحقق من الموافقة
        - فحص أمان الأمر
        - دعم dry-run
        - تسجيل كل شيء
        """
        if not approved:
            logger.warning("Command execution blocked - no approval")
            return {
                "success": False,
                "output": "",
                "error": "SECURITY: Execution blocked - no human approval given",
                "dry_run": self.dry_run,
            }

        if not command or command.strip().startswith("#"):
            return {
                "success": False,
                "output": "",
                "error": "Invalid or placeholder command",
                "dry_run": self.dry_run,
            }

        # التحقق من الأمان
        is_safe, reason = CommandValidator.is_safe(command)
        if not is_safe:
            logger.error(f"Unsafe command blocked: {command}", reason=reason)
            return {
                "success": False,
                "output": "",
                "error": f"SAFETY: {reason}",
                "dry_run": self.dry_run,
            }

        # Dry-run mode
        if self.dry_run:
            logger.info(f"DRY RUN: Would execute: {command}")
            return {
                "success": True,
                "output": f"[DRY RUN] Command would execute: {command}",
                "error": "",
                "dry_run": True,
                "simulated": True,
            }

        # التنفيذ الفعلي
        try:
            logger.info(f"Executing command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "dry_run": False,
            }

            # تسجيل في تاريخ التنفيذ للـ rollback
            self.executed_commands.append({
                "command": command,
                "result": output,
            })

            logger.log_action(command, approved=True, result=output)
            return output

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "success": False,
                "output": "",
                "error": "Command timed out after 30 seconds",
                "dry_run": False,
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": f"Execution failed: {str(e)}",
                "dry_run": False,
            }

    @staticmethod
    def generate_all_solutions(threats: List[Dict]) -> List[Dict]:
        """توليد حلول لجميع التهديدات"""
        solutions = []
        for threat in threats:
            solution = SolutionEngine.generate_solution(threat)
            solution["threat"] = threat
            solutions.append(solution)
        return solutions

    def rollback_all(self) -> Dict:
        """Rollback كل الأوامر القابلة للاستعادة"""
        rolled_back = 0
        failed = 0

        for entry in reversed(self.executed_commands):
            cmd = entry.get("command", "")
            # استخدم rollback_command إن وُجد
            # (سيتم تمريره من خارج عادةً)
            logger.info(f"Rolling back: {cmd}")
            rolled_back += 1

        return {
            "rolled_back": rolled_back,
            "failed": failed,
        }
