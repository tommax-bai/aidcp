## Context

The installed AIDCP 0.3.25 package built from Edge `c8e26e4` reproduced two post-login races on a live AdsPower profile. Native reported `authenticated` at `11:22:43.406`, while the Facebook `privacy/consent` document began at `11:22:43.494`; Edge therefore established identity and connected to Cloud about 80 ms before the blocking page existed. A later browse command reached that page and returned `no_target`.

The live page is not the existing cookie-consent overlay. It is the exact first-time `ad_free_subscription` review flow: an introduction with one `Get started` control, followed by an account-level subscription/data-processing choice. The first click makes no privacy choice, while the successor does. The same startup race can hide the already-supported `Remember Password?` modal because the current coordinator stops at the first authenticated observation.

Native already owns exact auth-page classification, one-signal/one-action replay protection, fresh target revalidation, humanized CDP pointer movement before press/release, and bounded postcondition polling. The change must extend those contracts instead of adding Electron DOM access, GUI automation, or a second competing page watcher.

## Goals / Non-Goals

**Goals:**

- Hold startup through a bounded authenticated quiet window so late post-login prompts are observed before Cloud connection.
- Add an exact, independent signal for the first-time ad-data review introduction and one Native `Get started` action.
- Treat the successor account choice as an unbounded controlled manual state, then resume in the same process/browser/CDP generation after the operator finishes.
- Let the existing Remember Password `OK` capability run during the authenticated quiet window.
- Move the CDP pointer before every click, inspect loading/disabled/target-disappearance states after dispatch, and confirm the ad-data action only when the exact successor choice structure appears within a 30-second budget.

**Non-Goals:**

- Automatically choosing subscription, free-with-ads, personalized, or less-personalized options.
- Treating the Feed “manage your ad experience” card as the same prompt or clicking its `Get started` link.
- Generic consent/dialog clicking, changes to cookie-consent overlay policy, browser-chrome automation, Cloud protocol, risk state, packaging, deployment, or AdsPower `user/update` retry policy.

## Decisions

### 1. Keep one auth coordinator and add an authenticated quiet window

After the first structurally confirmed `authenticated` observation, the coordinator SHALL continue read-only probes for 15 seconds. A supported late prompt resets the quiet window and is handled by the same serial consumer; only 15 seconds with no supported blocker permits identity read and Cloud startup.

A separate post-login watcher was rejected because it would race the startup coordinator for signal ownership and replay state. Returning immediately on cookies was rejected by the observed 80 ms navigation race.

### 2. Model the introduction as a dedicated auth-page signal, not generic consent

Native SHALL emit `ad_data_review_get_started` only when all of the following agree: Facebook origin, `/privacy/consent/`, `flow=ad_free_subscription`, `afs_variant=first_time`, the observed introduction heading/body, and one visible enabled topmost `Get started` control. The Feed card with the same label cannot match because its route and bounded page structure differ.

The matching action SHALL be `facebook_auth_start_ad_data_review`, preserving the auth owner, fresh signal id, consumed-signal budget, and Native pointer path.

### 3. Confirm the successor, not the temporary loading state

The action verifier SHALL poll for up to 30 seconds. It SHALL observe whether the original control becomes disabled/disappears and whether the document enters a loading state, but those facts only prove dispatch/progress. Success requires the exact successor choice structure containing both subscription and free-with-ads options. A document change by itself, blank loading shell, the old signal merely disappearing, timeout, or an unsupported destination is ambiguous after input and MUST NOT trigger a replay.

The existing generic “signal gone” verifier was rejected for this action because the live page temporarily reduced to the account name before the successor hydrated.

### 4. Defer identity reads while the privacy choice is unresolved

The exact successor page SHALL return `manual_login_required` with enumerated reason `facebook_ad_data_choice_required`. Electron projects a specific “需要处理” message and releases only the serial launch waiter; the core, browser, CDP session, and slot remain owned.

The retained wait re-enters the same coordinator at the existing sparse cadence. `waitForLoginIdentity` gains an explicit `defer` preflight result so it skips identity reads while this reason remains active; otherwise valid cookies would bypass the choice page. Once the operator finishes and the coordinator completes a new authenticated quiet window, the next stable identity read proceeds normally.

### 5. Reuse Remember Password recognition and Native input

The existing exact dialog text, unique visible/topmost `OK`, fresh-signal validation, and `facebook_auth_confirm_remember_password` action remain authoritative. Extending the authenticated quiet window makes the capability reachable when the card renders after cookies become valid; no second selector set or direct DOM `click()` is added.

## Risks / Trade-offs

- [Normal Facebook startup gains up to 15 seconds] → The delay is bounded, occurs before Cloud work, and closes the reproduced late-navigation race.
- [Facebook changes the ad-data wording or route] → Native returns an unsupported/manual-safe result and does not click a same-label Feed link.
- [The introduction click enters loading but never reaches the choice page] → Report ambiguous after input, retain no replay authority, and expose bounded diagnostics.
- [An operator changes accounts while completing the manual choice] → Startup still performs the existing stable identity read after the manual gate before any Cloud connection.
- [The manual choice is never completed] → The retained session remains explicitly “需要处理” and responds to pause/close through the existing confirmed browser-close path.

## Migration Plan

1. Implement in an isolated `aidcp-edge` worktree with router, Native command, coordinator, retained-wait, lifecycle projection, and regression tests.
2. Run focused TypeScript/router/Electron tests, typecheck, Native fmt/clippy/tests, and strict OpenSpec validation.
3. Fast-forward Edge `master` and control `main` only after all gates pass.
4. Packaging/installation remains a separate explicit action. Rollback is a source revert; there is no data, protocol, or schema migration.

## Open Questions

None for source implementation. The exact Remember Password card was not present on the surviving live profile, so installed-package verification must separately reconfirm its real DOM and post-click state when that card next appears.
