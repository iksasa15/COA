"""
Structured Logging System
=========================
Professional logging with JSON format + file rotation
"""

import logging
import json
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional


class JSONFormatter(logging.Formatter):
    """منسق الـ logs بصيغة JSON للمعالجة الآلية"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }

        # إضافة معلومات الخطأ إن وجدت
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # إضافة أي حقول إضافية
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


class COALogger:
    """
    المسجل الرئيسي للنظام
    - يكتب JSON logs للتحليل الآلي
    - يحتفظ بـ rotation (5 ملفات × 10MB)
    """

    _instance: Optional['COALogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        """إعداد الـ logger مرة واحدة"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        self._logger = logging.getLogger("COA")
        self._logger.setLevel(logging.DEBUG)

        # منع التكرار
        if self._logger.handlers:
            return

        # Handler 1: ملف JSON مع rotation
        json_handler = RotatingFileHandler(
            log_dir / "coa.json.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8',
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.DEBUG)

        # Handler 2: ملف نصي قابل للقراءة البشرية
        text_handler = RotatingFileHandler(
            log_dir / "coa.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding='utf-8',
        )
        text_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s'
        ))
        text_handler.setLevel(logging.INFO)

        self._logger.addHandler(json_handler)
        self._logger.addHandler(text_handler)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """تسجيل مع بيانات إضافية"""
        extra = {'extra_data': kwargs} if kwargs else None
        self._logger.log(level, message, extra=extra)

    def log_threat(self, threat: dict):
        """تسجيل خاص للتهديدات"""
        self.warning(
            f"Threat detected: {threat.get('type')}",
            severity=threat.get('severity'),
            source=threat.get('source'),
            threat_type=threat.get('type'),
        )

    def log_action(self, command: str, approved: bool, result: dict = None):
        """تسجيل الإجراءات المتخذة"""
        status = "approved" if approved else "rejected"
        self.info(
            f"Security action {status}",
            command=command,
            approved=approved,
            success=result.get('success') if result else None,
        )


# Singleton instance جاهز للاستخدام
logger = COALogger()
