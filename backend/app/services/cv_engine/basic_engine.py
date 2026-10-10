"""Basic computer-vision analysis engine performing image quality gating and visual extraction."""
import os
from typing import Dict, Any, List, Optional
from PIL import Image, ImageStat, ImageFilter
from app.services.cv_engine.base import BaseImageAnalysisEngine, ImageAnalysisOutput


class BasicImageAnalysisEngine(BaseImageAnalysisEngine):
    """Production-ready baseline CV engine for image quality gating and visual extraction.

    Safety Notice:
    Does NOT fabricate disease diagnoses or fake ML accuracies.
    Performs verified image analysis:
    - Resolution and dimension gating (min 150x150)
    - Luminance and lighting verification (detects underexposure / overexposure)
    - Contrast analysis (detects washed-out or flat images)
    - Edge density and sharpness evaluation (detects excessive blur)
    - Color spectrum / erythema ratio analysis for dermatological context
    """

    ENGINE_VERSION = "v1.1.0-cv_reliability"

    # Quality Gate Thresholds
    MIN_DIMENSION = 150
    MIN_LUMINANCE = 35.0    # Underexposed / too dark
    MAX_LUMINANCE = 240.0   # Overexposed / washed out
    MIN_CONTRAST = 12.0     # Flat / lacking detail
    MIN_EDGE_SHARPNESS = 1.8# Out of focus / motion blur
    MIN_ASPECT_RATIO = 0.2  # Extreme vertical distortion
    MAX_ASPECT_RATIO = 5.0  # Extreme horizontal distortion

    @property
    def version(self) -> str:
        return self.ENGINE_VERSION

    def analyze_image(
        self, image_path: str, context: Optional[Dict[str, Any]] = None
    ) -> ImageAnalysisOutput:
        """Analyze image file for visual quality and extract structured observations."""
        if not os.path.exists(image_path):
            return ImageAnalysisOutput(
                status="FAILED",
                quality_gate="FAILED",
                quality_score=0.0,
                reasons=["Image file not found on storage"],
                actionable_guidance=["Please re-upload the pet image from your local device."],
                recommendation="Please re-upload the pet image.",
                engine_version=self.ENGINE_VERSION,
            )

        try:
            with Image.open(image_path) as img:
                # Force loading pixel data to catch corrupted files
                img.load()
                width, height = img.size
                img_format = img.format or "UNKNOWN"
                mode = img.mode

                # Convert to RGB if palette/RGBA
                if mode != "RGB":
                    rgb_img = img.convert("RGB")
                else:
                    rgb_img = img.copy()

            # Analyze luminance and contrast using grayscale
            gray_img = rgb_img.convert("L")
            stat = ImageStat.Stat(gray_img)
            mean_luminance = stat.mean[0]
            contrast_std = stat.stddev[0]

            # Calculate edge sharpness via filter
            edges = gray_img.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_energy = edge_stat.mean[0]
            edge_extrema = edges.getextrema()
            edge_max = edge_extrema[1] if isinstance(edge_extrema, tuple) else 0

            # Color profile analysis
            rgb_stat = ImageStat.Stat(rgb_img)
            mean_r, mean_g, mean_b = rgb_stat.mean[0], rgb_stat.mean[1], rgb_stat.mean[2]
            erythema_ratio = mean_r / (mean_g + mean_b + 1e-5)

        except Exception as e:
            return ImageAnalysisOutput(
                status="FAILED",
                quality_gate="FAILED",
                quality_score=0.0,
                reasons=[f"Unable to decode image file: {str(e)}"],
                actionable_guidance=["Please ensure the image file is not corrupted and try again."],
                recommendation="Please ensure the image file is not corrupted and try again.",
                engine_version=self.ENGINE_VERSION,
            )

        # -------------------------------------------------------------------
        # Quality Gate Evaluation
        # -------------------------------------------------------------------
        reasons: List[str] = []
        actionable_guidance: List[str] = []

        aspect_ratio = round(width / max(1, height), 2)
        is_sufficient_res = width >= self.MIN_DIMENSION and height >= self.MIN_DIMENSION
        is_well_lit = self.MIN_LUMINANCE <= mean_luminance <= self.MAX_LUMINANCE
        is_sufficient_contrast = contrast_std >= self.MIN_CONTRAST
        # Image is sharp if edge energy is above threshold or maximum gradient is pronounced
        is_sharp = edge_energy >= self.MIN_EDGE_SHARPNESS or edge_max >= 160
        is_balanced_aspect = self.MIN_ASPECT_RATIO <= aspect_ratio <= self.MAX_ASPECT_RATIO

        # 1. Dimension Check
        if not is_sufficient_res:
            reasons.append(
                f"Image resolution is too low ({width}x{height}px; minimum {self.MIN_DIMENSION}x{self.MIN_DIMENSION}px required)"
            )
            actionable_guidance.append(
                "Move closer to your pet or use higher camera resolution so physical details are clearly visible."
            )

        # 2. Lighting Check
        if mean_luminance < self.MIN_LUMINANCE:
            reasons.append("Insufficient lighting (image is too dark for reliable visual assessment)")
            actionable_guidance.append(
                "Improve lighting: turn on indoor lights or move near a window to illuminate the pet's area of concern."
            )
        elif mean_luminance > self.MAX_LUMINANCE:
            reasons.append("Overexposed (image is too bright or washed out by direct light/flash)")
            actionable_guidance.append(
                "Avoid direct harsh flash or intense glare; capture the photo in balanced ambient lighting."
            )

        # 3. Contrast Check
        if not is_sufficient_contrast:
            reasons.append("Low visual contrast (image lacks distinct discernible features or visual detail)")
            actionable_guidance.append(
                "Ensure the pet and affected area are clearly centered and distinct from the background."
            )

        # 4. Blur / Sharpness Check
        if not is_sharp:
            reasons.append("Excessive blur detected (image lacks sharp edge definition or camera lost focus)")
            actionable_guidance.append(
                "Hold the camera steady or rest your hands on a stable surface. Tap your screen to focus directly on the affected area before taking the photo."
            )

        # 5. Aspect Ratio Distortion Check
        if not is_balanced_aspect:
            reasons.append(f"Extreme aspect ratio distortion ({width}x{height}px)")
            actionable_guidance.append(
                "Capture with standard photographic framing rather than an extreme crop or panoramic ratio."
            )

        # Quality metrics dictionary
        quality_metrics = {
            "width": width,
            "height": height,
            "format": img_format,
            "aspect_ratio": aspect_ratio,
            "mean_luminance": round(mean_luminance, 1),
            "contrast_std": round(contrast_std, 1),
            "edge_energy": round(edge_energy, 2),
            "edge_max": edge_max,
            "is_well_lit": is_well_lit,
            "is_sufficient_resolution": is_sufficient_res,
            "is_sufficient_contrast": is_sufficient_contrast,
            "is_sharp": is_sharp,
            "is_balanced_aspect_ratio": is_balanced_aspect,
        }

        # If any quality check fails, return REQUIRES_BETTER_IMAGE
        if reasons:
            poor_obs = {
                "observation_type": "visual_quality",
                "observation_label": "POOR_IMAGE_QUALITY",
                "severity": "moderate",
                "region": "overall_image",
                "description": (
                    "The image does not meet quality requirements for reliable visual inspection: "
                    + "; ".join(reasons)
                ),
                "source": "computer_vision",
                "model_version": self.ENGINE_VERSION,
                "extra_data": {
                    "reasons": reasons,
                    "actionable_guidance": actionable_guidance,
                    "quality_metrics": quality_metrics,
                },
            }
            combined_rec = (
                "Please take a new photo following these recommendations: "
                + " ".join(actionable_guidance)
            )
            return ImageAnalysisOutput(
                status="REQUIRES_BETTER_IMAGE",
                quality_gate="REQUIRES_BETTER_IMAGE",
                quality_score=round(max(0.1, 0.4 - len(reasons) * 0.08), 2),
                quality_metrics=quality_metrics,
                visual_observations=[poor_obs],
                reasons=reasons,
                actionable_guidance=actionable_guidance,
                recommendation=combined_rec,
                engine_version=self.ENGINE_VERSION,
            )

        # -------------------------------------------------------------------
        # Quality Gate PASSED -> Extract Computer Vision Observations
        # -------------------------------------------------------------------
        norm_quality = min(1.0, 0.65 + (contrast_std / 255.0) + min(0.2, (width * height) / 2_000_000))
        observations: List[Dict[str, Any]] = []

        # 1. Quality Confirmation Observation
        observations.append({
            "observation_type": "visual_quality",
            "observation_label": "SUITABLE_FOR_ANALYSIS",
            "severity": "normal",
            "region": "overall_image",
            "description": (
                "Image demonstrates adequate resolution, balanced lighting, "
                "sufficient contrast, and sharp focus for visual inspection."
            ),
            "source": "computer_vision",
            "model_version": self.ENGINE_VERSION,
            "extra_data": {
                "measured_feature": "Resolution, lighting, contrast, and edge sharpness verified",
                "clinical_note": "Quality criteria met for computational feature screening.",
            },
        })

        # 2. Color Profile / Dermatological Observation
        context = context or {}
        has_skin_context = any(
            "skin" in str(sym.get("category", "")).lower()
            or "skin" in str(sym.get("name", "")).lower()
            or "red" in str(sym.get("name", "")).lower()
            or "itch" in str(sym.get("name", "")).lower()
            or "rash" in str(sym.get("name", "")).lower()
            for sym in context.get("symptoms", [])
        )

        if erythema_ratio > 0.85:
            obs_desc = (
                f"Computer vision chromatic inspection detected elevated red-channel distribution (ratio: {erythema_ratio:.2f}). "
                "Visual redness may correspond to localized superficial inflammation, abrasion, or irritation, "
                "but represents an image-processing measurement rather than a definitive veterinary diagnosis."
            )
            if has_skin_context:
                obs_desc += " Coincides with reported dermatological symptoms."

            observations.append({
                "observation_type": "visual_feature",
                "observation_label": "ELEVATED_ERYTHEMA_DETECTED",
                "severity": "mild" if erythema_ratio < 1.1 else "moderate",
                "region": "focal_region",
                "description": obs_desc,
                "source": "computer_vision",
                "model_version": self.ENGINE_VERSION,
                "extra_data": {
                    "measured_feature": f"Red-channel to green/blue chromatic ratio: {erythema_ratio:.2f} (baseline expectation: < 0.85)",
                    "clinical_note": "Superficial redness may correlate with localized dermatological inflammation or irritation. In-person veterinary examination is required for differential diagnosis.",
                    "erythema_ratio": round(erythema_ratio, 2),
                    "has_skin_symptom_context": has_skin_context,
                },
            })
        else:
            observations.append({
                "observation_type": "visual_feature",
                "observation_label": "STANDARD_COLOR_DISTRIBUTION",
                "severity": "normal",
                "region": "overall_image",
                "description": (
                    "Visual chromatic distribution falls within expected baseline parameters without localized discoloration. "
                    "Note: Standard coloration does not rule out non-visual dermatological conditions, microscopic parasites, or internal discomfort."
                ),
                "source": "computer_vision",
                "model_version": self.ENGINE_VERSION,
                "extra_data": {
                    "measured_feature": f"Color balance within expected spectrum (erythema ratio: {erythema_ratio:.2f})",
                    "clinical_note": "Normal coloration at visual resolution does not rule out underlying dermatological or systemic conditions.",
                    "erythema_ratio": round(erythema_ratio, 2),
                },
            })

        return ImageAnalysisOutput(
            status="SUCCESS",
            quality_gate="PASSED",
            quality_score=round(norm_quality, 2),
            quality_metrics=quality_metrics,
            visual_observations=observations,
            reasons=[],
            actionable_guidance=[],
            recommendation=(
                "Image successfully verified. Visual observations have been added "
                "to the health assessment context."
            ),
            engine_version=self.ENGINE_VERSION,
        )
