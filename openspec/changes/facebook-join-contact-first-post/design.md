## Context

The current Facebook comment pipeline is:

`pick joined group → require keyword → search.execute(container, keyword) → pick permalink → note.open(url) → compose/approve → interaction.comment`.

The scheduled `contact_comment` action calls the same pipeline with `injectContact=true`, but does not request `joinFirst`; only explicit `/comment --join --contact` currently joins a group first. The standalone scheduled `join` action is a separate scheduler action and must remain join-only.

A read-only probe against the Tianxing Bai AdsPower profile established two runtime facts:

1. the first hydrated top-level group-feed post can expose a stable group-post permalink and a comment affordance without using Facebook search;
2. after opening that permalink, document-order extraction can read a background feed post while the target post is open in a dialog. Existing canonical target helpers already resolve the correct article for write targeting, so read extraction must reuse that identity boundary.

The Gi Vo real-account regression probe established a third runtime fact: a hydrated group-feed timestamp anchor can render with a DOM `href` that is only the group root plus an opaque fragment, while Facebook's own React link/story props on that same anchor still carry the canonical `/groups/<group>/posts/<post>` URL. The card can simultaneously expose a working post-level comment editor. Treating DOM `href` as the only permalink witness therefore produces a false `no_candidates`.

The later Gi Vo Cloud-orchestrated runs established a fourth fact. The group page completed loading with a 1066px viewport, while its first two post cards started around 1951px and 2249px and neither was visible. The legacy JavaScript handler already understood `selection: first_commentable_group_post`, but the Native command mapper and Rust `NoteOpenParams` dropped `selection/container`. Native therefore performed an ordinary current-page detail read instead of the bounded first-post hydration defined here. Cloud waited for a canonical `note.detail` and then collapsed the timeout into the same user message as `no_candidates`.

The join `observation_only` incident, including alias-versus-numeric group identity, is owned by another task and is not changed here.

## Goals / Non-Goals

**Goals:**

- Route Facebook comments by configuration: non-empty keywords use the existing search path; empty keywords use the first commentable group-feed post.
- Keep first-post selection read-only and bounded, then open the selected permalink before composing.
- Bind post text, sampled discussion, and the eligible comment editor to the same canonical target post.
- Make Facebook scheduled contact comments join a new group before commenting, with the existing automatic risk, approval, contact, attempt-cap, and honest-outcome gates.
- Rename the Facebook-facing scheduled action to “加群评论（联系）” without exposing an extra empty-keyword mode indicator.
- Preserve the standalone scheduled auto-join action as join-only.

**Non-Goals:**

- Fixing group join recognition, membership scope, `observation_only`, alias/numeric group ID mapping, pending joins, or join-button localization.
- Adding a fallback from first post to second post, from first-post mode to search, or from search mode to first-post mode.
- Renaming persisted `contact_comment` keys, API fields, database columns, or non-Facebook contact-comment behavior.
- Packaging/releasing an Edge installer or deploying OL.

## Decisions

### 1. Extend `note.open` instead of inventing a search-shaped empty-keyword command

Cloud will send `note.open` with an optional Facebook-only selection request:

- `selection: 'first_commentable_group_post'`
- `container: <group URL>`
- the existing task lease `taskId`

Edge navigates the group discussion stream, selects the first hydrated top-level post with a canonical group-post permalink and an observable post-level comment affordance, then opens that permalink and emits the normal `note.detail`. This is a read/open operation, not a search, so no `search.execute` or search activity receipt is produced.

The active Native path MUST preserve both optional fields across TypeScript-to-Rust decoding and route this discriminator before the generic Facebook `note.open` path. Dropping unknown optional fields is not compatible behavior here because it silently changes the targeting mode.

Alternative considered: call `search.execute` with an empty keyword. Rejected because it would misreport a non-search as a search, conflicts with the command’s non-empty keyword contract, and would keep the exact step the product is removing.

Alternative considered: add a new protocol message plus a new result event. Rejected as unnecessary protocol surface because `note.open` already owns target navigation and detail delivery.

### 2. Empty keywords are a routing choice, not “configuration disabled”

`EffectiveFacebookCommentConfig.enabled` will depend on whether the selected comment-body mode has a usable body source:

- generated mode is usable without keywords;
- template mode requires at least one valid template.

At execution time:

- `keywords.length > 0` → choose one configured keyword and use the existing group search;
- `keywords.length === 0` → call first-post open directly.

There is no cross-mode fallback. Search returning no candidates remains a search-path failure; first-post selection returning no eligible post remains a first-post-path failure.

The composer omits its keyword-specific instruction when the keyword is empty and grounds generation in the target post and discussion. The lexical relevance gate remains active when a configured keyword supplies a stable anchor. In empty-keyword mode it is skipped because treating an entire post—especially unsegmented CJK text—as a “keyword” would reject natural paraphrases; all deterministic URL/contact/mention/spam/length/signal gates and the configured approval policy remain active.

### 3. First post means first eligible top-level feed card

The Edge selector scans the visible group feed in DOM/feed order and accepts the first card that:

- is a top-level post card, not a nested comment article;
- exposes a canonical Facebook group-post permalink;
- exposes a post-level comment control or a visible post-level comment editor.

The permalink witness MAY be either the anchor's canonical DOM `href` or a canonical URL explicitly present in Facebook's React link/story data for that same rendered anchor. React inspection MUST be bounded, tied back to the exact DOM anchor/card, and accept only URL shapes that derive a canonical Facebook group-post identity. It MUST NOT decode opaque fragments, infer IDs from text, or synthesize a permalink. If both witnesses are absent or ambiguous, the card is ineligible and selection remains fail-closed.

Because Facebook can initially stop the group page at the cover/composer while feed cards remain unhydrated, Edge MAY use the existing bounded feed scroll/probe budget to bring the first feed cards into the rendered viewport. This is hydration of the same first-post mode, not a fallback to search or a different targeting strategy. Selection remains DOM/feed ordered across the hydrated cards.

The Native implementation performs an immediate probe followed by a fixed, bounded number of viewport-relative downward scrolls on the exact canonical group container. Each round re-probes rendered cards and stops on the first eligible card, bottom/no-movement evidence, or the fixed bound. It never navigates home between rounds, never changes groups, and never promotes a later post after the first eligible candidate fails target/editor validation.

It does not skip an already-commented first post to choose a later post. Cloud may read the first post and then reject it through existing dedupe; that terminal result remains honest and no second post is substituted.

### 4. Read and write share the canonical target root

After permalink navigation, Edge derives the canonical post ID and resolves the exact article through the existing `FB_TARGET_HELPERS_JS` three-stage resolver. Caption extraction, nested-comment sampling, editor readiness, input targeting, and post-submit verification all use that same target boundary.

When Facebook renders the post-level comment editor through a DOM portal outside the target card subtree, Edge MAY bind it through the target card's exclusive rendered bounds only if the editor center is covered by exactly one physical post card and that card is the canonical target. A center covered by another card, multiple cards, or multiple candidate editors is ambiguous and MUST fail closed. This is not a document-first or nearest-editor fallback.

Zero or multiple matching targets returns `target_context_mismatch`; the task does not compose, approve, or submit. Document-order `top[0]`, first-dialog, and document-first-editor fallbacks are forbidden.

Cloud still correlates `note.detail.noteId` by canonical post identity for explicit URL opens. For first-post selection, Edge returns the selected canonical permalink as `noteId`, and Cloud requires it to derive a valid Facebook post identity before accepting it.

Equivalent canonical group-post URL forms remain equivalent at this boundary. In particular, `/groups/<group>/posts/<post>`, `/groups/<group>/permalink/<post>`, and `/groups/<group>?multi_permalinks=<post>` are accepted when they derive a stable post identity; page posts, Reels, empty `multi_permalinks`, and unknown URL shapes are rejected.

### 5. Facebook scheduled contact comment reuses the existing join-comment orchestrator

For Facebook only, the content scheduler calls the existing command entry with:

- `injectContact: true`
- `joinFirst: true`
- `priority: 'automatic'`
- the configured approval mode
- no manual override and no force flag

This uses the existing new-group selector and requires platform-confirmed `joined`/`already_member` before commenting. Join failures and ambiguous states remain non-commented outcomes. The attempt ledger is recorded only when the combined task is actually triggered, as today.

Non-Facebook scheduled contact comments do not receive `joinFirst` and retain their current behavior.

The independent scheduled `join` action remains wired only to `FacebookGroupJoinScheduler.triggerScheduled`; it never calls the comment scheduler.

### 6. Rename only user-facing Facebook semantics

Internal and persisted action key `contact_comment` stays unchanged. In the Facebook Console view and Facebook scheduled notifications it is rendered as “加群评论（联系）”. Non-Facebook UI continues to use its existing contact-comment wording.

The keyword editor no longer treats an empty list as an error or shows an empty-keyword status. It may describe keywords as optional, but does not display “当前使用群内首帖”.

## Risks / Trade-offs

- [First visible post can be pinned/admin content] → This is intentional “first eligible post” semantics; no ranking or search fallback is added.
- [First post was already commented] → Existing dedupe stops the run; it does not silently move to a second post.
- [Facebook DOM changes remove permalink or comment affordance] → Bounded selection returns `no_candidates`; no guessed target or write occurs.
- [Group cover/composer consumes the initial viewport] → Native performs bounded same-container viewport scrolling and reports `no_candidates` only after the probe budget is exhausted; timeout and editor-readiness failures retain distinct user-visible reasons.
- [Facebook hides the canonical permalink behind React link/story props] → A bounded, anchor-scoped React read may recover only an explicit canonical group-post URL; shape drift or ambiguity still returns `no_candidates`.
- [Detail page contains background feed plus multiple dialogs] → Canonical identity resolution, not DOM order or first dialog, binds the read context.
- [Facebook scheduled contact comment now consumes both join and comment activity] → Existing join and comment risk gates remain in force; the content scheduler keeps account single-flight and cross-scheduler exclusion.
- [Other task changes join code concurrently] → This change does not edit join executor, join membership recognition, or join scope logic; integration must still rebase and rerun tests before landing.

## Migration Plan

1. Land protocol/type and Edge read-path support first in the feature branches.
2. Land Cloud routing and scheduled join-contact behavior with tests.
3. Land Console label and empty-keyword UX.
4. Fast-forward each repository after rebasing onto its latest default branch and rerun focused/full validation required by the protocol/comment path.
5. Deploy Cloud to DEV from the clean default checkout. Edge source changes are validated in source only unless the user separately authorizes packaging/release.

Rollback is source-level: revert the Cloud routing/trigger commit and Console label commit; old Edge ignores no new message type because the change only extends `note.open` payload. During mixed-version deployment, Cloud must not send the new selection fields until the matching Edge build is present.

## Open Questions

None. Product decisions are fixed for this change.
