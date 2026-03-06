"""
Main pipeline orchestrator.
Coordinates all stages and handles errors gracefully.
"""

import time
from pathlib import Path

from peakflow.config import settings
from peakflow.models.schemas import AnalysisResult, GatingResult
from peakflow.pipeline.stage1_gating import run_gating
from peakflow.pipeline.stage2_context import ContextDetector
from peakflow.pipeline.stage3_pose import PoseExtractor
from peakflow.pipeline.stage4_matching import ReferenceMatcher
from peakflow.pipeline.stage5_dtw import (
    extract_feature_sequence,
    dtw_align,
    compute_deviations,
    get_attention_weights,
)
from peakflow.pipeline.stage6_feedback import FeedbackGenerator


class PipelineOrchestrator:
    """Orchestrates the full analysis pipeline."""

    def __init__(self, use_llm: bool = True):
        """
        Initialize the pipeline.

        Args:
            use_llm: Whether to use Claude API for feedback generation.
                     If False, uses rule-based fallback feedback.
        """
        self.use_llm = use_llm
        self._pose_extractor = None
        self._context_detector = None
        self._reference_matcher = None
        self._feedback_generator = None

    @property
    def pose_extractor(self) -> PoseExtractor:
        """Lazy load pose extractor (loads YOLO + MediaPipe models)."""
        if self._pose_extractor is None:
            self._pose_extractor = PoseExtractor()
        return self._pose_extractor

    @property
    def context_detector(self) -> ContextDetector:
        """Lazy load context detector."""
        if self._context_detector is None:
            self._context_detector = ContextDetector()
        return self._context_detector

    @property
    def reference_matcher(self) -> ReferenceMatcher:
        """Lazy load reference matcher."""
        if self._reference_matcher is None:
            self._reference_matcher = ReferenceMatcher()
        return self._reference_matcher

    @property
    def feedback_generator(self) -> FeedbackGenerator:
        """Lazy load feedback generator."""
        if self._feedback_generator is None:
            self._feedback_generator = FeedbackGenerator()
        return self._feedback_generator

    def analyze(self, video_path: str | Path) -> AnalysisResult:
        """
        Run full analysis pipeline.
        Fails fast at each stage with informative errors.
        """
        start_time = time.time()
        video_path = str(video_path)

        # Initialize result
        result = AnalysisResult(
            video_path=video_path,
            gating=GatingResult(passed=False),
            processing_time_ms=0,
        )

        # Stage 1: Gating
        gating = run_gating(video_path)
        result.gating = gating

        if not gating.passed:
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 3: Pose extraction (includes person detection)
        pose_sequence, rejection = self.pose_extractor.process_video(video_path)

        if rejection:
            result.gating.passed = False
            result.gating.rejection_reason = rejection
            from peakflow.pipeline.stage1_gating import get_rejection_message
            result.gating.rejection_message = get_rejection_message(rejection)
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        result.pose_sequence = pose_sequence

        # Stage 2: Context detection
        context = self.context_detector.detect(pose_sequence)
        result.context = context

        # Stage 4: Reference matching
        user_embedding = self.reference_matcher.compute_embedding(pose_sequence)
        match_result = self.reference_matcher.match(
            user_embedding, stance=context.stance, direction=context.direction
        )
        result.match = match_result

        if not match_result.matched_references:
            # No matching references - skip DTW but still generate basic feedback
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 5: DTW alignment
        best_ref = match_result.matched_references[0]
        pro_poses = self.reference_matcher.load_reference_poses(best_ref)

        if pro_poses:
            user_features = extract_feature_sequence(pose_sequence, context.stance.value)
            pro_features = extract_feature_sequence(pro_poses, context.stance.value)

            weights = get_attention_weights()
            alignment = dtw_align(user_features, pro_features, weights)
            deviation = compute_deviations(
                user_features, pro_features, alignment, pose_sequence.fps
            )
            result.deviation = deviation

            # Stage 6: Feedback
            if self.use_llm and settings.ANTHROPIC_API_KEY:
                try:
                    feedback = self.feedback_generator.generate(
                        deviation=deviation,
                        context=context,
                        style_cluster=match_result.style_cluster,
                        match=match_result,
                    )
                except Exception:
                    feedback = self.feedback_generator.generate_fallback(
                        deviation=deviation,
                        context=context,
                        match=match_result,
                    )
            else:
                feedback = self.feedback_generator.generate_fallback(
                    deviation=deviation,
                    context=context,
                    match=match_result,
                )
            result.feedback = feedback

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def analyze_quick(self, video_path: str | Path) -> AnalysisResult:
        """
        Run quick analysis (gating + pose only).
        Useful for validation before full analysis.
        """
        start_time = time.time()
        video_path = str(video_path)

        result = AnalysisResult(
            video_path=video_path,
            gating=GatingResult(passed=False),
            processing_time_ms=0,
        )

        # Stage 1: Gating
        gating = run_gating(video_path)
        result.gating = gating

        if not gating.passed:
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 3: Pose extraction
        pose_sequence, rejection = self.pose_extractor.process_video(video_path)

        if rejection:
            result.gating.passed = False
            result.gating.rejection_reason = rejection
            from peakflow.pipeline.stage1_gating import get_rejection_message
            result.gating.rejection_message = get_rejection_message(rejection)
        else:
            result.pose_sequence = pose_sequence

            # Stage 2: Context detection (quick)
            context = self.context_detector.detect(pose_sequence)
            result.context = context

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result
