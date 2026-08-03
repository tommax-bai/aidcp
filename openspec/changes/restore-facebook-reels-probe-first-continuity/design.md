## Context

The maintained Facebook Reels actuator already limits each `page.scroll` command to one trusted key and accepts only canonical `/reel/<id>` progress. Its remaining admission path still asks unstable page structure to authorize that reversible key: one active video must win a viewport heuristic, global next controls must establish exactly one axis, blocker text must not match broad body-copy patterns, and repeated probes must preserve the same canonical observation.

The captured live `/reel/` shape is keyboard-safe but contains a disabled `Next items` control plus an active viewport-scale `Next Card` overlay. The router reports no unique axis, so Rust returns `reels_target_unavailable` before sending any key. Similar DOM classifications have changed repeatedly, making structural fallback refinements a source of stalls rather than continuity.

This change follows `remove-facebook-reels-video-key`. It preserves that change's one-write and canonical-identity boundaries, but supersedes structural-axis authorization and command independence with a small, non-blocking keyboard-probe preference. Cloud's current source already continues the relevant terminal Reels outcomes through normal admission; the observed OL runtime may still predate that continuation and is outside this source-only change.

## Goals / Non-Goals

**Goals:**

- Make reversible Reels navigation depend only on stable surface, input-safety, cancellation, and deadline facts.
- Ensure an input-safe Reels command can always make one bounded keyboard probe even when active-video or control structure is missing, ambiguous, disabled, occluded, or changing.
- Learn the useful key from canonical outcomes across normally admitted commands without creating a pending latch or retry loop.
- Keep navigation success, view accounting, cadence, and interactions tied to a freshly resolved canonical Reel card.
- Remove obsolete axis-target production code and cover the composed JavaScript-to-Rust behavior that previously escaped router-only tests.

**Non-Goals:**

- Dispatch two keys, wheel input, or a pointer fallback within one command.
- Treat input delivery, DOM movement, video replacement, or route hydration alone as success.
- Relax exact-target or verified-postcondition gates for likes, comments, follows, joins, or publishing.
- Add a policy knob, protocol field, database state, retry debt, or Cloud fast-path.
- Package or install Edge, deploy Cloud, verify an OL runtime SHA, or act on a real account.

## Decisions

### 1. Stable safety facts alone authorize a keyboard probe

Before input, Edge will require a live bound Facebook command, an exact Reels route, a fresh explicit keyboard-safe result, and open cancellation/deadline gates. Keyboard safety continues to reject editable focus, login, captcha, and consent states. A checkpoint or non-Reels route fails the exact-surface gate.

Active-video uniqueness, canonical identity, next-control labels, geometry, disabled state, hit testing, occlusion, and axis classification will not authorize or veto the reversible key. Broad body-copy matches such as generic action restrictions will also stop vetoing Reels keyboard browsing; exact login/captcha/consent evidence remains authoritative. These structural observations may still participate in card reporting and irreversible interaction targeting.

Alternative considered: retain the axis classifier as a soft first-key hint. Rejected because it preserves a large unstable mechanism whose only remaining effect can be learned more reliably from canonical outcomes.

### 2. Session state chooses a key but never blocks a command

Each Facebook session stores one preferred Reels probe key. A new session starts with ArrowRight. A command reads that preference once and dispatches exactly that key. After the trusted key gesture is delivered, the tentative preference changes to the other key; if bounded observation confirms canonical progress, the successful key becomes preferred again. Therefore an unconfirmed command makes the next normally admitted command try the other key, while a confirmed command keeps using the learned direction.

The preference contains no content identity, transition latch, timestamp, retry count, or eligibility flag. A command that sends no input does not change it. Resetting the browser/session merely returns to ArrowRight; it cannot strand the browse loop.

Alternative considered: try both keys inside one command. Rejected because a delayed first transition could cause a double advance and would bypass normal pacing.

### 3. Canonical post-state remains the only progress fact

After the single key, Edge runs the existing bounded canonical observation. A previously identified Reel succeeds only when the active reportable `noteId` changes; an anonymous pre-state succeeds only when a canonical active Reel appears. A unique active video remains necessary to bind a reported card or irreversible interaction, but it is a postcondition/targeting fact rather than keyboard admission authority.

No canonical progress produces one honest ambiguous receipt and no card, view, cadence, or interaction. This negative observation updates only the soft key preference and cannot disable later commands.

### 4. Reels entry observes first, then uses the same probe boundary

Configured Reels entry retains its bounded canonical hydration window because a card can often be reported without input. If no reportable card appears but the exact Reels surface is keyboard-safe, the same command proceeds to one keyboard probe. Missing or ambiguous video structure cannot terminate the entry before that probe. Unsafe or off-surface entry still performs zero input.

### 5. Remove the axis-target path from maintained scrolling

The `reel_next_target` router command, Rust decoder, axis/control eligibility logic, and tests that assert zero input for unresolved or competing axes will be removed from the maintained scroll path. The active-video/card probe remains for canonical reporting and interactions. Feed scrolling and the `native_reels_actuator_required` boundary remain unchanged, so JavaScript document scrolling cannot silently replace Native input on Reels.

### 6. Validate composed behavior and normal continuation

Router tests will prove that the captured live shape is explicitly keyboard-safe without requiring a reportable active card. Fake CDP tests will prove the complete command behavior: axisless first probe, cross-command alternation, confirmed-key retention, and zero input for editable focus, login, captcha, non-Reels, cancellation, or insufficient deadline. Cloud coverage will parameterize the existing three terminal continuation reasons and prove they still pass through ordinary dwell and admission rather than becoming an immediate retry.

## Risks / Trade-offs

- [ArrowRight is ineffective on a vertical account] -> The command ends honestly; the next normally admitted command tries ArrowDown. There is no same-command retry.
- [A key moves an anonymous Reel but canonical identity does not hydrate] -> Edge reports no view and alternates the next probe. The possible movement is not promoted to business success.
- [The first key was effective but canonical observation missed it] -> The next command may try the other key once. One-key-per-command and normal Cloud pacing bound the effect; no structural guess can provide stronger stable evidence.
- [Session recreation forgets the learned key] -> The new session starts with one ArrowRight probe and can relearn; no durable migration is required.
- [OL still runs pre-continuation Cloud code] -> Source validation cannot prove deployed OL behavior. No OL deployment or runtime claim will be made without explicit authorization.

## Migration Plan

1. Apply this change after the source behavior from `remove-facebook-reels-video-key`; keep its one-key, canonical-only, and Cloud-continuation boundaries.
2. Land the Edge implementation and focused Cloud regression independently, then validate the OpenSpec change strictly.
3. Integrate and push source changes only. Do not package/install Edge or deploy DEV/OL as part of this request.
4. Roll back the Edge commit to restore structural-axis authorization if validation fails; there is no schema, protocol, policy, or durable-data migration.

## Open Questions

None.
