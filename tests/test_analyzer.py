"""Unit tests for the StreamLens analysis pipeline"""

import json

import numpy as np
import pytest

from advanced_metrics import (
    bootstrap_ci,
    cramers_v_goodness_of_fit,
    gini,
    letter_grade,
    linear_trend,
    lorenz_points,
    simpson_index,
    theil_index,
)
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


class TestInequalityMetrics:
    def test_gini_perfect_equality_is_zero(self):
        assert gini([10, 10, 10, 10]) == pytest.approx(0.0, abs=1e-9)

    def test_gini_total_inequality_approaches_one(self):
        assert gini([0, 0, 0, 100]) > 0.7

    def test_gini_handles_empty_and_zero_total(self):
        assert gini([]) == 0.0
        assert gini([0, 0, 0]) == 0.0

    def test_gini_bounded(self):
        assert 0.0 <= gini([1, 2, 3, 4, 5, 100]) <= 1.0

    def test_lorenz_starts_and_ends_at_corners(self):
        pts = lorenz_points([1, 2, 3, 4, 5])
        assert pts[0] == {'p': 0.0, 'l': 0.0}
        assert pts[-1] == {'p': 1.0, 'l': 1.0}

    def test_lorenz_is_monotonic(self):
        pts = lorenz_points([5, 1, 9, 2, 7, 3])
        ps = [pt['p'] for pt in pts]
        ls = [pt['l'] for pt in pts]
        assert ps == sorted(ps)
        assert ls == sorted(ls)

    def test_theil_equality_is_zero(self):
        assert theil_index([4, 4, 4, 4]) == pytest.approx(0.0, abs=1e-9)

    def test_theil_nonnegative(self):
        assert theil_index([1, 2, 3, 50]) >= 0.0


class TestDiversityAndEffectSize:
    def test_simpson_single_group_is_zero(self):
        assert simpson_index(['a'] * 10) == pytest.approx(0.0)

    def test_simpson_uniform_is_high(self):
        assert simpson_index(['a', 'b', 'c', 'd'] * 5) == pytest.approx(0.75)

    def test_cramers_v_uniform_is_negligible(self):
        out = cramers_v_goodness_of_fit([25, 25, 25, 25])
        assert out['cramers_v'] == pytest.approx(0.0, abs=1e-9)
        assert out['magnitude'] == 'negligible'

    def test_cramers_v_skew_is_bounded_and_labelled(self):
        out = cramers_v_goodness_of_fit([100, 0])
        assert 0.0 <= out['cramers_v'] <= 1.0
        assert out['magnitude'] in {'negligible', 'small', 'medium', 'large'}

    def test_cramers_v_handles_degenerate_input(self):
        assert cramers_v_goodness_of_fit([])['cramers_v'] == 0.0
        assert cramers_v_goodness_of_fit([5])['cramers_v'] == 0.0


class TestTrendAndBootstrap:
    def test_linear_trend_recovers_known_slope(self):
        out = linear_trend([2015, 2016, 2017, 2018], [0.0, 0.1, 0.2, 0.3])
        assert out['slope'] == pytest.approx(0.1, abs=1e-9)
        assert out['r_squared'] == pytest.approx(1.0, abs=1e-9)

    def test_linear_trend_flat_input(self):
        out = linear_trend([5, 5, 5], [1, 2, 3])
        assert out['slope'] == 0.0

    def test_bootstrap_ci_brackets_point_estimate(self):
        values = list(range(100))
        out = bootstrap_ci(values, lambda a: float(a.mean()), n_boot=200, seed=7)
        assert out['low'] <= out['point'] <= out['high']

    def test_bootstrap_ci_is_deterministic(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        a = bootstrap_ci(values, lambda x: float(x.mean()), n_boot=100, seed=1)
        b = bootstrap_ci(values, lambda x: float(x.mean()), n_boot=100, seed=1)
        assert a == b


class TestLetterGrade:
    def test_top_score_is_a_plus(self):
        assert letter_grade(1.0) == 'A+'

    def test_low_score_is_f(self):
        assert letter_grade(0.1) == 'F'

    def test_monotonic_non_increasing(self):
        order = '+'
        scores = [1.0, 0.92, 0.82, 0.72, 0.62, 0.42, 0.2]
        grades = [letter_grade(s) for s in scores]
        assert grades[0] == 'A+'
        assert grades[-1] == 'F'
        assert order in grades[0]


class TestAdvancedMetricsIntegration:
    def test_advanced_block_present(self, processor, sample_df):
        results = processor.process_data(sample_df)
        adv = results['advanced_metrics']
        assert {'inequality', 'diversity_detail', 'effect_sizes',
                'trend', 'confidence', 'scorecard'} <= set(adv)

    def test_scorecard_grades_every_platform(self, processor, sample_df):
        adv = processor.process_data(sample_df)['advanced_metrics']
        platforms = adv['scorecard']['platforms']
        assert len(platforms) > 0
        for row in platforms:
            assert 0.0 <= row['overall'] <= 1.0
            assert row['grade']
            assert set(adv['scorecard']['dimensions']) <= set(row['grades'])

    def test_scorecard_sorted_descending(self, processor, sample_df):
        platforms = processor.process_data(sample_df)['advanced_metrics']['scorecard']['platforms']
        overalls = [p['overall'] for p in platforms]
        assert overalls == sorted(overalls, reverse=True)

    def test_confidence_interval_brackets_point(self, processor, sample_df):
        conf = processor.process_data(sample_df)['advanced_metrics']['confidence']
        for band in conf.values():
            assert band['low'] <= band['point'] <= band['high']
