## 1. Edge authority and migration

- [ ] 1.1 Remove the Edge wait-threshold default, persisted setting, and
  `AIDCP_BROWSER_COLD_STANDBY_MIN_WAIT_MS` override; evaluate current remaining
  wait only against the validated Cloud hint.
- [ ] 1.2 Ignore legacy `browserColdStandbyMinWaitMs` during settings load,
  omit it from readback, reject it from save patches, and remove it on the next
  successful normal settings write.
- [ ] 1.3 Add focused regressions proving a stale 20-minute local value and
  Edge environment override cannot veto a five-minute Cloud hint, while
  missing/malformed hints and short current waits remain fail-safe.

## 2. Cloud and contract alignment

- [x] 2.1 Update Cloud source commentary and focused contract coverage to state
  that `browserStandby.minWaitMs` is the single wait-threshold authority without
  changing hint generation or wire shape.
  <!-- aidcp-cloud: source comment plus resolved-threshold boundary coverage;
  focused browser-standby/protocol 42/42 and typecheck passed; runtime code and
  wire shape unchanged. -->
- [x] 2.2 Update `docs/protocol.md` and reconcile the active
  `browser-slot-scheduling` cold-standby delta so neither documents a local
  Edge threshold.
  <!-- aidcp: protocol example/authority wording and the active proposal,
  design, tasks, and cold-standby delta aligned; git diff --check passed.
  Historical acceptance records remain historical evidence. -->

## 3. Validation

- [ ] 3.1 Run Edge focused cold-standby/settings tests, acceptance tests, full
  tests, and typecheck.
- [ ] 3.2 Run Cloud focused browser-standby/protocol tests, full tests, and
  typecheck.
- [ ] 3.3 Run `openspec validate make-cloud-standby-threshold-authoritative
  --strict` and bounded drift searches for the removed Edge setting/override.

## 4. Integration and closeout

- [ ] 4.1 Commit and serially land Edge and Cloud changes on their default
  branches, recording commit SHAs and validation evidence here.
- [ ] 4.2 Commit and push the control-repo artifacts, record that no Cloud
  runtime deployment is needed, and preserve the explicit boundary that no
  installed Edge client changes until a separately authorized package/release.
- [ ] 4.3 Archive the completed OpenSpec change and run strict validation of
  the synchronized baseline.
