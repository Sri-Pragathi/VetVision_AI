"""HTML Rendering service for formatting structured assessment reports into clean, printable HTML."""
import html
from typing import Dict, Any, List


class ReportHtmlRenderer:
    """Renders structured assessment report data into semantic, responsive, injection-safe HTML."""

    @staticmethod
    def _esc(val: Any) -> str:
        """Safely escape text for HTML injection prevention."""
        if val is None:
            return ""
        return html.escape(str(val))

    @classmethod
    def render(cls, report_data: Dict[str, Any]) -> str:
        """Generate a complete standalone HTML document from report_data."""
        meta = report_data.get("metadata") or {}
        pet = report_data.get("pet") or {}
        asmt = report_data.get("assessment") or {}
        symptoms = report_data.get("symptoms") or []
        findings = report_data.get("follow_up_findings") or []
        obs = report_data.get("observations") or {}
        img_analysis = report_data.get("image_analysis") or {}
        risk = report_data.get("risk_analysis") or {}
        explainability = report_data.get("explainability") or []
        emergency = report_data.get("emergency") or {}
        recommendation = report_data.get("recommendation") or {}
        handoff = report_data.get("veterinary_handoff") or {}
        disclaimer = report_data.get("disclaimer") or ""

        risk_level = risk.get("risk_level", "LOW")
        risk_score = risk.get("risk_score", 0)
        is_emergency = emergency.get("is_emergency", False) or risk_level == "EMERGENCY"

        # Theme color based on risk level
        badge_color = {
            "LOW": "#2e7d32",
            "MODERATE": "#e65100",
            "HIGH": "#c62828",
            "EMERGENCY": "#b71c1c",
        }.get(risk_level, "#37474f")

        # Build symptoms rows
        symptoms_html = ""
        if symptoms:
            for s in symptoms:
                symptoms_html += f"""
                <tr>
                    <td><strong>{cls._esc((s.get('name') or '').title())}</strong></td>
                    <td>{cls._esc(s.get('category'))}</td>
                    <td><span class="tag tag-{cls._esc((s.get('severity') or '').lower())}">{cls._esc(s.get('severity'))}</span></td>
                    <td>{cls._esc(s.get('duration_display') or s.get('duration'))}</td>
                    <td>{cls._esc(s.get('notes') or 'None')}</td>
                </tr>
                """
        else:
            symptoms_html = "<tr><td colspan='5'>No symptoms reported.</td></tr>"

        # Build follow-up findings rows
        findings_html = ""
        if findings:
            for f in findings:
                p_tag = f"tag-{cls._esc((f.get('priority') or 'medium').lower())}"
                findings_html += f"""
                <tr>
                    <td>{cls._esc(f.get('question'))}</td>
                    <td><strong>{cls._esc(f.get('answer'))}</strong></td>
                    <td><span class="tag {p_tag}">{cls._esc(f.get('priority'))}</span></td>
                </tr>
                """
        else:
            findings_html = "<tr><td colspan='3'>No adaptive follow-up responses recorded.</td></tr>"

        # Build observations table
        obs_rows = ""
        for k, v in obs.items():
            label = k.replace("_", " ").title()
            val_display = cls._esc(v) if v else "<span class='text-muted'>Normal / Not observed</span>"
            obs_rows += f"<tr><td>{label}</td><td>{val_display}</td></tr>"

        # Build image observations
        images_list = img_analysis if isinstance(img_analysis, list) else (img_analysis.get("images") or [])
        images_html = ""
        if images_list:
            for img in images_list:
                status = img.get("status")
                if status == "NOT_PROVIDED":
                    images_html += "<p class='text-muted'>Image analysis: No image provided.</p>"
                    continue
                if status == "PENDING":
                    images_html += "<div class='card subcard'><p class='text-muted'>Image analysis: Analysis not completed.</p></div>"
                    continue
                if status == "REQUIRES_BETTER_IMAGE":
                    warn_msg = cls._esc(img.get("quality_warnings") or img.get("quality", {}).get("warning") or "Image quality insufficient for reliable visual analysis.")
                    guidance = cls._esc(img.get("actionable_guidance") or "")
                    guidance_p = f"<p style='margin-top: 4px; font-size: 12px; color: #78350f;'><strong>Actionable Tip:</strong> {guidance}</p>" if guidance else ""
                    images_html += f"""
                    <div class="card subcard" style="border-left: 4px solid #f59e0b; background: #fffbeb;">
                        <div class="flex-between">
                            <strong>Photographic Record</strong>
                            <span class="tag tag-warning">Quality Warning</span>
                        </div>
                        <p style="margin-top: 6px; font-size: 13px; color: #b91c1c;">⚠️ {warn_msg}</p>
                        {guidance_p}
                    </div>
                    """
                    continue

                obs_items = img.get("visual_observations") or img.get("observations") or []
                if isinstance(obs_items, list):
                    obs_list_html = "".join([
                        f"<li><strong>{cls._esc(o.get('observation_label'))}</strong> ({cls._esc(o.get('severity', 'normal'))}): {cls._esc(o.get('description'))}</li>"
                        for o in obs_items
                    ]) or "<li>No distinct visual abnormalities detected.</li>"
                else:
                    obs_list_html = f"<li>{cls._esc(str(obs_items))}</li>"

                q_gate = img.get("quality_gate") or "PASSED"
                q_class = "tag-passed" if q_gate == "PASSED" else "tag-warning"
                photo_title = img.get("original_filename") or f"Image #{cls._esc(str(img.get('image_id'))[:8]) if img.get('image_id') else '1'}"
                images_html += f"""
                <div class="card subcard">
                    <div class="flex-between">
                        <strong>Visual Record: {cls._esc(photo_title)}</strong>
                        <span class="tag {q_class}">Quality: {cls._esc(q_gate)}</span>
                    </div>
                    <ul class="obs-list">{obs_list_html}</ul>
                </div>
                """
        else:
            images_html = "<p class='text-muted'>Image analysis: No image provided.</p>"

        # Build explainability factors
        explain_html = ""
        if explainability:
            for exp in explainability:
                explain_html += f"""
                <div class="explain-item">
                    <div class="explain-header">
                        <span class="explain-factor">{cls._esc(exp.get('factor'))}</span>
                        <span class="explain-contrib">{cls._esc(exp.get('contribution'))}</span>
                    </div>
                    <div class="explain-finding">Finding: {cls._esc(exp.get('observed_finding'))}</div>
                    <div class="explain-text">{cls._esc(exp.get('explanation'))}</div>
                </div>
                """
        else:
            explain_html = "<p class='text-muted'>No specific explainability factors computed.</p>"

        # Data Quality & Contradiction Warnings
        quality_warnings = (
            report_data.get("risk_analysis", {}).get("data_quality_warnings")
            or report_data.get("data_quality_warnings")
            or []
        )
        warnings_html = ""
        if quality_warnings:
            items_html = "".join([
                f"<div style='margin-bottom: 8px;'><strong>⚠️ {cls._esc(w.get('title'))}:</strong> {cls._esc(w.get('message'))}</div>"
                for w in quality_warnings
            ])
            warnings_html = f"""
            <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: #92400e;">
                <div style="font-weight: 700; margin-bottom: 6px;">Clinical Data Quality & Uncertainty Notices:</div>
                {items_html}
            </div>
            """

        # Emergency banner
        emergency_banner = ""
        if is_emergency:
            emergency_banner = f"""
            <div class="alert alert-emergency">
                <h3>⚠️ ACUTE EMERGENCY ALERT</h3>
                <p><strong>{cls._esc(emergency.get('status'))}</strong></p>
                <p>Seek immediate emergency veterinary care. Do not wait for a routine appointment.</p>
            </div>
            """

        # Complete HTML
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VetVision AI — Health Assessment Report v{cls._esc(meta.get('report_version'))}</title>
    <style>
        :root {{
            --primary: #1976d2;
            --danger: #b71c1c;
            --warning: #e65100;
            --success: #2e7d32;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
            line-height: 1.5;
        }}
        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            padding: 36px;
            border: 1px solid var(--border);
        }}
        .header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .brand h1 {{ margin: 0; font-size: 24px; color: var(--primary); }}
        .brand p {{ margin: 4px 0 0; color: var(--text-muted); font-size: 13px; }}
        .meta-box {{ text-align: right; font-size: 12px; color: var(--text-muted); }}
        .badge-version {{
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 4px;
        }}
        .risk-banner {{
            background: {badge_color};
            color: #ffffff;
            padding: 16px 20px;
            border-radius: 8px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .risk-banner h2 {{ margin: 0; font-size: 22px; }}
        .risk-score {{ font-size: 28px; font-weight: 700; }}
        .alert-emergency {{
            background: #fee2e2;
            border: 2px solid #ef4444;
            color: #991b1b;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
        }}
        .alert-emergency h3 {{ margin-top: 0; }}
        .section {{ margin-bottom: 28px; }}
        .section-title {{
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary);
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
            margin-bottom: 14px;
        }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
        .info-card {{
            background: #f8fafc;
            padding: 12px 16px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }}
        .info-card label {{ font-size: 11px; text-transform: uppercase; color: var(--text-muted); display: block; }}
        .info-card span {{ font-size: 14px; font-weight: 600; color: var(--text); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{ background: #f1f5f9; color: var(--text-muted); font-weight: 600; }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .tag-mild {{ background: #e0f2fe; color: #0369a1; }}
        .tag-moderate {{ background: #ffedd5; color: #c2410c; }}
        .tag-severe, .tag-emergency {{ background: #fee2e2; color: #b91c1c; }}
        .tag-high {{ background: #fee2e2; color: #b91c1c; }}
        .tag-medium {{ background: #fef3c7; color: #b45309; }}
        .tag-low {{ background: #f1f5f9; color: #475569; }}
        .tag-passed {{ background: #dcfce7; color: #15803d; }}
        .tag-warning {{ background: #fef3c7; color: #b45309; }}
        .handoff-box {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 24px;
        }}
        .handoff-box h3 {{ margin-top: 0; color: #166534; font-size: 16px; }}
        .explain-item {{
            background: #f8fafc;
            border-left: 3px solid var(--primary);
            padding: 10px 14px;
            margin-bottom: 8px;
            border-radius: 0 4px 4px 0;
            font-size: 13px;
        }}
        .explain-header {{ display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 2px; }}
        .explain-finding {{ color: var(--text-muted); font-size: 12px; margin-bottom: 2px; }}
        .subcard {{
            background: #ffffff;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 8px;
        }}
        .flex-between {{ display: flex; justify-content: space-between; align-items: center; }}
        .obs-list {{ margin: 8px 0 0; padding-left: 20px; font-size: 13px; }}
        .disclaimer-box {{
            background: #f1f5f9;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 14px;
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 30px;
        }}
        .text-muted {{ color: var(--text-muted); }}
        @media print {{
            body {{ padding: 0; background: #ffffff; }}
            .report-container {{ box-shadow: none; border: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <!-- Header -->
        <div class="header">
            <div class="brand">
                <h1>VETVISION AI</h1>
                <p>Veterinary Health Assessment Report</p>
            </div>
            <div class="meta-box">
                <span class="badge-version">Report v{cls._esc(meta.get('report_version'))}</span><br>
                <strong>Report ID:</strong> {cls._esc(meta.get('report_id'))[:8]}...<br>
                <strong>Date:</strong> {cls._esc(meta.get('generated_at'))[:10]}<br>
                <strong>Assessment ID:</strong> {cls._esc(asmt.get('assessment_id'))[:8]}...
            </div>
        </div>

        {emergency_banner}
        {warnings_html}

        <!-- Risk Assessment Banner -->
        <div class="risk-banner">
            <div>
                <h2>OVERALL TRIAGE RISK: {cls._esc(risk_level)}</h2>
                <div>{cls._esc(recommendation.get('action'))}</div>
            </div>
            <div class="risk-score">{cls._esc(risk_score)}/100</div>
        </div>

        <!-- Veterinary Handoff Summary -->
        <div class="handoff-box">
            <h3>🩺 Attending Veterinarian Clinical Intake Brief</h3>
            <p><strong>Patient:</strong> {cls._esc(handoff.get('patient'))}</p>
            <p><strong>Primary Complaint:</strong> {cls._esc(handoff.get('primary_complaint'))}</p>
            <p><strong>Triage Assessment:</strong> {cls._esc(handoff.get('triage_risk'))} | <em>{cls._esc(handoff.get('emergency_status'))}</em></p>
            <p><strong>Recommended Next Step:</strong> {cls._esc(handoff.get('recommended_action'))}</p>
        </div>

        <!-- Pet Profile -->
        <div class="section">
            <div class="section-title">Pet Demographics & Profile</div>
            <div class="grid-3">
                <div class="info-card"><label>Name</label><span>{cls._esc(pet.get('name'))}</span></div>
                <div class="info-card"><label>Species / Breed</label><span>{cls._esc(pet.get('species'))} / {cls._esc(pet.get('breed') or 'Mixed')}</span></div>
                <div class="info-card"><label>Age</label><span>{cls._esc(pet.get('age_display') or (str(pet.get('age')) + ' years' if pet.get('age') is not None else 'Unknown'))}</span></div>
                <div class="info-card"><label>Sex</label><span>{cls._esc(pet.get('sex') or 'Not specified')}</span></div>
                <div class="info-card"><label>Weight</label><span>{cls._esc(str(pet.get('weight')) + ' kg' if pet.get('weight') else 'Not recorded')}</span></div>
                <div class="info-card"><label>Vaccination Status</label><span>{cls._esc(pet.get('vaccination_status') or 'Not recorded')}</span></div>
            </div>
            <div class="grid-2" style="margin-top: 8px;">
                <div class="info-card"><label>Allergies</label><span>{cls._esc(pet.get('allergies') or 'None reported')}</span></div>
                <div class="info-card"><label>Existing Conditions</label><span>{cls._esc(pet.get('existing_conditions') or 'None reported')}</span></div>
            </div>
        </div>

        <!-- Reported Symptoms -->
        <div class="section">
            <div class="section-title">Reported Symptoms ({len(symptoms)})</div>
            <table>
                <thead>
                    <tr><th>Symptom</th><th>Category</th><th>Severity</th><th>Duration</th><th>Notes</th></tr>
                </thead>
                <tbody>{symptoms_html}</tbody>
            </table>
        </div>

        <!-- Adaptive Follow-Up Findings -->
        <div class="section">
            <div class="section-title">Clinical Follow-Up Q&A ({len(findings)})</div>
            <table>
                <thead>
                    <tr><th>Clinical Question</th><th>Recorded Response</th><th>Priority</th></tr>
                </thead>
                <tbody>{findings_html}</tbody>
            </table>
        </div>

        <!-- Physiological Observations -->
        <div class="section">
            <div class="section-title">Physical & Behavioral Observations</div>
            <table>
                <thead>
                    <tr><th style="width: 40%;">Metric</th><th>Observation</th></tr>
                </thead>
                <tbody>{obs_rows}</tbody>
            </table>
        </div>

        <!-- Computer Vision Image Analysis -->
        <div class="section">
            <div class="section-title">Computer Vision Visual Observations</div>
            {images_html}
        </div>

        <!-- Explainability Section -->
        <div class="section">
            <div class="section-title">Why This Risk Level? (Factor Analysis)</div>
            {explain_html}
        </div>

        <!-- Recommended Action -->
        <div class="section">
            <div class="section-title">Recommended Clinical Next Steps</div>
            <div class="info-card" style="border-left: 4px solid var(--primary);">
                <strong>{cls._esc(recommendation.get('action'))}</strong>
                <p style="margin: 6px 0 0; font-size: 13px; color: var(--text-muted);">{cls._esc(recommendation.get('guidance'))}</p>
            </div>
        </div>

        <!-- Safety Disclaimer -->
        <div class="disclaimer-box">
            <strong>VETERINARY MEDICAL NOTICE & DISCLAIMER:</strong><br>
            {cls._esc(disclaimer)}
        </div>
    </div>
</body>
</html>
"""
