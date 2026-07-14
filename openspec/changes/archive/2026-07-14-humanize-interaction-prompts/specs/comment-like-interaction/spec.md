## MODIFIED Requirements

### Requirement: Occasional comment-like decision on note detail

During the detail-page comment-reading window (after the comment section has been scrolled on-screen and before any note-level interaction fires), the system SHALL occasionally select at most ONE other person's comment to like, based on an LLM value judgement over the note body and the on-screen candidate comments. Most visits SHALL abstain. The selection SHALL exclude the bot's own comment, any already-liked comment, and any comment without a usable anchor. The value-judgement criteria SHALL derive from the account persona (`like_principle` / `tone` / interests injected into the prompt), NOT from a fleet-wide fixed rubric — the prompt MUST NOT hard-code a single taste model (e.g. the "interest / knowledge-depth / resonance" three-axis wording) identically for all accounts; universal negative rules (ads / self-promo / off-topic / "reads like something you would write yourself") remain as fixed exclusions.

#### Scenario: Picks a single high-value comment

- **WHEN** the pre-gate allows a comment-like this visit and at least one candidate comment qualifies
- **THEN** the appraiser selects exactly one comment (never two or more) judged most worth liking by criteria derived from the account persona

#### Scenario: Persona drives which comment gets liked

- **WHEN** two accounts with different personas (e.g. knowledge-seeking vs humor-loving) evaluate the same candidate comments
- **THEN** their prompts carry different persona-derived criteria, allowing different picks; the criteria section MUST NOT be byte-identical across personas

#### Scenario: Abstains when nothing is worth liking

- **WHEN** no candidate comment qualifies (all already-liked, anchorless, own, or low value)
- **THEN** the visit likes no comment and emits no like command

#### Scenario: Never targets own or already-liked comments

- **WHEN** the candidate list includes the bot's own just-posted comment or a comment already in the liked state
- **THEN** those candidates are filtered out before selection
