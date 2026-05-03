#!/usr/bin/env python3
"""
COA — محاكاة آمنة لإشارات تهديد (لاختبار اللوحة / الويب فقط)
============================================================
لا يُنفّذ هجوماً حقيقياً: يشغّل عمليات محلية على جهازك تُفعّل قواعد COA
(منافذ مشبوهة، مسار tmp، نمط اسم مشبوه) ثم تبقى قيد التشغيل مدة محددة.

الاستخدام:
  cd COA_Project && source venv/bin/activate
  python scripts/scan_attack_simulator.py
  # ثم من المتصفح: لوحة الأداء → فحص

  python scripts/scan_attack_simulator.py --duration 60
  python scripts/scan_attack_simulator.py --no-curl   # بدون عميل من /tmp
"""

from __future__ import annotations

import argparse
import atexit
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path


def _find_sleep() -> Path | None:
    for p in ("/bin/sleep", "/usr/bin/sleep"):
        if Path(p).is_file():
            return Path(p)
    return None


def _find_bash() -> Path | None:
    for p in ("/bin/bash", "/usr/local/bin/bash"):
        if Path(p).is_file():
            return Path(p)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="COA local scan simulator (benign heuristics triggers)")
    ap.add_argument("--duration", type=int, default=240, help="Seconds to keep child processes alive (default 240)")
    ap.add_argument("--port", type=int, default=4444, help="Suspicious local listener port (must be in COA SUSPICIOUS_PORTS)")
    ap.add_argument("--no-curl", action="store_true", help="Skip /tmp curl client + listener (only sleep + masquerade)")
    args = ap.parse_args()

    if sys.platform == "win32":
        print("هذا السكربت مخصص لـ macOS/Linux (يعتمد على /tmp ونسخ ثنائيات).", file=sys.stderr)
        return 2

    tmp = Path(tempfile.gettempdir())
    tag = uuid.uuid4().hex[:8]
    children: list[subprocess.Popen] = []

    def cleanup(*_: object) -> None:
        for p in children:
            try:
                p.terminate()
            except Exception:
                pass
        time.sleep(0.2)
        for p in children:
            try:
                p.kill()
            except Exception:
                pass

    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(130)))
    signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), sys.exit(143)))
    atexit.register(cleanup)

    sleep_src = _find_sleep()
    if not sleep_src:
        print("لم يُعثر على sleep في النظام.", file=sys.stderr)
        return 1

    sleep_copy = tmp / f"coa_scanlab_sleep_{tag}"
    # copyfile يتجنب copystat/chflags التي تفشل أحياناً تحت /var/folders على macOS
    shutil.copyfile(sleep_src, sleep_copy)
    os.chmod(sleep_copy, 0o755)
    hold = max(15, args.duration)
    p_sleep = subprocess.Popen([str(sleep_copy), str(hold)], start_new_session=True)
    children.append(p_sleep)
    print(f"[+] عملية من /tmp (runs_from_temp): PID {p_sleep.pid}  {sleep_copy}")

    bash = _find_bash()
    if bash:
        # اسم عملية يطابق نمط انتحال في threat_analyzer (MASQUERADING_PATTERNS)
        p_masq = subprocess.Popen(
            [str(bash), "-c", f"exec -a svch0st {sleep_src} {hold}"],
            start_new_session=True,
        )
        children.append(p_masq)
        print(f"[+] عملية باسم مشبوه (masquerading_name): PID {p_masq.pid}  (exec -a svch0st)")

    if not args.no_curl:
        curl = shutil.which("curl")
        if not curl:
            print("[!] curl غير موجود — تخطّي منفذ مشبوه محلي.", file=sys.stderr)
        else:
            curl_copy = tmp / f"coa_scanlab_curl_{tag}"
            shutil.copyfile(curl, curl_copy)
            os.chmod(curl_copy, 0o755)

            allowed = (4444, 5555, 6666, 1337, 31337, 8080, 9090)
            port = args.port if args.port in allowed else 4444
            if args.port not in allowed:
                print(f"[!] استخدام المنفذ {port} (من قائمة COA).", file=sys.stderr)

            chosen: int | None = None
            for candidate in (port,) + tuple(p for p in allowed if p != port):
                probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    probe.bind(("127.0.0.1", candidate))
                    probe.close()
                    chosen = candidate
                    break
                except OSError:
                    try:
                        probe.close()
                    except OSError:
                        pass

            if chosen is None:
                print("[!] كل المنافذ المجرّبة مشغولة — تخطّي curl.", file=sys.stderr)
            else:
                port = chosen

                def listener(bind_port: int) -> None:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    conn = None
                    try:
                        s.bind(("127.0.0.1", bind_port))
                        s.listen(1)
                        s.settimeout(max(15.0, float(hold)))
                        conn, _ = s.accept()
                        try:
                            conn.recv(8192)
                        except OSError:
                            pass
                        time.sleep(hold)
                    finally:
                        try:
                            if conn:
                                conn.close()
                        except OSError:
                            pass
                        try:
                            s.close()
                        except OSError:
                            pass

                th = threading.Thread(target=listener, args=(port,), daemon=True)
                th.start()
                time.sleep(0.45)

                p_curl = subprocess.Popen(
                    [
                        str(curl_copy),
                        "-sS",
                        f"http://127.0.0.1:{port}/coa-scanlab",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                children.append(p_curl)
                print(
                    f"[+] اتصال من نسخة curl تحت /tmp إلى 127.0.0.1:{port} "
                    f"(suspicious_port + runs_from_temp على صف الاتصال): PID {p_curl.pid}"
                )

    print()
    print("—" * 52)
    print("الآن شغّل «فحصاً» من لوحة الويب (مع web_api.py).")
    print("بعد انتهاء الاختبار أوقف هذا السكربت بـ Ctrl+C (يُنهي العمليات الفرعية).")
    print("—" * 52)
    print()

    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        cleanup()
        return 130

    cleanup()
    print("\n[+] انتهت المدة — تم إيقاف العمليات.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
