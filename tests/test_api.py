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
    assert 'StreamLens' in res.text


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


def test_learn(client):
    res = client.get('/api/learn')
    assert res.status_code == 200
    cards = res.json()
    assert len(cards) >= 5
    assert all({'title', 'summary', 'detail', 'try_it'} <= set(c) for c in cards)


def test_export_has_download_header(client):
    res = client.get('/api/export')
    assert res.status_code == 200
    assert 'attachment' in res.headers['content-disposition']
