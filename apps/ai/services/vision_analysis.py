from django.utils import timezone

from ..models import DocumentExtraction, ExtractionMethod, DocumentVisualAnalysis
from ..vision.huggingface import HuggingFaceVisionProvider


class DocumentVisualAnalysisService:
    def __init__(self):
        self.provider = (
            HuggingFaceVisionProvider()
        )

    def analyze(
        self,
        *,
        document,
    ) -> DocumentVisualAnalysis:

        result = self.provider.analyze_storage_image(
            storage_key=document.s3_key,
            content_type=document.content_type,
        )

        summary = self._build_text_representation(
            result
        )

        analysis, _ = (
            DocumentVisualAnalysis.objects
            .get_or_create(
                document=document,
            )
        )

        analysis.analysis = result

        analysis.summary = summary

        analysis.model_name = (
            self.provider.MODEL_NAME
        )

        analysis.analyzed_at = timezone.now()

        analysis.save()

        # Make the visual analysis available to
        # the existing chunking pipeline.
        DocumentExtraction.objects.update_or_create(
            document=document,
            defaults={
                "extracted_text": summary,
                "extraction_method": (
                    ExtractionMethod.VISION
                ),
                "extractor_version": (
                    "huggingface-vision-v1"
                ),
                "character_count": len(summary),
            },
        )

        return analysis

    @staticmethod
    def _build_text_representation(
        result: dict,
    ) -> str:

        lines = []

        lines.append(
            "IMAGE SUMMARY"
        )

        lines.append(
            result["image_summary"]
        )

        lines.append(
            "\nVEHICLE DETECTED"
        )

        lines.append(
            "Yes"
            if result["vehicle_detected"]
            else "No"
        )

        lines.append(
            "\nDAMAGE AREAS"
        )

        for item in result[
            "damage_areas"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nVISIBLE OBJECTS"
        )

        for item in result[
            "visible_objects"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nVISIBLE TEXT"
        )

        for item in result[
            "visible_text"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nOBSERVATIONS"
        )

        for item in result[
            "observations"
        ]:
            lines.append(
                f"- {item}"
            )

        lines.append(
            "\nLIMITATIONS"
        )

        for item in result[
            "limitations"
        ]:
            lines.append(
                f"- {item}"
            )

        return "\n".join(lines).strip()
