use serde::Serialize;
use wasm_bindgen::prelude::*;

#[derive(Serialize)]
struct DemoDecision {
    category: &'static str,
    blocked: bool,
    reason: &'static str,
    blocked_fragment: &'static str,
    safe_response: &'static str,
    standard_reaction_ms: u32,
    intercept_ms: u32,
}

#[wasm_bindgen]
pub fn govern_demo(prompt: &str) -> String {
    let lowered = prompt.to_lowercase();
    let decision = if contains_any(&lowered, &["email", "phone", "customer list", "export", "ssn"]) {
        DemoDecision {
            category: "pii",
            blocked: true,
            reason: "Direct identifiers entered the draft path.",
            blocked_fragment: "jordan@example.com, +1 202 555 0148, and customer reference 000-00-0000",
            safe_response: "I will not expose direct identifiers. I can help you redact, segment, or validate the data safely instead.",
            standard_reaction_ms: 118,
            intercept_ms: 11,
        }
    } else if contains_any(&lowered, &["token", "secret", "credential", "api key", "webhook"]) {
        DemoDecision {
            category: "secrets",
            blocked: true,
            reason: "Credential-shaped material entered the response path.",
            blocked_fragment: "sk-demo-9f2c4a7b-token and webhook secret whsec_demo_12345",
            safe_response: "I will not echo live credentials. Replace them with placeholders and I can still help you debug the flow.",
            standard_reaction_ms: 96,
            intercept_ms: 9,
        }
    } else if contains_any(&lowered, &["lyrics", "chorus", "verse", "copyrighted", "full song"]) {
        DemoDecision {
            category: "copyright",
            blocked: true,
            reason: "The request crosses from analysis into reproduction.",
            blocked_fragment: "[protected chorus omitted in this public demo]",
            safe_response: "I will not reproduce protected lyrics or melody fragments. I can describe cadence, rhyme density, and hook structure instead.",
            standard_reaction_ms: 104,
            intercept_ms: 12,
        }
    } else if contains_any(&lowered, &["teens", "teen", "kids", "child", "repeat", "scroll"]) {
        DemoDecision {
            category: "minors",
            blocked: true,
            reason: "The requested objective optimizes for unsafe retention behaviour around minors.",
            blocked_fragment: "requeue the same creator every few swipes, shorten recovery intervals, and intensify late-night repetition for teens",
            safe_response: "I will not optimize for compulsive usage around minors. I can suggest variety injection, session limits, and age-aware safety defaults instead.",
            standard_reaction_ms: 129,
            intercept_ms: 13,
        }
    } else {
        DemoDecision {
            category: "safe",
            blocked: false,
            reason: "No risky fragment detected.",
            blocked_fragment: "",
            safe_response: "The current music surface shows heavy attention concentration with enough remaining genre and collaboration spread to keep strategic openings visible.",
            standard_reaction_ms: 74,
            intercept_ms: 7,
        }
    };

    serde_json::to_string(&decision).unwrap_or_else(|_| "{\"category\":\"error\",\"blocked\":false}".to_string())
}

fn contains_any(input: &str, terms: &[&str]) -> bool {
    terms.iter().any(|term| input.contains(term))
}
