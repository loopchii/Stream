from __future__ import annotations

from typing import Any, Mapping


def _pct(value: Any, digits: int = 0) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "unknown"


def _num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "unknown"


def _compact_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "unknown"


def _section(
    title: str,
    purpose: str,
    learn: str,
    if_changes: str,
    improve: str,
    limits: str,
    scale: str,
) -> dict[str, str]:
    return {
        "title": title,
        "purpose": purpose,
        "learn": learn,
        "if_changes": if_changes,
        "improve": improve,
        "limits": limits,
        "scale": scale,
    }


def build_critical_spine(
    generated_at: str,
    sample_size: int,
    representation: Mapping[str, Any],
    music_report: Mapping[str, Any],
    music_index: Mapping[str, Any],
    data_engineering: Mapping[str, Any],
) -> dict[str, Any]:
    overall = representation.get("overall_metrics") or {}
    advanced = representation.get("advanced_metrics") or {}
    inequality = advanced.get("inequality") or {}
    screen_time_ineq = inequality.get("screen_time") or {}
    network = representation.get("network_metrics") or {}
    temporal = representation.get("temporal_analysis") or []
    first_year = temporal[0] if temporal else {}
    last_year = temporal[-1] if temporal else {}

    music_overview = music_report.get("overview") or {}
    music_bias = music_report.get("bias") or {}
    music_quality = music_report.get("quality") or {}
    music_predictability = music_report.get("predictability") or {}
    music_inequality = music_report.get("inequality") or {}
    music_resonance = music_report.get("resonance") or {}
    music_intel_summary = music_index.get("summary") or {}
    contracts = data_engineering.get("contracts") or []
    quality_highlights = data_engineering.get("quality_highlights") or []
    coverage = music_quality.get("coverage") or music_bias.get("coverage") or {}
    publication_year_share = coverage.get("publication_year_share") or coverage.get("publication_year_explicit_share")

    visuals = {
        "dashFieldMap": _section(
            title="Multi-dimensional bias field",
            purpose=(
                "Show whether imbalance is broad across the field or concentrated inside a smaller "
                "platform-genre pocket. This is the first orientation surface, not the final verdict."
            ),
            learn=(
                f"The current synthetic run tracks parity at {_num(overall.get('gender_parity'))} and diversity at "
                f"{_num(overall.get('diversity_index'))}. The bubble field matters because a healthy average can still "
                "hide a small cluster where power keeps narrowing."
            ),
            if_changes=(
                "If the upper-right cluster collapses when you change year, genre, or media type, the story is "
                "fragile. If it survives those slices, the signal is stronger and more portable."
            ),
            improve=(
                "Improve this read by increasing sample size, checking the row explorer, and confirming whether the "
                "same cluster holds in the network, timeline, and role pattern surfaces."
            ),
            limits=(
                "This view is synthetic and descriptive. It can show where to ask harder questions, but it cannot "
                "claim a real platform changed behavior without a real catalog lane."
            ),
            scale=(
                "For larger companies, treat this as a triage surface: which segment deserves audit time, budget, or "
                "human review first."
            ),
        ),
        "dashLandscape": _section(
            title="3D representation landscape",
            purpose=(
                "Stress-test the earlier field map in one extra dimension so a point that looked healthy in 2D can be "
                "challenged once another axis is visible."
            ),
            learn=(
                "This view is here to catch summary optimism. If a point keeps its position after a third axis is "
                "introduced, the signal is harder to dismiss as a charting artifact."
            ),
            if_changes=(
                "If the depth layer scrambles the earlier winners, your earlier explanation was under-specified. If "
                "the clusters stay coherent, the original story is more structurally sound."
            ),
            improve=(
                "Pair this with effect sizes and the decision grade. Three dimensions are useful, but they still need "
                "quality gates and confidence language."
            ),
            limits=(
                "3D is powerful for pattern separation but weaker for exact reading. The value is shape, not "
                "precision-by-eye."
            ),
            scale=(
                "Use it in reviews when you need one image that shows whether a claim survives dimensional pressure "
                "before it becomes an executive talking point."
            ),
        ),
        "dashNetwork": _section(
            title="Character interaction topology",
            purpose=(
                "Show whether representation gaps are also social-topology gaps: who gets clustered together, who "
                "gets isolated, and who becomes the center of narrative gravity."
            ),
            learn=(
                f"Current gender homophily is {_num(network.get('gender_homophily'))} with density "
                f"{_num(network.get('density'))}. That matters because visibility alone does not tell you whether the "
                "same groups keep inheriting the social center."
            ),
            if_changes=(
                "If homophily weakens once you change genre or platform, the exclusion point may be format-specific. "
                "If it stays high, the pattern is more structural."
            ),
            improve=(
                "Improve this analysis with more row depth, richer interaction definitions, and a comparison against "
                "dialogue share so centrality is not mistaken for speech power."
            ),
            limits=(
                "This is still a modeled graph. It helps reason about topology, but it is not evidence of actual "
                "writer-room intent."
            ),
            scale=(
                "At company scale, this is the surface that translates best into product, content, and policy review "
                "because it turns vague fairness claims into relationship structure."
            ),
        ),
        "dashTimeline": _section(
            title="Temporal evolution",
            purpose=(
                "Separate durable movement from one-year noise. A serious repository should show whether improvement "
                "is compounding, stalling, or just moving the imbalance elsewhere."
            ),
            learn=(
                f"The synthetic lane moves from parity {_num(first_year.get('gender_parity'))} to "
                f"{_num(last_year.get('gender_parity'))}. Read that beside diversity and sentiment, not as a single "
                "hero line."
            ),
            if_changes=(
                "If one metric improves while another stalls, the system is not truly getting better; it is changing "
                "where the pressure sits."
            ),
            improve=(
                "Improve this read with wider time coverage, documented gaps, and publication notes that explain "
                "whether the field is measuring releases, recirculation, or catalog resurfacing."
            ),
            limits=(
                "Trend lines are compelling, but they are only as honest as the date coverage beneath them."
            ),
            scale=(
                "This is the surface that helps a larger team decide whether to treat a finding as a blip, a trend, "
                "or a governance issue that deserves intervention."
            ),
        ),
        "dashRoles": _section(
            title="Role pattern surface",
            purpose=(
                "Reveal whether improvement at the top line is being canceled out by narrow role assignment underneath."
            ),
            learn=(
                "Typecasting matters because a catalog can look broad while still reserving agency, authority, or "
                "speech power for the same few archetypes."
            ),
            if_changes=(
                "If the role shape becomes balanced only in one platform or one genre, the system is not broadening; "
                "it is localizing the fix."
            ),
            improve=(
                "Improve this analysis by pairing role patterns with dialogue allocation, screen time, and "
                "intersectional ratios so role labels do not carry the whole claim alone."
            ),
            limits=(
                "Archetype labels compress nuance. They are useful for pattern detection, not for exhausting the "
                "meaning of a character."
            ),
            scale=(
                "This translates well for content and procurement teams because it explains how representation can "
                "look better on paper while staying narratively old."
            ),
        ),
        "exploreRows": _section(
            title="Row explorer",
            purpose=(
                "Give contributors and reviewers a direct path back to the evidence so the repo never asks for blind "
                "trust."
            ),
            learn=(
                f"The current runtime is carrying {_compact_int(representation.get('row_count', sample_size))} "
                "synthetic rows. This view matters because every persuasive summary should still be traceable to a "
                "row-level source."
            ),
            if_changes=(
                "If the row slice changes the story, the summary was oversold. That is a feature, not a failure."
            ),
            improve=(
                "Add pagination, stronger schema cues, and more comparison affordances so contributors can pressure "
                "the data faster."
            ),
            limits=(
                "Raw rows are necessary, but they do not explain themselves. They need contracts, quality checks, and "
                "honest labeling."
            ),
            scale=(
                "For larger teams this is where debugging, procurement review, and contributor onboarding start."
            ),
        ),
        "learnDataSystem": _section(
            title="Data engineering operating model",
            purpose=(
                "Explain how the pipeline behaves before anyone is asked to trust the visuals it produces."
            ),
            learn=(
                f"There are {len(contracts)} public contracts and {len(quality_highlights)} explicit quality "
                "highlights in the current system surface. That is the spine underneath the charts."
            ),
            if_changes=(
                "If quality gates fail or contracts drift, the visual layer should become less confident immediately."
            ),
            improve=(
                "Keep expanding lineage, refresh posture, and coverage notes so a contributor can see where a claim "
                "is strong, thin, or intentionally withheld."
            ),
            limits=(
                "Documentation can still drift if it is not regenerated from the same backend that serves the UI."
            ),
            scale=(
                "This is the part that makes the repo feel operational rather than theatrical to senior engineers and "
                "data leads."
            ),
        ),
        "scorecardVerdict": _section(
            title="Decision grade",
            purpose=(
                "Compress complexity into a usable decision signal only after the nuance has already been made visible."
            ),
            learn=(
                f"The current screen-time gini proxy is {_num(screen_time_ineq.get('gini'))}. The grade matters only "
                "because the repo lets a reader walk backward into the ingredients."
            ),
            if_changes=(
                "If a small shift flips the grade dramatically, the compression is too brittle and needs more context."
            ),
            improve=(
                "Keep effect sizes, trend fit, and caveats close to the grade so no one mistakes compression for full "
                "truth."
            ),
            limits=(
                "A grade is useful for decisions, not for understanding the full field. It should route someone into "
                "the evidence, not replace it."
            ),
            scale=(
                "This is the executive surface: fast to read, but only credible if the lower layers remain inspectable."
            ),
        ),
        "exploreMedia": _section(
            title="Media-format comparison",
            purpose=(
                "Separate platform effects from format effects so a pattern is not mistaken for a platform truth when it "
                "is actually being driven by animation, film, series, or reality structure."
            ),
            learn=(
                "This view exists to answer a practical question: does the pattern still hold once the media format "
                "changes, or was the original signal just hitching a ride on one production format?"
            ),
            if_changes=(
                "If the signal disappears when media type changes, the earlier claim needs to narrow. If it stays "
                "stable, the pattern is more portable."
            ),
            improve=(
                "Improve this lane with clearer cohort sizes, stronger notes about edge cases, and side-by-side "
                "confidence language for thin slices."
            ),
            limits=(
                "Format labels are useful but incomplete. They should guide follow-up analysis, not stand in for it."
            ),
            scale=(
                "For larger teams, this helps explain whether a problem belongs to the whole system or just one format lane."
            ),
        ),
        "exploreGenre": _section(
            title="Genre-specific pressure",
            purpose=(
                "Show where a broad claim starts to splinter once genre enters, because many fairness or virality stories "
                "turn out to be genre-specific rather than universal."
            ),
            learn=(
                "The value here is not only the averages. It is seeing whether one genre keeps absorbing the same "
                "advantage while other lanes behave very differently."
            ),
            if_changes=(
                "If a result flips direction across genres, the repo should stop speaking in global terms and get more exact."
            ),
            improve=(
                "Improve this with better genre coverage notes, more year-aware comparisons, and clearer handling of "
                "miscellaneous or unclassified rows."
            ),
            limits=(
                "Genre labels are noisy and culturally loaded. They are a useful organizing surface, not a perfect ontology."
            ),
            scale=(
                "This becomes a budgeting and programming surface when teams need to know which lanes are actually driving the issue."
            ),
        ),
        "insightsSignals": _section(
            title="Generated findings layer",
            purpose=(
                "Translate the analytical field into readable conclusions without severing those conclusions from their evidence."
            ),
            learn=(
                "These generated findings matter only when they stay traceable to filters, cohorts, and metrics. Their "
                "job is to shorten time-to-understanding, not replace inspection."
            ),
            if_changes=(
                "If the generated wording changes dramatically under a small slice adjustment, the finding is unstable and "
                "should be presented more cautiously."
            ),
            improve=(
                "Keep attaching confidence, sample shape, and contradiction checks so the writing stays honest instead of polished."
            ),
            limits=(
                "Plain-language summaries are convenient, but they can over-smooth complexity if they are not constantly tied back to structure."
            ),
            scale=(
                "For larger companies, this is the handoff layer between deep analysis and people who need to act on it quickly."
            ),
        ),
        "libraryPropagationStudio": _section(
            title="Bias propagation studio",
            purpose=(
                "Show how a pattern becomes a system: where a small skew enters, how it compounds, and why downstream "
                "surfaces can end up looking natural even when the starting point was not."
            ),
            learn=(
                "This is the explanatory spine for people who can sense that something feels off but need to see the chain "
                "from input to consequence."
            ),
            if_changes=(
                "If one propagation step dominates the whole story, that is the intervention point. If many small steps "
                "compound, the system needs layered correction rather than one patch."
            ),
            improve=(
                "Improve it by adding more counterfactual examples and clearer notes about where the repo is modeling versus directly observing."
            ),
            limits=(
                "Propagation diagrams can look more certain than they are. They should declare where the evidence is direct and where it is inferential."
            ),
            scale=(
                "This is useful for ethics, policy, and engineering audiences because it connects abstract harm to a tractable chain."
            ),
        ),
        "mvPowerLaw": _section(
            title="Power-law attention tail",
            purpose=(
                "Test whether attention is being distributed broadly or whether a tiny winner tail is doing most of "
                "the work."
            ),
            learn=(
                f"The real music lane covers {_compact_int(music_overview.get('n_songs'))} songs and {_compact_int(music_overview.get('total_views'))} views. "
                "The power-law fit matters because virality claims usually sound organic long after the field has "
                "already become tail-dominated."
            ),
            if_changes=(
                "If the tail gets steeper, breakout concentration is easing. If it gets heavier, scale and incumbent "
                "reach are doing more of the outcome shaping."
            ),
            improve=(
                "Improve this with wider cohorts, better year segmentation, and side-by-side cohort comparisons so one "
                "leaderboard does not stand in for a market."
            ),
            limits=(
                "A heavy tail is descriptive, not accusatory. It tells you how concentrated attention looks, not why "
                "any individual song won."
            ),
            scale=(
                "This is where larger companies can see whether discovery infrastructure is broadening the field or "
                "mainly amplifying incumbent advantage."
            ),
        ),
        "mvInequality": _section(
            title="Inequality of attention",
            purpose=(
                "Turn the winner-take-most feeling into measurable concentration so the conversation can move beyond "
                "impression."
            ),
            learn=(
                f"The current real-data Gini is {_num(music_inequality.get('gini'))} and top-10 share is "
                f"{_pct(music_inequality.get('top10_channel_share'))}. That is the concrete shape of the field."
            ),
            if_changes=(
                "If concentration drops while views remain strong, the market may be opening. If concentration rises, "
                "the field is becoming easier to describe but harder to enter."
            ),
            improve=(
                "Keep cohort segmentation visible so inequality is not mistaken for one universal market law."
            ),
            limits=(
                "Concentration metrics are blunt. They tell you where the center is, not what artistic or platform "
                "forces created it."
            ),
            scale=(
                "Useful for strategy, procurement, and creator economics because it shows whether success is being "
                "distributed or hoarded."
            ),
        ),
        "mvCorrelation": _section(
            title="Correlation architecture",
            purpose=(
                "Separate what travels with scale from what appears to matter on its own."
            ),
            learn=(
                "Raw correlation is only the first pass. The partial layer matters because it tests whether a feature "
                "still holds once channel size stops carrying it."
            ),
            if_changes=(
                "If a feature looks strong in the raw view but collapses in the partial view, scale was doing most of the talking."
            ),
            improve=(
                "Improve this lane with more contrastive explanations, cleaner feature provenance, and clearer labeling of pre- versus post-publication fields."
            ),
            limits=(
                "Correlation can suggest where to look harder, but it does not prove mechanism."
            ),
            scale=(
                "This is the layer that keeps a music or media strategy conversation from drifting into superstition."
            ),
        ),
        "mvArchetypes": _section(
            title="Viral archetypes",
            purpose=(
                "Turn a noisy leaderboard into a handful of reusable release shapes so readers can reason about strategies, not just songs."
            ),
            learn=(
                "The clusters matter because they tell you whether success keeps arriving through the same small set of release patterns."
            ),
            if_changes=(
                "If archetypes collapse into one blob when the feature mix changes, the segmentation is decorative. If they remain separable, it is carrying real structure."
            ),
            improve=(
                "Keep naming the cluster assumptions, exposing cluster counts, and checking whether the groupings survive under different windows."
            ),
            limits=(
                "Cluster names are interpretive. They help memory and discussion, but they should not be mistaken for immutable market categories."
            ),
            scale=(
                "This is where product, label, and platform teams can start comparing release tactics without flattening everything into one average."
            ),
        ),
        "mvNetwork": _section(
            title="Tag universe",
            purpose=(
                "Map the neighboring language around music releases so the repo can show whether discovery is broadening or just recirculating a familiar cluster."
            ),
            learn=(
                "This surface is useful because it shows bridge tags, central tags, and isolated tag pockets that are easy to miss in a table."
            ),
            if_changes=(
                "If the same tags remain central under different cohorts, the field is more repetitive than its long tail suggests."
            ),
            improve=(
                "Improve it by keeping tag cleaning visible, adding time windows, and showing when a dense cluster is being carried by only a few channels."
            ),
            limits=(
                "Tags are packaging signals as much as musical signals, so they should be read with that commercial bias in mind."
            ),
            scale=(
                "For search, discovery, and editorial teams, this becomes a practical map of how the catalog is being framed."
            ),
        ),
        "mvPredictability": _section(
            title="Predictability surface",
            purpose=(
                "Force the repo to be honest about how much can actually be forecast before publication."
            ),
            learn=(
                f"The current out-of-fold ensemble R² is {_num(music_predictability.get('ensemble_r2'))}. That "
                "matters because a low but honest score is more useful than a glamorous model with leakage."
            ),
            if_changes=(
                "If predictive lift rises with clean features, the field has legible structure. If it only rises when "
                "you leak post-publication data, the model is pretending."
            ),
            improve=(
                "Keep leakage blocks explicit, add calibration notes, and broaden the feature audit so contributors "
                "can improve the model without gaming the story."
            ),
            limits=(
                "Prediction is not explanation. Even a strong model does not tell you whether the mechanism is fair or "
                "healthy."
            ),
            scale=(
                "For larger teams this is the bridge between analytical curiosity and something operationally useful."
            ),
        ),
        "mvResonance": _section(
            title="Resonance mapper",
            purpose=(
                "Give the repo a way to talk about repeated attention pressure without pretending it can observe hidden "
                "platform internals."
            ),
            learn=(
                "This visual is useful because it makes the public shape of repetition legible: duration fit, release "
                "pressure, concentration, and tag/title echo can still reveal an environment optimized for recurrence."
            ),
            if_changes=(
                "If resonance narrows and stabilizes around the same tracks, the field is leaning toward manufactured "
                "repeatability. If it diffuses, discovery may be opening up."
            ),
            improve=(
                "Improve it with better cohort windows, more public context data, and clearer translation between "
                "repeat pressure and human consequence."
            ),
            limits=(
                "This is a public proxy, not a claim about hidden recommender code or audio waveforms."
            ),
            scale=(
                "This is where virality stops sounding mystical and starts looking environmental."
            ),
        ),
        "mvWhatIf": _section(
            title="What-if predictor",
            purpose=(
                "Give readers a safe way to stress the public model and see how one feature change alters the rank story."
            ),
            learn=(
                "This matters because most people need to feel the slope of the model before they understand what the summary metrics are saying."
            ),
            if_changes=(
                "If a tiny control change produces a wild output swing, the model or feature space needs better calibration."
            ),
            improve=(
                "Improve it with clearer uncertainty language, cohort-aware presets, and more visible notes about what the model does not know."
            ),
            limits=(
                "A simulator is a directional instrument, not a guarantee of outcome."
            ),
            scale=(
                "This is the most approachable bridge from research to practical planning because it lets non-specialists test consequences directly."
            ),
        ),
        "mvBias": _section(
            title="Bias in the top 100",
            purpose=(
                "Show that virality is not only a music question. It is also a distribution, exposure, and advantage "
                "question."
            ),
            learn=(
                f"Publication year coverage is {_pct(publication_year_share)} and notation link rate is "
                f"{_pct(music_intel_summary.get('notation_link_rate'))}. That honesty matters because missing context "
                "should lower confidence, not be paved over."
            ),
            if_changes=(
                "If gender, genre, or language concentration shifts under a new role lens, the conclusion should "
                "change in consequence, not in facts."
            ),
            improve=(
                "Keep growing country, year, and notation coverage so this section can move from structural hints to "
                "deeper musical and market evidence."
            ),
            limits=(
                "This lane uses public data and public inference. It should stay explicit about what is observed, what "
                "is classified, and what is still unknown."
            ),
            scale=(
                "For entertainment, platform, and creator teams, this is the section that translates abstract bias "
                "into market shape."
            ),
        ),
        "mv3DLandscape": _section(
            title="3D virality landscape",
            purpose=(
                "Give the reader one higher-dimensional pass on views, virality, and channel scale at the same time so strategy does not get trapped in a flat ranking."
            ),
            learn=(
                "The point is not the spectacle. The point is to see whether breakout songs occupy genuinely different terrain or are just scaled-up versions of the same release pattern."
            ),
            if_changes=(
                "If the 3D shape shows clear separation, strategy families are more believable. If it turns into a compressed cloud, the market is behaving more uniformly than the labels suggest."
            ),
            improve=(
                "Improve it with stronger cohort filters and better explanatory labels so the depth dimension stays legible to non-specialists."
            ),
            limits=(
                "3D scenes are intuitive for shape and weaker for precise reading. They need companion annotations."
            ),
            scale=(
                "This is useful in demos and reviews because it gives one quick sense of whether the field has multiple lanes or one narrow groove."
            ),
        ),
        "mvSongsExplorer": _section(
            title="Public songs explorer",
            purpose=(
                "Keep the real-data lane falsifiable by letting readers inspect, sort, and challenge the rows beneath "
                "the story."
            ),
            learn=(
                f"The current score-aware lane has {_compact_int(music_intel_summary.get('discovered_music_files'))} discovered "
                "local music files and "
                f"{_compact_int(music_intel_summary.get('matched_catalog_songs'))} matched catalog songs. That tells the "
                "reader how deep the note-aware bridge actually goes today."
            ),
            if_changes=(
                "If the summary feels persuasive but the rows or note links look thin, the repo should say so plainly."
            ),
            improve=(
                "Keep adding pagination, stronger schema cues, and more score-linked public files so contributors can "
                "build on a real substrate instead of a screenshot."
            ),
            limits=(
                "An explorer is only useful if the repository keeps the row layer honest and updated."
            ),
            scale=(
                "This is the collaborator surface: the place where people can verify, extend, and actually contribute."
            ),
        ),
    }

    return {
        "generated_at": generated_at,
        "sample_size": sample_size,
        "summary": {
            "posture": "critical_reading_before_claims",
            "promise": (
                "Each visual should answer a concrete question, name its boundary, and suggest how to improve the "
                "analysis instead of simply asking to be believed."
            ),
            "honesty_contract": [
                "Public visuals should stay traceable to row-level or export-level evidence.",
                "If coverage is thin, confidence should fall in plain view.",
                "If a chart is visually strong but analytically weak, the repo should say so directly.",
                "The system should translate what changes when the signal moves, not just that it moved.",
            ],
        },
        "visuals": visuals,
    }
