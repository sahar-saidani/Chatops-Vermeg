import os
import json
import logging
from pathlib import Path
from datetime import datetime
from app.config.settings import settings
from app.models.schemas import DeepAnalysisReport

logger = logging.getLogger("installation_agent")

class ReportGenerator:
    """Generates file reports (JSON, Markdown, HTML) summing up scanner, dependency, config, and risk analysis."""
    
    @staticmethod
    def generate(report: DeepAnalysisReport) -> Path:
        reports_dir = settings.get_absolute_path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Output JSON files
        # Master installation Discovery report
        inst_json_path = reports_dir / "installation_report.json"
        inst_json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        
        # Dependency Graph JSON
        dep_graph_path = reports_dir / "dependency_graph.json"
        dep_graph_path.write_text(report.dependency_graph.model_dump_json(indent=2), encoding="utf-8")
        
        # Configuration Inventory JSON
        configs_inventory = {
            "timestamp": report.timestamp,
            "configurations": {
                k: v.model_dump() for k, v in report.configs_analysis.items()
            }
        }
        configs_json_path = reports_dir / "configuration_inventory.json"
        configs_json_path.write_text(json.dumps(configs_inventory, indent=2), encoding="utf-8")
        
        # Risk Report JSON
        risk_json_path = reports_dir / "risk_report.json"
        risk_json_path.write_text(report.risk_report.model_dump_json(indent=2), encoding="utf-8")
        
        # 2. Output Markdown summary
        md_content = ReportGenerator._build_markdown(report)
        inst_md_path = reports_dir / "installation_report.md"
        inst_md_path.write_text(md_content, encoding="utf-8")
        
        # 3. Output HTML Dashboard
        html_content = ReportGenerator._build_html(report)
        inst_html_path = reports_dir / "installation_report.html"
        inst_html_path.write_text(html_content, encoding="utf-8")
        
        logger.info(f"Report generation complete. Files exported to: {reports_dir}")
        return reports_dir

    @staticmethod
    def _build_markdown(report: DeepAnalysisReport) -> str:
        md = []
        md.append(f"# Installation Discovery & Correlation Agent Report")
        md.append(f"**Generated at:** {report.timestamp}\n")
        
        md.append(f"## 1. Executive Summary")
        md.append(f"- **Total Scanned Files:** {report.scan_results.total_files}")
        md.append(f"- **Total Workspace Size:** {report.scan_results.total_size_bytes} bytes")
        md.append(f"- **Duplicate Files Found:** {len(report.scan_results.duplicates)}")
        md.append(f"- **Detected Install Entrypoints:** {len(report.scan_results.entrypoints)}")
        md.append(f"- **Risk Rating:** {report.risk_report.score}/100")
        
        status = "SECURE" if report.risk_report.score < 30 else "WARNING" if report.risk_report.score < 60 else "CRITICAL"
        md.append(f"- **System Risk Profile Status:** **{status}**\n")
        
        md.append(f"## 2. Risk & Vulnerability Analysis")
        md.append(f"### Score Card: {report.risk_report.score} / 100")
        if report.risk_report.risk_factors:
            md.append("| Risk Code | Category | Impact | Reason |")
            md.append("| --- | --- | --- | --- |")
            for factor, r in zip(report.risk_report.risk_factors, report.risk_report.reasons):
                md.append(f"| `{factor}` | {r['factor']} | +{r['impact']} | {r['detail']} |")
        else:
            md.append("*No risk factors identified.*")
            
        md.append("\n### Recommendations")
        for rec in report.risk_report.recommendations:
            md.append(f"- {rec}")
            
        md.append(f"\n## 3. Discovered Installers & Entrypoints")
        if report.scan_results.entrypoints:
            for entry in report.scan_results.entrypoints:
                md.append(f"- `{Path(entry).name}` (Location: `{entry}`)")
        else:
            md.append("*No installer entrypoints found.*")
            
        md.append(f"\n## 4. Configuration Inventory")
        if report.configs_analysis:
            for filepath, c_res in report.configs_analysis.items():
                fname = Path(filepath).name
                md.append(f"### Configuration: `{fname}`")
                md.append(f"- **Application Name:** {c_res.application_name or 'N/A'}")
                md.append(f"- **Version:** {c_res.version or 'N/A'}")
                md.append(f"- **Ports Exposed:** {', '.join(map(str, c_res.ports)) if c_res.ports else 'None'}")
                if c_res.database_host:
                    md.append(f"- **Database Connection:** `{c_res.username or 'admin'}@{c_res.database_host}:{c_res.database_port or ''}/{c_res.database_name or ''}`")
                if c_res.docker_images:
                    md.append(f"- **Docker Images Referenced:** `{', '.join(c_res.docker_images)}`")
                if c_res.kubernetes_resources:
                    md.append(f"- **Kubernetes Manifests:** `{', '.join(c_res.kubernetes_resources)}`")
        else:
            md.append("*No configurations parsed.*")
            
        md.append(f"\n## 5. Dependency Graph Findings")
        dg = report.dependency_graph
        md.append(f"- **Total Unique Dependencies Listed:** {len(dg.nodes)}")
        md.append(f"- **Missing Packages/Runtimes:** {len(dg.missing_dependencies)}")
        md.append(f"- **Duplicate Package Names:** {len(dg.duplicate_dependencies)}")
        md.append(f"- **Version Conflict Detections:** {len(dg.version_conflicts)}")
        md.append(f"- **Unsupported Versions Found:** {len(dg.unsupported_versions)}")
        
        if dg.version_conflicts:
            md.append("\n### Version Conflicts Details")
            for pkg, vers in dg.version_conflicts.items():
                md.append(f"- `{pkg}`: Found conflicting versions `{', '.join(vers)}`")
                
        if dg.unsupported_versions:
            md.append("\n### Unsupported Runtime Versions")
            for unsup in dg.unsupported_versions:
                md.append(f"- {unsup}")
                
        md.append(f"\n## 6. Validation Report Summary")
        val = report.validation_report
        md.append(f"- **Overall Project Valid:** **{val.is_valid}**")
        md.append(f"- **Total Errors:** {len(val.errors)}")
        md.append(f"- **Total Warnings:** {len(val.warnings)}")
        
        if val.errors:
            md.append("\n### Critical Errors")
            for err in val.errors:
                md.append(f"- **[{err.type}]** in `{Path(err.file_path).name}`: {err.message} (Severity: `{err.severity.upper()}`)")
                
        if val.warnings:
            md.append("\n### Validation Warnings")
            for wrn in val.warnings:
                md.append(f"- **[{wrn.type}]** in `{Path(wrn.file_path).name}`: {wrn.message}")
                
        return "\n".join(md)

    @staticmethod
    def _build_html(report: DeepAnalysisReport) -> str:
        status = "SECURE" if report.risk_report.score < 30 else "WARNING" if report.risk_report.score < 60 else "CRITICAL RISK"
        status_color = "#10B981" if status == "SECURE" else "#F59E0B" if status == "WARNING" else "#EF4444"
        
        errors_html = "".join([
            f"<li><span style='color: #ef4444; font-weight: bold;'>[ERROR]</span> <strong>{Path(err.file_path).name}</strong> ({err.type}): {err.message}</li>"
            for err in report.validation_report.errors
        ])
        
        warnings_html = "".join([
            f"<li><span style='color: #f59e0b; font-weight: bold;'>[WARNING]</span> <strong>{Path(wrn.file_path).name}</strong> ({wrn.type}): {wrn.message}</li>"
            for wrn in report.validation_report.warnings
        ])
        
        recs_html = "".join([f"<li>{rec}</li>" for rec in report.risk_report.recommendations])
        
        configs_list = ""
        for fp, c_res in report.configs_analysis.items():
            configs_list += f"""
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; margin-bottom: 10px; border-radius: 6px;">
                <strong style="color: #f8fafc;">{Path(fp).name}</strong><br/>
                <span style="font-size: 13px;">
                    App Name: {c_res.application_name or 'N/A'} | Version: {c_res.version or 'N/A'}<br/>
                    Ports: {', '.join(map(str, c_res.ports)) if c_res.ports else 'None'} 
                    {f'| Database: {c_res.database_host}' if c_res.database_host else ''}
                </span>
            </div>
            """
            
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DevOps Discovery Agent Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {{
            --bg: #090d16;
            --card: rgba(30, 41, 59, 0.4);
            --border: rgba(255, 255, 255, 0.08);
            --primary: #4f46e5;
            --primary-light: #818cf8;
            --text: #94a3b8;
            --title: #f8fafc;
        }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .wrapper {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 30px;
            position: relative;
            margin-bottom: 24px;
        }}
        .header h1 {{
            color: var(--title);
            margin: 0;
            font-size: 26px;
            letter-spacing: -0.5px;
        }}
        .status-badge {{
            position: absolute;
            top: 30px;
            right: 30px;
            background: {status_color};
            color: #fff;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 700;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .metric-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--title);
        }}
        .section {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .section h2 {{
            color: var(--title);
            margin-top: 0;
            margin-bottom: 16px;
            font-size: 18px;
            border-left: 4px solid var(--primary-light);
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid var(--border);
            padding: 10px;
            text-align: left;
            font-size: 14px;
        }}
        th {{
            background: rgba(255, 255, 255, 0.04);
            color: var(--title);
        }}
        ul {{
            margin: 0;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="header">
            <span class="status-badge">{status}</span>
            <h1>Installation Discovery & Correlation Report</h1>
            <div style="margin-top: 8px; font-size: 13px;">Agent timestamp: {report.timestamp}</div>
        </div>

        <div class="grid">
            <div class="metric-card">
                <div class="metric-title">Scanned Files</div>
                <div class="metric-value">{report.scan_results.total_files}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Entrypoints</div>
                <div class="metric-value">{len(report.scan_results.entrypoints)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Size</div>
                <div class="metric-value">{report.scan_results.total_size_bytes} B</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Risk Score</div>
                <div class="metric-value" style="color: {status_color};">{report.risk_report.score}/100</div>
            </div>
        </div>

        <div class="section">
            <h2>Risk Factor Inventory</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Category</th>
                        <th style="width: 15%;">Impact</th>
                        <th>Evidence / Technical Detail</th>
                    </tr>
                </thead>
                <tbody>
        """
        if report.risk_report.reasons:
            for r in report.risk_report.reasons:
                html += f"""
                    <tr>
                        <td><strong>{r['factor']}</strong></td>
                        <td><span style="color: #ef4444; font-weight: bold;">+{r['impact']}</span></td>
                        <td>{r['detail']}</td>
                    </tr>
                """
        else:
            html += "<tr><td colspan='3'>No risk items flagged in this audit run.</td></tr>"
            
        html += f"""
                </tbody>
            </table>
            <h3 style="color: var(--title); font-size: 15px; margin-top: 20px;">Remediation Recommendations</h3>
            <ul>
                {recs_html or "<li>Clean static run: no recommendations needed.</li>"}
            </ul>
        </div>

        <div class="section">
            <h2>Validation Status</h2>
            <div style="margin-bottom: 15px;">
                State: <span style="font-weight: bold; color: {'#10b981' if report.validation_report.is_valid else '#ef4444'};">
                    {'VALID' if report.validation_report.is_valid else 'INVALID'}
                </span>
            </div>
            {f"<h3>Errors ({len(report.validation_report.errors)})</h3><ul>{errors_html}</ul>" if errors_html else ""}
            {f"<h3>Warnings ({len(report.validation_report.warnings)})</h3><ul>{warnings_html}</ul>" if warnings_html else ""}
        </div>

        <div class="section">
            <h2>Discovered Configurations</h2>
            {configs_list or "<p>No configurations found.</p>"}
        </div>
    </div>
</body>
</html>
"""
        return html
