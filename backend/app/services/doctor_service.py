"""Doctor service for clinical review queue, patient case details, and veterinary assessments."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import or_, desc, select
from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.pet import Pet
from app.models.user import User
from app.models.risk_analysis import AssessmentRiskAnalysis
from app.models.doctor_review import DoctorReview
from app.utils.error_handlers import NotFoundException, ValidationException


class DoctorService:
    """Service providing clinical case queue and review capabilities for verified doctors."""

    @classmethod
    def list_clinical_cases(
        cls,
        triage_level: Optional[str] = None,
        review_status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """List clinical intake cases with triage metrics and review statuses.

        Args:
            triage_level: Optional filter ('critical', 'urgent', 'routine', 'non_urgent',
                          or 'EMERGENCY', 'HIGH', 'MODERATE', 'LOW').
            review_status: 'all', 'pending', or 'reviewed'.
            search: Search query against pet name, pet breed, or pet owner name.
            page: Current page (1-indexed).
            per_page: Items per page.

        Returns:
            Dictionary with items list and pagination metadata.
        """
        query = db.session.query(HealthAssessment).join(
            Pet, HealthAssessment.pet_id == Pet.id
        ).join(
            User, Pet.owner_id == User.id
        ).outerjoin(
            AssessmentRiskAnalysis, HealthAssessment.id == AssessmentRiskAnalysis.assessment_id
        )

        # Apply search filter
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Pet.name.ilike(term),
                    Pet.breed.ilike(term),
                    User.name.ilike(term),
                    User.email.ilike(term),
                )
            )

        # Apply review_status filter
        if review_status and review_status.lower() in ("pending", "reviewed"):
            status_filter = review_status.lower()
            reviewed_subquery = select(DoctorReview.assessment_id).filter(
                DoctorReview.status == DoctorReview.STATUS_REVIEWED
            )

            if status_filter == "reviewed":
                query = query.filter(HealthAssessment.id.in_(reviewed_subquery))
            elif status_filter == "pending":
                query = query.filter(~HealthAssessment.id.in_(reviewed_subquery))

        # Apply triage_level filter
        if triage_level and triage_level.strip():
            tl = triage_level.strip().upper()
            level_map = {
                "CRITICAL": "EMERGENCY",
                "URGENT": "HIGH",
                "ROUTINE": "MODERATE",
                "NON_URGENT": "LOW",
                "NON-URGENT": "LOW",
            }
            target_risk = level_map.get(tl, tl)
            override_map = {
                "EMERGENCY": "critical",
                "HIGH": "urgent",
                "MODERATE": "routine",
                "LOW": "non_urgent",
            }
            target_override = override_map.get(tl, triage_level.strip().lower())

            review_override_subquery = select(DoctorReview.assessment_id).filter(
                DoctorReview.override_triage_level.ilike(target_override)
            )

            query = query.filter(
                or_(
                    AssessmentRiskAnalysis.risk_level.ilike(target_risk),
                    HealthAssessment.id.in_(review_override_subquery),
                )
            )

        # Order by newest assessments first
        query = query.order_by(desc(HealthAssessment.created_at))

        # Pagination
        total = query.count()
        pages = max(1, (total + per_page - 1) // per_page)
        offset = (page - 1) * per_page
        assessments = query.offset(offset).limit(per_page).all()

        items = []
        for assessment in assessments:
            pet = assessment.pet
            owner = pet.owner if pet else None
            risk = assessment.risk_analysis
            latest_review = assessment.doctor_reviews[0] if assessment.doctor_reviews else None

            # Determine clinical review status
            is_reviewed = latest_review is not None and latest_review.status == DoctorReview.STATUS_REVIEWED
            effective_status = "reviewed" if is_reviewed else "pending"

            # Determine effective triage label
            if latest_review and latest_review.override_triage_level:
                effective_triage = latest_review.override_triage_level
            elif risk:
                risk_map = {
                    "EMERGENCY": "critical",
                    "HIGH": "urgent",
                    "MODERATE": "routine",
                    "LOW": "non_urgent",
                }
                effective_triage = risk_map.get(risk.risk_level.upper(), risk.risk_level.lower())
            else:
                effective_triage = "routine"

            pet_dict = pet.to_dict() if pet else {}
            if owner:
                pet_dict["owner_name"] = owner.name
                pet_dict["owner_email"] = owner.email

            items.append({
                "assessment_id": assessment.id,
                "status": assessment.status,
                "current_step": assessment.current_step,
                "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
                "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
                "review_status": effective_status,
                "effective_triage": effective_triage,
                "pet": pet_dict,
                "risk_analysis": {
                    "risk_level": risk.risk_level,
                    "risk_score": risk.risk_score,
                    "is_emergency": risk.is_emergency,
                    "recommendation": risk.recommendation,
                } if risk else None,
                "symptoms_count": len(assessment.symptoms),
                "images_count": len(assessment.images),
                "latest_review": latest_review.to_dict() if latest_review else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @classmethod
    def get_clinical_case(cls, assessment_id: str) -> Dict[str, Any]:
        """Fetch comprehensive clinical data for an intake case.

        Args:
            assessment_id: ID of the health assessment.

        Returns:
            Dictionary containing pet history, owner info, symptoms,
            question answers, CV images, AI risk analysis, and doctor reviews.
        """
        assessment = db.session.get(HealthAssessment, assessment_id)
        if not assessment:
            raise NotFoundException(f"Clinical assessment '{assessment_id}' not found.")

        pet = assessment.pet
        owner = pet.owner if pet else None
        risk = assessment.risk_analysis

        # Collect answered triage questions
        answers = []
        if hasattr(assessment, "answers"):
            raw_answers = assessment.answers.all() if hasattr(assessment.answers, "all") else assessment.answers
            for ans in raw_answers:
                answers.append(ans.to_dict(include_question=True))

        # Doctor reviews
        doctor_reviews = [dr.to_dict() for dr in assessment.doctor_reviews]
        latest_review = doctor_reviews[0] if doctor_reviews else None

        pet_dict = pet.to_dict() if pet else {}
        if owner:
            pet_dict["owner"] = {
                "id": owner.id,
                "name": owner.name,
                "email": owner.email,
            }

        return {
            "assessment_id": assessment.id,
            "status": assessment.status,
            "current_step": assessment.current_step,
            "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
            "pet": pet_dict,
            "symptoms": [s.to_dict() for s in assessment.symptoms],
            "observations": assessment.observations.to_dict() if assessment.observations else None,
            "answers": answers,
            "images": [img.to_dict() for img in assessment.images],
            "risk_analysis": risk.to_dict() if risk else None,
            "reports": [r.to_dict() for r in assessment.reports],
            "doctor_reviews": doctor_reviews,
            "latest_review": latest_review,
        }

    @classmethod
    def submit_doctor_review(
        cls,
        assessment_id: str,
        doctor_id: str,
        review_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit or update a clinical review for an assessment.

        Args:
            assessment_id: ID of the health assessment.
            doctor_id: ID of the authenticated reviewing doctor.
            review_data: Dict with override_triage_level, doctor_notes,
                         recommendations, prescriptions, status.

        Returns:
            Dictionary representing the persisted DoctorReview.
        """
        assessment = db.session.get(HealthAssessment, assessment_id)
        if not assessment:
            raise NotFoundException(f"Clinical assessment '{assessment_id}' not found.")

        # Check for existing review by this doctor for this assessment
        review = DoctorReview.query.filter_by(
            assessment_id=assessment_id,
            doctor_id=doctor_id,
        ).first()

        override_triage = review_data.get("override_triage_level")
        if override_triage and override_triage not in DoctorReview.VALID_TRIAGE_LEVELS:
            raise ValidationException(
                f"Invalid triage level '{override_triage}'. Must be one of: {sorted(DoctorReview.VALID_TRIAGE_LEVELS)}"
            )

        status = review_data.get("status", DoctorReview.STATUS_REVIEWED)
        if status not in DoctorReview.VALID_STATUSES:
            raise ValidationException(
                f"Invalid status '{status}'. Must be one of: {sorted(DoctorReview.VALID_STATUSES)}"
            )

        if not review:
            review = DoctorReview(
                assessment_id=assessment_id,
                doctor_id=doctor_id,
                status=status,
                override_triage_level=override_triage,
                doctor_notes=review_data.get("doctor_notes"),
                recommendations=review_data.get("recommendations"),
                prescriptions=review_data.get("prescriptions"),
                reviewed_at=datetime.now(timezone.utc),
            )
            db.session.add(review)
        else:
            review.status = status
            review.override_triage_level = override_triage
            review.doctor_notes = review_data.get("doctor_notes")
            review.recommendations = review_data.get("recommendations")
            review.prescriptions = review_data.get("prescriptions")
            review.reviewed_at = datetime.now(timezone.utc)

        db.session.commit()
        db.session.refresh(review)
        return review.to_dict()
