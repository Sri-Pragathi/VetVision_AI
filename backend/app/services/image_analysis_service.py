"""Image Analysis Service coordinating secure upload, validation, storage, and CV analysis."""
import os
import uuid
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image

from app.extensions import db
from app.models.health_assessment import HealthAssessment
from app.models.assessment_image import AssessmentImage, ImageObservation
from app.services.assessment_service import AssessmentService
from app.services.storage_service import BaseImageStorage, LocalStorageService
from app.services.cv_engine.base import BaseImageAnalysisEngine
from app.services.cv_engine.basic_engine import BasicImageAnalysisEngine
from app.utils.error_handlers import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
)


class ImageAnalysisService:
    """Service orchestrating pet photographic attachments and computer vision pipeline."""

    _default_storage: BaseImageStorage = LocalStorageService()
    _default_engine: BaseImageAnalysisEngine = BasicImageAnalysisEngine()

    @classmethod
    def set_default_engine(cls, engine: BaseImageAnalysisEngine) -> None:
        """Allow runtime registration of custom computer vision engines."""
        cls._default_engine = engine

    @classmethod
    def set_default_storage(cls, storage: BaseImageStorage) -> None:
        """Allow runtime registration of custom image storage providers."""
        cls._default_storage = storage

    @classmethod
    def _verify_image_ownership(cls, image_id: str, user_id: str) -> AssessmentImage:
        """Verify image exists and belongs to an assessment owned by user."""
        image = db.session.get(AssessmentImage, image_id)
        if not image:
            raise NotFoundException(f"Assessment image '{image_id}' not found.")

        # Check ownership via attached pet
        assessment = image.assessment
        if not assessment or not assessment.pet or assessment.pet.owner_id != user_id:
            raise ForbiddenException("You do not have permission to access this assessment image.")

        return image

    @classmethod
    def upload_assessment_image(
        cls,
        assessment_id: str,
        user_id: str,
        file_obj: Any,
        storage: Optional[BaseImageStorage] = None,
    ) -> Dict[str, Any]:
        """Validate and securely store an image uploaded for a health assessment."""
        # 1. Enforce assessment existence and user ownership
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)

        # 2. Lifecycle state check
        if assessment.status == HealthAssessment.STATUS_CANCELLED:
            raise ValidationException("Cannot upload images to a cancelled assessment.")

        # 3. File existence check
        if not file_obj or not getattr(file_obj, "filename", None):
            raise ValidationException("No image file provided for upload.")

        filename = secure_filename(file_obj.filename)
        if not filename or "." not in filename:
            raise ValidationException("Invalid image filename format.")

        ext = filename.rsplit(".", 1)[1].lower()
        allowed_exts = current_app.config.get(
            "ALLOWED_IMAGE_EXTENSIONS", {"jpg", "jpeg", "png", "webp"}
        )
        if ext not in allowed_exts:
            raise ValidationException(
                f"Unsupported image format '.{ext}'. Allowed formats: {', '.join(sorted(allowed_exts))}."
            )

        # 4. Read bytes and check size limits
        file_bytes = file_obj.read()
        if len(file_bytes) == 0:
            raise ValidationException("Uploaded file is empty (0 bytes).")

        max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
        if len(file_bytes) > max_bytes:
            raise ValidationException(
                f"File size exceeds maximum allowable limit of {max_bytes // (1024 * 1024)} MB."
            )

        # 5. Decode and validate image content via Pillow
        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
            pil_img.verify()  # Verifies image integrity
            # Reopen to read dimensions after verify()
            pil_img = Image.open(io.BytesIO(file_bytes))
            width, height = pil_img.size
            img_format = (pil_img.format or ext).upper()
        except Exception:
            raise ValidationException("Uploaded file is corrupted or not a valid image.")

        # Resolve MIME type
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }
        mime_type = mime_map.get(ext, f"image/{ext}")

        # 6. Generate safe unique storage key
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        relative_storage_key = f"assessments/{assessment.id}/{unique_name}"

        # 7. Persist to storage
        active_storage = storage or cls._default_storage
        saved_key = active_storage.save_file(file_bytes, relative_storage_key)

        # 8. Record in database
        image_record = AssessmentImage(
            assessment_id=assessment.id,
            pet_id=assessment.pet_id,
            original_filename=filename,
            storage_path=saved_key,
            mime_type=mime_type,
            file_size=len(file_bytes),
            width=width,
            height=height,
            processing_status=AssessmentImage.STATUS_READY,
            analysis_status=AssessmentImage.ANALYSIS_PENDING,
        )
        db.session.add(image_record)
        db.session.commit()

        return image_record.to_dict()

    @classmethod
    def get_assessment_images(
        cls, assessment_id: str, user_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve all images attached to an assessment."""
        assessment = AssessmentService._verify_assessment_ownership(assessment_id, user_id)
        images = (
            AssessmentImage.query
            .filter_by(assessment_id=assessment.id)
            .order_by(AssessmentImage.created_at.asc())
            .all()
        )
        return [img.to_dict(include_observations=True) for img in images]

    @classmethod
    def get_image_by_id(cls, image_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve single assessment image metadata."""
        image = cls._verify_image_ownership(image_id, user_id)
        return image.to_dict(include_observations=True)

    @classmethod
    def analyze_image(
        cls,
        image_id: str,
        user_id: str,
        engine: Optional[BaseImageAnalysisEngine] = None,
        storage: Optional[BaseImageStorage] = None,
    ) -> Dict[str, Any]:
        """Run computer vision analysis on an uploaded assessment image."""
        image = cls._verify_image_ownership(image_id, user_id)

        if image.assessment.status == HealthAssessment.STATUS_CANCELLED:
            raise ValidationException("Cannot analyze image from a cancelled assessment.")

        # Update status to ANALYZING
        image.processing_status = AssessmentImage.STATUS_ANALYZING
        db.session.commit()

        # Resolve local absolute filesystem path
        active_storage = storage or cls._default_storage
        abs_path = active_storage.get_absolute_path(image.storage_path)

        # Build clinical context
        context = {
            "species": image.pet.species if image.pet else None,
            "symptoms": [
                {"name": s.symptom.name, "category": s.symptom.category, "severity": s.severity}
                for s in image.assessment.symptoms
            ] if image.assessment and image.assessment.symptoms else [],
        }

        # Run CV Engine
        active_engine = engine or cls._default_engine
        output = active_engine.analyze_image(abs_path, context=context)

        # Clear existing observations for idempotent re-analysis
        for existing_obs in list(image.observations):
            db.session.delete(existing_obs)
        db.session.flush()

        # Save new visual observations
        for obs_data in output.visual_observations:
            obs_record = ImageObservation(
                assessment_image_id=image.id,
                observation_type=obs_data.get("observation_type", "visual_feature"),
                observation_label=obs_data.get("observation_label", "UNKNOWN"),
                severity=obs_data.get("severity", "normal"),
                region=obs_data.get("region", "overall_image"),
                description=obs_data.get("description", ""),
                source=obs_data.get("source", "computer_vision"),
                model_version=obs_data.get("model_version", active_engine.version),
                extra_data=obs_data.get("extra_data"),
            )
            db.session.add(obs_record)

        # Update image status
        image.quality_gate = output.quality_gate
        if output.status in ("SUCCESS", AssessmentImage.ANALYSIS_ANALYZED):
            image.analysis_status = AssessmentImage.ANALYSIS_ANALYZED
            image.processing_status = AssessmentImage.STATUS_ANALYZED
        elif output.status == AssessmentImage.ANALYSIS_REQUIRES_BETTER_IMAGE:
            image.analysis_status = AssessmentImage.ANALYSIS_REQUIRES_BETTER_IMAGE
            image.processing_status = AssessmentImage.STATUS_ANALYZED
        else:
            image.analysis_status = AssessmentImage.ANALYSIS_FAILED
            image.processing_status = AssessmentImage.STATUS_FAILED

        db.session.commit()

        result = image.to_dict(include_observations=True)
        result["quality_score"] = output.quality_score
        result["quality_metrics"] = output.quality_metrics
        result["reasons"] = output.reasons
        result["recommendation"] = output.recommendation
        result["disclaimer"] = output.disclaimer
        result["engine_version"] = output.engine_version

        return result

    @classmethod
    def get_image_analysis(cls, image_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve stored computer-vision analysis for an image."""
        image = cls._verify_image_ownership(image_id, user_id)

        if image.analysis_status == AssessmentImage.ANALYSIS_PENDING:
            raise NotFoundException(
                f"No computer-vision analysis has been executed for image '{image_id}' yet."
            )

        data = image.to_dict(include_observations=True)
        data["disclaimer"] = (
            "This image analysis provides computational computer-vision observations "
            "for early-warning support and does not replace professional veterinary "
            "examination or diagnosis."
        )
        return data

    @classmethod
    def delete_image(
        cls,
        image_id: str,
        user_id: str,
        storage: Optional[BaseImageStorage] = None,
    ) -> bool:
        """Delete an assessment image from both storage and database."""
        image = cls._verify_image_ownership(image_id, user_id)

        # Remove from storage
        active_storage = storage or cls._default_storage
        active_storage.delete_file(image.storage_path)

        # Remove from DB (cascade deletes observations)
        db.session.delete(image)
        db.session.commit()

        return True
