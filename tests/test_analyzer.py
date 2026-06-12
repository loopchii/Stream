"""Unit tests for the StreamLens analysis pipeline"""

import json

import numpy as np
import pytest

from streamlens_processor import (
    BiasDetector,
    DataProcessor,
    NetworkAnalyzer,
    RepresentationAnalyzer,
)


@pytest.fixture
def analyzer():
    return RepresentationAnalyzer()


@pytest.fixture
def processor():
    return DataProcessor()


@pytest.fixture
def sample_df(processor):
    return processor.generate_synthetic_data(n_samples=500)


class TestDiversityIndex:
    def test_empty_returns_zero(self, analyzer):
        assert analyzer.calculate_diversity_index([]) == 0

    def test_single_category_returns_zero(self, analyzer):
        assert analyzer.calculate_diversity_index(['white'] * 10) == 0

    def test_uniform_distribution_is_max(self, analyzer):
        result = analyzer.calculate_diversity_index(['a', 'b', 'c', 'd'] * 25)
        assert result == pytest.approx(1.0)

    def test_bounded_zero_one(self, analyzer):
        result = analyzer.calculate_diversity_index(['a'] * 90 + ['b'] * 10)
        assert 0 <= result <= 1


class TestGenderParity:
    def test_empty_returns_zero(self, analyzer):
        assert analyzer.calculate_gender_parity({}) == 0

    def test_perfect_parity(self, analyzer):
        assert analyzer.calculate_gender_parity({'male': 50, 'female': 50}) == pytest.approx(1.0)

    def test_complete_imbalance(self, analyzer):
        assert analyzer.calculate_gender_parity({'male': 100, 'female': 0}) == pytest.approx(0.0)


class TestBiasDetector:
    def test_dialogue_bias_empty_input(self):
        assert BiasDetector().detect_dialogue_bias({}) == {}

    def test_dialogue_bias_percentages_sum_to_100(self):
        biases = BiasDetector().detect_dialogue_bias(
            {'word_counts': {'male': 600, 'female': 400}}
        )
        total = sum(b['percentage'] for b in biases.values())
        assert total == pytest.approx(100.0)

    def test_role_stereotyping(self, sample_df):
        stereotypes = BiasDetector().detect_role_stereotyping(sample_df)
        assert stereotypes
        for data in stereotypes.values():
            assert 0 <= data['stereotype_score'] <= 1


class TestNetworkAnalyzer:
    def test_build_network(self):
        interactions = [
            {'character1': 'A', 'character2': 'B', 'weight': 2},
            {'character1': 'A', 'character2': 'B', 'weight': 1},
            {'character1': 'B', 'character2': 'C'},
        ]
        G = NetworkAnalyzer().build_character_network(interactions)
        assert G.number_of_nodes() == 3
        assert G['A']['B']['weight'] == 3

    def test_homophily_handles_missing_attribute(self):
        G = NetworkAnalyzer().build_character_network(
            [{'character1': 'A', 'character2': 'B'}]
        )
        assert NetworkAnalyzer().detect_homophily(G, 'gender') == 0.0


class TestDataProcessor:
    def test_synthetic_data_shape(self, sample_df):
        assert len(sample_df) == 500
        assert {'platform', 'genre', 'year', 'gender', 'race'} <= set(sample_df.columns)
        assert (sample_df['screen_time'] >= 0).all()
        assert (sample_df['dialogue_words'] >= 0).all()

    def test_process_data_structure(self, processor, sample_df):
        results = processor.process_data(sample_df)
        assert 'overall_metrics' in results
        assert 0 <= results['overall_metrics']['gender_parity'] <= 1

    def test_temporal_analysis_sorted(self, processor, sample_df):
        results = processor.process_data(sample_df)
        years = [r['year'] for r in results['temporal_analysis']]
        assert years == sorted(years)

    def test_export_is_json_serializable(self, processor, sample_df, tmp_path):
        results = processor.process_data(sample_df)
        out = tmp_path / 'results.json'
        clean = processor.export_results(results, filename=str(out))
        json.dumps(clean)
        assert out.exists()

    def test_export_converts_numpy_types(self, processor, tmp_path):
        results = {
            'int': np.int64(5),
            'float': np.float64(1.5),
            'bool': np.bool_(True),
            'array': np.array([1, 2]),
            'nested': {('a', 'b'): np.int32(1)},
        }
        clean = processor.export_results(results, filename=str(tmp_path / 'r.json'))
        json.dumps(clean)
        assert clean['int'] == 5
        assert clean['bool'] is True
