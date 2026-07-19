## Why

Feishu currently parses one message as one command, so `/publish Tianxing Bai; /comment Tianxing Bai --join --contact --force` is misread as one publish nickname and neither intended task is admitted. Even when operators send the commands separately, a browser-lease wait can still consume the two-attempt budget and end as `max_attempts`, while the delegated comment executor silently drops the already-parsed `--contact` flag.

## What Changes

- Accept a bounded semicolon-separated list of recognized slash commands in one Feishu message, validate and admit each segment independently, and report each segment's true acceptance or rejection.
- Start admitted child commands independently so cloud-only preparation can overlap; do not serialize them by textual order.
- Preserve one active browser writer per environment. Equal-priority ready requests execute by Edge receive order (priority, then monotonic FIFO order); later requests remain queued.
- Treat resource waiting before any browser/platform command as queueing rather than an attempt: it MUST NOT increment `attempt_count` or `failure_count`, and MUST NOT terminate as `max_attempts` solely because another task held the browser.
- Carry the complete manual comment switch set through the delegated path, including `--join[=<url>]`, `--contact`, and `--force` together.
- Keep publish/comment human approval and platform-confirmed completion semantics unchanged. “Accepted/queued” remains distinct from “published/commented”.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `feishu-command-ingestion`: add semicolon-batch parsing, per-segment admission/results, and fast-ack-safe asynchronous dispatch.
- `user-delegated-tasks`: define browser-resource waiting as a non-attempt queue state and define deterministic equal-priority ordering for simultaneously ready sibling commands.

## Impact

- `aidcp-cloud`: `src/feishu/commands.ts`, Feishu receiver result delivery, delegated-task parser/service/worker/executors/store, and focused tests.
- `aidcp-edge`: no protocol or behavior change expected; the existing single-active-lease priority/FIFO coordinator is the ordering authority and receives regression coverage only if needed.
- OpenSpec: modifies `feishu-command-ingestion` and `user-delegated-tasks`; existing `manual-command-override` and `group-chat-injection` requirements provide the `--join --contact --force` regression contract.
- Deployment: cloud runtime behavior changes and therefore requires serial landing on `aidcp-cloud/master`, `dev` deployment, and event-driven real-environment validation. No Edge package is required.
