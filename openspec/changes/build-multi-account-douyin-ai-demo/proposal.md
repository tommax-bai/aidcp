## Why

Prospective users need an independently runnable Douyin demonstration that proves the multi-account login, inbound-message, comment, and AI-reply product loop without importing AIDCP runtime services. Existing community projects demonstrate parts of the mechanism, but their license and browser requirements do not support copying one repository wholesale or claiming a fully browserless flow.

## What Changes

- Create a standalone `douyin-ai-demo` Git repository with its own TypeScript web service, SQLite data store, static operations UI, tests, Docker image, and deployment examples.
- Add an operator-scoped multi-account workflow with short-lived Chromium QR authorization/context capture, encrypted retained web sessions, explicit reauthorization, and one active runtime per Douyin identity.
- Keep direct-message receive/send and comment reads independent from a continuously running browser after authorization; model direct messages as an account-level WebSocket stream rather than a polling-only source.
- Establish a historical baseline before automation, normalize new text direct messages and comments, and deduplicate them by stable platform event identity.
- Integrate the existing OpenAI-compatible `chat-llm` boundary without exposing platform credentials or coupling model code to Douyin protocol code.
- Route comment replies through one explicit configured capability: official API, bounded account-level headed Chromium worker, or unavailable. The Chromium worker starts only for an eligible comment write and closes after a verified outcome.
- Record only an explicit platform receipt as `confirmed`; preserve timeouts, disconnects, and unreadable post-dispatch outcomes as terminal `submitted_unknown` without automatic retry.
- Ship a deterministic fixture adapter so the complete UI and worker flow can be exercised without a real account, while keeping experimental private-web adapters fail-closed and clearly labeled.
- Document license provenance, private-protocol drift, configuration, local operation, deployment isolation, and the separate real-account acceptance gates.
- Extend the deployed DEV demo with the same operator-visible loop as the WeChat Channels demo: a web-presented Douyin QR, bounded Chromium session capture, encrypted retained login state, Doubao/Ark generation, exact-conversation direct-message delivery, incremental comment reads, and exact-target comment replies through a bounded account-level Chromium worker.
- Keep the same bounded authorization Chromium context alive when Douyin returns the explicit secondary-verification response, and expose only an operator-authenticated, one-time screenshot/input surface for the official verification UI. No verification configuration, QR token, Cookie, browser endpoint, or temporary input is projected or persisted.
- Correct the observed secondary-verification frame loop by treating a verified nested official dialog/iframe hierarchy as one surface, distinguishing temporarily missing, ambiguous, UC-renderer-pending, and unsupported-UC surfaces from stale account revisions, and requiring an explicit token-bound confirmation after `error_code=2046` even when legacy session Cookies exist.

## Capabilities

### New Capabilities

- `douyin-multi-account-auth`: Operator-scoped multi-account QR authorization, encrypted retained sessions, account uniqueness, reauthorization, and logout.
- `douyin-inbound-runtime`: Direct-message WebSocket lifecycle, comment baseline/incremental reads, normalized inbound records, durable deduplication, and per-source health.
- `douyin-reply-delivery`: Exact-target direct-message delivery and official/Chromium/unavailable comment-reply routing with honest terminal outcomes.
- `chat-llm-auto-reply`: Model-independent reply generation for eligible new text items with stop/resume and generation ownership checks.
- `douyin-demo-operations-ui`: Account, QR, source-health, reply-capability, timeline, automation, and runtime-state projection through an operator-protected web UI.

### Modified Capabilities

None.

## Impact

- New local repository: `/Users/baitianxing/codes/douyin-ai-demo`; no runtime dependency on AIDCP Edge, Cloud, Console, databases, or deployment services.
- New Node.js 24, TypeScript, Fastify, SQLite, WebSocket, Playwright, and OpenAI-compatible chat dependencies isolated to the standalone repository.
- Real mode touches undocumented Douyin web interfaces and therefore remains experimental, schema-checked, and fail-closed. The default fixture mode performs no platform login or write.
- Comment writes require either operator-provided official application permission or a local Chromium executable. Authentication capture and the account-level comment worker may use the same bounded Chrome runtime already proven deployable on DEV, but each browser lifecycle remains short-lived and account-scoped. The first source-validation pass included no real-account write and deployed only the offline Fixture to DEV. The operator has now requested a real-capability DEV follow-up covering both private messages and comments without a configuration-only comment lock. DEV therefore enables the process-level real-write capability while every new real account still starts with its account-level automation switch off; only an explicit UI action for that exact scanned account admits new post-baseline private messages and comments for observed write/readback checks.
- Community repositories without a clear license are used only as architectural evidence; no source is copied from them.
