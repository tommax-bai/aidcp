## MODIFIED Requirements

### Requirement: Rule browsing does not use persona relevance or interaction preference

For an account admitted to Facebook rule mode, Cloud SHALL select structurally eligible unseen Facebook content in reported order without reading Soul identity, interests, like affinity or `mandatory_interactions`, and without invoking the persona relevance or persona interaction appraisers. Rule mode MUST NOT require the account to have a bound persona: admission, browsing and the fixed like intent SHALL proceed for an unbound account without substituting any default or replacement persona. Login/challenge/consent checks, canonical content identity, duplicate/visited checks, a Soul-free prohibited-content safety gate, platform capability, pacing, target validation and post-action verification MUST remain in force.

#### Scenario: Persona mismatch does not skip a rule-mode card
- **WHEN** the next safe, structurally valid unseen Facebook content is unrelated to any persona interests
- **THEN** rule mode MAY browse it without calling the persona content evaluator

#### Scenario: Mandatory persona rule does not redirect selection
- **WHEN** a bound Soul contains a `mandatory_interactions` rule and rule mode is active
- **THEN** that rule does not prioritize a card, create an interaction intent or alter the fixed ten-view cadence

#### Scenario: Safety rejection still blocks a card
- **WHEN** a structurally visible card fails the Soul-free prohibited-content or page-identity safety gate
- **THEN** rule mode rejects it with a named reason and does not count it or act on it

#### Scenario: Unbound account is admitted to rule mode
- **WHEN** a Facebook environment has rule mode enabled and its bound account has no persona
- **THEN** rule-mode admission, browsing and the batch like proceed normally and the system MUST NOT substitute a default persona or emit `no_persona`

## ADDED Requirements

### Requirement: The rule batch comment leg requires a template body scheme

Before invoking the join-contact orchestrator, the rule batch SHALL resolve the account's effective comment body scheme. The comment leg MAY proceed only when that effective scheme is template — either an explicit template scheme or the existing default for an account with no explicit scheme, in both cases resolving the body through the established account-template-first, region-template-fallback order. When the effective scheme is explicitly generated, the comment leg MUST terminate with a stable named reason, the batch MUST keep its browse and like outcomes and settle as partial, and the system MUST NOT invoke the comment generator, MUST NOT read any persona and MUST NOT substitute a template for the operator's explicit choice.

Template bodies SHALL continue to pass the existing deterministic body validation, separate contact injection, approval policy, target re-check, platform confirmation and truthful terminal accounting. This requirement MUST NOT weaken any of them, and MUST NOT change the join-contact orchestration path itself.

#### Scenario: Default scheme account comments from the region template
- **WHEN** an unbound-persona account with no explicit body scheme reaches the comment leg after a confirmed join
- **THEN** the body resolves through the region template for that group and the comment proceeds under the existing validation, approval and confirmation gates

#### Scenario: Explicit template account uses its own templates
- **WHEN** the account explicitly selects the template scheme and has non-empty account templates
- **THEN** the body comes from the account templates without reading any persona

#### Scenario: Explicit generated scheme makes the comment leg unexecutable
- **WHEN** the account explicitly selects the generated scheme and the batch reaches the comment leg
- **THEN** the comment leg terminates with a stable named reason, the generator is not invoked and the batch settles as partial with its browse and like outcomes intact

#### Scenario: Missing template is an honest stop, not a persona fallback
- **WHEN** the effective scheme is template but the group has no region or the region has no valid template
- **THEN** the existing named stop applies and the system MUST NOT fall back to the generator, another region's template or any default text

#### Scenario: Template body still passes every safety gate
- **WHEN** a resolved template body contains a URL, contact details, mentions or other prohibited content
- **THEN** deterministic validation rejects it before submission and the batch does not report comment success
