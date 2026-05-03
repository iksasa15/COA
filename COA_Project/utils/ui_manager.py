"""
UI Manager - Beautiful CLI Interface
====================================
Uses Rich library for professional console output
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from rich.text import Text
from rich.align import Align
from rich import box
import pyfiglet
import time
import math
import os
import threading
from typing import Callable, TypeVar

T = TypeVar("T")


console = Console()


class UIManager:
    """مدير الواجهة المرئية الكامل للنظام"""

    @staticmethod
    def display_banner():
        """عرض شعار الترحيب"""
        banner = pyfiglet.figlet_format("C.O.A", font="slant")
        subtitle = "Council of Agents — AI-Powered Security Scanner"
        version = "v1.0.0 | Local & Private"

        console.print("\n")
        console.print(Align.center(Text(banner, style="bold cyan")))
        console.print(Align.center(Text(subtitle, style="bold white")))
        console.print(Align.center(Text(version, style="dim")))
        console.print("\n")

    @staticmethod
    def section_header(title: str, icon: str = "▶"):
        """عرض عنوان قسم"""
        console.print(
            Panel(
                f"[bold white]{icon} {title}[/bold white]",
                style="cyan",
                box=box.DOUBLE_EDGE,
                padding=(0, 2),
            )
        )

    @staticmethod
    def info(message: str):
        """رسالة معلومات"""
        console.print(f"[cyan]ℹ️  {message}[/cyan]")

    @staticmethod
    def success(message: str):
        """رسالة نجاح"""
        console.print(f"[bold green]✅ {message}[/bold green]")

    @staticmethod
    def warning(message: str):
        """رسالة تحذير"""
        console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")

    @staticmethod
    def danger(message: str):
        """رسالة خطر"""
        console.print(f"[bold red]🚨 {message}[/bold red]")

    @staticmethod
    def agent_message(agent_name: str, message: str, color: str = "magenta"):
        """رسالة من وكيل"""
        console.print(f"[bold {color}][{agent_name}][/bold {color}] {message}")

    @staticmethod
    def show_progress(task_description: str, total: int = 100):
        """عرض شريط تقدم"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )

    @staticmethod
    def display_threats_table(threats: list):
        """عرض جدول التهديدات"""
        if not threats:
            UIManager.success("No threats detected! Your system is clean. 🎉")
            return

        table = Table(
            title="🚨 Detected Threats",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold red",
            title_style="bold red",
        )

        table.add_column("#", style="dim", width=4)
        table.add_column("Severity", style="bold")
        table.add_column("Type", style="yellow")
        table.add_column("Process/Connection", style="cyan")
        table.add_column("Details", style="white")

        for i, threat in enumerate(threats, 1):
            severity = threat.get("severity", "Unknown")
            severity_color = {
                "CRITICAL": "bold red",
                "HIGH": "red",
                "MEDIUM": "yellow",
                "LOW": "green",
            }.get(severity, "white")

            table.add_row(
                str(i),
                f"[{severity_color}]{severity}[/{severity_color}]",
                threat.get("type", "N/A"),
                threat.get("source", "N/A"),
                threat.get("details", "N/A"),
            )

        console.print(table)

    @staticmethod
    def ask_confirmation(command: str, description: str) -> bool:
        """
        ⚠️ صمام الأمان - Human in the Loop
        يسأل المستخدم قبل تنفيذ أي أمر
        """
        console.print("\n")
        console.print(
            Panel(
                f"[bold yellow]Command to execute:[/bold yellow]\n"
                f"[white on black] {command} [/white on black]\n\n"
                f"[bold cyan]Purpose:[/bold cyan] {description}",
                title="🔒 Human Approval Required",
                border_style="yellow",
                box=box.DOUBLE,
            )
        )
        return Confirm.ask(
            "[bold yellow]Do you authorize executing this command?[/bold yellow]",
            default=False,
        )

    @staticmethod
    def display_summary(stats: dict):
        """عرض ملخص الفحص"""
        table = Table(
            title="📊 Scan Summary",
            box=box.HEAVY,
            show_header=False,
            title_style="bold cyan",
        )

        table.add_column("Metric", style="bold cyan")
        table.add_column("Value", style="bold white")

        for key, value in stats.items():
            table.add_row(key, str(value))

        console.print(table)

    @staticmethod
    def loading_animation(message: str, duration: float = 2.0):
        """رسم متحرك للتحميل"""
        with console.status(f"[cyan]{message}[/cyan]", spinner="dots"):
            time.sleep(duration)

    @staticmethod
    def run_with_council_progress(description: str, fn: Callable[[], T]) -> T:
        """
        تشغيل مهمة طويلة (مجلس CrewAI) مع شريط تقدم ونسبة مئوية تقريبية + زمن منقضٍ.
        النسبة لا تعكس خطوات CrewAI الحقيقية؛ تُقترب من سقف دون 100% ثم 100% عند الانتهاء.
        """
        try:
            est = float(os.environ.get("COA_COUNCIL_PROGRESS_EST_SEC", "90") or "90")
        except ValueError:
            est = 90.0
        est = max(15.0, min(est, 600.0))

        result: list[T] = []
        exc_holder: list[BaseException] = []

        def worker() -> None:
            try:
                result.append(fn())
            except BaseException as e:
                exc_holder.append(e)

        th = threading.Thread(target=worker, daemon=False)
        th.start()
        poll = 0.15
        elapsed = 0.0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=28, complete_style="cyan", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task(description, total=100)
            while th.is_alive():
                elapsed += poll
                # سقف أقل من 100% حتى لا يبدو أن العمل على وشك الانتهاء ثم يتجمد دقائق.
                base = 88.0 * (1.0 - math.exp(-elapsed / max(est * 0.5, 1.0)))
                if elapsed > est:
                    over = elapsed - est
                    base = min(93.0, max(base, 82.0 + min(11.0, over * 0.035)))
                pct = min(93.0, base)
                progress.update(task_id, completed=pct)
                th.join(timeout=poll)
            progress.update(task_id, completed=100.0)
        th.join()
        if exc_holder:
            raise exc_holder[0]
        if not result:
            raise RuntimeError("council worker finished without result")
        return result[0]

    @staticmethod
    def divider():
        """فاصل بصري"""
        console.print("─" * console.width, style="dim")
