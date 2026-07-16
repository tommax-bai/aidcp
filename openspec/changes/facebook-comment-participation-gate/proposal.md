## Why

Some Facebook groups turn on admin-configured **Participant Approval / Participation Questions** (public groups) or **Limited Membership** (private groups). The first time an account tries to comment in such a group, Facebook interrupts the action with a "request to participate + answer questions + agree to rules" gate instead of posting the comment; the contribution then waits for a human admin. Our comment path does not recognize this gate at comment time, and — worse — the post-submit confirmation can misread a **pending-admin-approval comment** (which Facebook renders to the author with a real comment id and a "pending review" badge) as **posted**, producing a silent false-green that violates the project's "never silently fake success" red line.

## What Changes

- **Harden post-submit confirmation against pending-approval comments (止血, highest priority).** A comment node that carries a "pending approval / awaiting review / 待审核 / needs admin approval" indicator MUST NOT be confirmed as posted, even if it has a server-assigned comment id or reaction/reply affordances. This only makes confirmation stricter; it introduces none of the previously-removed membership false positives.
- **Recognize a participation-approval gate at comment time and report it honestly.** Add a precise participation-gate detector (a visible `role="dialog"` / participation surface whose text carries participation-approval phrasing — NOT a bare body-text match for "回答问题", which the code deliberately removed to avoid two documented false positives). When both confirmation paths fail, the edge classifies the state as a participation gate and returns a new honest reason `pending_group_approval` (submitted:false — the comment did not go live; it became a participation application) instead of collapsing into the ambiguous "submitted but unconfirmed" bucket.
- **Do not type the marketing comment into a participation answer box.** When a participation-approval dialog is present before typing, the edge returns `pending_group_approval` without dumping the comment body into the answer field.
- **Cloud surfaces a distinct, honest outcome.** Add `pending_group_approval` to the Facebook comment outcome enum and outcome mapping; the result card says "该群需管理员批准参与后才能评论（评论未上墙，待人工处理）" and MUST NOT be colored green; it MUST NOT be counted as a real submission (no dedup-as-success), and MUST NOT be blindly retried in place (retry re-hits the gate).
- **Non-goal (explicitly out of scope):** auto-answering participation questions. Even a correct answer still waits for a human admin (the comment will not post immediately) and leaks automation traces into an admin-visible queue. Answered ≠ posted. Deferred to a separate proposal.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `facebook-comment-verification`: (1) success confirmation gains a pending-approval veto so a pending-admin-approval comment is never confirmed as posted; (2) the "unconfirmable submission is honestly ambiguous" outcome is split so a recognized participation-approval gate is reported as a distinct honest `pending_group_approval` state (not posted, not dedup-as-submitted) rather than collapsed into `verification_ambiguous`.

## Impact

- **aidcp-edge** (`src/facebook/comment-executor.ts`, hot path — serialize): add pending-approval veto to `buildAckVerifyJs` / `buildScopedVerifyJs`; add a precise `buildParticipationGateJs` probe; call it in the post-Enter confirmation segment (and optionally before typing); add `pending_group_approval` to `FacebookCommentStepReason`; stop treating the participation answer box as a legitimate comment editor.
- **aidcp-cloud** (`src/comment-agent/comment-scheduler.ts` outcome mapping — hot path — serialize; `src/comment-agent/facebook-comment-audit-store.ts` outcome enum): add `pending_group_approval` outcome + mapping + human-readable card text; ensure the scheduler treats it as gated (no false-green, no dedup-as-success, no blind retry).
- **Tests**: unit tests for the pure JS-string helpers (pending-approval veto; participation-gate phrase/DOM detection) plus cloud outcome-mapping/card. Existing publish/authorization red-line acceptance (`AC-PUB-*`) unaffected.
- **Real-machine (decoupled to `docs/real-machine-acceptance-backlog.md`, does not block stub-level landing/deploy)**: on a tom-group test account, enter a public group with Participant Approval on and comment as a non-participant; capture live DOM to confirm the exact Simplified-Chinese button/badge wording and lift the detector/veto phrase set from "semantically high-confidence" to "verbatim-confirmed".
