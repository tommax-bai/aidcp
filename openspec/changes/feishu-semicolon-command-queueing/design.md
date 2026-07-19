## Context

Feishu fast-ack already moves command execution into a background promise, and exact `/publish` / `/comment` commands already become independently persisted delegated tasks. The missing layer is message-level batching: both parsers currently consume the entire message as one command. The delegated worker can run compatible tasks concurrently, while the Edge `EdgeTaskCoordinator` is already the single authority for one active browser writer and selects queued acquisitions by priority then monotonic receive order.

There are two adjacent defects. First, the delegated parser stores `targetConstraints.injectContact=true`, but the comment executor does not pass it into `CommentScheduler.triggerManual`. Second, a comment whose Edge lease acquisition times out returns `not_started`, yet the worker has already incremented `attempt_count`; two pure resource waits can therefore exhaust the default two attempts without a browser command ever running.

`publish-scheduler.ts` remains a single-writer hotspot owned by the active `publish-trigger-and-apply` / `publish-claim-reject-defer-not-fail` sequence. This change supplies generic non-attempt defer support but does not alter publish claim shapes.

## Goals / Non-Goals

**Goals:**

- Turn one semicolon-separated Feishu message into independently admitted child commands without losing fast-ack or honest downstream result semantics.
- Allow child tasks to prepare concurrently; let the existing Edge lease coordinator serialize actual browser work.
- Make equal-priority simultaneous readiness deterministic: Edge receive order is the FIFO tiebreaker.
- Remove pre-start resource waits from attempt/failure budgets while retaining crash-safe attempt reconciliation once work may have started.
- Restore complete `--join[=<url>] --contact --force` propagation on the delegated manual-comment path.

**Non-Goals:**

- No parallel page writers, no Edge protocol change, and no desktop package.
- No bypass of publish/comment approval, content safety, platform verification, or per-account isolation.
- No change to publish generation claim codes; the active `publish-claim-reject-defer-not-fail` change remains responsible for those scheduler shapes.
- No promise that cloud preparation itself is browser-free: Facebook comment search/read/approval intentionally holds a keep-open lease once browser discovery begins.

## Decisions

### D1: Split only at a command boundary

Add a bounded batch splitter that recognizes ASCII `;` and full-width `；` only when the following non-space text starts with a supported slash command. A semicolon inside a nickname or `--join=<url>` is not a boundary unless it is followed by a recognized command token. Single-command text follows the existing path byte-for-byte.

Each child receives a deterministic source reference derived from the Feishu message id plus child index. This lets replay dedupe the same child while allowing two intentionally repeated commands in one batch to remain distinct.

**Rejected:** plain `text.split(';')`; it corrupts URLs/names and loses source identity. **Rejected:** sequential `await` in textual order; it prevents independent preparation and contradicts the requested ready-order behavior.

### D2: Dispatch children concurrently and settle independently

`CommandRouter` exposes a batch method that starts every child immediately and uses per-child error capture. One invalid child does not roll back or suppress valid siblings. The receiver keeps fast-ack: it invokes the batch method in the existing detached background chain, then emits each non-silent command result/card independently. Exact write commands remain silent at admission; their existing approval/result cards remain the business truth.

### D3: Edge receive order resolves equal-priority simultaneity

No new cloud mutex is added across publish and comment. When both reach the same Edge environment, the coordinator still permits one active lease. It selects higher priority first and, for equal `human` priority, the lower monotonic receive-order counter. “Same time” therefore means first frame observed by Edge, not wall-clock milliseconds and not original semicolon order. Same-priority tasks queue and never preempt one another.

### D4: A proven pre-start defer is not an attempt

Extend deferred execution results with an explicit machine-readable `attemptStarted:false`. Only executors that can prove zero browser/platform commands were dispatched may set it. For that shape, the worker atomically removes the provisional attempt ledger row and reverses its earlier `attempt_count` increment before releasing the task as `deferred`; `failure_count` and `skipped_count` remain unchanged. The normal task claim-release event preserves queue observability.

All other deferred results keep the existing attempt ledger. In particular, preemption after browser work, ambiguous submission, or any result that cannot prove zero side effects MUST NOT discard the attempt; crash recovery continues to reconcile a dispatched row before retrying.

`facebook_group_comment` is deliberately conservative: its comment phase can report `not_started` after the preceding join phase has already joined the group. That composite result therefore retains the attempt ledger unless a future terminal shape proves that neither phase dispatched work. A trigger receipt that rejects before the composite task starts (for example Edge offline before joining) may still use `attemptStarted:false`.

### D5: Flags are projected from persisted task constraints at execution

The delegated comment executor passes `injectContact`, `joinGroup` / `groupUrl`, and `force` from the persisted target constraints to `CommentScheduler.triggerManual`. This is a bug fix to existing `manual-command-override` and `group-chat-injection` contracts, not a new override: human approval and all hard safety gates remain intact.

## Risks / Trade-offs

- **[A malformed separator accidentally creates a command]** → Require a recognized slash-command lookahead and cover URL/name cases.
- **[Batch replay creates duplicate children]** → Derive stable per-index source refs from the original message id; keep existing delegated dedupe.
- **[Discarding an attempt after side effects permits duplicates]** → Only the explicit `attemptStarted:false` shape may discard; composite join-comment terminal results stay conservative because joining may already have occurred.
- **[One child blocks batch result delivery]** → Run children concurrently with per-child settlement; current exact write admission is short and downstream work remains asynchronous.
- **[Hotspot conflict with publish changes]** → Do not edit `publish-scheduler.ts`; land this change serially on current `master`, rerun all delegated/publish acceptance tests, then deploy dev.

## Migration Plan

1. Land the cloud-only change on `aidcp-cloud/master`; no data migration or Edge package is required.
2. Deploy to `dev` after backup and health checks.
3. Validate parsing and queue accounting with automated tests, then use the `Tianxing Bai` AdsPower environment without desktop UI control: start the environment directly, observe Feishu/Cloud/Edge lease events and PostgreSQL ledgers, and approve the two real actions through their normal gates.
4. Roll back by restoring the previous cloud runtime. Persisted delegated tasks remain schema-compatible; no new columns or enums are introduced.

## Open Questions

None. The equal-priority tie-breaker is explicitly Edge receive order.
