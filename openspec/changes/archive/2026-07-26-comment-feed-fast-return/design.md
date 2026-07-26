## Context

`/comment` is parsed twice in the current command path: the legacy command parser provides direct-router compatibility, while the active delegated-task parser converts the command into a durable single-comment intent. That intent reaches `CommentScheduler`, which sends `interaction.comment` to Edge. Xiaohongshu and Facebook then use separate executors, but both currently hold the page and wait for a post-submit confirmation signal before returning a terminal result.

The new switch deliberately trades platform confirmation for browser availability. It must not weaken any pre-submit targeting, human review, captcha, content-safety, or editor-readback gate, and it must not turn a dispatched write into a claimed success.

## Goals / Non-Goals

**Goals:**

- Accept trailing `--feed` on manual `/comment` commands, alongside existing flags in any trailing order.
- Propagate one explicit boolean through durable task constraints, scheduler options, protocol payloads, and both platform executors.
- Once submit has been dispatched, wait exactly 500 ms, skip confirmation polling, navigate to the platform home page, and return `submitted_unconfirmed`/`verification_ambiguous` semantics.
- Preserve deduplication and no-retry behavior for the unconfirmed write.
- Keep commands without `--feed` and all automatic paths unchanged.

**Non-Goals:**

- Claiming the comment is platform-confirmed or incrementing confirmed-comment counters.
- Skipping pre-submit safety, account, approval, targeting, or text-readback checks.
- Applying fast return to autonomous or scheduled commenting.
- Waiting for home-feed hydration after navigation; dispatching the direct home navigation is the boundary.

## Decisions

1. **Model `--feed` as a durable task constraint and protocol boolean.** Both command parsers recognize the switch, but only the legacy single-comment executor promotes it into scheduler options. The scheduler passes it to the platform-specific edge step, and `InteractionCommentPayload.fastReturnToFeed` carries it across the Cloud/Edge contract. This survives queued delegated execution and avoids hidden process-local state. An edge-only environment toggle was rejected because it cannot be scoped to one operator command.

2. **Branch only after the irreversible submit dispatch.** All existing checks and the final cancellation checkpoint remain before the click/Enter. The fast branch begins only after dispatch succeeds, sleeps 500 ms, navigates to the canonical platform home URL, and then reports an unconfirmed submitted outcome. Branching earlier was rejected because it could bypass validation or report a write that was never dispatched.

3. **Keep the commit window through the 500 ms delay and home navigation dispatch.** This prevents takeover from interrupting the short post-submit transition and racing another writer onto the same page. The window closes in the existing `finally` block.

4. **Use existing honest terminal categories.** Xiaohongshu reports `submitted_unconfirmed`; Facebook reports `verification_ambiguous`, which Cloud already normalizes to submitted-but-unconfirmed and records for deduplication without marking success. A new success-like result was rejected because no platform result was observed.

5. **Navigate directly without feed hydration waits.** Xiaohongshu uses its canonical Explore URL and Facebook uses its canonical home URL via `Page.navigate`. This satisfies the requested 500 ms handoff and avoids replacing publish-result waiting with another long page-readiness wait.

## Risks / Trade-offs

- [The comment may later fail, be rejected, or require approval] → Receipts remain submitted-unconfirmed, no confirmed-success counters are incremented, and no automatic retry occurs.
- [Home navigation dispatch can fail after submit] → Still return submitted-unconfirmed, log the navigation failure, and do not reclassify the already-dispatched comment as not sent.
- [Cloud/Edge version skew drops the new behavior] → The optional protocol field defaults false; deploy Cloud before or with Edge and retain default behavior on older Edge versions.
- [Fast navigation can remove useful platform evidence] → The mode is explicit and manual-only; the default confirmation path remains available by omitting `--feed`.

## Migration Plan

1. Deploy Cloud parsing/propagation with the optional field defaulting false.
2. Deploy Edge support for both platforms.
3. Verify focused parser, propagation, executor, protocol, and no-regression tests.
4. Roll back by reverting the optional field propagation/branches; persisted tasks without the field continue using default confirmation.

## Open Questions

None.
