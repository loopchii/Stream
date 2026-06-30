# Governance

This repository is a public LOOPCHii research surface. It is independent from private LOOPCHii runtime systems and should stay that way.

Governance in this repo means something practical:

- the scope is visible
- the maintainership is clear
- the claim boundary is defended
- contributors know what can and cannot land

## Repository steward

Primary stewardship currently sits with Cazandra Aporbo under LOOPCHii.

That stewardship includes:

- approving or declining changes that alter the public claim boundary
- maintaining separation between public repo surfaces and private LOOPCHii work
- keeping documentation aligned with actual code and data behavior
- correcting overstatements when they appear

## What this repo governs

This repo governs its own public surfaces:

- the browser experience in `index.html`
- the FastAPI surface in `app.py`
- committed static artifacts in `data/`
- reproducibility and runtime checks in `stream_backend/`
- documentation and contributor guidance

It does not govern or disclose private LOOPCHii enforcement systems, private customer data, or private infrastructure design.

## Decision standard for merges

Changes should improve at least one of these:

- reproducibility
- clarity
- source discipline
- analytical usefulness
- documentation quality
- accessibility or interaction quality

Changes should not:

- introduce unverified claims
- blur synthetic and public data lanes
- weaken attribution
- add private architecture
- make the repo sound more capable than the code proves

## Public claim boundary

Every major contribution should respect these rules:

1. Synthetic representation analysis must stay labeled as synthetic.
2. Public music analysis must stay tied to documented public-source inputs.
3. Derived metrics must be traceable to code in the repository.
4. Legal or privacy claims should match the documented data boundary.
5. Uncertainty should remain visible when evidence is incomplete.

## Documentation parity

If a change affects:

- licensing
- data provenance
- privacy posture
- contributor expectations
- public claim strength

then the related documentation should be updated in the same change set.

At minimum, that usually means checking:

- `README.md`
- `contributing.md`
- `docs/PRIVACY_AND_DATA.md`
- `docs/ETHICS.md`
- `data/README.md`

## Correction policy

If a claim, attribution line, or data-use statement is wrong, the correction should be:

- visible
- prompt
- tied to the exact surface that was wrong

Quietly fixing a public misstatement without documenting the boundary change is not good governance.

## Escalation triggers

Open an issue or pause a merge when a change:

- adds a new third-party dataset
- changes the legal or privacy posture
- introduces a new high-impact claim
- pulls the repo closer to private LOOPCHii architecture
- uses identity labels or inferred attributes in a more consequential way

## Release discipline

For public releases, the minimum expectation is:

- tests or runtime checks pass
- static artifacts are refreshed when required
- relevant docs match the current behavior
- the repo still reads as a serious open analysis repository rather than a marketing shell

## Governance posture in one sentence

This repository should remain inspectable, bounded, and useful enough to earn trust without pretending it contains more than it does.
