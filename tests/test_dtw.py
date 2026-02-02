"""Tests for Stage 5: DTW Alignment."""

import numpy as np
import pytest

from peakflow.models.enums import Phase
from peakflow.pipeline.stage5_dtw import (
    attention_weighted_distance,
    dtw_align,
    compute_deviations,
    get_attention_weights,
)


class TestAttentionWeightedDistance:
    """Tests for weighted distance calculation."""

    def test_zero_distance_identical_vectors(self):
        """Test that identical vectors have zero distance."""
        vec = np.array([1.0, 2.0, 3.0])
        weights = np.ones(3)
        dist = attention_weighted_distance(vec, vec, weights)
        assert dist == pytest.approx(0.0)

    def test_distance_with_weights(self):
        """Test that weights affect distance calculation."""
        vec1 = np.array([0.0, 0.0])
        vec2 = np.array([1.0, 1.0])

        # Equal weights
        weights_equal = np.array([1.0, 1.0])
        dist_equal = attention_weighted_distance(vec1, vec2, weights_equal)

        # Higher weight on first dimension
        weights_first = np.array([2.0, 1.0])
        dist_first = attention_weighted_distance(vec1, vec2, weights_first)

        # Weighted distance should be higher with higher weights
        assert dist_first > dist_equal

    def test_distance_symmetric(self):
        """Test that distance is symmetric."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([4.0, 5.0, 6.0])
        weights = np.array([1.0, 0.5, 2.0])

        dist_forward = attention_weighted_distance(vec1, vec2, weights)
        dist_backward = attention_weighted_distance(vec2, vec1, weights)

        assert dist_forward == pytest.approx(dist_backward)


class TestDTWAlign:
    """Tests for DTW alignment."""

    def test_identical_sequences(self):
        """Test DTW alignment of identical sequences."""
        seq = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]])

        result = dtw_align(seq, seq)

        # Path should be diagonal for identical sequences
        assert len(result.path) == 3
        assert result.path == [(0, 0), (1, 1), (2, 2)]
        assert result.total_cost == pytest.approx(0.0)

    def test_different_length_sequences(self):
        """Test DTW alignment of sequences with different lengths."""
        user_seq = np.array([[1.0], [2.0], [3.0], [4.0]])
        pro_seq = np.array([[1.5], [3.5]])

        result = dtw_align(user_seq, pro_seq)

        # Should have a valid alignment path
        assert len(result.path) > 0
        # Path should cover both sequences
        user_indices = [p[0] for p in result.path]
        pro_indices = [p[1] for p in result.path]
        assert max(user_indices) == len(user_seq) - 1
        assert max(pro_indices) == len(pro_seq) - 1

    def test_dtw_with_weights(self):
        """Test that weights affect DTW cost."""
        user_seq = np.array([[1.0, 0.0], [2.0, 0.0]])
        pro_seq = np.array([[1.0, 1.0], [2.0, 1.0]])

        # Higher weight on second dimension
        weights_high = np.array([0.1, 1.0])
        result_high = dtw_align(user_seq, pro_seq, weights_high)

        # Lower weight on second dimension
        weights_low = np.array([1.0, 0.1])
        result_low = dtw_align(user_seq, pro_seq, weights_low)

        # Cost should be higher when the differing dimension has higher weight
        assert result_high.total_cost > result_low.total_cost

    def test_normalized_cost(self):
        """Test that normalized cost is computed correctly."""
        seq1 = np.array([[1.0], [2.0], [3.0]])
        seq2 = np.array([[1.5], [2.5], [3.5]])

        result = dtw_align(seq1, seq2)

        # Normalized cost should be total cost / path length
        expected_normalized = result.total_cost / len(result.path)
        assert result.normalized_cost == pytest.approx(expected_normalized)


class TestComputeDeviations:
    """Tests for deviation analysis."""

    def test_deviation_analysis_structure(self):
        """Test that deviation analysis returns correct structure."""
        user_seq = np.array([
            [150.0, 160.0, 140.0, 10.0, 45.0, 45.0, 0.5],
            [145.0, 155.0, 135.0, 15.0, 50.0, 50.0, 0.4],
            [140.0, 150.0, 130.0, 20.0, 55.0, 55.0, 0.3],
        ])
        pro_seq = np.array([
            [160.0, 170.0, 150.0, 5.0, 40.0, 40.0, 0.6],
            [155.0, 165.0, 145.0, 10.0, 45.0, 45.0, 0.5],
            [150.0, 160.0, 140.0, 15.0, 50.0, 50.0, 0.4],
        ])

        alignment = dtw_align(user_seq, pro_seq)
        deviations = compute_deviations(user_seq, pro_seq, alignment, fps=30.0)

        # Check structure
        assert deviations.primary_error is not None
        assert 0.0 <= deviations.severity <= 1.0
        assert deviations.phase in [Phase.ENTRY, Phase.LOADING, Phase.DRIVE, Phase.EXIT]
        assert len(deviations.joint_deviations) == 7  # 7 features

    def test_zero_deviation_identical_sequences(self):
        """Test that identical sequences have zero deviation."""
        seq = np.array([
            [150.0, 160.0, 140.0, 10.0, 45.0, 45.0, 0.5],
            [145.0, 155.0, 135.0, 15.0, 50.0, 50.0, 0.4],
        ])

        alignment = dtw_align(seq, seq)
        deviations = compute_deviations(seq, seq, alignment, fps=30.0)

        # All deviations should be approximately zero
        for jd in deviations.joint_deviations:
            assert jd.mean_deviation == pytest.approx(0.0, abs=0.01)
            assert jd.max_deviation == pytest.approx(0.0, abs=0.01)


class TestGetAttentionWeights:
    """Tests for attention weights retrieval."""

    def test_weights_shape(self):
        """Test that weights have correct shape."""
        weights = get_attention_weights()
        assert len(weights) == 7  # 7 features

    def test_weights_positive(self):
        """Test that all weights are positive."""
        weights = get_attention_weights()
        assert all(w > 0 for w in weights)
