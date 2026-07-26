## Context

The Native-only production boundary is correct, but the first Facebook cutover compressed several evidence-backed action state machines into one-shot router calls. Two live failures now expose the same migration class:

- Reels receives and dispatches Like commands, yet the router rejects a uniquely associated `aria-label="赞"` control with numeric text before the proven DOM commit path.
- Publish reaches the correct Facebook home domain and page, yet the router omits `分享你的新鲜事` and returns `composer_entry_not_found`.

Source comparison shows the Reels failure is partly architectural: multilingual reaction constants are declared by `10-feed-like.js` and consumed by `30-reels.js`. Publish has a larger transaction regression. The retired executor made `navigate_entry` navigate and validate the home surface, while `select_mode` waited for a late entry, clicked once, and verified the editor. Native currently makes `navigate_entry` immediately probe/click after navigation and makes `select_mode` a successful no-op. Its entry and submit vocabularies are also strict subsets of the retired oracle.

A bounded audit of the other action families found one additional gap: Native Comment copies the editor, participation-gate, rejected, in-flight, Like, and Reply patterns, but narrows the pending-approval veto and omits established phrases such as administrator-approval and visible-after-approval variants. Current Group Join, Consent/blocker, and author-bound Reels Follow vocabularies are equivalent to or safe supersets of their retired oracles after the recent parity repairs.

## Goals / Non-Goals

**Goals:**

- Restore observed Reels Like, Publish entry/select-mode, and Comment approval semantics inside their Native capability owners.
- Give cross-surface reaction vocabulary one Native-only owner while keeping surface target evidence and transactions separate.
- Preserve one absolute command budget, one fresh write, same-target verification, and truthful effect phases.
- Make the action-vocabulary audit executable so later migrations cannot silently shrink proven language families.
- Keep equivalent Join, Consent/blocker, and Reels Follow behavior unchanged.

**Non-Goals:**

- Adding unobserved locale strings, fuzzy similarity, free-text content matching, retries, flags, or configuration.
- Reintroducing TypeScript page execution, `CloudElementSelector`, `LikeStepRunner`, or an online LLM-authorized write.
- Changing Cloud planning, probability, risk/quota accounting, protocol, command names, account lifecycle, or success receipts.
- Reworking unrelated Feed browsing, Group Join, Consent, Follow, installer, signing, or release behavior.
- Claiming real-account action success from fixture, fake-CDP, source, or artifact validation.

## Decisions

### Record a closed action-semantics audit before editing

The change treats the retired executors and their focused tests as behavior oracles, then classifies each action family:

- repair: reaction semantics/Reels Like, Publish entry/select/submit vocabulary and lifecycle, Comment pending-approval veto;
- retain with regression evidence: Reels Follow, Group Join, Consent/blocker, Comment editor/rejected/in-flight/ack controls;
- unsupported behavior remains unsupported.

Only observed or previously tested semantics are migrated. A broad union of every human translation was rejected because false-positive writes are more dangerous than an honest unsupported label.

### Put lexical reaction semantics before Feed Like and Reels

Add one explicitly ordered router fragment between shared DOM helpers and capability modules. It owns bounded neutral, bare-Like, reacted, remove/unlike, picker, and post-comment lexical primitives plus positive selected-state classification.

Feed Like and Reels consume those primitives. The fragment does not own card identity, active video, geometry, uniqueness, markers, actuation, or verification. Reels adds one surface rule: a supported bare Like label with numeric rendered text is neutral only after the existing active-video/right-rail/size/viewport/exclusion/uniqueness gates pass. Feed retains its direct-card, non-summary-toolbar, shared post action-bar witness.

Keeping the vocabulary in Feed Like was rejected because another capability then depends on Feed implementation order. Adding bare `赞` to every neutral matcher was rejected because Feed reaction summaries have the same lexical shape.

### Restore Publish stage ownership instead of adding a label-only patch

`PublishNavigateEntry` will:

1. pass the action gate;
2. navigate once to `FACEBOOK_HOME_URL`;
3. poll within the command budget, up to the established 20-second navigation window, for an interactive/complete home surface with a visible main region or already-open composer;
4. return confirmed without clicking the composer entry.

`PublishSelectMode` will:

1. validate `optionKind=target` and `optionValue=facebook_personal_timeline`;
2. pass the action gate and confirm the home surface from one Publish-owned snapshot containing URL, ready state, visible main, editor, blocking-dialog, and credential-input evidence;
3. return confirmed if the editor is already open;
4. poll for the entry for at most the established 20-second trigger window, bounded by the caller's absolute deadline;
5. freshly re-probe and dispatch at most one trusted pointer click;
6. spend only the remaining command budget verifying that one composer editor opened.

The established Facebook `select_mode` caller deadline is 40 seconds. The Native Publish executor, TypeScript adapter, client validation, and Rust command ceiling preserve that value end to end; the 20-second trigger window consumes the first part and editor verification receives only the remainder. The 30-second default remains unchanged for other Publish commands. Every awaited probe is followed by another absolute-deadline check so a slow CDP response cannot turn an expired command into success. As in the retired executor, bounded navigation and post-click confirmation loops treat a transient read error as an absent witness and continue only inside the existing deadline; initial target probes still surface their error and no retry can dispatch another write.

Before the click, loss of the home surface or target remains `not_started`. After the click, target loss or timeout is ambiguous and never retried. The router entry vocabulary is restored from the retired oracle: English variants, zh-CN `写点什么`/`创建帖子`/`分享你的新鲜事`, Vietnamese, and Spanish. One and only one canonical visible entry is required; ranking does not erase ambiguity. Submit restores zh-TW and Spanish forms already present in the oracle.

Keeping the current immediate `navigate_entry` click was rejected because the entry may render late and the stage no longer means navigation. Keeping `select_mode` as a no-op was rejected because it reports progress without opening the editor.

### Keep Comment lifecycle vocabulary inside Comment

Comment keeps its capability-owned editor and acknowledgement logic. The pending-approval expression is restored to the full retired positive veto set, and both initial participation gating and post-submit acknowledgement consume their intended distinct expressions. Submitted text is still removed before lifecycle matching; pending words in the user's own comment cannot veto a valid server acknowledgement.

Moving all action words into one global vocabulary was rejected because reaction, Publish, Comment, Join, and Consent phrases have different target scopes and safety meaning. Only genuinely cross-surface reaction semantics are shared.

### Prohibit generic online selection in the write transaction

Unknown labels produce existing safe not-found or unconfirmed results. No live element list leaves Native for Cloud selection, and no LLM result authorizes a click. An LLM may support a separate read-only discovery workflow, but new production vocabulary requires observed evidence, a capability rule, and fixtures.

### Validate source ownership, behavior, and packaging separately

Focused tests cover:

- retained Like locales, the observed `赞` plus count layout, decoys, ambiguity, and positive-only verification;
- every retired Publish entry/submit/submitted-state label family, late entry, already-open editor, home loss, one-click bound, and post-click timeout;
- full Comment pending-approval phrases and submitted-text stripping, plus executable retain-only matrices for Follow, Group Join, Consent, Comment editor, rejected, in-flight, Like, and Reply families;
- manifest order, capability ownership, parity ledger, and absence of generic selector/runner wiring.

Existing production-dist and Native artifact checks continue to prove page rules remain outside shipped JavaScript. Real-account acceptance remains a separate gate.

## Risks / Trade-offs

- [A new locale remains unknown] → Fail closed and add only evidence-backed vocabulary with a focused fixture.
- [A numeric summary resembles a Reel action] → Require the complete active-video right-rail witness and exact uniqueness.
- [Publish entry appears near the command deadline] → Use one absolute deadline; do not stack trigger and editor timeouts or click after budget expiry.
- [A slow CDP probe returns success after the deadline] → Recheck the absolute deadline after every awaited successful probe; keep pre-click expiry `not_started` and post-click expiry ambiguous.
- [A transient read fails during a bounded observation loop] → Preserve the retired read tolerance only for navigation and post-click confirmation; do not retry target resolution or actuation.
- [Publish leaves home while waiting] → Stop before dispatch with a home-state reason; never search another surface for similar text.
- [Comment body contains approval words] → Strip the submitted body before lifecycle matching and require own-row identity plus server/controls evidence.
- [Audit work causes unrelated rewrites] → Change only the three proven gap families and add retain-only regression assertions for the rest.
- [Automated tests do not prove React acceptance] → Report source/artifact validation separately and leave real-account writes unclaimed.

## Migration Plan

1. Update this OpenSpec change from the completed action-semantics audit.
2. Add the shared reaction fragment and migrate Feed Like/Reels lexical consumers.
3. Restore Publish navigation/select-mode state machines, localized entry/submit vocabulary, and parity-ledger descriptions.
4. Restore Comment pending-approval vocabulary without changing submit or success semantics.
5. Add focused router, Rust, source-boundary, and retained-oracle tests.
6. Run Cargo format/clippy/full tests, Edge focused/acceptance/full/typecheck, Native build/verification, production dist, desktop build-input, and strict OpenSpec validation.
7. Rebase and fast-forward integrate Edge and control changes, then rebuild the canonical local development Native artifact. The pending non-submit live probe and real Publish acceptance from `facebook-composer-open-deadline` remain required; installer, signing, runtime restart, and real-account writes remain separate gates.

Rollback is a revert of the Edge and control commits followed by rebuilding the prior Native artifact. There is no data, Cloud, protocol, or configuration migration.

## Open Questions

None. Further localized layout evidence becomes a capability-specific observed change rather than a fuzzy or LLM-authorized fallback.
