"""
HTML Report Generator
=====================
Beautiful interactive HTML reports for sharing
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class HTMLReportGenerator:
    """مولد تقارير HTML احترافية وتفاعلية"""

    @staticmethod
    def generate(
        system_info: Dict,
        analysis_result: Dict,
        events: list,
        output_path: Path,
    ) -> str:
        """توليد تقرير HTML كامل"""

        threats = analysis_result.get('threats', [])

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>C.O.A Security Report — {system_info.get('hostname', 'Unknown')}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
        padding: 20px;
        min-height: 100vh;
    }}
    .container {{
        max-width: 1200px;
        margin: 0 auto;
    }}
    .header {{
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 20px;
        text-align: center;
    }}
    .header h1 {{
        font-size: 36px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }}
    .subtitle {{ color: #94a3b8; font-size: 14px; }}
    .badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 500;
        margin: 0 4px;
    }}
    .badge-green {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; }}
    .badge-red {{ background: rgba(239, 68, 68, 0.2); color: #f87171; }}
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 20px;
    }}
    .stat-card {{
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 20px;
        transition: transform 0.2s;
    }}
    .stat-card:hover {{ transform: translateY(-2px); }}
    .stat-value {{
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 4px;
    }}
    .stat-label {{ color: #94a3b8; font-size: 13px; }}
    .critical {{ color: #ef4444; }}
    .high {{ color: #f97316; }}
    .medium {{ color: #eab308; }}
    .low {{ color: #22c55e; }}
    .safe {{ color: #22c55e; }}
    .section {{
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }}
    .section h2 {{
        font-size: 20px;
        margin-bottom: 16px;
        color: #f1f5f9;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
    }}
    th, td {{
        padding: 12px;
        text-align: right;
        border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        font-size: 13px;
    }}
    th {{
        background: rgba(15, 23, 42, 0.5);
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 11px;
    }}
    .severity-pill {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-weight: 500;
        font-size: 11px;
    }}
    .severity-CRITICAL {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
    .severity-HIGH {{ background: rgba(249, 115, 22, 0.2); color: #f97316; }}
    .severity-MEDIUM {{ background: rgba(234, 179, 8, 0.2); color: #eab308; }}
    .severity-LOW {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
    .confidence-HIGH {{ color: #ef4444; font-weight: 500; }}
    .confidence-MEDIUM {{ color: #eab308; }}
    .confidence-LOW {{ color: #94a3b8; }}
    .footer {{
        text-align: center;
        color: #64748b;
        font-size: 12px;
        padding: 20px;
    }}
    .icon {{ font-size: 20px; }}
    .info-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 12px;
    }}
    .info-item {{
        padding: 12px;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
    }}
    .info-key {{ color: #94a3b8; font-size: 12px; margin-bottom: 4px; }}
    .info-value {{ color: #f1f5f9; font-weight: 500; }}
    details {{ margin-top: 8px; }}
    summary {{ cursor: pointer; color: #60a5fa; font-size: 13px; }}
    .signal-tag {{
        display: inline-block;
        padding: 2px 8px;
        background: rgba(96, 165, 250, 0.1);
        color: #60a5fa;
        border-radius: 4px;
        font-size: 11px;
        margin: 2px;
    }}
</style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>🛡️ C.O.A Security Report</h1>
        <div class="subtitle">
            تقرير فحص أمني — Council of Agents
            <br>
            <span class="badge badge-green">Local & Private 🔒</span>
            <span class="badge badge-green">{len(threats)} Threats Analyzed</span>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value critical">{analysis_result.get('critical', 0)}</div>
            <div class="stat-label">Critical Threats</div>
        </div>
        <div class="stat-card">
            <div class="stat-value high">{analysis_result.get('high', 0)}</div>
            <div class="stat-label">High Severity</div>
        </div>
        <div class="stat-card">
            <div class="stat-value medium">{analysis_result.get('medium', 0)}</div>
            <div class="stat-label">Medium Severity</div>
        </div>
        <div class="stat-card">
            <div class="stat-value low">{analysis_result.get('low', 0)}</div>
            <div class="stat-label">Low Severity</div>
        </div>
    </div>

    <div class="section">
        <h2><span class="icon">💻</span> System Information</h2>
        <div class="info-grid">
"""

        # معلومات النظام
        for key, value in system_info.items():
            if key != 'scan_time':
                html += f"""
            <div class="info-item">
                <div class="info-key">{key.replace('_', ' ').title()}</div>
                <div class="info-value">{value}</div>
            </div>
"""

        html += """
        </div>
    </div>
"""

        # جدول التهديدات
        if threats:
            html += """
    <div class="section">
        <h2><span class="icon">🚨</span> Detected Threats</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Severity</th>
                    <th>Confidence</th>
                    <th>Score</th>
                    <th>Source</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
            for i, threat in enumerate(threats, 1):
                signals_html = ''.join(
                    f'<span class="signal-tag">{s}</span>'
                    for s in threat.get('signals', [])
                )

                html += f"""
                <tr>
                    <td>{i}</td>
                    <td><span class="severity-pill severity-{threat.get('severity', 'LOW')}">{threat.get('severity', 'N/A')}</span></td>
                    <td><span class="confidence-{threat.get('confidence', 'LOW')}">{threat.get('confidence', 'N/A')}</span></td>
                    <td>{threat.get('score', 0)}</td>
                    <td>{threat.get('source', 'N/A')}</td>
                    <td>
                        {threat.get('details', 'N/A')}
                        <details>
                            <summary>Signals ({len(threat.get('signals', []))})</summary>
                            {signals_html}
                        </details>
                    </td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        else:
            html += """
    <div class="section" style="text-align: center;">
        <h2 style="color: #22c55e;">✅ No Threats Detected</h2>
        <p style="color: #94a3b8; margin-top: 8px;">Your system appears to be clean.</p>
    </div>
"""

        # Event log
        html += """
    <div class="section">
        <h2><span class="icon">📜</span> Event Log</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
        for event in events:
            html += f"""
                <tr>
                    <td>{event.get('timestamp', 'N/A')}</td>
                    <td><strong>{event.get('type', 'N/A')}</strong></td>
                    <td>{event.get('details', 'N/A')}</td>
                </tr>
"""

        html += f"""
            </tbody>
        </table>
    </div>

    <div class="footer">
        Generated by C.O.A — Council of Agents<br>
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • All data remains local 🔒
    </div>
</div>
</body>
</html>"""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(output_path)
