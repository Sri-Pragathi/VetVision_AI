"""Report Service for compiling, versioning, and generating immutable assessment reports."""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.assessment_report import AssessmentReport
from app.services.assessment_service import AssessmentService
from app.services.risk_analysis_service import RiskAnalysisService
from app.services.report_html_renderer import ReportHtmlRenderer
from app.utils.error_handlers import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
)


class ReportService:
    """Orchestrates comprehensive, explainable veterinary reports and health summaries.

    Gathers validated clinical data across Steps 1–5 into an immutable point-in-time
    snapshot suitable for owner review, veterinary consultation, and PDF export.
    """

    STANDARD_DISCLAIMER = (
        "VetVision AI provides AI-assisted health risk and early-warning information "
        "for informational and triage support. It does not provide a definitive "
        "veterinary diagnosis and does not replace examination or advice from a "
        "qualified veterinarian. Seek professional veterinary care when symptoms "
        "are concerning, worsening, or urgent."
    )

    @classmethod
    def _verify_report_ownership(cls, report_id: str, user_id: str) -> AssessmentReport:
        """Verify report exists and belongs to assessment owned by the authenticated user."""
        report = db.session.get(AssessmentReport, report_id)
        if not report:
            raise NotFoundException(f"Assessment report '{report_id}' not found.")

        assessment = report.assessment
        if not assessment or not assessment.pet or assessment.pet.owner_id != user_id:
            raise ForbiddenException("You do not have permission to access this assessment report.")

        return report

    @classmethod
    def generate_assessment_report(
        cls, assessment_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Compile a versioned point-in-time report snapshot of an assessment session."""
        # 1. Enforce assessment existence and ownership
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        # 2. Lifecycle validation
        if assessment.status == HealthAssessment.STATUS_CANCELLED:
            raise ValidationException("Cannot generate report for a cancelled assessment.")

        if not assessment.symptoms:
            raise ValidationException(
                "Assessment must have at least one reported symptom to generate a clinical report."
            )

        # 3. Ensure Step 4 risk analysis exists (generate if not yet performed)
        risk_analysis = assessment.risk_analysis
        if not risk_analysis:
            RiskAnalysisService.analyze_assessment(assessment_id, user_id)
            db.session.refresh(assessment)
            risk_analysis = assessment.risk_analysis

        # 4. Determine next version number (Immutable history)
        latest_report = (
            AssessmentReport.query
            .filter_by(assessment_id=assessment.id)
            .order_by(AssessmentReport.report_version.desc())
            .first()
        )
        next_version = (latest_report.report_version + 1) if latest_report else 1

        # Mark previous report as archived if regenerating
        if latest_report:
            latest_report.report_status = AssessmentReport.STATUS_ARCHIVED

        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 5. Build Comprehensive Snapshot Sections
        pet = assessment.pet

        # Pet Profile Section
        age_display = f"{pet.age} years" if pet and pet.age is not None else "Not specified"
        pet_profile_data = {
            "id": pet.id if pet else None,
            "name": pet.name if pet else "Unknown",
            "species": pet.species if pet else "Unknown",
            "breed": pet.breed if pet else "Not specified",
            "age": pet.age if pet else None,
            "age_display": age_display,
            "sex": pet.sex if pet else "Not specified",
            "weight": pet.weight if pet else None,
            "allergies": pet.allergies if pet and pet.allergies else "None reported",
            "existing_conditions": pet.existing_conditions if pet and pet.existing_conditions else "None reported",
            "current_medications": pet.current_medications if pet and pet.current_medications else "None reported",
            "vaccination_status": pet.vaccination_status if pet and pet.vaccination_status else "Not specified",
        }

        # Assessment Summary Section
        notes_list = [n.note for n in assessment.notes if n.note] if assessment.notes else []
        asmt_summary_data = {
            "assessment_id": assessment.id,
            "status": assessment.status,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "total_symptoms": len(assessment.symptoms),
            "additional_notes": "\n".join(notes_list) if notes_list else "No additional notes recorded",
        }

        # Reported Symptoms Section
        symptoms_data = []
        for s in assessment.symptoms:
            val_formatted = int(s.duration_value) if (s.duration_value and s.duration_value.is_integer()) else s.duration_value
            dur_display = (
                f"{val_formatted} {s.duration_unit}"
                if s.duration_value and s.duration_unit
                else "Not specified"
            )
            symptoms_data.append({
                "symptom_id": s.symptom_id,
                "name": s.symptom.name if s.symptom else "Unknown Symptom",
                "category": s.symptom.category if s.symptom else "General",
                "severity": s.severity,
                "duration_value": s.duration_value,
                "duration_unit": s.duration_unit,
                "duration": dur_display,
                "duration_display": dur_display,
                "notes": s.notes if s.notes else None,
            })

        # Adaptive Follow-up Findings Section
        follow_up_data = []
        try:
            from app.models.assessment_answer import AssessmentAnswer
            answers = (
                AssessmentAnswer.query
                .filter_by(assessment_id=assessment.id)
                .order_by(AssessmentAnswer.created_at.asc())
                .all()
            )
            for ans in answers:
                q = ans.question
                ans_display = (
                    ans.selected_option.option_text
                    if ans.selected_option
                    else (
                        str(ans.numeric_value)
                        if ans.numeric_value is not None
                        else (
                            "Yes" if ans.boolean_value is True else ("No" if ans.boolean_value is False else (ans.answer_text or "Recorded"))
                        )
                    )
                )
                follow_up_data.append({
                    "question_id": ans.question_id,
                    "question": q.question_text if q else "Clinical question",
                    "category": q.category if q else "General",
                    "priority": q.priority if q else "medium",
                    "is_emergency_related": q.is_emergency_related if q else False,
                    "answer": ans_display,
                    "selected_option": ans.selected_option.option_text if ans.selected_option else None,
                    "selected_value": ans.selected_option.option_value if ans.selected_option else None,
                    "triggered_emergency": ans.triggered_emergency,
                })
        except Exception:
            follow_up_data = []

        # Clinical Observations Section
        obs_obj = assessment.observations
        observations_data = {
            "appetite": obs_obj.appetite if obs_obj else None,
            "water_intake": obs_obj.water_intake if obs_obj else None,
            "activity_level": obs_obj.activity_level if obs_obj else None,
            "breathing_change": obs_obj.breathing_change if obs_obj else None,
            "pain_observed": obs_obj.pain_observed if obs_obj else None,
            "stool_change": obs_obj.stool_change if obs_obj else None,
            "urine_change": obs_obj.urine_change if obs_obj else None,
            "behaviour_change": obs_obj.behaviour_change if obs_obj else None,
            "sleep_change": obs_obj.sleep_change if obs_obj else None,
        }

        # Image Analysis Section
        image_analysis_list = []
        if not assessment.images:
            image_analysis_list.append({
                "image_id": None,
                "status": "NOT_PROVIDED",
                "analysis_status": "NOT_PROVIDED",
                "quality": {
                    "quality_gate": None,
                    "check_passed": False,
                    "warning": "No image provided.",
                },
                "quality_gate": None,
                "quality_warnings": "No image provided.",
                "visual_observations": "Image analysis: No image provided.",
                "detected_visual_features": [],
                "color_features": [],
                "findings_summary": "Image analysis: No image provided.",
                "analysis_timestamp": None,
            })
        else:
            for img in assessment.images:
                if img.analysis_status in ["PENDING", "UPLOADED", "VALIDATING"]:
                    image_analysis_list.append({
                        "image_id": img.id,
                        "status": "PENDING",
                        "analysis_status": img.analysis_status,
                        "quality": {
                            "quality_gate": img.quality_gate or "UNKNOWN",
                            "check_passed": img.quality_gate == "PASSED",
                            "warning": None,
                        },
                        "quality_gate": img.quality_gate or "UNKNOWN",
                        "quality_warnings": None,
                        "visual_observations": "Image analysis: Analysis not completed.",
                        "detected_visual_features": [],
                        "color_features": [],
                        "findings_summary": "Image analysis: Analysis not completed.",
                        "analysis_timestamp": None,
                    })
                elif img.quality_gate != "PASSED" or img.analysis_status in ["REQUIRES_BETTER_IMAGE", "FAILED"]:
                    image_analysis_list.append({
                        "image_id": img.id,
                        "status": "REQUIRES_BETTER_IMAGE",
                        "analysis_status": img.analysis_status,
                        "quality": {
                            "quality_gate": img.quality_gate,
                            "check_passed": False,
                            "warning": "Image quality insufficient for reliable visual analysis.",
                        },
                        "quality_gate": img.quality_gate,
                        "quality_warnings": "Image quality insufficient for reliable visual analysis.",
                        "visual_observations": "Image analysis: Image quality insufficient for reliable visual analysis.",
                        "detected_visual_features": [],
                        "color_features": [],
                        "findings_summary": "Image analysis: Image quality insufficient for reliable visual analysis.",
                        "analysis_timestamp": img.updated_at.isoformat() if img.updated_at else None,
                    })
                else:
                    img_obs = [
                        {
                            "observation_type": o.observation_type,
                            "observation_label": o.observation_label,
                            "severity": o.severity,
                            "region": o.region,
                            "description": o.description,
                        }
                        for o in img.observations
                    ]
                    detected_feats = [o.observation_label for o in img.observations]
                    color_feats = [o.observation_label for o in img.observations if o.observation_type == "color_feature"]
                    image_analysis_list.append({
                        "image_id": img.id,
                        "status": "COMPLETED",
                        "analysis_status": img.analysis_status,
                        "quality": {
                            "quality_gate": img.quality_gate,
                            "check_passed": True,
                            "warning": None,
                        },
                        "quality_gate": img.quality_gate,
                        "quality_warnings": None,
                        "visual_observations": img_obs,
                        "detected_visual_features": detected_feats,
                        "color_features": color_feats,
                        "findings_summary": (
                            f"{len(img_obs)} visual observation(s) recorded."
                            if img_obs
                            else "No distinct visual abnormalities detected."
                        ),
                        "analysis_timestamp": img.updated_at.isoformat() if img.updated_at else None,
                    })

        # Risk Analysis Section
        risk_data = {
            "risk_level": risk_analysis.risk_level,
            "risk_score": risk_analysis.risk_score,
            "is_emergency": risk_analysis.is_emergency,
            "key_factors": risk_analysis.key_factors or [],
            "factor_breakdown": risk_analysis.factor_breakdown or {},
            "recommendation": risk_analysis.recommendation,
            "engine_version": risk_analysis.engine_version,
        }

        # Explainability Section
        explainability_data = []
        breakdown = risk_analysis.factor_breakdown or {}
        if "symptom_score" in breakdown:
            sym_names = ", ".join([s["name"] for s in symptoms_data[:3]])
            explainability_data.append({
                "factor": "Symptom Manifestations",
                "finding": f"{len(symptoms_data)} symptom(s) reported ({sym_names})",
                "observed_finding": f"{len(symptoms_data)} symptom(s) reported ({sym_names})",
                "contribution": f"{breakdown.get('symptom_score', 0)} pts",
                "relevance": "Baseline symptom severity",
                "explanation": "Calculated baseline severity from primary and co-occurring clinical signs.",
            })
        if breakdown.get("duration_score", 0) > 0:
            explainability_data.append({
                "factor": "Chronicity & Duration",
                "finding": "Persistent symptoms recorded over observation window",
                "observed_finding": "Persistent symptoms recorded over observation window",
                "contribution": f"+{breakdown.get('duration_score')} pts",
                "relevance": "Progressive risk over time",
                "explanation": "Extended duration increases clinical risk of progressive deterioration.",
            })
        if breakdown.get("observation_score", 0) > 0:
            explainability_data.append({
                "factor": "Physiological & Behavioral Impact",
                "finding": "Altered metabolic or activity markers recorded",
                "observed_finding": "Altered metabolic or activity markers recorded",
                "contribution": f"+{breakdown.get('observation_score')} pts",
                "relevance": "Acute physical stressors",
                "explanation": "Clinical observations such as appetite, respiration, or pain reflect acute stress.",
            })
        if breakdown.get("follow_up_score", 0) > 0:
            explainability_data.append({
                "factor": "Dynamic Diagnostic Findings",
                "finding": "Critical answers provided during adaptive inquiry",
                "observed_finding": "Critical answers provided during adaptive inquiry",
                "contribution": f"+{breakdown.get('follow_up_score')} pts",
                "relevance": "Condition-specific escalation",
                "explanation": "Follow-up questions surfaced high-priority indicators warranting heightened caution.",
            })
        if breakdown.get("vulnerability_modifier", 0) > 0:
            explainability_data.append({
                "factor": "Patient Vulnerability",
                "finding": f"Age or profile risk: {pet_profile_data.get('age_display')}",
                "observed_finding": f"Age or profile risk: {pet_profile_data.get('age_display')}",
                "contribution": f"+{breakdown.get('vulnerability_modifier')} pts",
                "relevance": "Physiologic reserve",
                "explanation": "Young, senior, or pets with pre-existing conditions have reduced physiologic reserve.",
            })
        if breakdown.get("image_score", 0) > 0:
            explainability_data.append({
                "factor": "Visual Feature Observations",
                "finding": "Photographic visual changes recorded by computer vision",
                "observed_finding": "Photographic visual changes recorded by computer vision",
                "contribution": f"+{breakdown.get('image_score')} pts",
                "relevance": "Objective visual signs",
                "explanation": "Visual assessment confirmed surface or anatomical features correlating with clinical presentation.",
            })
        if breakdown.get("emergency_override"):
            explainability_data.insert(0, {
                "factor": "Emergency Hard-Stop Prioritization",
                "finding": "Acute life-safety emergency criteria triggered",
                "observed_finding": "Acute life-safety emergency criteria triggered",
                "contribution": "Score floor enforced at >= 90",
                "relevance": "Critical safety override",
                "explanation": "Critical signs bypass routine scoring to protect patient life safety.",
            })
        if not explainability_data:
            explainability_data.append({
                "factor": "Baseline Clinical Presentation",
                "finding": "Mild isolated symptoms without secondary physiological disruption",
                "observed_finding": "Mild isolated symptoms without secondary physiological disruption",
                "contribution": f"{risk_analysis.risk_score} pts",
                "relevance": "Low-acuity baseline",
                "explanation": "Risk score reflects low baseline severity with normal vitals and behavior.",
            })

        # Emergency Section
        is_em = bool(risk_analysis.is_emergency)
        if is_em:
            emergency_status_str = "Emergency veterinary attention recommended"
        elif risk_analysis.risk_level == "HIGH":
            emergency_status_str = "Urgent evaluation recommended"
        else:
            emergency_status_str = "No emergency indicators identified"

        emergency_data = {
            "status": emergency_status_str,
            "is_emergency": is_em,
            "emergency_triggers": [f for f in (risk_analysis.key_factors or []) if "CRITICAL:" in f or "Acute" in f or "Hard-Stop" in f],
            "urgency_level": "EMERGENCY_IMMEDIATE" if is_em else ("URGENT" if risk_analysis.risk_level == "HIGH" else "ROUTINE_OR_MONITOR"),
            "action_urgency": "Immediate Emergency" if is_em else ("Urgent Evaluation" if risk_analysis.risk_level == "HIGH" else "Routine Monitoring"),
        }

        # Recommendation Section
        recommendation_data = {
            "primary_action": risk_analysis.recommendation,
            "action": risk_analysis.recommendation,
            "level": risk_analysis.risk_level,
            "urgency_level": emergency_data["urgency_level"],
            "guidance": (
                "Transport pet to the nearest emergency hospital immediately."
                if is_em
                else (
                    "Schedule an urgent clinical appointment as soon as possible."
                    if risk_analysis.risk_level == "HIGH"
                    else "Monitor hydration, appetite, and temperature. Schedule checkup if signs persist."
                )
            ),
        }

        # Veterinary Handoff Summary
        primary_sym_str = ", ".join([f"{s['name']} ({s['severity']}, {s['duration_display']})" for s in symptoms_data[:3]])
        important_symptoms_list = [f"{s['name']} (Severity: {s['severity']}, Duration: {s['duration_display']})" for s in symptoms_data]
        handoff_data = {
            "patient": f"{pet_profile_data['name']} ({pet_profile_data['species']}, {pet_profile_data['breed']}, {pet_profile_data['age_display']})",
            "pet_summary": f"{pet_profile_data['name']} ({pet_profile_data['species']}, {pet_profile_data['breed']}, {pet_profile_data['age_display']})",
            "primary_complaint": primary_sym_str or "General health assessment",
            "primary_reported_concerns": primary_sym_str or "General health assessment",
            "reported_symptoms": important_symptoms_list,
            "important_symptoms": important_symptoms_list,
            "duration_severity_summary": f"{len(symptoms_data)} reported symptom(s)",
            "relevant_follow_up_findings": [f"{f['question']}: {f['answer']}" for f in follow_up_data[:3]],
            "clinical_observations_summary": ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in observations_data.items() if v]) or "None recorded",
            "important_observations": [f"{k.replace('_', ' ').title()}: {v}" for k, v in observations_data.items() if v],
            "image_observations": [img.get("findings_summary") for img in image_analysis_list if img.get("findings_summary")],
            "risk_level": risk_analysis.risk_level,
            "triage_risk": f"{risk_analysis.risk_level} (Score: {risk_analysis.risk_score}/100)",
            "emergency_status": emergency_status_str,
            "emergency_indicators": emergency_status_str,
            "recommended_action": risk_analysis.recommendation,
            "recommended_next_action": risk_analysis.recommendation,
            "key_findings": risk_analysis.key_factors or [],
        }

        # Master Snapshot Assembly
        report_data = {
            "metadata": {
                "report_id": report_id,
                "report_version": next_version,
                "generated_at": now.isoformat(),
                "assessment_id": assessment.id,
                "generated_by": user_id,
                "system": "VetVision AI Clinical Assistance Engine",
                "engine_version": risk_analysis.engine_version,
            },
            "pet": pet_profile_data,
            "assessment": asmt_summary_data,
            "symptoms": symptoms_data,
            "follow_up_findings": follow_up_data,
            "observations": observations_data,
            "image_analysis": image_analysis_list,
            "risk_analysis": risk_data,
            "explainability": explainability_data,
            "emergency": emergency_data,
            "recommendation": recommendation_data,
            "veterinary_handoff": handoff_data,
            "disclaimer": cls.STANDARD_DISCLAIMER,
        }

        # 6. Persist Immutable Report Record
        report = AssessmentReport(
            id=report_id,
            assessment_id=assessment.id,
            report_version=next_version,
            report_status=AssessmentReport.STATUS_GENERATED,
            generated_at=now,
            generated_by=user_id,
            report_data=report_data,
            disclaimer=cls.STANDARD_DISCLAIMER,
        )
        db.session.add(report)
        db.session.commit()

        return report.to_dict()

    @classmethod
    def get_assessment_reports(
        cls, assessment_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve all historical and active report snapshots for an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        reports = (
            AssessmentReport.query
            .filter_by(assessment_id=assessment.id)
            .order_by(AssessmentReport.report_version.desc())
            .all()
        )
        return [r.to_dict(include_full_data=False) for r in reports]

    @classmethod
    def get_report_by_id(cls, report_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve a specific report snapshot with full structured data."""
        report = cls._verify_report_ownership(report_id, user_id)
        return report.to_dict(include_full_data=True)

    @classmethod
    def get_report_html(cls, report_id: str, user_id: str) -> str:
        """Render standalone, injection-safe HTML document for viewing or printing."""
        report = cls._verify_report_ownership(report_id, user_id)
        return ReportHtmlRenderer.render(report.report_data)
