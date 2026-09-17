from django.contrib import admin

from .models import DocumentExtraction, DocumentProcessingJob, DocumentChunk, DocumentVisualAnalysis


@admin.register(DocumentProcessingJob)
class DocumentProcessingJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "status",
        "attempt_number",
        "started_at",
        "completed_at",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "document__original_file_name",
        "document__s3_key",
        "error_message",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(DocumentExtraction)
class DocumentExtractionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "extraction_method",
        "extractor_version",
        "character_count",
        "extracted_at",
    )

    list_filter = (
        "extraction_method",
        "extractor_version",
    )

    search_fields = (
        "document__original_file_name",
        "extracted_text",
    )

    readonly_fields = (
        "extracted_at",
        "updated_at",
    )

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "chunk_index",
        "character_count",
        "start_character",
        "end_character",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "document__original_file_name",
        "text",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

@admin.register(DocumentVisualAnalysis)
class DocumentVisualAnalysisAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "document",
        "model_name",
        "analyzed_at",
        "created_at",
    )

    list_filter = (
        "model_name",
        "created_at",
    )

    search_fields = (
        "document__original_file_name",
        "summary",
    )

    readonly_fields = (
        "analyzed_at",
        "created_at",
        "updated_at",
    )