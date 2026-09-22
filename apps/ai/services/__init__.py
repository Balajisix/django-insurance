"""
AI business services, split by responsibility.

This package replaces the former single ``services.py`` module.
Everything that used to be importable as ``apps.ai.services.<Name>``
is re-exported here unchanged, so existing imports such as::

    from .services import ClaimAISummaryService

continue to work without modification.
"""

from .chunking import DocumentChunkingService
from .embedding import DocumentEmbeddingService
from .inconsistency import ClaimInconsistencyService
from .intelligence import ClaimAIIntelligenceService
from .missing_documents import MissingDocumentService
from .processing import DocumentProcessingService
from .rag import RAGService
from .retrieval import DocumentRetrievalService, RAGContextBuilder
from .summary import ClaimAISummaryService
from .summary_context import ClaimSummaryContextBuilder
from .vision_analysis import DocumentVisualAnalysisService
from .workflow import ClaimAIWorkflowService

__all__ = [
    "ClaimAIIntelligenceService",
    "ClaimAISummaryService",
    "ClaimAIWorkflowService",
    "ClaimInconsistencyService",
    "ClaimSummaryContextBuilder",
    "DocumentChunkingService",
    "DocumentEmbeddingService",
    "DocumentProcessingService",
    "DocumentRetrievalService",
    "DocumentVisualAnalysisService",
    "MissingDocumentService",
    "RAGContextBuilder",
    "RAGService",
]
