"""Tests for the real-data music virality pipeline and API endpoints.

Covers the statistical helpers (Gini edge cases, power-law MLE), the full
pipeline (load + feature engineering + analysis), and the FastAPI music routes.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import app
from music_pipeline import (
    archetype_analysis,
    bias_analysis,
    correlation_analysis,
    full_report,
    gini,
    inequality_analysis,
    load_dataset,
    mle_alpha,
    network_analysis,
    overview,
    power_law_analysis,
    predictability_analysis,
    simulate_grid,
    simulate_virality,
    songs_table,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def df():
    return load_dataset()


# --------------------------------------------------------------------------- #
# Statistical helpers
# --------------------------------------------------------------------------- #
class TestGini:
    def test_all_equal(self):
        assert gini([1, 1, 1, 1]) == 0.0

    def test_all_zero(self):
        assert gini([0, 0, 0]) == 0.0

    def test_empty(self):
        assert gini([]) == 0.0

    def test_known(self):
        g = gini([0, 0, 1, 1])
        assert 0.45 <= g <= 0.55

    def test_maximal(self):
        g = gini([0, 0, 0, 100])
        assert g > 0.7


class TestPowerLawMLE:
    def test_known_pareto(self):
        rng = np.random.default_rng(0)
        alpha_true = 2.5
        xmin = 1.0
        u = rng.random(5000)
        x = xmin * (u ** (-1.0 / (alpha_true - 1.0)))
        alpha_hat = mle_alpha(x, xmin)
        assert 2.2 < alpha_hat < 2.8

    def test_empty(self):
        assert mle_alpha([], 1.0) == 0.0

    def test_all_below_xmin(self):
        assert mle_alpha([0.1, 0.2, 0.3], 1.0) == 0.0


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
class TestPipeline:
    def test_load(self, df):
        assert len(df) > 0
        assert "view_count" in df.columns
        assert "virality_coefficient" in df.columns

    def test_overview(self, df):
        o = overview(df)
        assert o["n_songs"] >= 80
        assert o["total_views"] > 1e9
        assert o["n_channels"] > 10
        assert "data_source" in o

    def test_power_law(self, df):
        p = power_law_analysis(df)
        assert "alpha" in p
        assert p["alpha"] > 1.0
        assert "alpha_ci" in p
        assert len(p["ccdf"]) > 0

    def test_inequality(self, df):
        ineq = inequality_analysis(df)
        assert 0.0 <= ineq["gini"] <= 1.0
        assert ineq["theil"] >= 0.0
        assert len(ineq["lorenz"]) > 2
        assert ineq["top3_channel_share"] > 0

    def test_correlations(self, df):
        c = correlation_analysis(df)
        assert len(c["rows"]) > 0
        for row in c["rows"]:
            assert -1.0 <= row["spearman"] <= 1.0
            assert -1.0 <= row["partial_spearman"] <= 1.0

    def test_archetypes(self, df):
        a = archetype_analysis(df)
        total = sum(c["count"] for c in a["clusters"])
        assert total == len(df)
        assert len(a["points"]) == len(df)

    def test_network(self):
        n = network_analysis()
        assert n["n_nodes"] > 0
        assert n["n_edges"] >= 0

    def test_predictability(self, df):
        p = predictability_analysis(df)
        assert -1.0 <= p["ensemble_r2"] <= 1.0
        assert len(p["features"]) > 0

    def test_simulate_virality(self, df):
        s = simulate_virality(3.0, 5_000_000, 20, 1.0, df)
        assert "predicted_views" in s
        assert 0 <= s["percentile"] <= 100
        assert s["grade"]

    def test_simulate_grid(self, df):
        g = simulate_grid(df)
        assert len(g["grid"]) > 100
        for pt in g["grid"][:5]:
            assert "predicted_views" in pt
            assert "percentile" in pt

    def test_songs_table(self, df):
        songs = songs_table(df, limit=10)
        assert len(songs) == 10
        assert songs[0]["view_count"] >= songs[1]["view_count"]

    def test_bias_analysis(self, df):
        b = bias_analysis(df)
        assert 0.0 <= b["gender"]["gender_parity"] <= 1.0
        assert b["gender"]["counts"]["female"] > 0
        assert b["gender"]["counts"]["male"] > 0
        assert b["genres"]["gini"] >= 0.0
        assert b["collaboration"]["collab_count"] >= 0
        assert b["concentration"]["top5_share"] > 0
        assert b["overall_grade"]

    def test_archetypes_have_followers(self, df):
        a = archetype_analysis(df)
        for pt in a["points"]:
            assert "followers" in pt
            assert pt["followers"] > 0

    def test_full_report(self, df):
        r = full_report(df)
        expected_keys = [
            "overview", "power_law", "inequality", "correlations",
            "archetypes", "network", "predictability", "songs", "bias",
        ]
        for k in expected_keys:
            assert k in r


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #
class TestMusicAPI:
    def test_overview(self, client):
        res = client.get("/api/music/overview")
        assert res.status_code == 200
        assert res.json()["n_songs"] >= 80

    def test_powerlaw(self, client):
        res = client.get("/api/music/powerlaw")
        assert res.status_code == 200
        assert "alpha" in res.json()

    def test_inequality(self, client):
        res = client.get("/api/music/inequality")
        assert res.status_code == 200
        assert "gini" in res.json()

    def test_correlations(self, client):
        res = client.get("/api/music/correlations")
        assert res.status_code == 200
        assert "rows" in res.json()

    def test_archetypes(self, client):
        res = client.get("/api/music/archetypes")
        assert res.status_code == 200
        assert "clusters" in res.json()

    def test_network(self, client):
        res = client.get("/api/music/network")
        assert res.status_code == 200
        assert "n_nodes" in res.json()

    def test_predictability(self, client):
        res = client.get("/api/music/predictability")
        assert res.status_code == 200
        assert "ensemble_r2" in res.json()

    def test_songs(self, client):
        res = client.get("/api/music/songs?limit=5")
        assert res.status_code == 200
        assert len(res.json()) == 5

    def test_simulate(self, client):
        res = client.get(
            "/api/music/simulate?duration_min=3.5&channel_follower_count=10000000&tag_count=15"
        )
        assert res.status_code == 200
        d = res.json()
        assert "predicted_views" in d
        assert "percentile" in d

    def test_status(self, client):
        res = client.get("/api/music/status")
        assert res.status_code == 200
        assert "live_available" in res.json()

    def test_bias(self, client):
        res = client.get("/api/music/bias")
        assert res.status_code == 200
        d = res.json()
        assert "gender" in d
        assert "genres" in d
        assert "overall_grade" in d

    def test_refresh_no_key(self, client):
        res = client.post("/api/music/refresh")
        assert res.status_code == 503
