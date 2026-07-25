## Context

DEV runtime evidence exposed two separate breaks in one operator-visible path.

First, `FeishuWsReceiver` received publish-approval card callbacks without a `writeApproval` dependency. Its fail-closed response was correct, but the production composition had omitted the already-existing `writeApprovalDecision` authority. Approval from the console still wrote and consumed the same durable record, proving the store and write authority were healthy.

Second, a Facebook comment task completed search and dispatched `note.open`, while the Edge UI reported a detail-open activity. Cloud nevertheless timed out because it accepted `note.detail.arrived` only when the reported URL exactly equalled the requested URL. Native-only open navigated once, waited for document readiness, and sampled the page once; Facebook could still expose an unrelated hydrated article while the requested post was loading.

Cloud is being separated into service modes, but DEV currently still runs the monolith. This incident repair must keep a narrow dependency boundary that works wherever the receiver is composed without broadening into service-mode activation or ownership migration.

## Goals / Non-Goals

**Goals:**

- Make Feishu approval callbacks reach the existing durable approval write authority.
- Confirm that Facebook `note.open` evidence belongs to the requested canonical post before comment composition or approval.
- Preserve the Edge/Cloud ownership split: Edge validates browser state; Cloud orchestrates and correlates returned evidence.
- Return bounded, honest failures before Cloud's step deadline when the requested detail never hydrates.
- Cover the production composition and alternate Facebook permalink forms with regressions.

**Non-Goals:**

- Changing protocol v2 payloads or command names.
- Moving the Feishu receiver between Cloud service modes or completing the three-process rollout.
- Reintroducing local-file approval as an authority or fallback.
- Adding runtime knobs, unbounded retries, or treating a mismatch as success.
- Deploying OL or building/signing an Edge installer.

## Decisions

### Inject the durable approval authority at the Cloud composition root

Every `FeishuWsReceiver` construction will receive the existing `writeApprovalDecision` function through its typed `writeApproval` port. The receiver remains unaware of PostgreSQL and service segmentation, while Web, client, delegated-task, and Feishu ingress continue to converge on one first-writer-wins authority.

Direct store access from the receiver was rejected because it would create a second write owner. Restoring file signalling was rejected because it cannot provide process-independent atomicity and would contradict the durable approval contract. Weakening the missing-port error was rejected because an unwired authorization path must remain visibly unavailable, not report success.

### Use one canonical Facebook post identity at both validation boundaries

Cloud will correlate the requested target and returned detail through its existing canonical Facebook post-key helper. Equivalent URL forms for the same post will match; malformed URLs or different post identities will not.

Raw URL equality was rejected because Facebook legitimately presents one post through group, page, permalink, reel, video, and query-string forms. Path-only matching was rejected because it can collapse unrelated targets or miss equivalent identities.

### Make Native `note.open` perform post-action identity validation

After navigation and document readiness, the Native Page Engine will poll the existing Facebook router within the established detail-hydration window. It returns `NoteDetail` only after the result's canonical identity equals the requested target. Details for another post are discarded as transient evidence. If the target never appears, Edge returns an explicit failure before Cloud's open-step deadline.

Returning the first hydrated article was rejected because it converts stale page state into false target evidence. Letting Cloud retry navigation was rejected because browser-state validation belongs at Edge and would duplicate pacing. A configurable timeout was rejected because existing real-machine evidence and the baseline spec already define the bounded window.

### Keep protocol and non-Facebook behavior unchanged

The existing `note.detail.arrived` and `action.completed` events remain sufficient. The repair changes validation and composition only; other platforms and command routes keep their current semantics.

## Risks / Trade-offs

- [Facebook URL shapes drift] → Reuse the canonical shape whitelist already required by `facebook-note-scoped-targeting`, cover observed forms, and fail with no identity instead of guessing.
- [Polling adds latency on unavailable posts] → Keep the wait bounded to the established hydration evidence and below Cloud's deadline; expose an honest Edge failure.
- [A future service-mode composition omits the write port again] → Add a production-composition regression while retaining the receiver's visible fail-closed behavior.
- [Cloud and Edge identity parsers diverge] → Test equivalent URL forms and mismatch rejection on both sides; protocol continues carrying the URL so no migration is required.

## Migration Plan

1. Integrate and deploy the Cloud repair to DEV, then verify process health, listener, Feishu connectivity, and PostgreSQL-backed approval startup.
2. Rebuild the local Edge Native Page Engine and run source-level Native verification. Do not package an installer.
3. Verify the Feishu callback path and a Facebook comment-open path in DEV if a real-account probe is available; report it separately from code validation.
4. Roll back Cloud to the previous deploy backup if health or connectivity checks fail. The change has no schema migration and no protocol compatibility window.

## Open Questions

None. The incident evidence, existing canonical-identity contract, and current service composition define the required behavior.
