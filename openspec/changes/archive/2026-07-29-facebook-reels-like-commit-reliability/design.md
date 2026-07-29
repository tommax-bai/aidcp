## Context

The dedicated Reel reader binds actions to the largest visible video and its canonical `/reel/<id>` route, but its like path is older and simpler than the ordinary-Feed executor. It resolves a right-rail control, sends an immediate CDP move/press/release sequence to a saved coordinate, and polls for a selected state. The ordinary-Feed implementation has since established that Facebook uses different event semantics for the primary React reaction control and for reaction-picker items: the primary control is reliably activated in-page against the fresh DOM element, while picker items require trusted pointer events. Dev receipts on 2026-07-22 showed one Reel success followed by two dispatched writes that exhausted post-state verification without success.

This is an Edge-only behavior repair. Cloud remains the source of probability selection, risk and quota gating, and confirmed-success accounting.

## Goals / Non-Goals

**Goals:**

- Reliably commit a Like on the uniquely resolved active Reel across direct-toggle and reaction-picker layouts.
- Preserve exact-target and no-false-success guarantees under Reel movement, virtualized DOM replacement, and ambiguous controls.
- Make the terminal path observable without logging content, author identity, or raw DOM.
- Keep every write bounded to one primary activation and, only when proven necessary, one picker-item commit.

**Non-Goals:**

- Changing the Reel like probability, Cloud orchestration, quotas, cooldowns, protocol, or client activity presentation.
- Reusing Feed article selectors on the dedicated Reels DOM.
- Retrying a like on a newly active Reel after movement or treating reaction-count changes as proof.
- Building or releasing an installer.

## Decisions

### Resolve and activate the primary control in one fresh in-page operation

The commit operation will repeat the active-video, route, geometry, and exact supported-label resolution immediately before activation, verify the expected canonical Reel, and invoke `element.click()` on that fresh primary React control. It will not consume the coordinate returned by an earlier probe. This follows the proven Facebook primary-control event path and removes layout drift between probe and write.

Alternative considered: retain raw CDP press/release on the saved primary coordinate. This is rejected because the live failures occur after that sequence is dispatched, and other Facebook React controls already demonstrate that coordinate delivery is not equivalent to handler acceptance.

### Support one scoped reaction-picker commit

After the primary activation, the bounded verification loop first looks for a positive selected-state witness on the same Reel. If none exists, it may locate a unique visible reaction picker containing multiple recognized reaction items and a unique Like item. The locator returns only the Like item's viewport coordinate and the primary control coordinate; the caller commits that item with the shared humanized CDP pointer helper. Picker lookup never searches the whole document for a bare `Like` control and never clicks an off-screen coordinate.

Only one picker commit is allowed. If the picker is absent, ambiguous, off-screen, or remains unconfirmed, the action terminates honestly as `state_unchanged`; if the Reel identity changes or the target becomes ambiguous after a write, it terminates as `verify_indeterminate` and never clicks again.

Alternative considered: always perform two clicks. This is rejected because direct-toggle layouts would turn a successful Like back off or act on an unrelated control.

### Use explicit positive state witnesses and structured diagnostics

Verification will accept only same-Reel positive state signals: supported unlike/remove labels, `aria-pressed=true`, `aria-checked=true`, or a supported reacted-word transition on the resolved primary control. A generic descendant image or reaction count is not proof.

Diagnostics will record only stable tokens such as `primary_dom_click`, `picker_pointer_click`, `direct_selected`, `picker_missing`, `picker_ambiguous`, `reel_moved`, and the terminal reason. They will not include author names, captions, URLs beyond the already-known canonical command identity, or raw DOM.

## Risks / Trade-offs

- [A Reel layout requires pointer activation on the primary control] → The bounded dev probe must compare the primary DOM activation against the resulting control/picker state before integration; no second primary click is permitted in production fallback.
- [A non-reaction dialog resembles the picker] → Require multiple recognized reaction items, a unique supported Like item, viewport visibility, and active-Reel geometry association before returning coordinates.
- [Facebook updates selected-state markup] → Fail closed as `state_unchanged`, retain stable diagnostics, and add fixtures only from observed markup rather than broad text matching.
- [DOM virtualization moves the Reel after the primary write] → Return `verify_indeterminate` and suppress all further clicks because the platform outcome is unknown.

## Migration Plan

1. Implement and validate in an isolated `aidcp-edge` worktree.
2. Run focused Reel/Facebook tests, acceptance tests, the full Edge suite, and typecheck.
3. Fast-forward the verified Edge commit to `master`, rebuild the development runtime, restart the local development client, and run one bounded exact-target Reel probe with a same-Reel post-condition.
4. Roll back by reverting the Edge commit and rebuilding/restarting the development client; Cloud requires no rollback.

## Open Questions

- The bounded live probe must confirm whether the currently observed Reel primary control accepts fresh in-page activation and whether failed cases expose the same scoped reaction picker as ordinary Feed. If evidence contradicts this design, update the design and spec before integration rather than adding an unproven dual-primary-click fallback.
