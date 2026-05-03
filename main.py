#!/usr/bin/env python3
"""
C.O.A — تشغيل من جذر الريبو
===========================
يوجّه إلى COA_Project/main.py. إن وُجد `COA_Project/venv` يُعاد التشغيل تلقائياً
بـ Python الافتراضي للـ venv حتى تُحمَّل الحزم (pyfiglet، google-genai، …).

الموصى به: `cd COA_Project && source venv/bin/activate && python main.py ...`
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_APP_DIR = _ROOT / "COA_Project"
_APP_MAIN = _APP_DIR / "main.py"


def _venv_python(app_dir: Path) -> Path | None:
    for name in ("python3", "python"):
        p = app_dir / "venv" / "bin" / name
        if p.is_file() and os.access(p, os.X_OK):
            return p
    return None


if not _APP_MAIN.is_file():
    print(
        f"Cannot find {_APP_MAIN}\n"
        "Clone or copy the repo so COA_Project/main.py exists, or run:\n"
        "  cd COA_Project && python main.py ...",
        file=sys.stderr,
    )
    sys.exit(1)

_venv = _venv_python(_APP_DIR)
if _venv is not None and Path(sys.executable).resolve() != _venv.resolve():
    os.chdir(_APP_DIR)
    os.execv(str(_venv), [str(_venv), str(_APP_MAIN), *sys.argv[1:]])

os.chdir(_APP_DIR)
sys.path.insert(0, str(_APP_DIR))
sys.argv[0] = str(_APP_MAIN)
if _venv is None:
    print(
        "Note: no COA_Project/venv found — using current Python. "
        "For dependencies, run: cd COA_Project && python -m venv venv && "
        "source venv/bin/activate && pip install -r requirements.txt",
        file=sys.stderr,
    )
runpy.run_path(str(_APP_MAIN), run_name="__main__")
