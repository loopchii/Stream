"""Tests for the real-data music virality pipeline and API endpoints.

Covers the statistical helpers (Gini edge cases, power-law MLE), the full
pipeline (load + feature engineering + analysis), and the FastAPI music routes.
"""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import app
from music_decision_lab import build_decision_lab
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
    quality_report,
    resonance_analysis,
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
        assert "published_year_source" in songs[0]
        assert "vitality_score" in songs[0]
        assert "cultural_corridor" in songs[0]
        assert len(songs[0]["signature"]) >= 2

    def test_bias_analysis(self, df):
        b = bias_analysis(df)
        assert 0.0 <= b["gender"]["gender_parity"] <= 1.0
        assert b["gender"]["counts"]["female"] > 0
        assert b["gender"]["counts"]["male"] > 0
        assert b["genres"]["gini"] >= 0.0
        assert len(b["genre_breakdown"]) > 0
        assert b["collaboration"]["collab_count"] >= 0
        assert b["concentration"]["top5_share"] > 0
        assert "years" in b["publication_timeline"]
        years = b["publication_timeline"]["years"]
        assert years == list(range(years[0], years[-1] + 1))
        assert "missing_years" in b["publication_timeline"]
        assert {'artist', 'consumer', 'business', 'research'} <= set(b["role_perspectives"])
        assert b["role_perspectives"]["artist"]["question"]
        assert len(b["role_perspectives"]["artist"]["next_moves"]) >= 2
        assert b["role_perspectives"]["research"]["next_moves"][0]["target"]
        assert b["overall_grade"]

    def test_quality_report(self, df):
        q = quality_report(df)
        assert "cohorts" in q
        assert q["cohorts"]["core_top_100"]["songs"] >= 80
        assert q["cohorts"]["enriched_context"]["songs"] >= q["cohorts"]["core_top_100"]["songs"]
        assert len(q["source_audit"]) >= 1
        assert len(q["cleaning_steps"]) >= 3
        assert q["model_rigor"]["cv_folds"] == 5
        assert len(q["feature_manifest"]) >= 1
        assert q["coverage"]["publication_year_explicit_share"] >= 0.0
        assert q["coverage"]["publication_year_inferred_share"] >= 0.0
        assert q["coverage"]["genre_known_share"] >= 0.8
        assert len(q["coverage"]["genre_signal_sources"]) >= 2

    def test_primary_dataset_carries_year_hints(self, df):
        assert int((df["published_year"] > 0).sum()) >= 30

    def test_archetypes_have_followers(self, df):
        a = archetype_analysis(df)
        for pt in a["points"]:
            assert "followers" in pt
            assert pt["followers"] > 0

    def test_full_report(self, df):
        r = full_report(df)
        expected_keys = [
            "overview", "power_law", "inequality", "correlations",
            "archetypes", "network", "predictability", "resonance", "songs", "bias", "quality", "living_media",
        ]
        for k in expected_keys:
            assert k in r
        assert "metrics" in r["living_media"]
        assert "origin_detector" in r["living_media"]
        assert "bias_spectrum" in r["living_media"]
        assert "authenticity_profiles" in r["living_media"]
        assert "propagation_chain" in r["living_media"]
        assert len(r["living_media"]["metrics"]) >= 5
        assert len(r["living_media"]["origin_detector"]) >= 5
        assert len(r["living_media"]["bias_spectrum"]) >= 6
        assert len(r["living_media"]["somatic_profiles"]) >= 3
        assert len(r["living_media"]["provocations"]) >= 2

    def test_resonance(self, df):
        r = resonance_analysis(df)
        assert "scorecard" in r
        assert "top_tracks" in r
        assert "genre_pressure" in r
        assert "year_profile" in r
        assert r["scorecard"]["oscillation"] >= 0.0
        assert r["scorecard"]["stability"] >= 0.0
        assert "vitality" in r["scorecard"]
        assert "song_count" in r["year_profile"]
        assert "vitality" in r["year_profile"]
        if r["top_tracks"]:
            assert "somatic_pull" in r["top_tracks"][0]
            assert "vitality_score" in r["top_tracks"][0]
            assert "cultural_corridor" in r["top_tracks"][0]
            assert len(r["top_tracks"][0]["signature"]) >= 2

    def test_decision_lab(self, df):
        d = build_decision_lab(df)
        assert "drift" in d
        assert "experiments" in d
        assert "trust" in d
        assert "embodied" in d
        assert "cards" in d["experiments"]
        assert len(d["experiments"]["cards"]) >= 4
        assert "headline" in d["summary"]
        assert "summary_cards" in d["embodied"]
        assert "top_signatures" in d["embodied"]
        assert "cultural_corridors" in d["embodied"]
        assert "provocations" in d["embodied"]
        assert len(d["embodied"]["summary_cards"]) >= 4
        assert len(d["embodied"]["provocations"]) >= 2


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

    def test_resonance(self, client):
        res = client.get("/api/music/resonance")
        assert res.status_code == 200
        body = res.json()
        assert "scorecard" in body
        assert "top_tracks" in body

    def test_songs(self, client):
        res = client.get("/api/music/songs?limit=5")
        assert res.status_code == 200
        body = res.json()
        assert len(body) == 5
        assert "vitality_score" in body[0]
        assert "cultural_corridor" in body[0]
        assert "authenticity_index" in body[0]
        assert "engineered_signature" in body[0]

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
        assert "genre_breakdown" in d
        assert "publication_timeline" in d
        assert "overall_grade" in d

    def test_quality(self, client):
        res = client.get("/api/music/quality")
        assert res.status_code == 200
        body = res.json()
        assert "cohorts" in body
        assert "source_audit" in body
        assert "guardrails" in body

    def test_decision_lab_surface(self, client):
        res = client.get("/api/music/decision-lab")
        assert res.status_code == 200
        body = res.json()
        assert "drift" in body
        assert "experiments" in body
        assert "trust" in body
        assert "embodied" in body

    def test_living_media_surface(self, client):
        res = client.get("/api/music/living-media")
        assert res.status_code == 200
        body = res.json()
        assert "metrics" in body
        assert "somatic_profiles" in body
        assert "cultural_ecology" in body
        assert "origin_detector" in body
        assert "bias_spectrum" in body
        assert "authenticity_profiles" in body
        assert "propagation_chain" in body
        assert len(body["metrics"]) >= 5

        res = client.get("/api/music/intelligence")
        assert res.status_code == 200
        body = res.json()
        assert "living_media" in body

    def test_genres(self, client):
        res = client.get("/api/music/genres")
        assert res.status_code == 200
        rows = res.json()
        assert len(rows) > 0
        assert {"genre", "song_count", "view_share", "avg_views", "avg_duration_min", "collab_share"} <= set(rows[0])
        assert any(row["genre"] == "Latin" for row in rows)
        assert any(row["genre"] == "Pop" for row in rows)

    def test_timeline(self, client):
        res = client.get("/api/music/timeline")
        assert res.status_code == 200
        body = res.json()
        assert "years" in body

    def test_music_index_carries_genre(self, client):
        res = client.get("/api/music/index", params={"limit": 10})
        assert res.status_code == 200
        body = res.json()
        assert body["count"] == 10
        assert any(item.get("genre") for item in body["items"])

    def test_refresh_no_key(self, client):
        res = client.post("/api/music/refresh")
        assert res.status_code == 503
