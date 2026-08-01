# native-page-engine-production Specification

## Purpose
TBD - created by archiving change native-page-engine-production-cutover. Update Purpose after archive.
## Requirements
### Requirement: Production Xiaohongshu page automation MUST execute only through Native

Every registered Xiaohongshu `page_automation` command in an official customer build MUST execute through the Rust Native Page Engine. The Edge runtime MUST NOT run a JavaScript shadow evaluator, compare Native against JavaScript at runtime, or fall back to a legacy JavaScript Xiaohongshu executor when Native is unavailable, incompatible, crashes, times out, or returns failure.

#### Scenario: Native is healthy
- **WHEN** an admitted Xiaohongshu page command reaches the Edge executor and the compatible Native engine is ready
- **THEN** Edge sends exactly one high-level Native command and derives the external receipt from its correlated terminal result
- **AND** no legacy JavaScript page executor runs

#### Scenario: Native is missing or incompatible
- **WHEN** the required artifact is absent, has the wrong architecture/hash, or negotiates an unsupported protocol
- **THEN** Xiaohongshu page automation fails explicitly before dispatch
- **AND** Edge MUST NOT activate JavaScript fallback or claim the page task started

### Requirement: Native IPC MUST remain high-level, versioned, and bounded

The production IPC SHALL use a versioned, newline-delimited, correlated protocol with bounded records and diagnostics. It MAY carry the loopback endpoint, session/task/command identities, deadlines, typed business parameters, authorized file paths, and typed results. It MUST NOT accept arbitrary selectors, JavaScript, raw CDP methods, arbitrary debugger WebSocket URLs, Cloud envelopes, credentials, prompts, cookies, or storage values.

#### Scenario: Typed page command is accepted
- **WHEN** Edge sends a supported command with matching protocol/session/task identities and valid bounded parameters
- **THEN** Native accepts it and emits at most one correlated terminal result

#### Scenario: Caller attempts a generic browser operation
- **WHEN** IPC input contains a selector, script, raw CDP method, arbitrary WebSocket URL, or unknown command kind
- **THEN** Native rejects the record as a stable protocol/validation failure before sending anything to Chrome

### Requirement: Native MUST cover the complete registered Xiaohongshu command surface before cutover

The direct-production cutover SHALL cover the retained Xiaohongshu page/feed scroll and refresh commands, search, note open/close/read/image/comment traversal, source-aware navigation back, profile and notification traversal, like/collect/follow/comment/comment-like interactions, captcha capture/click page operations, allowlisted legacy plan steps, and all registered atomic publish steps including navigation, mode selection, field/topic/options, image/cover input, scheduling, submit, public-id capture, scheduled capture, and scheduled reconciliation. The obsolete whole-publish transaction SHALL be unregistered with no reachable or packaged JavaScript executor. Edge coordination commands MAY manage leases, session stop, pacing, and authorization, but MUST NOT retain Xiaohongshu CDP page operations. A customer build MUST NOT cut over while any registered Xiaohongshu page command still requires a distributable JavaScript executor.

#### Scenario: Command registry and Native manifest agree
- **WHEN** the desktop package is built
- **THEN** every registered Xiaohongshu `page_automation` command is present in the Native capability manifest and mapped by the selector-free TypeScript facade
- **AND** any unmapped or extra command fails the build

#### Scenario: A new Xiaohongshu page command is added later
- **WHEN** a new command is registered without a matching Native command, result mapping, and contract test
- **THEN** acceptance/package validation fails rather than silently routing it elsewhere

### Requirement: Native MUST own the downstream Xiaohongshu CDP session

After Edge page-automation admission, Native SHALL discover an allowed Xiaohongshu page from the supplied loopback DevTools endpoint, attach its own CDP WebSocket, enable required domains, refresh target state across navigation, and perform bounded reconnect after unexpected CDP loss. The Edge facade MUST NOT send raw page WebSocket URLs or perform Xiaohongshu-specific CDP actions on Native's behalf.

#### Scenario: Dynamic AdsPower endpoint is admitted
- **WHEN** Edge supplies the current loopback host/port for an admitted AdsPower profile
- **THEN** Native independently discovers and attaches the allowed Xiaohongshu target and reports session readiness

#### Scenario: CDP disconnect occurs before dispatch
- **WHEN** CDP disconnects before the command's platform-write dispatch phase and bounded reconnect cannot recover
- **THEN** Native returns an honest `not_started` failure and does not replay the command

#### Scenario: CDP disconnect occurs after dispatch
- **WHEN** CDP disconnects after a platform write may have been dispatched
- **THEN** Native attempts only bounded read-only post-check/recovery and returns `confirmed` or `ambiguous`
- **AND** it MUST NOT redispatch the write

### Requirement: Native command results MUST expose effect phase and honest evidence

Every terminal command result SHALL identify `not_started`, `dispatched`, `confirmed`, or `ambiguous`, carry a stable reason code, and include only the bounded evidence permitted by the existing external contract. Success receipts for likes, collects, follows, comments, publish submissions, scheduling, and other platform writes MUST require command-specific positive post-action evidence and an acted-on target identity when the baseline contract requires it.

#### Scenario: Click lands but post-condition is absent
- **WHEN** Native dispatches an interaction input but cannot prove the expected state transition on the intended target
- **THEN** the result is not `confirmed`
- **AND** Edge MUST NOT emit a successful `action.completed`

#### Scenario: Target identity changes before comment submit
- **WHEN** the current note identity no longer matches the approved target immediately before submit
- **THEN** Native returns `not_started` with the existing mismatch reason and does not send the comment

#### Scenario: Publish is submitted but public identity is unknown
- **WHEN** submit may have occurred but Native cannot prove the required public post identity
- **THEN** the result preserves the existing submitted/unknown or needs-review semantics and MUST NOT fabricate a post URL

### Requirement: Native MUST preserve task ownership and safe cancellation

Native SHALL accept only the active Edge `taskId`, enforce monotonically unique `commandId` values within the session, execute at most one page-writing command at a time, and reject stale or concurrent writers. Cancellation SHALL occur only at declared safe points; pointer/key pairs, file assignment, and submit dispatch are atomic regions whose partial execution cannot be reported as clean cancellation.

#### Scenario: Stale task sends a command
- **WHEN** a command carries a task identity that no longer owns the page executor
- **THEN** Native rejects it before CDP dispatch and leaves the current owner unaffected

#### Scenario: Cancellation arrives during an atomic input region
- **WHEN** cancellation arrives after input dispatch begins but before the atomic region completes
- **THEN** Native completes the atomic region, performs bounded post-check, and returns the truthful effect phase
- **AND** it MUST NOT label the command `not_started`

### Requirement: Native page output MUST preserve data minimization

Native SHALL return only data required by existing Edge/Cloud contracts, with configured limits on text, lists, images, comments, URLs, and diagnostics. It MUST NOT expose selectors, evaluated source, outerHTML, cookies, storage, authorization headers, raw network bodies, or unrestricted DOM snapshots over IPC or logs.

#### Scenario: Note detail is extracted
- **WHEN** Native reads a note detail page for an admitted command
- **THEN** it returns the bounded note fields required by `note.detail` and omits selectors, raw DOM, credentials, and unrelated page content

#### Scenario: Native encounters malformed page state
- **WHEN** required page evidence is missing or ambiguous
- **THEN** it returns a stable honest failure with bounded diagnostics rather than dumping DOM or guessing a known state

### Requirement: Existing Xiaohongshu safety and behavior contracts MUST survive migration

Native implementation SHALL preserve the authoritative baseline contracts for search result identity and filters, source-aware return, target attribution, human approval, risk-gated interactions, comment verification, publish field integrity, image requirements, scheduling, submit integrity, post-id capture, reconciling scheduled posts, reconnect honesty, and no-fake-success behavior. Migration to Rust MUST NOT weaken or bypass these requirements.

Captcha assistance SHALL preserve authorization, fresh screenshot and coordinate-map evidence, bounded image transport, exact-session binding, and fresh post-click verification. Legacy plan steps SHALL be restricted to an explicit Native action allowlist and MUST NOT accept free-form goals as locating instructions.

#### Scenario: Search lands on `search_result_ai`
- **WHEN** the platform uses the AI search textarea and `/search_result_ai` result route
- **THEN** Native uses the required real input gestures, confirms the current keyword/result route, applies and verifies requested filters, and harvests only result-page cards

#### Scenario: Required publish image is missing
- **WHEN** a publish command lacks a valid authorized image required by the baseline publish contract
- **THEN** Native fails before submit and MUST NOT downgrade to text-only publication

#### Scenario: Scheduled publish evidence is incomplete
- **WHEN** schedule controls do not prove the exact requested Beijing time and scheduled-submit mode
- **THEN** Native fails closed and MUST NOT submit immediately

### Requirement: Native rule material MUST be absent from distributable JavaScript

Official packages SHALL exclude the migrated Xiaohongshu selector sets, page scripts, locating logic, CDP action sequences, retry rules, and post-validation implementation from JavaScript/ASAR/source maps. The selector-free TypeScript facade MAY retain command/result schemas, lifecycle supervision, and external receipt mapping.

#### Scenario: Final package is inspected
- **WHEN** package leakage validation scans `app.asar`, unpacked resources, JavaScript, and source maps
- **THEN** forbidden legacy module paths and representative cleartext rule markers are absent
- **AND** the matching Native artifact and manifest are present outside ASAR

#### Scenario: Legacy module becomes reachable again
- **WHEN** a code or build change imports or includes a forbidden Xiaohongshu executor module
- **THEN** package graph/leakage validation fails the build

