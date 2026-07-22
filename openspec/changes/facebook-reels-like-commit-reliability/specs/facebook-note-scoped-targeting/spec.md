## ADDED Requirements

### Requirement: Reel like commit uses per-control event semantics and remains bound to the active Reel

For a Facebook like command targeting a canonical `/reel/<id>` identity, Edge MUST freshly resolve exactly one supported primary reaction control associated with the uniquely active video immediately before the write and MUST confirm that the current canonical Reel still equals the commanded identity. The primary React control SHALL be activated against the freshly resolved in-page element rather than by consuming a stale saved coordinate. Edge MUST then verify a positive selected-state witness on the same Reel.

If the primary activation does not produce a selected-state witness but opens a visible reaction picker, Edge MAY perform exactly one second-stage commit. It MUST locate a unique supported Like item only inside a unique visible picker containing multiple recognized reaction items, MUST reject ambiguous or off-screen picker targets, and MUST dispatch trusted CDP pointer events to that picker item. Edge MUST NOT search the whole document for a bare Like label and MUST NOT dispatch a second primary activation.

Across both direct-toggle and picker layouts, Edge MUST dispatch at most one primary activation and at most one picker commit. Same-Reel positive unlike/remove, `aria-pressed`, `aria-checked`, or supported reacted-word state MAY prove success; a reaction count, generic image descendant, dispatched event, or opened picker MUST NOT. Reel movement or target ambiguity after a write SHALL return `verify_indeterminate` without another click. An unchanged or unproven state SHALL return `state_unchanged`, and neither outcome may be recorded, budgeted, or displayed as a successful like.

#### Scenario: Fresh primary activation directly selects Like

- **WHEN** the commanded Reel is still uniquely active and its supported primary reaction control directly changes to a positive selected state after fresh in-page activation
- **THEN** Edge returns `ok:true` for that same Reel after one primary activation and dispatches no picker click

#### Scenario: Primary activation opens the reaction picker

- **WHEN** the commanded Reel remains uniquely active, the primary activation does not select Like, and one visible reaction picker contains multiple recognized reactions with one visible Like item
- **THEN** Edge dispatches one trusted pointer click to that picker-scoped Like item and returns success only after the same Reel exposes a positive selected-state witness

#### Scenario: Bare Like controls outside the picker are never fallback targets

- **WHEN** the document contains other controls whose label is Like while the active Reel picker is absent, ambiguous, or lacks a unique visible Like item
- **THEN** Edge dispatches no second-stage click outside the picker and returns a truthful non-success result

#### Scenario: Reel moves after the primary write

- **WHEN** the canonical active Reel or its unique active-video association changes after the primary activation and before confirmation
- **THEN** Edge returns `verify_indeterminate`, dispatches no picker or replacement primary click, and does not report success

#### Scenario: Dispatched events without selected state are not success

- **WHEN** Edge dispatches the bounded primary and optional picker events but reads no same-Reel positive selected-state witness
- **THEN** Edge returns `state_unchanged` and Cloud does not consume successful-like quota or display a successful like
