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
        doctor_review = report_data.get("doctor_review") or {}
        disclaimer = report_data.get("disclaimer") or ""
        care_guide = report_data.get("immediate_care_guide") or {}

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

        # Format AI Pet Care Guide
        care_guide_html = ""
        if care_guide:
            scenario_title = cls._esc(care_guide.get("title") or care_guide.get("scenario_title") or "General Supportive Care")
            intro_summary = cls._esc(care_guide.get("subtitle") or care_guide.get("intro_summary") or "")
            urgency_tier = cls._esc(care_guide.get("urgency", {}).get("classification") or care_guide.get("triage_urgency_level") or risk_level)

            # Section A: What to do now
            what_to_do_items = care_guide.get("section_a_what_to_do_now") or care_guide.get("what_to_do_now") or []
            what_to_do_rows = "".join([
                f"<li style='margin-bottom: 8px;'><span class='tag tag-passed' style='margin-right: 6px;'>{cls._esc(item.get('badge') or ('CRITICAL' if item.get('is_critical') else 'STEP ' + str(item.get('step', ''))))}</span><strong>{cls._esc(item.get('title'))}:</strong> {cls._esc(item.get('instruction') or item.get('detail'))}</li>"
                for item in what_to_do_items
            ])

            # Section B: What NOT to do
            what_not_to_do_items = care_guide.get("section_b_what_to_avoid") or care_guide.get("what_not_to_do") or []
            what_not_rows = "".join([
                f"<li style='margin-bottom: 8px;'><span class='tag tag-high' style='margin-right: 6px;'>NEVER</span><strong>{cls._esc(item.get('rule') or item.get('warning'))}</strong> — <span style='color: #991b1b;'>{cls._esc(item.get('detail') or item.get('reason'))}</span></li>"
                for item in what_not_to_do_items
            ])

            # Section C: What to monitor
            what_to_mon_items = care_guide.get("section_c_what_to_monitor") or care_guide.get("what_to_monitor") or []
            what_to_mon_rows = "".join([
                f"<li style='margin-bottom: 8px;'><strong>{cls._esc(item.get('indicator') or item.get('name') or str(item))}:</strong> Red flag: <span style='color: #c2410c;'>{cls._esc(item.get('red_flag') or item.get('cutoff') or 'Sudden worsening or change')}</span></li>"
                if isinstance(item, dict) else f"<li style='margin-bottom: 8px;'>{cls._esc(str(item))}</li>"
                for item in what_to_mon_items
            ])

            # Section D: When to seek care
            seek_care = care_guide.get("section_d_when_to_seek_care") or care_guide.get("when_to_seek_care") or {}
            tiers = seek_care.get("tiers") or {}
            red_flags = seek_care.get("emergency_escalation_criteria") or seek_care.get("critical_red_flags") or []
            red_flags_html = "".join([f"<li>⚠️ {cls._esc(rf)}</li>" for rf in red_flags])

            def _tier_badge(t_name, text):
                is_active = (t_name in urgency_tier or urgency_tier in t_name)
                border = "border: 2px solid #b71c1c; background: #fef2f2;" if is_active and "EMERGENCY" in t_name else (
                    "border: 2px solid #ea580c; background: #fff7ed;" if is_active and "URGENT" in t_name else (
                        "border: 2px solid #0284c7; background: #f0f9ff;" if is_active else "background: #f8fafc; border: 1px solid #e2e8f0;"
                    )
                )
                active_lbl = " <strong style='color:#b71c1c;'>[ACTIVE RECOMMENDATION]</strong>" if is_active else ""
                return f"<div style='padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; {border}'><strong style='font-size: 13px;'>{t_name}</strong>{active_lbl}<p style='margin: 4px 0 0; font-size: 12px; color: #334155;'>{cls._esc(text)}</p></div>"

            tier_boxes = (
                _tier_badge("EMERGENCY", tiers.get("EMERGENCY") or seek_care.get("cutoff_instruction") or "Immediate emergency clinic visit.") +
                _tier_badge("URGENT", tiers.get("URGENT") or "Same-day clinic evaluation.") +
                _tier_badge("APPOINTMENT", tiers.get("APPOINTMENT") or "Book within 24-48 hours.") +
                _tier_badge("HOME_MONITORING", tiers.get("HOME_MONITORING") or seek_care.get("action_recommendation") or "Monitor closely at home.")
            )

            # Section E: Why this guidance is shown
            why_guidance = care_guide.get("section_e_why_shown") or care_guide.get("why_guidance_shown") or {}
            reasons = why_guidance.get("rationale_factors") or why_guidance.get("primary_reasons") or []
            reasons_html = "".join([
                f"<li><strong>{cls._esc(r.get('category'))}:</strong> {cls._esc(r.get('finding'))} — <em>{cls._esc(r.get('impact'))}</em></li>"
                if isinstance(r, dict) else f"<li>{cls._esc(str(r))}</li>"
                for r in reasons
            ])
            visual_vs_reported = cls._esc(why_guidance.get("visual_vs_reported") or "")
            uncertainties = why_guidance.get("uncertainty_and_missing_data") or why_guidance.get("uncertainty_notes") or []
            uncertainties_html = "".join([f"<li style='color: #854d0e;'>⚠️ {cls._esc(u)}</li>" for u in uncertainties])

            # Emergency Contacts
            contacts = care_guide.get("emergency_after_hours") or care_guide.get("emergency_contacts") or {}
            poison_aspca = "ASPCA Animal Poison Control Center: (888) 426-4435 (24/7)"
            poison_helpline = "Pet Poison Helpline: (855) 764-7661 (24/7)"
            aaha_locator = "https://www.aaha.org/your-pet/find-a-hospital/"
            transport_tip = contacts.get("safe_search_instructions") or contacts.get("transport_tip") or "Call ahead so the emergency triage team is prepared."

            care_guide_html = f"""
            <!-- AI Pet Care Guide & Safety Precautions -->
            <div class="section" style="border: 2px solid #0284c7; border-radius: 10px; padding: 22px; background: #ffffff; margin-bottom: 28px;">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #e0f2fe; padding-bottom: 12px; margin-bottom: 16px;">
                    <div>
                        <h2 style="margin: 0; color: #0369a1; font-size: 18px;">🐾 AI Pet Care Guide & Immediate Precautions</h2>
                        <p style="margin: 4px 0 0; color: #64748b; font-size: 13px;">Understand what you can safely do now, what to avoid, and when your pet needs urgent veterinary care.</p>
                    </div>
                    <span class="tag tag-{cls._esc(urgency_tier.lower())}" style="font-size: 12px; padding: 4px 10px;">Care Tier: {cls._esc(urgency_tier)}</span>
                </div>
                <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; border-radius: 6px; margin-bottom: 18px; font-size: 13px; color: #166534;">
                    <strong>Assessment Focus ({scenario_title}):</strong> {intro_summary}
                </div>

                <!-- Section A -->
                <div style="margin-bottom: 18px;">
                    <h3 style="color: #0f766e; font-size: 15px; margin: 0 0 8px 0;">A. What to Do Now (First-Aid & Low-Risk Comfort Measures)</h3>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #1e293b;">{what_to_do_rows}</ul>
                </div>

                <!-- Section B -->
                <div style="margin-bottom: 18px; background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px 16px; border-radius: 6px;">
                    <h3 style="color: #991b1b; font-size: 15px; margin: 0 0 8px 0;">B. What NOT to Do (Strict Precautions & Contraindications)</h3>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #7f1d1d;">{what_not_rows}</ul>
                </div>

                <!-- Section C -->
                <div style="margin-bottom: 18px;">
                    <h3 style="color: #c2410c; font-size: 15px; margin: 0 0 8px 0;">C. What to Monitor (Objective Warning Signs & Deterioration Indicators)</h3>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #1e293b;">{what_to_mon_rows}</ul>
                </div>

                <!-- Section D -->
                <div style="margin-bottom: 18px;">
                    <h3 style="color: #1e293b; font-size: 15px; margin: 0 0 8px 0;">D. When to Seek Veterinary Care (Decision Matrix)</h3>
                    <div style="margin-bottom: 10px;">{tier_boxes}</div>
                    {"<div style='background: #fff7ed; border-left: 4px solid #ea580c; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #9a3412;'><strong>Critical Red-Flag Symptoms:</strong><ul style='margin: 4px 0 0; padding-left: 16px;'>" + red_flags_html + "</ul></div>" if red_flags else ""}
                </div>

                <!-- Section E -->
                <div style="margin-bottom: 18px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 14px 16px; border-radius: 6px;">
                    <h3 style="color: #0f172a; font-size: 15px; margin: 0 0 8px 0;">E. Why This Guidance Is Shown (Transparent Rationale)</h3>
                    <div style="font-size: 13px; color: #334155; margin-bottom: 6px;"><strong>Clinical Factors Considered:</strong></div>
                    <ul style="margin: 0 0 8px 0; padding-left: 18px; font-size: 12px; color: #475569;">{reasons_html}</ul>
                    {f"<div style='font-size: 12px; color: #475569; margin-bottom: 6px;'><strong>Visual & Diagnostic Correlation:</strong> {visual_vs_reported}</div>" if visual_vs_reported else ""}
                    {f"<div style='font-size: 12px; margin-top: 8px;'><strong>Data Completeness & Uncertainty:</strong><ul style='margin: 4px 0 0; padding-left: 18px;'>" + uncertainties_html + "</ul></div>" if uncertainties else ""}
                </div>

                <!-- After-Hours Emergency Contacts Box -->
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px 16px; border-radius: 6px; font-size: 12px; color: #1e3a8a;">
                    <div style="font-weight: 700; margin-bottom: 4px;">🌙 Night, Weekend & Holiday Veterinary Emergency Resources:</div>
                    <div>• <strong>ASPCA Animal Poison Control Center:</strong> {poison_aspca}</div>
                    <div>• <strong>Pet Poison Helpline:</strong> {poison_helpline}</div>
                    <div>• <strong>AAHA 24-Hour Emergency Hospital Locator:</strong> <a href="{aaha_locator}" target="_blank" style="color: #1d4ed8;">{aaha_locator}</a></div>
                    <div style="margin-top: 4px; font-style: italic;">🚨 Transport Guidance: {transport_tip}</div>
                </div>
            </div>
            """

        # Format Doctor Clinical Review Box if present (historical support only)
        doctor_review_html = ""
        if doctor_review and (doctor_review.get("doctor_notes") or doctor_review.get("override_triage_level") or doctor_review.get("prescriptions")):
            override_str = f" | Triage Assigned: <strong>{cls._esc((doctor_review.get('override_triage_level') or '').upper())}</strong>" if doctor_review.get("override_triage_level") else ""
            notes_str = f"<p><strong>Clinical Notes:</strong> {cls._esc(doctor_review.get('doctor_notes'))}</p>" if doctor_review.get("doctor_notes") else ""
            rec_str = f"<p><strong>Treatment Recommendations:</strong> {cls._esc(doctor_review.get('recommendations'))}</p>" if doctor_review.get("recommendations") else ""
            rx_str = f"<div class='info-card' style='background:#f0fdf4; border-left:4px solid #16a34a; margin-top:8px;'><label style='color:#166534;'>Prescriptions & Medications (Rx)</label><p style='margin:4px 0 0; color:#14532d; font-weight:600;'>{cls._esc(doctor_review.get('prescriptions'))}</p></div>" if doctor_review.get("prescriptions") else ""

            doctor_review_html = f"""
            <div class="handoff-box" style="background: #f0fdf4; border-color: #86efac; margin-bottom: 20px;">
                <h3 style="color: #166534;">🩺 Verified Veterinarian Clinical Review & Treatment Plan</h3>
                <p><strong>Reviewing Clinician:</strong> {cls._esc(doctor_review.get('doctor_name') or 'Attending Veterinarian')} ({cls._esc((doctor_review.get('reviewed_at') or '')[:10])}){override_str}</p>
                {notes_str}
                {rec_str}
                {rx_str}
            </div>
            """

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
        {doctor_review_html}

        <!-- Risk Assessment Banner -->
        <div class="risk-banner">
            <div>
                <h2>OVERALL TRIAGE RISK: {cls._esc(risk_level)}</h2>
                <div>{cls._esc(recommendation.get('action'))}</div>
            </div>
            <div class="risk-score">{cls._esc(risk_score)}/100</div>
        </div>

        {care_guide_html}

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
