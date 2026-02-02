"""Dependency injection for FastAPI."""

from functools import lru_cache

from peakflow.pipeline.orchestrator import PipelineOrchestrator


@lru_cache
def get_orchestrator() -> PipelineOrchestrator:
    """Get singleton instance of pipeline orchestrator."""
    return PipelineOrchestrator()


def get_orchestrator_no_llm() -> PipelineOrchestrator:
    """Get orchestrator without LLM for testing."""
    return PipelineOrchestrator(use_llm=False)
