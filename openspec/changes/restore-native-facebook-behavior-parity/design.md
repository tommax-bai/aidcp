## Context

Facebook page execution was moved from the TypeScript `FacebookSession` and its focused executors into a Native-only Rust process plus an embedded DOM router. The cutover preserved the external command envelope, but the first Native implementation collapsed stateful, multi-stage behaviors into mostly stateless one-shot DOM evaluations.

The comparison uses this authority order:

1. archived and active OpenSpec Facebook requirements;
2. Edge/Cloud protocol and result-reason semantics;
3. the retired TypeScript executor and its tests as the last known implementation oracle;
4. the current Native implementation only where it is at least as strict as the above.

Observed and source-confirmed gaps include:

- initial Feed scan polls one viewport and returns `present_unreportable`; ordinary Feed scrolling performs one scroll and has no session cursor or exhaustion proof;
- any zero-card viewport can become `empty` without stable empty/loading evidence, allowing Cloud to enter Reels while Feed content exists;
- refresh is a raw reload rather than a bounded SPA refresh with changed-card proof;
- generic checkpoint and Facebook throttle pages are not reported as unknown blockers, and cookie consent ignores the configured policy;
- target actions may fall back to the first article when the commanded post is absent;
- comment submission uses synthetic DOM keyboard events and changes the established `verification_ambiguous` reason, which can make an uncertain write retryable;
- join and publish return after a single short observation;
- commands that the Facebook platform never declared are partially implemented by the generic router.

### Facebook command parity ledger

| Platform behavior | Native disposition | Existing behavior oracle |
| --- | --- | --- |
| identity and page/blocker probes | supported; read-only and bounded | `facebook-identity-reader`, `overlay-detector`, and their tests |
| Feed startup, scroll, refresh, and back | supported; stateful home/search cursor | `facebook-session`, `feed-reader`, and Feed lifecycle tests |
| Reels cards, next, like, and follow | supported; active-video identity required | `reels-reader`, `like-executor`, and Reels tests |
| global or container search and note detail | supported; canonical result identity required | `facebook-session`, `comment-handler`, `comment-executor` |
| post like | supported; exact post or active Reel only | `like-executor` and note-scoped targeting tests |
| post comment | supported; exact editor, trusted submit, same-account acknowledgement | `comment-executor` and lifecycle/participation tests |
| group join | supported; current-group scope and durable post-click state | `join-executor` and target-scope tests |
| personal-timeline publish subset | supported; existing atom contract only | `publish-executor`, composer probes, and publish tests |
| collect, comment-like, image browse, comment scroll | unsupported; pre-dispatch `capability_unsupported` | `FacebookSession.reportUnsupportedCommand` |
| notification commands and author-profile browse | unsupported; pre-dispatch `capability_unsupported` | `FacebookSession` platform switch and tests |

## Goals / Non-Goals

**Goals:**

- Restore established Facebook behavior in the Native-only runtime without a TypeScript page fallback.
- Make every supported command stateful, bounded, exact-target, and honest about its terminal effect.
- Restore platform capability truth by rejecting unsupported commands before DOM actuation.
- Port focused behavior tests so future Native migrations cannot regress established contracts silently.

**Non-Goals:**

- Change Cloud orchestration, risk policy, pacing, quotas, or the Edge-Cloud protocol.
- Re-enable Facebook author-profile browsing, comment likes, carousel browsing, comment scrolling, notifications, or collect.
- Add retries, compatibility branches, or feature flags beyond the existing bounded product contracts.
- Build or release an Electron installer, deploy OL, or manufacture real-account write evidence.
- Repair the independent DEV `risk-accounting` database constraint failure.

## Decisions

### 1. Keep stateful Facebook browse state inside the Native session

`EngineSession` will own Facebook-only session state: active list URL/kind, seen canonical post identities, initial/unreportable continuation progress, and refresh reload timing. The embedded router remains responsible for bounded DOM extraction and returns structural observations such as canonical cards, loading state, scroll metrics, blockers, and click targets.

This is preferable to keeping state in the TypeScript facade because the Native process owns the CDP session and atomic command boundary. It also avoids reintroducing a split page executor.

### 2. Treat `empty`, `present_unreportable`, and `feed_exhausted` as different facts

Initial and ordinary Feed scans will use the existing loading-aware settle rule. Visible articles with no trusted permalink trigger bounded downward continuation, not Reels. `empty` requires stable explicit zero-content evidence with no loading or blocker. `feed_exhausted` requires no new canonical identity, no document growth, near-bottom state, and consecutive confirmation. Seen identities are filtered per Native session.

Reels remains Cloud-authorized only after a truthful explicit empty result. Native will not infer a surface switch from layout inconvenience.

### 3. Preserve the existing list surface across open/back/search/refresh

The Native session tracks the current home or search URL. Back returns to that list surface. Feed refresh first uses the Facebook home control and verifies a non-empty changed top identity; a raw reload is available only as the existing three-minute bounded fallback.

### 4. Separate read probes from trusted actuation

The embedded router may inspect DOM and return a unique scoped target with coordinates and post-action evidence. Irreversible or state-changing input is dispatched through CDP mouse, wheel, key, and text primitives from Rust. Synthetic `HTMLElement.click()`, synthetic keyboard events, and direct `textContent` mutation are not sufficient proof of a write.

The only exception is a read-only router operation or an existing platform interaction whose external contract explicitly does not require trusted input.

### 5. Fail closed on target ambiguity

A command carrying `noteId` must resolve exactly one canonical top-level article or the active Reel with the same stable identity. If it does not, the result is `target_not_found` or `ambiguous_target`; the runtime never falls back to DOM order, the first dialog article, or the current profile/page.

The same scoped root and identity are reused for post-action verification.

### 6. Preserve terminal reason semantics across the Native boundary

Comment submission uses these established terminal classes:

- confirmed server comment identity or equivalent same-account acknowledgement: success;
- pending group review: `pending_group_approval`;
- explicit platform rejection: `comment_rejected`;
- input not dispatched: a not-started failure;
- submission dispatched but not provable: `verification_ambiguous`.

Join, like/follow, and publish similarly preserve already-complete, pending/rejected, not-started, and ambiguous distinctions. Native `EffectPhase` remains the transport-level atomicity marker; action reason codes retain the product-level retry/idempotency meaning.

### 7. Enforce a Facebook command support table before router dispatch

The Native Facebook adapter will keep identity, probes, feed/Reels browse, search, note detail, exact-target like, Reel follow, comment, group join, and the existing Facebook publish atom subset.

Facebook `interaction.collect`, `interaction.like_comment`, `note.browse_images`, `note.scroll_comments`, notification commands, and `profile.open` remain unsupported. Unsupported commands return `capability_unsupported` without evaluating the page router. This prevents a generic command vocabulary from silently creating a platform capability.

### 8. Port behavior cases, not TypeScript implementation structure

Native tests will reuse the old fixtures and assertions for Feed settling/continuation/exhaustion, blockers and consent, exact-target like/comment, comment terminal classification, join readiness, and publish submit integrity. The old TypeScript classes are an oracle, not a dependency, and are not restored to the production bundle.

## Risks / Trade-offs

- [More Native state can survive a page navigation that invalidates it] → Reset or rebind state only on verified list-surface transitions and canonical document-generation changes.
- [DOM layouts differ by locale and account cohort] → Reuse the existing semantic selectors and canonical identities, require uniqueness, and fail honestly when evidence is insufficient.
- [Trusted coordinate targets can move between probe and click] → Scroll into view, re-probe immediately before dispatch, and verify the same canonical target after dispatch.
- [Bounded settling increases command duration] → Use the existing 30-second command deadline and the prior 6-second navigation / 3.5-second in-place / eight-round limits; do not stack independent waits.
- [Stricter capability truth can expose previously hidden command routing bugs] → Return a stable unsupported receipt and add platform command-matrix tests; do not add fallbacks.

## Migration Plan

1. Add the OpenSpec contract and parity ledger.
2. Implement in an isolated Edge worktree, first restoring read-side state and blocker gates, then exact-target write stages.
3. Run focused Native/legacy parity tests, acceptance tests, full Edge tests, typecheck, Cargo tests, and strict OpenSpec validation.
4. Integrate by fast-forward into Edge `master` and control `main`, push both, and rebuild the local Native Page Engine artifact used by source execution.
5. Do not package or release an installer. A real Facebook run remains the final runtime acceptance boundary; no write action is triggered solely for validation.

Rollback is the reverting Edge commit and rebuilding the prior Native binary. There is no database or protocol migration.

## Open Questions

None. Any newly discovered behavior not covered by an existing contract is recorded as a separate observed failure before adding recovery logic.
