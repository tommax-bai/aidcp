# Tasks — facebook-publish

## 1. Preconditions

- [ ] 1.1 Ground on `origin/main` (control repo) + `master` (aidcp-edge / aidcp-cloud); rebase before integrating.
- [ ] 1.2 Confirm dependency A `account-nurture-discipline-spine` is landed: nurture-disciplined per-day quotas and real rate-limit backoff exist, so a brand-new Facebook account is not on the normal full quota tier on Day 1.
- [ ] 1.3 Confirm dependency B `facebook-browse-and-like-loop` is landed BEFORE starting C: B is the change that first makes the `facebook` registry entry declare a non-comment capability and exercises the edge driver capability-assembly gate; publish builds on that gate rather than re-inventing it.
- [ ] 1.4 Confirm the publish approval three-layer defense in depth is reused as-is, not re-built: approval signal file contract (`/tmp/aidcp-publish-approve-<id>.json`), edge lease quiesce, `CommandSequencer` step-by-step sequence, and the version gate against approve-then-edit TOCTOU are all shared platform-neutral mechanisms.
- [ ] 1.5 Confirm the target is zero change to `protocol.ts` (both copies) and `docs/protocol.md` message counts; the new publish command kind is edge-side only, not a protocol message type.

## 2. aidcp-edge — Facebook publish executor

- [ ] 2.1 Implement a Facebook publish executor under `src/facebook/` that navigates to the Facebook composer surface (own timeline / target Page composer), fills the post body, optionally attaches images, and submits — never touching `creator.xiaohongshu.com` or xhs publish DOM.
- [ ] 2.2 Real-machine probe the Facebook composer to pin down selectors for the composer open control, the body editor, the optional image attach control, and the submit/post control; record selectors without secrets.
- [ ] 2.3 Route the Facebook publish executor only through the platform driver assembly so an xhs edge never reaches Facebook publish DOM and vice versa.

## 3. aidcp-edge — Facebook PublishCommandKind

- [ ] 3.1 Define a Facebook-specific publish command kind whose steps model the Facebook composer single flow (inline/dialog), NOT the xhs `select_mode` "上传图文" tab step, NOT xhs topic-`@`/hashtag, NOT xhs cover selection.
- [ ] 3.2 Keep the new kind edge-side (internal to the Facebook executor / command sequencing on the edge); MUST NOT introduce a new `protocol.ts` message type or change the `docs/protocol.md` counts.
- [ ] 3.3 Ensure the shared `CommandSequencer` still drives the Facebook publish steps under the same lease-quiesce + version-gate discipline as xhs.

## 4. aidcp-edge — publish post-verification

- [ ] 4.1 After submit, verify server-side that the post actually appears on the account's own timeline / target surface before reporting `ok`.
- [ ] 4.2 On a half-executed submit (composer closed but post not visible, or moderation/hold), return an honest failure reason; MUST NOT silently swallow into `ok`.
- [ ] 4.3 Bound the publish sequence with a watchdog timeout; on timeout return an honest `timeout`, never a fabricated success.

## 5. aidcp-cloud — registry publish + orchestration

- [ ] 5.1 Add `publish` to the `facebook` entry in the cloud platform registry; keep the edge driver capability vocabulary and the cloud registry capability vocabulary byte-for-byte aligned (a Facebook account can only reach publish after both declare it).
- [ ] 5.2 Wire Facebook publish orchestration through the EXISTING publish approval path (approval signal file contract + version gate + banned-phrase validation), not a Facebook-only branch; unauthorized (missing/invalid approval signal) MUST NOT publish.
- [ ] 5.3 Ensure Facebook publish counting flows through the existing risk actions and PG-backed quota accounting; a shadow / dry-run run records nothing and posts nothing.

## 6. Verification

- [ ] 6.1 Run `npm run test:acceptance` then full `npm test` then `npm run typecheck` on both aidcp-edge and aidcp-cloud.
- [ ] 6.2 `AC-PUB-*` (unauthorized never silently publishes) MUST pass for the Facebook path: no approval signal → no post; approve-then-edit → signature void → back to pending.
- [ ] 6.3 `AC-PROTO-*` (two `protocol.ts` copies do not drift) MUST pass; confirm no new protocol message type was added.
- [ ] 6.4 Add post-verification anti-false-success test cases: post visible → ok; half-executed/invisible → honest failure; sequence timeout → honest timeout.

## 7. Rollout (isolation window, ol)

- [ ] 7.1 Ship default-off: `AIDCP_FB_PUBLISH_AUTO=false`; shadow dry-run first (composition + approval dry-run, no real post), then flip to real posting.
- [ ] 7.2 Gate real posting on dependency B's Facebook production executor being re-proven and per-profile proxy/egress being ready.
- [ ] 7.3 Deploy to `ol` during the isolation window (never dev same-machine isales); back up before rsync, healthcheck after restart, roll back on failure.
- [ ] 7.4 Register real-machine acceptance items (composer selectors, verified-success path, false-success guard) in `docs/real-machine-acceptance-backlog.md`.
- [ ] 7.5 Record commit SHAs, validation output, probe notes, and deployment notes in this `tasks.md`; run `openspec validate facebook-publish --strict`.
