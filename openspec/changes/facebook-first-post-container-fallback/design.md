## Context

The empty-keyword Facebook comment path currently performs:

`navigate group → bounded scroll/probe → require canonical group-post URL → navigate detail → read context → approve → interaction.comment(noteId=permalink)`.

The Gi Vo DEV probe against `https://www.facebook.com/groups/718145812202687` showed a different valid rendering:

- the group page had a hydrated post body and a uniquely associated Vietnamese comment editor;
- the post wrapper was not exposed as a top-level `role=article`;
- all timestamp/story anchors were group-root URLs with opaque fragments;
- no canonical `/groups/<group>/(posts|permalink)/<post>` or `multi_permalinks` link existed in the rendered DOM.

The current router therefore returns zero `PageCard` candidates before it ever probes the existing editor. The keep-open lease already pins the browser from first-post selection through approval and submit, so the same rendered container can be used safely without navigating to a detail URL when Edge maintains an explicit target binding.

## Goals / Non-Goals

**Goals:**

- Prefer the existing canonical-permalink detail path whenever it is available.
- Let a uniquely bounded, hydrated first commentable post proceed without a permalink.
- Keep context extraction, editor focus/fill, pre-commit recheck, submit, and acknowledgement scoped to the same rendered container.
- Give Cloud a strict opaque target reference for approval, deterministic dedup, and the subsequent `interaction.comment`.
- Preserve honest failures and all existing lease, approval, validation, risk, quota, and server-confirmation gates.

**Non-Goals:**

- Inferring or fabricating a Facebook post ID.
- Treating arbitrary non-URL strings as Facebook targets.
- Replaying an in-place target after navigation, browser restart, or lease loss.
- Falling back from first-post mode to keyword search or advancing to a later post after a selected target is deduped.
- Packaging an installer, deploying DEV/OL, or performing a real-account write.

## Decisions

### 1. Canonical permalink remains preferred for the selected first container

The first-post probe identifies the first uniquely bounded commentable container. If that same container exposes a canonical group-post permalink, Edge uses the existing detail path. Otherwise it may issue:

`aidcp:facebook-group-feed-post:v1:<sha256>`

The digest is computed from normalized same-container evidence: canonical group path, author/profile path where present, story body, and stable media identifiers where present. It is a deterministic internal reference, not a Facebook post ID or permalink. Edge MUST NOT derive a URL from it.

Cloud accepts this format only from `note.detail` while waiting for `selection=first_commentable_group_post`, then passes the same value through approval, dedup, and `interaction.comment.noteId`. Normal `openPost`, search candidates, and other platform paths continue to require their existing canonical identities.

This ordering prevents a later permalink-bearing card from replacing an earlier permalinkless commentable post.

Alternative considered: loosen the permalink URL matcher to accept the observed group-root fragment. Rejected because the fragment does not identify a post.

Alternative considered: generate a random per-run token. Rejected because it would defeat repeat-run dedup.

### 2. The target reference is backed by a live DOM binding, not re-located by document order

The injected Facebook router keeps a page-local registry from target reference to:

- the selected DOM root;
- the normalized evidence used to derive the reference.

The root is also marked with the reference. Every later read/comment probe resolves the reference through that registry and confirms:

- the node is still connected and remains under the current group surface;
- the marker is unchanged;
- normalized evidence still matches;
- exactly one eligible comment editor belongs to that root.

If Facebook replaces/recycles the node, the page navigates, or the boundary becomes ambiguous, Edge fails with the corresponding target/editor reason. It MUST NOT reselect the document's first editor or another post.

Alternative considered: re-run “first post” selection immediately before submit. Rejected because feed order can change during approval and would permit commenting on a different post.

### 3. Container discovery is based on a unique comment boundary

On the group discussion stream, Edge orders eligible visible comment controls/editors by document position. For each, it finds the smallest containing post boundary that has post evidence (author plus body or media), stays inside the group main/feed scope, and does not contain a second peer comment editor. If a comment action must be activated to hydrate its editor, Edge may click only that action and then re-evaluate the same candidate boundary.

The first uniquely commentable boundary is eligible. Duplicate evidence, multiple peer editors in one boundary, missing post evidence, or a boundary that expands to the whole page is an honest non-selection. The probe never chooses a later boundary after one has been selected and later fails.

### 4. The existing protocol messages carry the opaque reference

No new message type is introduced:

- `note.open{selection,container,taskId}` requests selection;
- `note.detail.noteId` returns either a canonical permalink or the strict target reference;
- `interaction.comment.noteId` carries that same target reference back to Edge.

Both Edge and Cloud protocol comments/documentation describe the additional first-post-only form. Runtime validation remains narrower than the shared `string` wire type.

### 5. Post-submit verification remains scoped and honest

For an in-place target, comment acknowledgement scans only descendants of the bound root and still requires the existing own-account plus server acknowledgement evidence. A cleared editor, optimistic row, or count change remains insufficient. If the bound root disappears after Enter, the result is ambiguous/non-success according to the existing lifecycle; it is never promoted to confirmed.

## Risks / Trade-offs

- **[Facebook replaces the post DOM during approval]** → the binding fails closed as `target_moved_before_commit`; the operator may retry, but the implementation never silently targets a new node.
- **[A post edit changes the deterministic evidence]** → the reference changes on a later run and per-post dedup may not match; group coverage and normal server verification still apply, and no weaker identity is fabricated.
- **[Two rendered posts produce identical normalized evidence]** → the probe reports an ambiguous target and submits nothing.
- **[Localized markup changes remove the unique editor boundary]** → focused router fixtures cover current Chinese, English, and Vietnamese labels; unknown markup fails honestly rather than selecting the document's first editor.

## Migration Plan

1. Add the OpenSpec/protocol contract and red tests for a commentable post with no canonical link.
2. Implement and validate the Edge page-local target registry and in-place read/comment path.
3. Update Cloud first-post correlation and target plumbing, retaining canonical-only checks elsewhere.
4. Run focused Edge/Cloud tests, Native Rust tests/clippy, and both repository typechecks.
5. Integrate source only after validation. Per the current task boundary, do not package, deploy, or perform a real-account write.

Rollback is a normal source revert: canonical permalink first-post targeting remains an independent path, and no persisted schema is added.

## Open Questions

None. The DEV probe establishes the required DOM variant, and the user confirmed that permalink must not remain mandatory.
