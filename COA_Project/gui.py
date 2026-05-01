"""
C.O.A GUI - Graphical User Interface (legacy Tkinter)
======================================================
Prefer the React dashboard: run `python web_api.py` then `cd web && npm run dev`.

Run this file with: python gui.py  (requires Python built with Tk / python-tk on macOS)
"""

import sys
import threading
import queue
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

sys.path.insert(0, str(Path(__file__).parent))

from core.data_collector import SystemDataCollector
from core.threat_analyzer import ThreatAnalyzer
from core.solution_engine import SolutionEngine
from utils.report_generator import ReportGenerator
from utils.html_report import HTMLReportGenerator
from agents.defense_context_analyzer import DefenseContextAnalyzer
from agents.incident_reporter import IncidentReporter
from config.settings import REPORTS_DIR


class COAGui:
    """الواجهة الرسومية الكاملة للنظام"""

    # Dark theme colors
    BG_PRIMARY = "#0f172a"
    BG_SECONDARY = "#1e293b"
    BG_ACCENT = "#334155"
    FG_PRIMARY = "#e2e8f0"
    FG_MUTED = "#94a3b8"
    COLOR_CYAN = "#38bdf8"
    COLOR_GREEN = "#22c55e"
    COLOR_RED = "#ef4444"
    COLOR_ORANGE = "#f97316"
    COLOR_YELLOW = "#eab308"
    COLOR_PURPLE = "#a855f7"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("C.O.A — Council of Agents v2.0")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.BG_PRIMARY)

        self.scan_data = None
        self.analysis_result = None
        self.defense_context = None
        self.reporter = ReportGenerator()
        self.solution_engine = SolutionEngine(dry_run=False)
        self.event_queue = queue.Queue()

        self._setup_styles()
        self._build_ui()
        self._start_queue_processor()

    def _setup_styles(self):
        """إعداد الستايل للعناصر"""
        style = ttk.Style()
        style.theme_use('clam')

        # Treeview dark theme
        style.configure(
            "Treeview",
            background=self.BG_SECONDARY,
            foreground=self.FG_PRIMARY,
            fieldbackground=self.BG_SECONDARY,
            borderwidth=0,
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=self.BG_ACCENT,
            foreground=self.COLOR_CYAN,
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[('selected', self.COLOR_CYAN)],
            foreground=[('selected', self.BG_PRIMARY)],
        )

        # Progressbar
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=self.COLOR_CYAN,
            troughcolor=self.BG_ACCENT,
            borderwidth=0,
        )

        # Notebook
        style.configure(
            "TNotebook",
            background=self.BG_PRIMARY,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=self.BG_SECONDARY,
            foreground=self.FG_MUTED,
            padding=[20, 10],
            font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[('selected', self.COLOR_CYAN)],
            foreground=[('selected', self.BG_PRIMARY)],
        )

    def _build_ui(self):
        """بناء الواجهة"""
        # Header
        header = tk.Frame(self.root, bg=self.BG_PRIMARY, height=80)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            header,
            text="🛡️ C.O.A",
            font=("Segoe UI", 28, "bold"),
            fg=self.COLOR_CYAN,
            bg=self.BG_PRIMARY,
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Council of Agents v2.0",
            font=("Segoe UI", 12),
            fg=self.FG_MUTED,
            bg=self.BG_PRIMARY,
        ).pack(side=tk.LEFT, padx=(15, 0), pady=(12, 0))

        # Control Panel
        controls = tk.Frame(self.root, bg=self.BG_SECONDARY)
        controls.pack(fill=tk.X, padx=20, pady=10)

        self.scan_btn = tk.Button(
            controls,
            text="🔍 Start Scan",
            font=("Segoe UI", 11, "bold"),
            bg=self.COLOR_CYAN,
            fg=self.BG_PRIMARY,
            activebackground=self.COLOR_GREEN,
            relief=tk.FLAT,
            padx=25,
            pady=10,
            cursor="hand2",
            command=self.start_scan,
        )
        self.scan_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.dry_run_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            controls,
            text="🧪 Dry Run",
            variable=self.dry_run_var,
            font=("Segoe UI", 10),
            bg=self.BG_SECONDARY,
            fg=self.FG_PRIMARY,
            activebackground=self.BG_SECONDARY,
            selectcolor=self.BG_ACCENT,
        ).pack(side=tk.LEFT, padx=10)

        self.quick_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            controls,
            text="⚡ Quick Mode",
            variable=self.quick_var,
            font=("Segoe UI", 10),
            bg=self.BG_SECONDARY,
            fg=self.FG_PRIMARY,
            activebackground=self.BG_SECONDARY,
            selectcolor=self.BG_ACCENT,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            controls,
            text="📄 Export TXT",
            font=("Segoe UI", 10),
            bg=self.BG_ACCENT,
            fg=self.FG_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=lambda: self.export_report('txt'),
        ).pack(side=tk.RIGHT, padx=5, pady=10)

        tk.Button(
            controls,
            text="🌐 Export HTML",
            font=("Segoe UI", 10),
            bg=self.BG_ACCENT,
            fg=self.FG_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=lambda: self.export_report('html'),
        ).pack(side=tk.RIGHT, padx=5, pady=10)

        tk.Button(
            controls,
            text="📊 Incident Report",
            font=("Segoe UI", 10),
            bg=self.COLOR_PURPLE,
            fg=self.FG_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2",
            command=self.generate_incident_report,
        ).pack(side=tk.RIGHT, padx=5, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            style="Custom.Horizontal.TProgressbar",
            length=100,
            mode='indeterminate',
        )
        self.progress.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Stats cards
        self._build_stats_row()

        # Tabbed content
        self._build_tabs()

        # Status bar
        self.status_var = tk.StringVar(value="Ready to scan")
        status_bar = tk.Frame(self.root, bg=self.BG_SECONDARY, height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            fg=self.FG_MUTED,
            bg=self.BG_SECONDARY,
            anchor=tk.W,
        ).pack(fill=tk.X, padx=20, pady=5)

    def _build_stats_row(self):
        """صف البطاقات الإحصائية"""
        stats_frame = tk.Frame(self.root, bg=self.BG_PRIMARY)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)

        self.stat_labels = {}

        stats = [
            ("Connections", "0", self.COLOR_CYAN),
            ("Processes", "0", self.COLOR_GREEN),
            ("Critical", "0", self.COLOR_RED),
            ("High", "0", self.COLOR_ORANGE),
            ("Medium", "0", self.COLOR_YELLOW),
            ("Total Threats", "0", self.COLOR_PURPLE),
        ]

        for label, value, color in stats:
            card = tk.Frame(stats_frame, bg=self.BG_SECONDARY)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            val_label = tk.Label(
                card,
                text=value,
                font=("Segoe UI", 24, "bold"),
                fg=color,
                bg=self.BG_SECONDARY,
            )
            val_label.pack(pady=(15, 0))

            tk.Label(
                card,
                text=label,
                font=("Segoe UI", 10),
                fg=self.FG_MUTED,
                bg=self.BG_SECONDARY,
            ).pack(pady=(0, 15))

            self.stat_labels[label] = val_label

    def _build_tabs(self):
        """بناء التبويبات"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Tab 1: Threats
        threats_frame = tk.Frame(notebook, bg=self.BG_SECONDARY)
        notebook.add(threats_frame, text="🚨 Threats")

        columns = ("#", "Severity", "Confidence", "Score", "Source", "Details", "Action")
        self.threats_tree = ttk.Treeview(
            threats_frame, columns=columns, show="headings", height=15
        )
        for col in columns:
            self.threats_tree.heading(col, text=col)
            if col == "#":
                self.threats_tree.column(col, width=40)
            elif col in ("Severity", "Confidence", "Score"):
                self.threats_tree.column(col, width=90)
            elif col == "Details":
                self.threats_tree.column(col, width=400)
            else:
                self.threats_tree.column(col, width=150)

        # Severity color tags
        self.threats_tree.tag_configure("CRITICAL", foreground=self.COLOR_RED)
        self.threats_tree.tag_configure("HIGH", foreground=self.COLOR_ORANGE)
        self.threats_tree.tag_configure("MEDIUM", foreground=self.COLOR_YELLOW)
        self.threats_tree.tag_configure("LOW", foreground=self.COLOR_GREEN)

        scrollbar = ttk.Scrollbar(threats_frame, orient=tk.VERTICAL, command=self.threats_tree.yview)
        self.threats_tree.configure(yscrollcommand=scrollbar.set)

        self.threats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Tab 2: Processes
        proc_frame = tk.Frame(notebook, bg=self.BG_SECONDARY)
        notebook.add(proc_frame, text="⚙️ Processes")

        self.proc_tree = ttk.Treeview(
            proc_frame,
            columns=("PID", "Name", "CPU%", "RAM%", "Path"),
            show="headings",
            height=15,
        )
        for col, width in [("PID", 80), ("Name", 180), ("CPU%", 80), ("RAM%", 80), ("Path", 500)]:
            self.proc_tree.heading(col, text=col)
            self.proc_tree.column(col, width=width)

        proc_scroll = ttk.Scrollbar(proc_frame, orient=tk.VERTICAL, command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=proc_scroll.set)

        self.proc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        proc_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Tab 3: Network
        net_frame = tk.Frame(notebook, bg=self.BG_SECONDARY)
        notebook.add(net_frame, text="🌐 Network")

        self.net_tree = ttk.Treeview(
            net_frame,
            columns=("PID", "Process", "Local", "Remote", "Status", "Proto"),
            show="headings",
            height=15,
        )
        for col, width in [("PID", 70), ("Process", 180), ("Local", 180),
                           ("Remote", 180), ("Status", 120), ("Proto", 80)]:
            self.net_tree.heading(col, text=col)
            self.net_tree.column(col, width=width)

        net_scroll = ttk.Scrollbar(net_frame, orient=tk.VERTICAL, command=self.net_tree.yview)
        self.net_tree.configure(yscrollcommand=net_scroll.set)

        self.net_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        net_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

        # Tab 4: Logs
        log_frame = tk.Frame(notebook, bg=self.BG_SECONDARY)
        notebook.add(log_frame, text="📝 Logs")

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg=self.BG_PRIMARY,
            fg=self.FG_PRIMARY,
            insertbackground=self.FG_PRIMARY,
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tags for colored logs
        self.log_text.tag_configure("INFO", foreground=self.COLOR_CYAN)
        self.log_text.tag_configure("SUCCESS", foreground=self.COLOR_GREEN)
        self.log_text.tag_configure("WARNING", foreground=self.COLOR_YELLOW)
        self.log_text.tag_configure("ERROR", foreground=self.COLOR_RED)

    def _start_queue_processor(self):
        """معالج رسائل الـ thread"""
        try:
            while True:
                msg = self.event_queue.get_nowait()
                self._handle_queue_message(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._start_queue_processor)

    def _handle_queue_message(self, msg):
        """معالجة رسائل من الـ thread"""
        msg_type = msg.get('type')

        if msg_type == 'log':
            self.add_log(msg['text'], msg.get('level', 'INFO'))
        elif msg_type == 'status':
            self.status_var.set(msg['text'])
        elif msg_type == 'progress_start':
            self.progress.start(10)
        elif msg_type == 'progress_stop':
            self.progress.stop()
        elif msg_type == 'scan_complete':
            self.on_scan_complete(msg['data'])
        elif msg_type == 'scan_error':
            messagebox.showerror("Scan Error", msg['error'])

    def add_log(self, text, level="INFO"):
        """إضافة رسالة للـ log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {text}\n", level)
        self.log_text.see(tk.END)

    def start_scan(self):
        """بدء الفحص في thread منفصل"""
        self.scan_btn.config(state=tk.DISABLED)
        # مسح البيانات القديمة
        for tree in (self.threats_tree, self.proc_tree, self.net_tree):
            for item in tree.get_children():
                tree.delete(item)

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()

    def _run_scan(self):
        """تشغيل الفحص الفعلي (في thread)"""
        try:
            self.event_queue.put({'type': 'progress_start'})
            self.event_queue.put({'type': 'status', 'text': 'Collecting data...'})
            self.event_queue.put({'type': 'log', 'text': 'Starting scan', 'level': 'INFO'})

            # Collection
            system_data = SystemDataCollector.collect_all()
            self.event_queue.put({
                'type': 'log',
                'text': f'Collected {len(system_data["network_connections"])} conns, '
                        f'{len(system_data["processes"])} procs',
                'level': 'SUCCESS',
            })

            # Analysis
            self.event_queue.put({'type': 'status', 'text': 'Analyzing threats...'})
            analysis = ThreatAnalyzer.full_analysis(system_data)
            self.event_queue.put({
                'type': 'log',
                'text': f'Analysis done: {analysis["total_threats"]} threats found',
                'level': 'WARNING' if analysis["total_threats"] > 0 else 'SUCCESS',
            })

            defense_context = DefenseContextAnalyzer.analyze(system_data, analysis)
            self.event_queue.put({
                'type': 'log',
                'text': 'Defense Context Analyzer (Agent #5) completed',
                'level': 'INFO',
            })

            self.event_queue.put({'type': 'progress_stop'})
            self.event_queue.put({
                'type': 'scan_complete',
                'data': {
                    'system_data': system_data,
                    'analysis': analysis,
                    'defense_context': defense_context,
                },
            })

        except Exception as e:
            self.event_queue.put({'type': 'progress_stop'})
            self.event_queue.put({
                'type': 'log',
                'text': f'Scan failed: {e}',
                'level': 'ERROR',
            })
            self.event_queue.put({'type': 'scan_error', 'error': str(e)})

    def on_scan_complete(self, data):
        """عند اكتمال الفحص"""
        self.scan_data = data['system_data']
        self.analysis_result = data['analysis']
        self.defense_context = data.get('defense_context')

        # تحديث الإحصائيات
        self.stat_labels["Connections"].config(
            text=str(len(self.scan_data["network_connections"]))
        )
        self.stat_labels["Processes"].config(
            text=str(len(self.scan_data["processes"]))
        )
        self.stat_labels["Critical"].config(text=str(self.analysis_result.get("critical", 0)))
        self.stat_labels["High"].config(text=str(self.analysis_result.get("high", 0)))
        self.stat_labels["Medium"].config(text=str(self.analysis_result.get("medium", 0)))
        self.stat_labels["Total Threats"].config(text=str(self.analysis_result.get("total_threats", 0)))

        # تعبئة جدول التهديدات
        for i, threat in enumerate(self.analysis_result.get("threats", []), 1):
            self.threats_tree.insert(
                "", tk.END,
                values=(
                    i,
                    threat.get("severity"),
                    threat.get("confidence"),
                    threat.get("score"),
                    threat.get("source"),
                    threat.get("details"),
                    threat.get("recommended_action"),
                ),
                tags=(threat.get("severity"),),
            )

        # تعبئة العمليات
        for proc in self.scan_data.get("processes", [])[:100]:
            self.proc_tree.insert(
                "", tk.END,
                values=(
                    proc.get("pid"),
                    proc.get("name"),
                    f"{proc.get('cpu_percent', 0)}%",
                    f"{proc.get('memory_percent', 0)}%",
                    proc.get("path", "N/A"),
                ),
            )

        # تعبئة الاتصالات
        for conn in self.scan_data.get("network_connections", []):
            self.net_tree.insert(
                "", tk.END,
                values=(
                    conn.get("pid"),
                    conn.get("process_name"),
                    conn.get("local_address"),
                    conn.get("remote_address"),
                    conn.get("status"),
                    conn.get("protocol"),
                ),
            )

        self.status_var.set(f"✅ Scan complete — {self.analysis_result.get('total_threats', 0)} threats found")
        self.scan_btn.config(state=tk.NORMAL)

    def export_report(self, format_type):
        """تصدير التقرير"""
        if not self.analysis_result:
            messagebox.showinfo("No Data", "Please run a scan first")
            return

        try:
            if format_type == 'txt':
                path = self.reporter.generate(
                    self.scan_data["system_info"],
                    self.analysis_result,
                )
            elif format_type == 'html':
                output = REPORTS_DIR / "COA_Report.html"
                path = HTMLReportGenerator.generate(
                    self.scan_data["system_info"],
                    self.analysis_result,
                    self.reporter.events,
                    output,
                )
            messagebox.showinfo(
                "Report Saved",
                f"Report saved successfully to:\n{path}"
            )
            self.add_log(f"Report exported: {path}", "SUCCESS")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    def generate_incident_report(self):
        """توليد تقرير حادث احترافي"""
        if not self.analysis_result:
            messagebox.showinfo("No Data", "Please run a scan first")
            return

        try:
            output = REPORTS_DIR / "COA_Incident_Report.txt"
            path = IncidentReporter.generate_full_report(
                self.scan_data["system_info"],
                self.analysis_result,
                self.reporter.events,
                output,
                defense_context=self.defense_context,
            )
            messagebox.showinfo(
                "Incident Report",
                f"Professional incident report generated:\n{path}"
            )
            self.add_log(f"Incident report: {path}", "SUCCESS")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def run(self):
        """تشغيل الواجهة"""
        self.add_log("C.O.A GUI v2.0 started", "INFO")
        self.add_log("Click 'Start Scan' to begin", "INFO")
        self.root.mainloop()


if __name__ == "__main__":
    app = COAGui()
    app.run()
