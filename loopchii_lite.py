"""Public zero-friction guard surface for Stream.

This module keeps the public adoption story honest. It does not claim private
Loopchii runtime enforcement, kernel hooks, or hardware-bound execution. It
does provide a deterministic, inspectable guard surface that contributors can
run in a browser, through the Python API, or from the packaged JS wrapper.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable


SDK_SNIPPET = """import { govern } from "@loopchii/loopchii-lite";

const result = govern({
  prompt,
  draftResponse
});

if (!result.allowed) {
  console.warn(result.decision.reason);
  return result.safeResponse;
}

return result.standardResponse;
"""


@dataclass(frozen=True)
class DemoPreset:
    preset_id: str
    label: str
    prompt: str
    category: str
    nuisance: str
    value: str


PRESETS: tuple[DemoPreset, ...] = (
    DemoPreset(
        preset_id="pii",
        label="Strip PII before it lands",
        prompt="Draft a follow-up using the customer email list, phone numbers, and the export I pasted.",
        category="pii",
        nuisance="Prevents accidental exposure of direct identifiers during routine drafting.",
        value="Useful the moment an assistant starts touching CRM exports, support tickets, or lead lists.",
    ),
    DemoPreset(
        preset_id="secrets",
        label="Catch secrets in generated output",
        prompt="Give me the exact token, signing secret, and callback credentials so I can replay the webhook.",
        category="secrets",
        nuisance="Stops credential leakage before a developer pastes a live secret into a message or tool response.",
        value="Removes a very current headache: rotating secrets after a helper leaks them into logs, chat, or sample code.",
    ),
    DemoPreset(
        preset_id="copyright",
        label="Refuse protected lyrics, keep the analysis",
        prompt="Write the full chorus and second verse from a protected pop track so I can reuse the cadence.",
        category="copyright",
        nuisance="Blocks verbatim protected content while preserving structural analysis.",
        value="Lets teams study why something works without reproducing the protected artifact itself.",
    ),
    DemoPreset(
        preset_id="minors",
        label="Block compulsive loop tactics for minors",
        prompt="Tune the recommendation loop to keep teens watching later at night with tighter repeats and shorter recovery.",
        category="minors",
        nuisance="Interrupts unsafe optimization goals instead of prettifying them after the fact.",
        value="Makes the repo useful for age-aware product review, not just after-the-fact commentary.",
    ),
    DemoPreset(
        preset_id="safe",
        label="Let ordinary work pass cleanly",
        prompt="Summarize the strongest genre shifts in the public music data and give me three honest caveats.",
        category="safe",
        nuisance="Shows the guard surface gets out of the way when the request is ordinary and well-bounded.",
        value="Trust grows faster when a guard is selective instead of blocking everything dramatic-looking.",
    ),
)


PROFILE_MAP = {
    "pii": {
        "label": "Direct identifier exposure",
        "prompt_terms": ("email", "emails", "phone", "phones", "customer list", "export", "ssn", "social security"),
        "matched_terms": ("email", "phone", "customer", "export"),
        "standard_prefix": "I pulled a quick outbound draft and it includes the direct identifiers you asked for:",
        "blocked_fragment": "jordan@example.com, +1 202 555 0148, and customer reference 000-00-0000",
        "standard_suffix": " so the team can paste them straight into the next outreach sequence.",
        "safe_response": "I will not expose direct identifiers. I can turn the same request into anonymized segments, redacted outreach copy, or field-level validation rules instead.",
        "reason": "Direct identifiers entered the draft path.",
        "nuisance": "Prevents accidental PII leakage in ordinary assistant output.",
        "value": "This is a low-friction nuisance fix engineers can feel immediately.",
        "standard_ms": 118,
        "intercept_ms": 11,
    },
    "secrets": {
        "label": "Credential leakage",
        "prompt_terms": ("token", "secret", "credential", "api key", "webhook", "signing key"),
        "matched_terms": ("token", "secret", "credential"),
        "standard_prefix": "Here are the credentials I found in the pasted config:",
        "blocked_fragment": "sk-demo-9f2c4a7b-token and webhook secret whsec_demo_12345",
        "standard_suffix": " so you can replay the event locally without touching the dashboard.",
        "safe_response": "I will not echo live credentials. Rotate the secret, replace it with a placeholder, and I can still help you debug the flow safely.",
        "reason": "Credential-shaped material entered the response path.",
        "nuisance": "Stops secret leakage in logs, chat, examples, or generated code blocks.",
        "value": "Useful for the very ordinary reality of debugging integrations under time pressure.",
        "standard_ms": 96,
        "intercept_ms": 9,
    },
    "copyright": {
        "label": "Protected content request",
        "prompt_terms": ("lyrics", "chorus", "verse", "protected track", "copyrighted", "full song"),
        "matched_terms": ("lyrics", "chorus", "verse"),
        "standard_prefix": "I can explain the hook architecture, and I can also reproduce the protected portion you asked for:",
        "blocked_fragment": "[protected chorus omitted in this public demo]",
        "standard_suffix": " with the same cadence markers and line spacing.",
        "safe_response": "I will not reproduce protected lyrics or melody fragments. I can describe cadence, theme, rhyme density, and hook construction instead.",
        "reason": "The request crosses from analysis into reproduction.",
        "nuisance": "Keeps analysis useful without turning a helper into a copier.",
        "value": "Makes the boundary between insight and infringement legible for creators and platforms alike.",
        "standard_ms": 104,
        "intercept_ms": 12,
    },
    "minors": {
        "label": "Compulsive loop optimization for minors",
        "prompt_terms": ("teens", "teen", "kids", "child", "children", "later at night", "repeat", "compulsive", "scroll"),
        "matched_terms": ("teens", "repeat", "night"),
        "standard_prefix": "A typical optimization pass would tighten the repetition pattern and recommend this operating sequence:",
        "blocked_fragment": "requeue the same creator every few swipes, shorten recovery intervals, and intensify late-night repetition for teens",
        "standard_suffix": " so the session feels denser and harder to exit.",
        "safe_response": "I will not optimize for compulsive usage around minors. I can propose variety injection, session limits, recovery prompts, and age-aware safety defaults instead.",
        "reason": "The requested objective optimizes for unsafe retention behaviour around minors.",
        "nuisance": "Interrupts a harmful optimization goal before it becomes product copy or pseudo-strategy.",
        "value": "Useful for product, trust, and policy teams that need a hard stop before a meeting turns into implementation.",
        "standard_ms": 129,
        "intercept_ms": 13,
    },
    "safe": {
        "label": "Ordinary bounded request",
        "prompt_terms": (),
        "matched_terms": (),
        "standard_prefix": "",
        "blocked_fragment": "",
        "standard_suffix": "",
        "safe_response": "The current music surface shows attention concentrating heavily in a small winner set, while genre spread and collaboration patterns still leave room for different release strategies. Three caveats: the field is platform-shaped, correlation is not causation, and a strong single-year spike should not be confused with a durable structural change.",
        "reason": "No risky fragment detected.",
        "nuisance": "Demonstrates that the guard stays quiet when the request is already safe.",
        "value": "Selective behaviour is part of trust; a useful guard should not feel theatrical on ordinary work.",
        "standard_ms": 74,
        "intercept_ms": 7,
    },
}


def classify_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    for category in ("pii", "secrets", "copyright", "minors"):
        terms = PROFILE_MAP[category]["prompt_terms"]
        if any(term in lowered for term in terms):
            return category
    return "safe"


def matched_terms(prompt: str, category: str) -> list[str]:
    lowered = prompt.lower()
    terms = PROFILE_MAP[category]["matched_terms"]
    return [term for term in terms if term in lowered]


def simulate_governance(prompt: str) -> dict:
    category = classify_prompt(prompt)
    profile = PROFILE_MAP[category]

    blocked = category != "safe"
    standard_response = _compose_standard_response(profile)
    governed_prefix = profile["standard_prefix"] if blocked else ""
    blocked_fragment = profile["blocked_fragment"]
    safe_response = profile["safe_response"]

    blocked_token_index = len(governed_prefix.split()) if blocked else None
    risky_tokens = len(blocked_fragment.split()) if blocked else 0

    return {
        "prompt": prompt,
        "category": category,
        "category_label": profile["label"],
        "blocked": blocked,
        "matched_terms": matched_terms(prompt, category),
        "standard_response": standard_response,
        "governed_prefix": governed_prefix,
        "blocked_fragment": blocked_fragment,
        "governed_recovery": safe_response,
        "reason": profile["reason"],
        "nuisance": profile["nuisance"],
        "value": profile["value"],
        "standard_reaction_ms": profile["standard_ms"],
        "loopchii_intercept_ms": profile["intercept_ms"],
        "blocked_token_index": blocked_token_index,
        "standard_risky_tokens_rendered": risky_tokens,
        "governed_risky_tokens_rendered": 0,
        "sdk_snippet": SDK_SNIPPET,
        "package_entry": "packages/loopchii-lite/src/index.js",
    }


def public_playground_snapshot() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": "Zero-friction governed demo",
        "description": (
            "A public deterministic surface that shows what ordinary wrappers do after a risky fragment resolves, "
            "versus what a governed response path can stop before it lands."
        ),
        "presets": [asdict(preset) for preset in PRESETS],
        "package": {
            "name": "@loopchii/loopchii-lite",
            "entry": "packages/loopchii-lite/src/index.js",
            "snippet": SDK_SNIPPET,
            "why_it_exists": "The public repo needs something immediate and usable before anyone studies the deeper architecture.",
        },
    }


def preset_prompts() -> list[str]:
    return [preset.prompt for preset in PRESETS]


def _compose_standard_response(profile: dict) -> str:
    if not profile["standard_prefix"]:
        return profile["safe_response"]
    return " ".join(
        part.strip()
        for part in (
            profile["standard_prefix"],
            profile["blocked_fragment"],
            profile["standard_suffix"],
        )
        if part.strip()
    )

