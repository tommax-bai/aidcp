## Context

The current Edge capability calculation correctly keeps comment and DM writes false until both Cloud per-channel write controls and controlled write-probe evidence are present. It also rejects `commentCreate` and `dmSendText` before fetch because their descriptors are marked unobserved. The named dev account now has active auth, matching identity, healthy read probes, and no write pause/circuit, and the operator has explicitly accepted an unverified dev test even though the two Cloud per-channel write booleans remain false.

The first-party bundle currently loaded by the authorized browser identifies the candidate paths `/comment/create_comment` and `/private-msg/send-private-msg`, the DM `msgPack` shape, and server identifiers returned for accepted writes. This is enough to exercise a bounded test path but is not equivalent to a captured successful request, so production evidence labels must remain honest.

## Goals / Non-Goals

**Goals:**

- Let the unpackaged Electron dev client report comment-reply and DM-text as usable when all gates other than the two per-channel Cloud write booleans and prior-probe evidence pass.
- Dispatch candidate platform requests with no automatic retry and preserve the existing durable idempotency/executing marker.
- Confirm only from a channel-specific platform server identifier.
- Emit searchable diagnostics that identify the unverified dev override.
- Keep packaged, `ol`, custom, unauthenticated, wrong-identity, read-disabled, globally paused, killed, circuit-open, and missing/invalid Cloud-control paths closed.
- Exercise the dev write path without applying destructive migration `0046` to the PostgreSQL database still shared by dev and ol.

**Non-Goals:**

- Claim that the candidate descriptors have passed production capture or compliance review.
- Enable image DM, automatic probe sends, blind retries, or automatic resend after an ambiguous result.
- Change Cloud approval, risk-state, account/thread rate-limit, policy, or result-state contracts outside the explicit reviewed dev exception.
- Apply, rewrite, or emulate migration `0046`, or enable legacy-schema writes outside the named dev deployment.

## Decisions

### 1. Use a two-boundary dev opt-in

Electron injects an exact unverified-write token only when `app.isPackaged=false`, the selected Cloud key is `dev`, and the environment platform is `wechat_channels`. The Edge core consumes that token as a build/test gate. This is preferred over changing defaults because packaged clients and non-dev Cloud selections remain fail-closed without relying on operator memory.

### 2. Bypass only the two dev write grants and prior-probe evidence

The override replaces the conjunction of `Cloud per-channel write boolean + writeProbeVerified + passed write probe` for comment reply and DM text only. It does not fabricate or bypass the scoped/versioned Cloud-control snapshot, active auth, identity match, healthy channel read capability, global/local write gates, account kill switches, or endpoint circuits. Cloud still owns approval, policy, risk, quota, attempt creation, and dispatch. This wider bypass is intentionally limited to the exact unpackaged/named-dev token boundary because the operator requested both dev send capabilities open for live calibration.

### 3. Permit the exact pre-0046 schema only in the named dev deployment

Cloud keeps `legacy_read_only` fail-closed outside dev. When `AIDCP_DEPLOY_ENV=dev`, the existing global interaction-write switch is sufficient for `interactionWritesAllowed` to admit only the exact pre-0046 schema already classified by startup; missing, partially migrated, or inconsistent schemas remain disabled. No second Cloud token or duplicate configuration is introduced.

The compatibility path does not change schema or retry semantics. The old unconditional unique constraint on `interaction_send_attempts.idempotency_key` remains in force, the unused `retryable` column keeps its existing `DEFAULT false`, and no automatic resend is introduced. A pre-dispatch retry using the same deterministic key therefore still fails closed instead of reaching the platform twice.

For an already reviewed send in this same dev mode, Cloud skips the configured post-login cooldown and a RiskController denial whose reason is strictly quota-only (`quota:*`). This is necessary because `dm_reply` deliberately has zero derived quota unless an operator writes a shared `quota_config` override; writing that shared row would affect ol. The exception does not bypass missing auth/capability, `restricted`/`frozen` risk state, interaction account/thread rate limits, approval, CAS, idempotency, or result verification. The client labels `INTERACTION_RATE_LIMITED` as Cloud-local and reserves “platform rate limited” for `WECHAT_RATE_LIMITED`.

### 4. Label candidate descriptors separately

The two write descriptors carry an `official_bundle_candidate` evidence label and remain non-capture-backed. Serialization permits them only when the dev test token is active. Ordinary runtime paths continue rejecting every unobserved descriptor before fetch.

### 5. Use first-party candidate shapes and strict ack parsing

Comment create uses the observed service path plus `exportId`, `rootCommentId`, `replyCommentId`, and text content. DM send first resolves the peer username from the already verified session-info read, then sends the first-party `msgPack` shape with message type `1`, a client message id, and the bound Finder identity as sender.

Comment confirmation requires `data.comment.commentId`; DM confirmation requires a zero `data.baseResp.errcode` and `data.svrMsgId`. Missing or changed shapes open the endpoint circuit and produce failed/ambiguous truth according to whether dispatch occurred.

### 6. Preserve no-retry and ambiguous recovery semantics

Both write descriptors remain `retrySafe=false`. The existing claimed/executing/completed state and history-only reconciliation remain authoritative; a timeout or unreadable response after fetch is never retried blindly.

## Risks / Trade-offs

- [Candidate request fields may be incomplete] -> Restrict to unpackaged dev, send once, classify response honestly, and open only the affected endpoint circuit on schema drift.
- [A real dev account message may become externally visible] -> Require the existing user approval/send action; no probe or startup path sends automatically.
- [An operator manually exports the token outside Electron] -> Require the exact token and retain scoped Cloud controls plus every auth/read/kill/circuit/risk gate; document it as an emergency development escape hatch, not a production grant.
- [Platform accepts but the response is lost] -> Keep the attempt ambiguous and use unique history verification without resend.
- [Legacy-schema dev behavior leaks to ol] -> Require `AIDCP_DEPLOY_ENV=dev` in addition to the existing global write switch; ol retains the schema gate.
- [Shared database is mutated for a dev test] -> Do not run migration `0046`; preserve the current schema and its stricter uniqueness constraint.
- [A zero shared DM quota makes dev testing impossible] -> Bypass only `quota:*` and login cooldown in named dev code; do not write shared `quota_config`, and keep risk-state plus account/thread rate gates.

## Migration Plan

1. Integrate the Edge source change without building an installer.
2. Restart the unpackaged dev Electron client so its WeChat child receives the new token.
3. Verify auth capabilities report both text write booleans true for the named dev environment.
4. Keep the existing global interaction-write switch enabled in dev, restart only `aidcp-cloud.service`, and verify runtime controls project both text writes true and reviewed sends pass the local login/quota-only gates without executing migration `0046`, adding another Cloud token, or writing shared quota rows.
5. Let the operator issue one comment and one DM test through the normal reviewed workflow; inspect platform response and history evidence.
6. If either candidate drifts, turn off the Edge dev token or the Cloud global write switch; the endpoint circuit also closes that channel automatically.

## Open Questions

- The first successful/failed real request must be used to replace candidate evidence with a sanitized capture manifest before any production enablement.
