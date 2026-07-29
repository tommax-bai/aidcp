## 1. Edge authority and migration

- [x] 1.1 Remove the Edge wait-threshold default, persisted setting, and
  `AIDCP_BROWSER_COLD_STANDBY_MIN_WAIT_MS` override; evaluate current remaining
  wait only against the validated Cloud hint.
  <!-- aidcp-edge: local default/env/max removed; enabled, warmup, three-minute
  min-hold, safety gates, and wake paths unchanged. -->
- [x] 1.2 Ignore legacy `browserColdStandbyMinWaitMs` during settings load,
  omit it from readback, reject it from save patches, and remove it on the next
  successful normal settings write.
  <!-- aidcp-edge: shared sanitizer is applied after load and on both sides of
  the central save merge, so in-memory readback and the next write are clean. -->
- [x] 1.3 Add focused regressions proving a stale 20-minute local value and
  Edge environment override cannot veto a five-minute Cloud hint, while
  missing/malformed hints and short current waits remain fail-safe.
  <!-- aidcp-edge 2459214: stale setting/env, minWaitMs below 1000, snapshot
  revocation, pending/active/manual states, and task-idle reuse are covered;
  focused 44/44, acceptance 31/31, typecheck, and adversarial re-review passed. -->

## 2. Cloud and contract alignment

- [x] 2.1 Update Cloud source commentary and focused contract coverage to state
  that `browserStandby.minWaitMs` is the single wait-threshold authority without
  changing hint generation or wire shape.
  <!-- aidcp-cloud babdd84: source comment plus resolved-threshold boundary
  coverage; runtime code and wire shape unchanged. -->
- [x] 2.2 Update `docs/protocol.md` and reconcile the active
  `browser-slot-scheduling` cold-standby delta so neither documents a local
  Edge threshold.
  <!-- aidcp: protocol example/authority wording and the active proposal,
  design, tasks, and cold-standby delta aligned; git diff --check passed.
  Historical acceptance records remain historical evidence. -->

## 3. Validation

- [x] 3.1 Run Edge focused cold-standby/settings tests, acceptance tests, full
  tests, and typecheck.
  <!-- aidcp-edge 2459214: focused 44/44, acceptance 31/31, full
  2709 passed / 1 gated skip / 0 failed, typecheck and diff check passed. -->
- [x] 3.2 Run Cloud focused browser-standby/protocol tests, full tests, and
  typecheck.
  <!-- aidcp-cloud babdd84: focused 42/42, integration acceptance passed,
  full 3867 passed / 11 gated skips / 0 failed, typecheck passed. -->
- [x] 3.3 Run `openspec validate make-cloud-standby-threshold-authoritative
  --strict` and bounded drift searches for the removed Edge setting/override.
  <!-- Both this change and browser-slot-scheduling validate strictly. Edge
  runtime has no local threshold default/env/max/read; only the named legacy
  key remains in the migration stripper. Protocol example is 300000. -->

## 4. Integration and closeout

- [x] 4.1 Commit and serially land Edge and Cloud changes on their default
  branches, recording commit SHAs and validation evidence here.
  <!-- Serial ff-only land complete: aidcp-cloud master babdd84, then
  aidcp-edge master 2459214. Both canonical checkouts fast-forwarded. -->
- [x] 4.2 Commit and push the control-repo artifacts, record that no Cloud
  runtime deployment is needed, and preserve the explicit boundary that no
  installed Edge client changes until a separately authorized package/release.
  <!-- Control artifacts are committed on the isolated branch and queued for
  ff-only main push. Cloud changed comments/tests only, so no runtime deploy.
  Edge source is landed, but installed clients remain unchanged: no package,
  signing, installer, or release was performed. -->
- [ ] 4.3 Archive the completed OpenSpec change and run strict validation of
  the synchronized baseline.
