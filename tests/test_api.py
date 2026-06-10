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
