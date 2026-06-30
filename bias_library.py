"""Library of documented bias types in media and representation research.

Each entry describes a real, named bias studied in media/representation
research. Definitions are conceptual and truthful; none invent statistics.
"""

BIAS_LIBRARY = [
    # ---- Gender ----
    {"id": "gender-lead-gap", "category": "gender", "name": "Lead Role Gender Gap",
     "definition": "Men are cast in lead/protagonist roles far more often than women.",
     "example": "An action catalog where most protagonists are male.",
     "why_it_matters": "Leads drive the story; whoever holds them defines whose perspective audiences inhabit.",
     "measured_here": True},
    {"id": "dialogue-gap", "category": "gender", "name": "Dialogue Gap",
     "definition": "Female characters receive systematically fewer spoken words than male characters.",
     "example": "Script analyses repeatedly find male characters speak the majority of lines even in female-led films.",
     "why_it_matters": "Speech is narrative power: fewer words means less agency and influence on the plot.",
     "measured_here": True},
    {"id": "smurfette", "category": "gender", "name": "Smurfette Principle",
     "definition": "A single female character in an otherwise all-male ensemble.",
     "example": "A five-person team with exactly one woman whose trait is 'the girl'.",
     "why_it_matters": "Frames womanhood itself as a personality trait rather than half the population.",
     "measured_here": False},
    {"id": "bechdel-fail", "category": "gender", "name": "Bechdel Test Failure",
     "definition": "No two named women converse about something other than a man.",
     "example": "Entire feature films where women never speak to each other.",
     "why_it_matters": "A deliberately low bar — failing it signals women exist only relative to men.",
     "measured_here": True},
    {"id": "fridging", "category": "gender", "name": "Fridging",
     "definition": "Harming or killing a female character solely to motivate a male protagonist.",
     "example": "The hero's wife dies in the opening scene to justify his revenge arc.",
     "why_it_matters": "Reduces women to plot devices instead of people with their own arcs.",
     "measured_here": False},
    {"id": "male-gaze", "category": "gender", "name": "Male Gaze Framing",
     "definition": "Camera work and framing that presents women primarily as objects to be looked at.",
     "example": "Introductory shots that pan over a woman's body before showing her face.",
     "why_it_matters": "Trains audiences to evaluate women by appearance before character.",
     "measured_here": False},
    {"id": "romantic-only", "category": "gender", "name": "Romantic-Interest Typecasting",
     "definition": "Women cast disproportionately as love interests rather than agents of the plot.",
     "example": "A scientist character whose only scenes concern her relationship with the hero.",
     "why_it_matters": "Limits the imagined futures of audiences who see themselves only as someone's partner.",
     "measured_here": True},
    {"id": "ambition-penalty", "category": "gender", "name": "Ambition Penalty",
     "definition": "Ambitious female characters written as villains or punished by the narrative.",
     "example": "The career-driven woman who 'learns her lesson' and gives it all up.",
     "why_it_matters": "Codes ambition as masculine and punishes audiences who aspire.",
     "measured_here": False},
    {"id": "stem-gap", "category": "gender", "name": "STEM Role Gap",
     "definition": "Scientists, engineers and tech experts on screen are overwhelmingly male.",
     "example": "Hacker and genius-inventor roles defaulting to men.",
     "why_it_matters": "On-screen role models shape real-world career aspiration, especially in childhood.",
     "measured_here": False},
    {"id": "age-gap-casting", "category": "gender", "name": "Romantic Age-Gap Casting",
     "definition": "Male leads paired with much younger female love interests, rarely the reverse.",
     "example": "A 50-year-old lead whose romantic partner is 25.",
     "why_it_matters": "Normalizes valuing women by youth while letting men age into prestige.",
     "measured_here": False},
    {"id": "nonbinary-erasure", "category": "gender", "name": "Non-binary Erasure",
     "definition": "Non-binary people are nearly absent from mainstream casts.",
     "example": "Catalogs with thousands of characters and only a handful outside the gender binary.",
     "why_it_matters": "Invisibility tells real people their existence is not part of the shared story.",
     "measured_here": True},

    # ---- Race & ethnicity ----
    {"id": "racial-lead-gap", "category": "race", "name": "Racial Lead Gap",
     "definition": "Leads are disproportionately white relative to the population.",
     "example": "A platform's top-billed cast skewing heavily white year after year.",
     "why_it_matters": "Decides whose stories are treated as universal and whose as niche.",
     "measured_here": True},
    {"id": "tokenism", "category": "race", "name": "Tokenism",
     "definition": "A single minority character included to signal diversity without depth.",
     "example": "The one Black friend with no storyline of their own.",
     "why_it_matters": "Substitutes optics for actual representation and flattens identity into a checkbox.",
     "measured_here": False},
    {"id": "whitewashing", "category": "race", "name": "Whitewashing",
     "definition": "Casting white actors in roles written as people of color.",
     "example": "A film adaptation recasting an explicitly Asian protagonist as white.",
     "why_it_matters": "Erases the few roles explicitly written for underrepresented actors.",
     "measured_here": False},
    {"id": "racial-dialogue-gap", "category": "race", "name": "Racial Dialogue Gap",
     "definition": "Characters of color receive fewer words than white characters with similar billing.",
     "example": "A diverse ensemble where white characters still dominate the script.",
     "why_it_matters": "Casting diversity is hollow if the script gives the words to the same group.",
     "measured_here": True},
    {"id": "ethnic-villain", "category": "race", "name": "Ethnic Villain Coding",
     "definition": "Villains given foreign accents or ethnic coding while heroes stay local.",
     "example": "Action franchises where antagonists default to a foreign accent.",
     "why_it_matters": "Builds an instinctive link between 'foreign' and 'threat'.",
     "measured_here": False},
    {"id": "model-minority", "category": "race", "name": "Model Minority Trope",
     "definition": "Asian characters confined to studious, quiet, technical archetypes.",
     "example": "The Asian classmate who exists to be good at math.",
     "why_it_matters": "Even 'positive' stereotypes deny individuality and create impossible standards.",
     "measured_here": False},
    {"id": "magical-minority", "category": "race", "name": "Magical Minority Trope",
     "definition": "Minority characters who exist to spiritually guide a white protagonist.",
     "example": "The wise Black mentor with no inner life who dies for the hero's growth.",
     "why_it_matters": "Centers white narratives even inside roles given to people of color.",
     "measured_here": False},
    {"id": "brownface-accent", "category": "race", "name": "Accent Caricature",
     "definition": "Exaggerated accents played for comedy.",
     "example": "A South Asian character whose every line is an accent joke.",
     "why_it_matters": "Turns identity into a punchline that follows real people into daily life.",
     "measured_here": False},
    {"id": "colorism", "category": "race", "name": "Colorism",
     "definition": "Lighter-skinned actors favored for leading and romantic roles.",
     "example": "Darker-skinned actors cast as villains or background while leads stay light-skinned.",
     "why_it_matters": "Adds a second hierarchy inside already underrepresented groups.",
     "measured_here": False},
    {"id": "racial-screen-time", "category": "race", "name": "Racial Screen-Time Gap",
     "definition": "Characters of color get fewer minutes on screen even when cast.",
     "example": "Poster-prominent minority characters with minimal actual scenes.",
     "why_it_matters": "Marketing diversity that the runtime doesn't deliver is a bait-and-switch.",
     "measured_here": True},
    {"id": "interchangeable-casting", "category": "race", "name": "Ethnic Interchangeability",
     "definition": "Treating distinct ethnicities as interchangeable in casting.",
     "example": "Casting any East Asian actor for any East Asian nationality.",
     "why_it_matters": "Signals that specific cultures don't matter, only a generic 'look'.",
     "measured_here": False},

    # ---- Age ----
    {"id": "age-cliff", "category": "age", "name": "Casting Age Cliff",
     "definition": "Roles for women drop sharply after 40 while men keep leading into their 60s.",
     "example": "Award-winning actresses reporting role droughts at exactly the age male peers peak.",
     "why_it_matters": "Halves the careers of one gender and erases older women from public imagination.",
     "measured_here": True},
    {"id": "elder-invisibility", "category": "age", "name": "Elder Invisibility",
     "definition": "Characters over 50 are heavily underrepresented relative to the population.",
     "example": "Casts where over-50s are a small fraction despite being a third of viewers.",
     "why_it_matters": "An aging audience never sees its own present, only its past.",
     "measured_here": True},
    {"id": "grumpy-elder", "category": "age", "name": "Grumpy Elder Trope",
     "definition": "Older characters reduced to stubborn, technophobic comic relief.",
     "example": "The grandparent whose jokes are all about not understanding phones.",
     "why_it_matters": "Replaces the diversity of late life with a single condescending gag.",
     "measured_here": False},
    {"id": "teen-adult-casting", "category": "age", "name": "Adult-as-Teen Casting",
     "definition": "Casting late-20s actors as teenagers.",
     "example": "High-school dramas cast almost entirely with adults.",
     "why_it_matters": "Sets impossible appearance standards for actual teenagers.",
     "measured_here": False},
    {"id": "age-dialogue-gap", "category": "age", "name": "Age Dialogue Gap",
     "definition": "Older characters speak less than their share of the cast.",
     "example": "Ensemble shows where over-50 characters get the fewest lines per episode.",
     "why_it_matters": "Even when present, elders are seen and not heard.",
     "measured_here": True},

    # ---- Writing & dialogue ----
    {"id": "sentiment-skew", "category": "writing", "name": "Sentiment Skew",
     "definition": "Some demographics are consistently written with more negative emotional tone.",
     "example": "A group whose lines are disproportionately angry, fearful or sad.",
     "why_it_matters": "Tone is subtext: it quietly teaches audiences how to feel about a group.",
     "measured_here": True},
    {"id": "competence-gap", "category": "writing", "name": "Competence Framing Gap",
     "definition": "Identical actions framed as brilliant for one group, lucky for another.",
     "example": "His risky plan is genius; her identical plan 'somehow works'.",
     "why_it_matters": "Audiences absorb who is allowed to be skilled.",
     "measured_here": False},
    {"id": "sassy-sidekick", "category": "writing", "name": "Sassy Sidekick Trope",
     "definition": "Minority characters written as quippy support with no interior life.",
     "example": "The one-liner best friend who vanishes between the hero's scenes.",
     "why_it_matters": "Personality without story is decoration, not representation.",
     "measured_here": False},
    {"id": "trauma-only", "category": "writing", "name": "Trauma-Only Storylines",
     "definition": "Marginalized characters whose plots are exclusively about suffering.",
     "example": "LGBTQ+ arcs that are only coming-out pain or tragedy.",
     "why_it_matters": "Joy is part of life; stories that allow a group only pain distort reality.",
     "measured_here": False},
    {"id": "accent-intelligence", "category": "writing", "name": "Accent-Intelligence Coding",
     "definition": "Regional or working-class accents written as markers of low intelligence.",
     "example": "The rural-accented character who exists to misunderstand things.",
     "why_it_matters": "Maps class prejudice directly onto how people are born speaking.",
     "measured_here": False},
    {"id": "exposition-imbalance", "category": "writing", "name": "Expertise Voice Imbalance",
     "definition": "Explanations and expertise are voiced through one demographic.",
     "example": "Documentaries where nearly all expert talking heads are men.",
     "why_it_matters": "Defines who sounds like authority.",
     "measured_here": False},
    {"id": "named-role-gap", "category": "writing", "name": "Named-Role Gap",
     "definition": "Underrepresented actors more often cast in unnamed background parts.",
     "example": "Credits listing 'Nurse #2' while speaking roles skew one way.",
     "why_it_matters": "Names are narrative existence; the unnamed are scenery.",
     "measured_here": False},

    # ---- Narrative & tropes ----
    {"id": "bury-your-gays", "category": "narrative", "name": "Bury Your Gays",
     "definition": "LGBTQ+ characters killed off at disproportionate rates.",
     "example": "A long pattern of same-sex couples ending in one partner's death.",
     "why_it_matters": "Teaches queer audiences their stories end badly by default.",
     "measured_here": False},
    {"id": "disability-inspiration", "category": "narrative", "name": "Inspiration Porn",
     "definition": "Disabled characters existing solely to inspire able-bodied characters.",
     "example": "The wheelchair-using classmate whose role is making others grateful.",
     "why_it_matters": "Objectifies disability as a moral prop instead of a lived experience.",
     "measured_here": False},
    {"id": "disability-villain", "category": "narrative", "name": "Disability Villain Coding",
     "definition": "Scars, prosthetics and disfigurement used as shorthand for evil.",
     "example": "Villains marked by facial scars while heroes are unblemished.",
     "why_it_matters": "Links visible difference with moral corruption.",
     "measured_here": False},
    {"id": "white-savior", "category": "narrative", "name": "White Savior Arc",
     "definition": "Stories about marginalized communities centered on a white rescuer.",
     "example": "A historical drama about racism whose hero is a white ally.",
     "why_it_matters": "Hands the narrative of a community's struggle to someone outside it.",
     "measured_here": False},
    {"id": "poverty-tourism", "category": "narrative", "name": "Poverty Spectacle",
     "definition": "Working-class life shown only as misery or comedy for outside audiences.",
     "example": "Reality formats that frame poor families as entertainment.",
     "why_it_matters": "Replaces solidarity with spectatorship.",
     "measured_here": False},
    {"id": "redemption-gap", "category": "narrative", "name": "Redemption Arc Gap",
     "definition": "Redemption arcs offered to some demographics and denied to others.",
     "example": "The troubled white antihero is complex; a minority character doing the same is simply a criminal.",
     "why_it_matters": "Complexity is empathy; rationing it rations audience compassion.",
     "measured_here": False},
    {"id": "default-hetero", "category": "narrative", "name": "Heteronormative Default",
     "definition": "All characters presumed straight unless a plot point says otherwise.",
     "example": "Large casts with zero incidental queer characters.",
     "why_it_matters": "Makes a sizable share of the audience a permanent special case.",
     "measured_here": False},
    {"id": "queerbaiting", "category": "narrative", "name": "Queerbaiting",
     "definition": "Hinting at queer relationships for engagement without committing on screen.",
     "example": "Marketing that teases a same-sex pairing the show never acknowledges.",
     "why_it_matters": "Monetizes a community's hope while avoiding its representation.",
     "measured_here": False},

    # ---- Casting & production ----
    {"id": "director-gap", "category": "production", "name": "Director Gender Gap",
     "definition": "Women direct a small fraction of top-budget productions.",
     "example": "Studio slates where female directors are confined to lower budgets.",
     "why_it_matters": "Whoever directs decides every other bias on this list.",
     "measured_here": False},
    {"id": "writers-room-gap", "category": "production", "name": "Writers' Room Homogeneity",
     "definition": "Writing staff demographics far narrower than the audience's.",
     "example": "Shows about diverse cities written by homogeneous rooms.",
     "why_it_matters": "You can't write lives no one in the room has lived.",
     "measured_here": False},
    {"id": "budget-gap", "category": "production", "name": "Budget Allocation Gap",
     "definition": "Projects led by underrepresented creators receive smaller budgets and marketing.",
     "example": "A diverse-led show canceled for ratings it was never marketed to reach.",
     "why_it_matters": "Underfunding manufactures the 'failure' used to justify the next underfunding.",
     "measured_here": False},
    {"id": "authentic-casting", "category": "production", "name": "Identity-Mismatch Casting",
     "definition": "Able-bodied, cis, or hearing actors cast in disabled, trans, or Deaf roles.",
     "example": "Award-winning performances in roles the community could have played itself.",
     "why_it_matters": "Takes both the role and the paycheck from the people being depicted.",
     "measured_here": False},
    {"id": "stunt-pay-gap", "category": "production", "name": "Pay Disparity",
     "definition": "Co-leads of different demographics paid wildly different salaries.",
     "example": "Reported negotiations where a female co-lead earned a fraction of her partner's fee.",
     "why_it_matters": "The industry's private valuation of whose presence 'sells'.",
     "measured_here": False},
    {"id": "crew-gap", "category": "production", "name": "Below-the-Line Gap",
     "definition": "Cinematography, sound, and technical crews remain heavily homogeneous.",
     "example": "Camera departments with near-zero female department heads.",
     "why_it_matters": "Technical craft shapes the image itself — including who is lit and framed well.",
     "measured_here": False},

    # ---- Platform & algorithmic ----
    {"id": "thumbnail-bias", "category": "algorithmic", "name": "Thumbnail Personalization Bias",
     "definition": "Recommendation systems can choose artwork that misrepresents diverse casts to different users.",
     "example": "Artwork emphasizing minor white characters when shown to some users.",
     "why_it_matters": "Personalization can quietly resegregate the storefront.",
     "measured_here": False},
    {"id": "recommendation-loop", "category": "algorithmic", "name": "Recommendation Feedback Loop",
     "definition": "Engagement-trained algorithms amplify whatever was historically promoted.",
     "example": "Diverse titles surfacing less because they were surfaced less before.",
     "why_it_matters": "Yesterday's bias becomes tomorrow's 'data-driven' decision.",
     "measured_here": False},
    {"id": "category-ghetto", "category": "algorithmic", "name": "Category Ghettoization",
     "definition": "Diverse titles shelved into niche categories instead of mainstream rows.",
     "example": "A universal family drama categorized only under a demographic label.",
     "why_it_matters": "Tells general audiences these stories aren't for them.",
     "measured_here": False},
    {"id": "search-bias", "category": "algorithmic", "name": "Search Ranking Skew",
     "definition": "Search and autocomplete favoring established (historically homogeneous) hits.",
     "example": "Generic queries returning the same legacy catalog first.",
     "why_it_matters": "Discovery is destiny on streaming platforms.",
     "measured_here": False},
    {"id": "metric-myopia", "category": "algorithmic", "name": "Completion-Metric Myopia",
     "definition": "Judging shows on metrics that penalize culturally specific storytelling.",
     "example": "Slow-burn international titles canceled on week-one completion rates.",
     "why_it_matters": "A single metric becomes a quiet censor of storytelling styles.",
     "measured_here": False},

    # ---- Intersectional ----
    {"id": "intersectional-gap", "category": "intersectional", "name": "Intersectional Lead Gap",
     "definition": "Women of color underrepresented far beyond what gender or race gaps alone predict.",
     "example": "Lead shares for women of color far below either women overall or people of color overall.",
     "why_it_matters": "Bias multiplies at intersections; single-axis fixes miss the people most excluded.",
     "measured_here": True},
    {"id": "double-standard-age", "category": "intersectional", "name": "Gendered Ageism",
     "definition": "Age penalties land harder on women than men at every age bracket.",
     "example": "Older male leads paired against a revolving cast of young women.",
     "why_it_matters": "Two biases compound into one steep cliff.",
     "measured_here": True},
    {"id": "queer-poc-gap", "category": "intersectional", "name": "Queer POC Underrepresentation",
     "definition": "LGBTQ+ characters of color are rare even within queer representation.",
     "example": "Queer storylines defaulting to white characters.",
     "why_it_matters": "Representation that only reaches a group's most privileged members isn't done.",
     "measured_here": False},
    {"id": "disabled-woc-gap", "category": "intersectional", "name": "Disabled Women of Color Erasure",
     "definition": "Characters at triple intersections are nearly absent from screens.",
     "example": "Catalogs with effectively zero disabled women of color in named roles.",
     "why_it_matters": "Total invisibility is the strongest message a medium can send.",
     "measured_here": False},
]

CATEGORIES = sorted({b["category"] for b in BIAS_LIBRARY})

PIPELINE_STAGES = [
    {
        "id": "greenlight",
        "label": "Greenlight",
        "short_label": "Scope",
        "note": "What receives money, mandate, and time.",
    },
    {
        "id": "writing",
        "label": "Writing",
        "short_label": "Voice",
        "note": "Who gets motive, dialogue, and interiority.",
    },
    {
        "id": "casting",
        "label": "Casting",
        "short_label": "Presence",
        "note": "Who gets status, desirability, and screen real estate.",
    },
    {
        "id": "framing",
        "label": "Framing",
        "short_label": "Emphasis",
        "note": "Camera, edit, soundtrack, and narrative stress.",
    },
    {
        "id": "packaging",
        "label": "Packaging",
        "short_label": "Shelf",
        "note": "Artwork, synopsis, tagging, and genre labeling.",
    },
    {
        "id": "ranking",
        "label": "Ranking",
        "short_label": "Loop",
        "note": "Search, recommendation, and repeat exposure.",
    },
    {
        "id": "memory",
        "label": "Audience Memory",
        "short_label": "Memory",
        "note": "What gets normalized, desired, or forgotten.",
    },
]

ROLE_LIBRARY = [
    {"id": "creator", "label": "Creator"},
    {"id": "operator", "label": "Operator"},
    {"id": "buyer", "label": "Buyer"},
    {"id": "public", "label": "Public"},
]

CATEGORY_ROUTES = {
    "gender": {
        "entry_stage": "writing",
        "path": ["writing", "casting", "framing", "packaging", "memory"],
        "fundamental": "voice allocation",
        "dissonance": "one gender is treated as default competence or centrality",
        "repair": "rebalance speaking power and role gravity before exposure multiplies the gap",
        "harm": {"representation": 92, "revenue": 66, "trust": 78, "safety": 55},
        "wave": {"amplitude": 0.82, "spread": 0.66, "persistence": 0.78, "drift": 0.46},
    },
    "race": {
        "entry_stage": "casting",
        "path": ["casting", "framing", "packaging", "ranking", "memory"],
        "fundamental": "narrative legitimacy",
        "dissonance": "who gets to feel universal versus marked or niche",
        "repair": "repair the casting and packaging boundary before search turns a bias into discoverability law",
        "harm": {"representation": 95, "revenue": 72, "trust": 83, "safety": 67},
        "wave": {"amplitude": 0.88, "spread": 0.72, "persistence": 0.84, "drift": 0.52},
    },
    "age": {
        "entry_stage": "casting",
        "path": ["casting", "framing", "packaging", "memory"],
        "fundamental": "life-stage visibility",
        "dissonance": "some ages are treated as prestige and others as expiry",
        "repair": "restore role volume across ages before stereotype hardens into expectation",
        "harm": {"representation": 78, "revenue": 58, "trust": 71, "safety": 42},
        "wave": {"amplitude": 0.7, "spread": 0.54, "persistence": 0.73, "drift": 0.39},
    },
    "writing": {
        "entry_stage": "writing",
        "path": ["writing", "framing", "packaging", "memory"],
        "fundamental": "explanation rights",
        "dissonance": "some groups are given shorthand while others are given complexity",
        "repair": "rewrite the scene before edit and synopsis flatten the same distortion again",
        "harm": {"representation": 74, "revenue": 51, "trust": 77, "safety": 48},
        "wave": {"amplitude": 0.76, "spread": 0.5, "persistence": 0.69, "drift": 0.43},
    },
    "narrative": {
        "entry_stage": "writing",
        "path": ["writing", "framing", "memory"],
        "fundamental": "story consequence",
        "dissonance": "harm is normalized as destiny for some people and complexity for others",
        "repair": "interrupt the trope before the audience is asked to call it realism",
        "harm": {"representation": 81, "revenue": 44, "trust": 75, "safety": 63},
        "wave": {"amplitude": 0.8, "spread": 0.48, "persistence": 0.82, "drift": 0.47},
    },
    "production": {
        "entry_stage": "greenlight",
        "path": ["greenlight", "writing", "casting", "packaging", "ranking"],
        "fundamental": "resource asymmetry",
        "dissonance": "bias enters before the audience sees a frame because the opportunity set is already tilted",
        "repair": "repair budget and staffing before the catalogue pretends the outcome was merit alone",
        "harm": {"representation": 89, "revenue": 81, "trust": 74, "safety": 36},
        "wave": {"amplitude": 0.9, "spread": 0.74, "persistence": 0.88, "drift": 0.42},
    },
    "algorithmic": {
        "entry_stage": "ranking",
        "path": ["ranking", "memory"],
        "fundamental": "feedback eligibility",
        "dissonance": "what was overexposed yesterday becomes the reason to overexpose it again tomorrow",
        "repair": "add counterfactual retrieval, exposure floors, and ranking audits before repetition becomes policy",
        "harm": {"representation": 86, "revenue": 76, "trust": 88, "safety": 69},
        "wave": {"amplitude": 0.84, "spread": 0.8, "persistence": 0.91, "drift": 0.58},
    },
    "intersectional": {
        "entry_stage": "casting",
        "path": ["casting", "framing", "packaging", "ranking", "memory"],
        "fundamental": "compounded exclusion",
        "dissonance": "the people missing from single-axis fixes disappear again once categories combine",
        "repair": "test intersections on purpose because averages will flatter the system otherwise",
        "harm": {"representation": 97, "revenue": 69, "trust": 84, "safety": 72},
        "wave": {"amplitude": 0.93, "spread": 0.76, "persistence": 0.9, "drift": 0.5},
    },
}

ENTRY_STAGE_OVERRIDES = {
    "thumbnail-bias": "packaging",
    "search-bias": "ranking",
    "recommendation-loop": "ranking",
    "category-ghetto": "packaging",
    "metric-myopia": "ranking",
    "director-gap": "greenlight",
    "writers-room-gap": "greenlight",
    "budget-gap": "greenlight",
    "crew-gap": "greenlight",
    "whitewashing": "casting",
    "authentic-casting": "casting",
    "male-gaze": "framing",
}


def _stage_lookup():
    return {stage["id"]: stage for stage in PIPELINE_STAGES}


def _category_profile(category: str) -> dict:
    return CATEGORY_ROUTES.get(category, CATEGORY_ROUTES["writing"])


def _path_with_override(item: dict, base_path: list[str], entry_stage: str) -> list[str]:
    if entry_stage in base_path:
        start = base_path.index(entry_stage)
        return base_path[start:]
    return [entry_stage] + [stage for stage in base_path if stage != entry_stage]


def _harm_profile(category: str, measured_here: bool) -> dict:
    profile = dict(_category_profile(category)["harm"])
    if measured_here:
        profile["trust"] = min(99, profile["trust"] + 6)
        profile["representation"] = min(99, profile["representation"] + 3)
    return profile


def _wave_profile(category: str, measured_here: bool) -> dict:
    wave = dict(_category_profile(category)["wave"])
    if measured_here:
        wave["persistence"] = round(min(0.98, wave["persistence"] + 0.05), 3)
        wave["spread"] = round(min(0.95, wave["spread"] + 0.03), 3)
    return {key: round(float(value), 3) for key, value in wave.items()}


def _role_routes(item: dict, path: list[str], harm: dict) -> dict:
    first = path[0]["label"]
    last = path[-1]["label"]
    measured = "This one is also measured inside Stream, so the library and live metrics can reinforce each other." if item["measured_here"] else "This one is field knowledge first, which means it should sharpen review before the metric layer ever feels certain."
    return {
        "creator": {
            "headline": "What a creator can do",
            "summary": f"Interrogate the script, casting, or packaging boundary where this pattern enters first: {first}. {measured}",
            "actions": [
                f"Check whether {item['name'].lower()} begins in premise, dialogue allocation, or who gets narrative rescue.",
                "Rewrite for agency, not just optics: who acts, who explains, who is looked at, who is believed.",
                f"Do not stop at the cut. Ask how the same pattern might be reintroduced by packaging or ranking before it reaches {last}.",
            ],
        },
        "operator": {
            "headline": "What an operator can instrument",
            "summary": f"This pattern enters at {first} and tends to survive until {last}. The system question is where to place checks before repetition turns into policy.",
            "actions": [
                "Add stage-level checks where the pattern first becomes legible instead of waiting for the final report card.",
                "Compare row-level evidence, packaging labels, and recommendation outcomes so the same distortion is not hidden by one aggregate.",
                "Treat recurrence as a systems problem: if the same bias keeps reappearing, the pipeline is teaching itself the wrong baseline.",
            ],
        },
        "buyer": {
            "headline": "What a buyer or executive should care about",
            "summary": f"The commercial risk is not only reputational. Bias that survives from {first} to {last} narrows demand, wastes catalogue value, and makes forecasting less honest.",
            "actions": [
                f"Read the revenue signal with the representation signal. This pattern currently carries a revenue pressure of {harm['revenue']}/100.",
                "Ask whether underperformance is being manufactured by shelving, framing, or exposure rules rather than the work itself.",
                "Use the result to find missed demand, avoid stale commissioning logic, and reduce preventable trust erosion.",
            ],
        },
        "public": {
            "headline": "What an ordinary viewer or listener can learn",
            "summary": f"This pattern matters because it changes what feels normal. Once it survives long enough to reach {last}, it starts teaching audiences what to expect from real people.",
            "actions": [
                "Notice who gets complexity, who gets shorthand, and who only arrives as atmosphere or warning.",
                "Track the shelf as much as the story: what is missing, what is over-repeated, and what is made to seem niche.",
                "Use the result as a way to ask better questions, not just to label something bad and move on.",
            ],
        },
    }


def bias_propagation_surface() -> dict:
    stage_map = _stage_lookup()
    items = []
    for item in BIAS_LIBRARY:
        category = item["category"]
        profile = _category_profile(category)
        entry_stage = ENTRY_STAGE_OVERRIDES.get(item["id"], profile["entry_stage"])
        path_ids = _path_with_override(item, profile["path"], entry_stage)
        path = [stage_map[stage_id] for stage_id in path_ids if stage_id in stage_map]
        harm = _harm_profile(category, item["measured_here"])
        wave = _wave_profile(category, item["measured_here"])
        items.append(
            {
                "id": item["id"],
                "name": item["name"],
                "category": category,
                "measured_here": item["measured_here"],
                "entry_stage": entry_stage,
                "entry_label": stage_map[entry_stage]["label"],
                "propagation_path": path_ids,
                "path_labels": [stage["label"] for stage in path],
                "fundamental": profile["fundamental"],
                "dissonance": profile["dissonance"],
                "repair": profile["repair"],
                "propagation_summary": (
                    f"{item['name']} usually becomes visible in {stage_map[entry_stage]['label']}, "
                    f"then keeps its force through {' → '.join(stage['short_label'] for stage in path)}."
                ),
                "consequence": item["why_it_matters"],
                "harm_profile": harm,
                "wave_profile": wave,
                "role_routes": _role_routes(item, path, harm),
            }
        )
    return {
        "stages": PIPELINE_STAGES,
        "roles": ROLE_LIBRARY,
        "items": items,
        "notes": {
            "headline": "Bias rarely appears once. It enters, gets reinforced, then starts to feel natural.",
            "method": "This propagation layer is a public interpretive map built from the documented bias library and the live Stream metrics, not a claim of hidden private instrumentation.",
        },
    }
