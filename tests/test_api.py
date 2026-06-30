"""API tests for the StreamLens FastAPI server"""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope='module')
def client():
    return TestClient(app)


def test_health(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'


def test_dashboard_served(client):
    res = client.get('/')
    assert res.status_code == 200
    assert 'Stream' in res.text


def test_results(client):
    res = client.get('/api/results')
    assert res.status_code == 200
    body = res.json()
    assert 'overall_metrics' in body
    assert 'temporal_analysis' in body


def test_overview(client):
    res = client.get('/api/metrics/overview')
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body['gender_parity'] <= 1


def test_characters_filtering(client):
    res = client.get('/api/characters', params={'platform': 'netflix', 'limit': 10})
    assert res.status_code == 200
    records = res.json()
    assert len(records) <= 10
    assert all(r['platform'] == 'netflix' for r in records)


def test_analyze_validates_input(client):
    res = client.post('/api/analyze', params={'n_samples': 10})
    assert res.status_code == 422


def test_analyze_runs(client):
    res = client.post('/api/analyze', params={'n_samples': 200})
    assert res.status_code == 200
    assert 'overall_metrics' in res.json()


def test_genres(client):
    res = client.get('/api/metrics/genres')
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) > 0
    assert {'genre', 'diversity', 'gender_parity', 'male_lead_share', 'dialogue_gap'} <= set(rows[0])


def test_media_types(client):
    res = client.get('/api/metrics/media')
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) > 0
    assert {'media_type', 'diversity', 'gender_parity', 'avg_sentiment', 'sample_size'} <= set(rows[0])


def test_music_quality_surface(client):
    res = client.get('/api/music/quality')
    assert res.status_code == 200
    body = res.json()
    coverage = body['coverage']
    assert 'publication_year_explicit_share' in coverage
    assert 'publication_year_inferred_share' in coverage


def test_music_timeline_surface(client):
    res = client.get('/api/music/timeline')
    assert res.status_code == 200
    body = res.json()
    assert 'years' in body
    assert 'missing_years' in body
    if body['years']:
        assert body['years'] == list(range(body['years'][0], body['years'][-1] + 1))


def test_platform_media_types(client):
    res = client.get('/api/metrics/platform-media')
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) > 0
    assert {'platform', 'media_type', 'diversity', 'gender_parity', 'avg_screen_time', 'avg_sentiment', 'lead_share', 'sample_size'} <= set(rows[0])


def test_characters_media_type_filter(client):
    res = client.get('/api/characters', params={'media_type': 'film', 'limit': 10})
    assert res.status_code == 200
    records = res.json()
    assert all(r['media_type'] == 'film' for r in records)


def test_bias_library(client):
    res = client.get('/api/bias-library')
    assert res.status_code == 200
    body = res.json()
    assert body['total'] >= 50
    assert all({'id', 'category', 'name', 'definition', 'example', 'why_it_matters', 'measured_here'}
               <= set(b) for b in body['items'])


def test_bias_library_category_filter(client):
    res = client.get('/api/bias-library', params={'category': 'gender'})
    assert res.status_code == 200
    body = res.json()
    assert body['total'] > 0
    assert all(b['category'] == 'gender' for b in body['items'])


def test_bias_dimensions(client):
    res = client.get('/api/metrics/bias')
    assert res.status_code == 200
    body = res.json()
    for key in ('age_bias', 'racial_dialogue_bias', 'sentiment_bias', 'screen_time_bias'):
        assert key in body
    for v in body['sentiment_bias'].values():
        assert 'avg_sentiment' in v and 'deviation_from_mean' in v


def test_network(client):
    res = client.get('/api/metrics/network')
    assert res.status_code == 200
    body = res.json()
    assert body['nodes'] > 0
    assert -1 <= body['gender_homophily'] <= 1


def test_intersectionality(client):
    res = client.get('/api/metrics/intersectionality', params={'limit': 5})
    assert res.status_code == 200
    body = res.json()
    assert len(body['most_underrepresented']) <= 5
    ratios = [g['ratio'] for g in body['most_underrepresented']]
    assert ratios == sorted(ratios)


def test_insights(client):
    res = client.get('/api/insights')
    assert res.status_code == 200
    insights = res.json()
    assert len(insights) > 0
    assert {'category', 'title', 'detail'} <= set(insights[0])


def test_lenses_catalog(client):
    res = client.get('/api/lenses/catalog')
    assert res.status_code == 200
    body = res.json()
    assert len(body['items']) >= 4
    assert {'lens_id', 'display_name', 'description'} <= set(body['items'][0])


def test_lenses_demo_stream(client):
    res = client.get('/api/lenses/demo-stream', params={'limit': 6})
    assert res.status_code == 200
    body = res.json()
    assert body['count'] <= 6
    assert len(body['items']) == body['count']
    if body['items']:
        assert {'record', 'finding_count', 'findings'} <= set(body['items'][0])


def test_media_lab_overview(client):
    res = client.get('/api/media-lab/overview')
    assert res.status_code == 200
    body = res.json()
    assert {'compulsive_usage', 'generative_guard', 'causal_map', 'events'} <= set(body)


def test_media_lab_compulsive_loop(client):
    res = client.get('/api/media-lab/compulsive-loop')
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body['risk_score'] <= 1
    assert body['recommended_friction_ms'] >= 0


def test_media_lab_generative_guard(client):
    res = client.get('/api/media-lab/generative-guard')
    assert res.status_code == 200
    body = res.json()
    assert body['blocked'] is True
    assert body['remaining_nonzero_bytes'] == 0


def test_media_lab_causal_map(client):
    res = client.get('/api/media-lab/causal-map')
    assert res.status_code == 200
    body = res.json()
    assert body['node_count'] > 0
    assert body['edge_count'] > 0


def test_learn(client):
    res = client.get('/api/learn')
    assert res.status_code == 200
    cards = res.json()
    assert len(cards) >= 5
    assert all({'title', 'summary', 'detail', 'try_it'} <= set(c) for c in cards)


def test_data_engineering_surface(client):
    res = client.get('/api/system/data-engineering')
    assert res.status_code == 200
    body = res.json()
    assert {'generated_at', 'operating_model', 'service_levels', 'delivery_surfaces', 'stages', 'lineage', 'reproducibility', 'contracts', 'quality_highlights'} <= set(body)
    assert body['operating_model']['dataset_count'] >= 2
    assert len(body['service_levels']) >= 4
    assert len(body['delivery_surfaces']) >= 3
    assert len(body['stages']) >= 4
    assert len(body['contracts']) >= 2
    assert body['reproducibility']['seed'] == 42
    assert len(body['reproducibility']['default_sample_sizes']) >= 4
    first_contract = body['contracts'][0]
    assert {'dataset_id', 'grain', 'primary_key', 'partition_keys', 'quality_checks', 'schema_profile', 'schema'} <= set(first_contract)
    assert len(first_contract['quality_checks']) >= 3
    assert len(first_contract['schema']) >= 5
    assert first_contract['schema_profile']['column_count'] >= 5


def test_governance_surface(client):
    res = client.get('/api/system/governance')
    assert res.status_code == 200
    body = res.json()
    assert {'summary', 'domains', 'questions', 'contribution_paths'} <= set(body)
    assert body['summary']['repository_mode'] == 'independent_open_source_surface'
    assert len(body['domains']) >= 5
    assert any(domain['id'] == 'gdpr_boundary' for domain in body['domains'])


def test_streaming_readiness_surface(client):
    res = client.get('/api/system/streaming-readiness')
    assert res.status_code == 200
    body = res.json()
    assert {'positioning', 'architecture_concerns', 'production_expectations_missing', 'roadmap'} <= set(body)
    assert body['positioning']['maturity_label'] == 'research_foundation_with_operational_signals'
    assert len(body['architecture_concerns']) >= 3
    assert len(body['production_expectations_missing']['runtime_guarantees']) >= 5
    assert len(body['roadmap']['quick_wins']) >= 3


def test_bias_propagation_surface(client):
    res = client.get('/api/system/bias-propagation')
    assert res.status_code == 200
    body = res.json()
    assert {'stages', 'roles', 'items', 'notes'} <= set(body)
    assert len(body['stages']) >= 6
    assert len(body['roles']) >= 4
    assert len(body['items']) >= 50
    first = body['items'][0]
    assert {'id', 'name', 'category', 'entry_stage', 'propagation_path', 'harm_profile', 'wave_profile', 'role_routes'} <= set(first)
    assert len(first['propagation_path']) >= 2
    assert {'creator', 'operator', 'buyer', 'public'} <= set(first['role_routes'])


def test_trojan_horse_surface(client):
    res = client.get('/api/system/trojan-horse')
    assert res.status_code == 200
    body = res.json()
    assert {'generated_at', 'headline', 'description', 'presets', 'package'} <= set(body)
    assert len(body['presets']) >= 5
    assert body['package']['name'] == '@loopchii/loopchii-lite'


def test_playground_simulate_blocks_pii(client):
    res = client.get('/api/playground/simulate', params={'prompt': 'Use the customer email export and phone list.'})
    assert res.status_code == 200
    body = res.json()
    assert body['blocked'] is True
    assert body['category'] == 'pii'
    assert body['governed_risky_tokens_rendered'] == 0


def test_export_has_download_header(client):
    res = client.get('/api/export')
    assert res.status_code == 200
    assert 'attachment' in res.headers['content-disposition']


def test_advanced_metrics(client):
    res = client.get('/api/metrics/advanced')
    assert res.status_code == 200
    body = res.json()
    assert {'inequality', 'diversity_detail', 'effect_sizes',
            'trend', 'confidence', 'scorecard'} <= set(body)
    assert 0 <= body['inequality']['screen_time']['gini'] <= 1
    assert body['inequality']['screen_time']['lorenz'][0] == {'p': 0.0, 'l': 0.0}


def test_scorecard(client):
    res = client.get('/api/metrics/scorecard')
    assert res.status_code == 200
    body = res.json()
    assert len(body['platforms']) > 0
    for row in body['platforms']:
        assert 0 <= row['overall'] <= 1
        assert row['grade']
    overalls = [p['overall'] for p in body['platforms']]
    assert overalls == sorted(overalls, reverse=True)


def test_simulate_parity_balanced(client):
    res = client.get('/api/simulate/parity', params={'female_ratio': 0.5})
    assert res.status_code == 200
    body = res.json()
    assert body['parity'] == pytest.approx(1.0)
    assert body['grade'] == 'A+'


def test_simulate_parity_extreme(client):
    res = client.get('/api/simulate/parity', params={'female_ratio': 0.0})
    assert res.status_code == 200
    assert res.json()['parity'] == pytest.approx(0.0)


def test_simulate_parity_validates_range(client):
    res = client.get('/api/simulate/parity', params={'female_ratio': 1.5})
    assert res.status_code == 422
