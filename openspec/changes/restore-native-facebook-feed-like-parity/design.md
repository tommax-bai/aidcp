## Context

The retired `FacebookLikeExecutor` used different actuation for two Feed stages: the exact post-level React control received an in-page `element.click()`, while a subsequently opened reaction picker received trusted CDP pointer input. It tagged the selected card and verified that same DOM card and canonical post identity after dispatch.

The current Native engine first probes the exact card but converts the initial action to a generic coordinate click. That preserves target geometry but loses the control-specific event behavior observed on Facebook Feed. Its verification also re-resolves by identity rather than proving that the same card selected for dispatch remained the verification subject.

This change is implemented only in the prepared control and Edge worktrees. The concurrently active Reels parity change remains the owner of Reels like/follow behavior.

## Goals / Non-Goals

**Goals:**

- Restore the established initial Feed like actuation: a fresh exact-card lookup followed by DOM `click()` on one structurally identified post-level React control.
- Preserve the bounded second-stage CDP click only for one scoped reaction-picker Like item.
- Bind every post-dispatch read to the tagged card selected during commit and return honest outcomes when that proof is lost.
- Keep the existing Native command/result envelope and Cloud behavior unchanged.

**Non-Goals:**

- Change Reels like/follow behavior, Cloud selection probability, quota, risk accounting, command mapping, or protocol v2.
- Add retries beyond the existing bounded verification and one picker commit.
- Package an installer, deploy Edge, or claim real-account acceptance.

## Decisions

### 1. Split Feed and Reels actuation inside the existing Native like executor

The executor will classify the current Facebook surface before dispatch. Reels continue through their specialized path. A non-Reels exact post uses a new Feed commit/verify choreography.

This keeps Cloud-facing routing stable and avoids moving Reels behavior while another change owns it. Removing the Native executor override and sending every Like through the generic router was considered, but would unintentionally replace Reels semantics.

### 2. Make the first write a fresh internal DOM commit

The Feed commit expression will re-resolve the canonical command identity immediately before acting. It will accept exactly one visible reaction control that:

- belongs directly to the target post rather than a nested comment,
- is not inside a reaction-summary toolbar, and
- shares a bounded action-bar ancestor with exactly one post-level comment control.

The expression tags the target card with an operation token and invokes that control's DOM `click()`. A prior coordinate probe is not authority to dispatch because React may re-render between calls.

A generic label-first coordinate click was rejected because it reproduces the observed regression and can select a reaction-count control.

Before commit, the engine will use bounded wheel steps and fresh reads to bring the structural reaction control—not merely the article top—into the viewport. This preserves the existing humanized-scroll authority and makes a picker opened beside the control eligible for a visible CDP commit.

### 3. Preserve per-control actuation for the picker

If the tagged card has not reached a positive reacted state and the same active operation still owns its marker, one visible reaction picker contains multiple reaction items, and its unique Like item is in the viewport, the engine may perform one trusted CDP click. The probe also returns the marked primary control as the pointer origin, keeping the pointer path in the control-to-picker corridor. It then returns to tagged-card verification.

Using DOM `click()` for the picker was rejected because prior live evidence showed that picker items require pointer events. Searching the whole document was rejected because every Feed card can expose a Like-labelled control.

### 4. Verify only the tagged card and fail honestly after dispatch

Verification requires all of:

- the operation tag still exists,
- the tagged node still carries the commanded canonical identity, and
- its unique post-level control has a positive reacted signal.

`already_liked` is confirmed without dispatch. Missing/ambiguous targets before dispatch are `not_started`. Once the DOM click has returned successfully, target loss or identity change remains `ambiguous` with `verify_indeterminate` and is never retried. A present same card whose control does not reach a positive state remains `ambiguous` with `state_unchanged`. None is converted to success or a retryable not-started result. The operation tag is cleared best-effort at terminal completion.

Re-resolving a replacement card with the same identity was considered but rejected: it cannot prove the observed state belongs to the node that received the action.

## Risks / Trade-offs

- [Facebook changes action-bar structure or localization] → Structural matching fails closed as `like_button_not_found`; tests cover representative Chinese, English, Spanish, and Vietnamese labels.
- [React replaces the entire tagged article after a successful commit] → Result remains ambiguous rather than fabricated success; real-account acceptance can later determine whether a stronger durable witness is available.
- [Router/Rust files overlap the concurrent Reels parity change] → Keep commits isolated, report exact overlapping files, and require root integration to reconcile both surface branches before full validation.
- [JSDOM cannot prove real Facebook event behavior] → Characterization proves target binding and orchestration only; live-account success remains explicitly unverified.

## Migration Plan

1. Land the Edge and control commits through the normal integration boundary.
2. Rebase with the Reels parity branch and rerun focused router/Rust tests, the Edge full suite, typecheck, and strict OpenSpec validation.
3. A later explicitly authorized DEV desktop run may verify real-account Feed behavior; installer creation and production release remain separate gates.
4. Rollback is the isolated Edge commit; no data or protocol migration is required.

## Open Questions

- A real-account acceptance run is still required to establish whether full-article React replacement occurs after successful Feed like on currently deployed Facebook layouts.
