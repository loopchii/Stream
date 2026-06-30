const SDK_SNIPPET = `import { govern } from "@loopchii/loopchii-lite";

const result = govern({
  prompt,
  draftResponse
});

if (!result.allowed) {
  console.warn(result.decision.reason);
  return result.safeResponse;
}

return result.standardResponse;
`;

const PRESETS = [
  {
    preset_id: "pii",
    label: "Strip PII before it lands",
    prompt: "Draft a follow-up using the customer email list, phone numbers, and the export I pasted.",
    category: "pii",
    nuisance: "Prevents accidental exposure of direct identifiers during routine drafting.",
    value: "Useful the moment an assistant starts touching CRM exports, support tickets, or lead lists."
  },
  {
    preset_id: "secrets",
    label: "Catch secrets in generated output",
    prompt: "Give me the exact token, signing secret, and callback credentials so I can replay the webhook.",
    category: "secrets",
    nuisance: "Stops credential leakage before a developer pastes a live secret into a message or tool response.",
    value: "Removes a very current headache: rotating secrets after a helper leaks them into logs, chat, or sample code."
  },
  {
    preset_id: "copyright",
    label: "Refuse protected lyrics, keep the analysis",
    prompt: "Write the full chorus and second verse from a protected pop track so I can reuse the cadence.",
    category: "copyright",
    nuisance: "Blocks verbatim protected content while preserving structural analysis.",
    value: "Lets teams study why something works without reproducing the protected artifact itself."
  },
  {
    preset_id: "minors",
    label: "Block compulsive loop tactics for minors",
    prompt: "Tune the recommendation loop to keep teens watching later at night with tighter repeats and shorter recovery.",
    category: "minors",
    nuisance: "Interrupts unsafe optimization goals instead of prettifying them after the fact.",
    value: "Makes the repo useful for age-aware product review, not just after-the-fact commentary."
  },
  {
    preset_id: "safe",
    label: "Let ordinary work pass cleanly",
    prompt: "Summarize the strongest genre shifts in the public music data and give me three honest caveats.",
    category: "safe",
    nuisance: "Shows the guard surface gets out of the way when the request is ordinary and well-bounded.",
    value: "Trust grows faster when a guard is selective instead of blocking everything dramatic-looking."
  }
];

const PROFILE_MAP = {
  pii: {
    label: "Direct identifier exposure",
    promptTerms: ["email", "emails", "phone", "phones", "customer list", "export", "ssn", "social security"],
    matchedTerms: ["email", "phone", "customer", "export"],
    standardPrefix: "I pulled a quick outbound draft and it includes the direct identifiers you asked for:",
    blockedFragment: "jordan@example.com, +1 202 555 0148, and customer reference 000-00-0000",
    standardSuffix: " so the team can paste them straight into the next outreach sequence.",
    safeResponse: "I will not expose direct identifiers. I can turn the same request into anonymized segments, redacted outreach copy, or field-level validation rules instead.",
    reason: "Direct identifiers entered the draft path.",
    nuisance: "Prevents accidental PII leakage in ordinary assistant output.",
    value: "This is a low-friction nuisance fix engineers can feel immediately.",
    standardMs: 118,
    interceptMs: 11
  },
  secrets: {
    label: "Credential leakage",
    promptTerms: ["token", "secret", "credential", "api key", "webhook", "signing key"],
    matchedTerms: ["token", "secret", "credential"],
    standardPrefix: "Here are the credentials I found in the pasted config:",
    blockedFragment: "sk-demo-9f2c4a7b-token and webhook secret whsec_demo_12345",
    standardSuffix: " so you can replay the event locally without touching the dashboard.",
    safeResponse: "I will not echo live credentials. Rotate the secret, replace it with a placeholder, and I can still help you debug the flow safely.",
    reason: "Credential-shaped material entered the response path.",
    nuisance: "Stops secret leakage in logs, chat, examples, or generated code blocks.",
    value: "Useful for the very ordinary reality of debugging integrations under time pressure.",
    standardMs: 96,
    interceptMs: 9
  },
  copyright: {
    label: "Protected content request",
    promptTerms: ["lyrics", "chorus", "verse", "protected track", "copyrighted", "full song"],
    matchedTerms: ["lyrics", "chorus", "verse"],
    standardPrefix: "I can explain the hook architecture, and I can also reproduce the protected portion you asked for:",
    blockedFragment: "[protected chorus omitted in this public demo]",
    standardSuffix: " with the same cadence markers and line spacing.",
    safeResponse: "I will not reproduce protected lyrics or melody fragments. I can describe cadence, theme, rhyme density, and hook construction instead.",
    reason: "The request crosses from analysis into reproduction.",
    nuisance: "Keeps analysis useful without turning a helper into a copier.",
    value: "Makes the boundary between insight and infringement legible for creators and platforms alike.",
    standardMs: 104,
    interceptMs: 12
  },
  minors: {
    label: "Compulsive loop optimization for minors",
    promptTerms: ["teens", "teen", "kids", "child", "children", "later at night", "repeat", "compulsive", "scroll"],
    matchedTerms: ["teens", "repeat", "night"],
    standardPrefix: "A typical optimization pass would tighten the repetition pattern and recommend this operating sequence:",
    blockedFragment: "requeue the same creator every few swipes, shorten recovery intervals, and intensify late-night repetition for teens",
    standardSuffix: " so the session feels denser and harder to exit.",
    safeResponse: "I will not optimize for compulsive usage around minors. I can propose variety injection, session limits, recovery prompts, and age-aware safety defaults instead.",
    reason: "The requested objective optimizes for unsafe retention behaviour around minors.",
    nuisance: "Interrupts a harmful optimization goal before it becomes product copy or pseudo-strategy.",
    value: "Useful for product, trust, and policy teams that need a hard stop before a meeting turns into implementation.",
    standardMs: 129,
    interceptMs: 13
  },
  safe: {
    label: "Ordinary bounded request",
    promptTerms: [],
    matchedTerms: [],
    standardPrefix: "",
    blockedFragment: "",
    standardSuffix: "",
    safeResponse: "The current music surface shows attention concentrating heavily in a small winner set, while genre spread and collaboration patterns still leave room for different release strategies. Three caveats: the field is platform-shaped, correlation is not causation, and a strong single-year spike should not be confused with a durable structural change.",
    reason: "No risky fragment detected.",
    nuisance: "Demonstrates that the guard stays quiet when the request is already safe.",
    value: "Selective behaviour is part of trust; a useful guard should not feel theatrical on ordinary work.",
    standardMs: 74,
    interceptMs: 7
  }
};

function composeStandardResponse(profile) {
  if (!profile.standardPrefix) {
    return profile.safeResponse;
  }
  return [profile.standardPrefix, profile.blockedFragment, profile.standardSuffix]
    .map((part) => (part || "").trim())
    .filter(Boolean)
    .join(" ");
}

export function classifyPrompt(prompt = "") {
  const lowered = String(prompt).toLowerCase();
  for (const category of ["pii", "secrets", "copyright", "minors"]) {
    const terms = PROFILE_MAP[category].promptTerms;
    if (terms.some((term) => lowered.includes(term))) {
      return category;
    }
  }
  return "safe";
}

export function buildPresetSuite() {
  return PRESETS.slice();
}

export function simulateSplitScreen(prompt = "") {
  const category = classifyPrompt(prompt);
  const profile = PROFILE_MAP[category];
  const lowered = String(prompt).toLowerCase();
  const blocked = category !== "safe";
  const standardResponse = composeStandardResponse(profile);
  const governedPrefix = blocked ? profile.standardPrefix : "";
  const blockedFragment = profile.blockedFragment;
  const safeResponse = profile.safeResponse;
  const matchedTerms = profile.matchedTerms.filter((term) => lowered.includes(term));
  const blockedTokenIndex = blocked ? governedPrefix.split(/\s+/).filter(Boolean).length : null;
  const riskyTokens = blocked ? blockedFragment.split(/\s+/).filter(Boolean).length : 0;

  return {
    prompt,
    category,
    categoryLabel: profile.label,
    blocked,
    matchedTerms,
    standardResponse,
    governedPrefix,
    blockedFragment,
    governedRecovery: safeResponse,
    reason: profile.reason,
    nuisance: profile.nuisance,
    value: profile.value,
    standardReactionMs: profile.standardMs,
    loopchiiInterceptMs: profile.interceptMs,
    blockedTokenIndex,
    standardRiskyTokensRendered: riskyTokens,
    governedRiskyTokensRendered: 0,
    sdkSnippet: SDK_SNIPPET,
    packageEntry: "packages/loopchii-lite/src/index.js"
  };
}

export function govern({ prompt = "", draftResponse = "" } = {}) {
  const simulation = simulateSplitScreen(prompt);
  const standardResponse = draftResponse || simulation.standardResponse;
  return {
    allowed: !simulation.blocked,
    category: simulation.category,
    standardResponse,
    safeResponse: simulation.blocked ? simulation.governedRecovery : standardResponse,
    decision: {
      mode: simulation.blocked ? "apoptosis" : "pass",
      reason: simulation.reason,
      matchedTerms: simulation.matchedTerms,
      interceptMs: simulation.loopchiiInterceptMs
    },
    telemetry: {
      riskyTokensRendered: simulation.governedRiskyTokensRendered,
      standardRiskyTokensRendered: simulation.standardRiskyTokensRendered,
      blockedTokenIndex: simulation.blockedTokenIndex
    }
  };
}

export { SDK_SNIPPET };
