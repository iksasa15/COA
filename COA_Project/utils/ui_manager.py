"""
UI Manager - Beautiful CLI Interface
====================================
Uses Rich library for professional console output
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Confirm
from rich.text import Text
from rich.align import Align
from rich import box
import pyfiglet
import time


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
    def divider():
        """فاصل بصري"""
        console.print("─" * console.width, style="dim")
