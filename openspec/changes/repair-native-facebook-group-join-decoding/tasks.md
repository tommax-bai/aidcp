## 1. Diagnostic-First Native Contract

- [x] 1.1 Create the isolated Edge worktree, install its physical dependencies, and add failing Rust/protocol/client fixtures for wrapper, result-kind, nested typed-field, redaction, and optional-diagnostic behavior.
  <!-- Edge worktree uses codex/repair-native-facebook-group-join-decoding from origin/master with physical npm dependencies. Pre-implementation red gates: Rust failed to compile on absent diagnostic types/fields; TypeScript client test rejected because diagnostic was not forwarded. -->
- [x] 1.2 Implement the bounded Native error diagnostic and TypeScript forwarding without changing the stable error code, static message, or group-join field contract.
  <!-- Rust lib 87/87, Native client 13/13, and TypeScript typecheck passed. The diagnostic contains finite stages, bounded field path, JSON category, and no offending value/parser text. -->
- [x] 1.3 Annotate each full group-join decode boundary with its finite operation stage and preserve a bounded diagnostic when the best-effort reuse probe is discarded.
  <!-- Group Join distinguishes reuse, action-gate page/consent/result, readiness, click, and verification; the swallowed reuse optimization emits only serialized bounded diagnostic fields. -->
- [x] 1.4 Build the diagnostic-only Native binary and run `group_join(click=false)` against the exact open `Tianxing Bai` group page; record the observed operation stage, decode stage, field path, JSON category, binary hash, and no-click boundary.
  <!-- sha256 63d2f83eb6f7dd55b502c0607997cf3836bf3d9a54d363dd9828847e93d596b6: readiness_probe/cdp_exception/object, with no field path because the router threw before JSON. Three content-free direct repetitions classified TypeError at assembled line 13:55, cannot_read_property querySelectorAll. Root cause: commentEditor(null) during transient body-less navigation. click=false entered no commit/click path. Installed and unmodified current binaries reproduced the generic failure. -->

## 2. Evidence-Driven Group Join Repair

- [x] 2.1 Add the captured null-root router regression fixture and repair only the nullable `commentEditor` boundary, without a page-wide fallback, new retry, or typed-field coercion.
  <!-- The characterization failed with the exact TypeError/querySelectorAll stack. The focused fixture now returns bounded found=false, joined=false, composerPresent=false; the full Facebook router suite passes 68/68. -->
- [x] 2.2 Classify `group_join(click=false)` as observation-only while retaining conservative ambiguity for `click=true` failures whose actuation boundary is unknown.
  <!-- NativeCommand::may_write follows params.click == Some(true); focused Rust coverage passes for false, absent, and true. -->
- [x] 2.3 Inspect the bounded real target-header structure, add the observed `已加入` sibling-layout fixture, and narrowly repair current-group scope while keeping all existing recommendation/foreign-group adversarial fixtures green.
  <!-- Real path uses vanity tuyendung.dongvan while its header member link uses numeric 1611255345558924; literal comparison truncated scope before the sibling 已加入 control. The resolver learns that one numeric alias only inside a non-main unique-heading ancestor with no third group identity. Router suite passes 70/70 including a main-level recommendation /members decoy. -->
- [x] 2.4 Rebuild and rerun the exact real observation-only command; confirm typed decoding and target membership readback without a click, and record the installed-client/source boundary.
  <!-- Final source binary sha256 de3d86804e3c5167f8a8644c6e6e6679ee0b25ce4729c7f968ede1cc046cf789 returned confirmed/already_member, clicked=false, commitWindows=0, targetGroupId=tuyendung.dongvan, scopeResolved=true, membershipSignals=[已加入], and the joined candidate inTargetScope=true. /Applications/AIDCP.app remains unchanged and still contains the old generic-failing binary. -->

## 3. Validation and Integration

- [x] 3.1 Run focused Facebook router, TypeScript Native client/browse-session, Rust unit, and Rust fake-CDP group-join tests.
  <!-- Focused TypeScript passed 104/104, including Facebook router 70/70; Rust lib passed 88/88 with one test thread; Fake-CDP Group Join passed 3/3. The unrelated publish deadline fixture passed in isolation but can start after its deadline under Rust's parallel test load, producing NotStarted instead of its intended post-click Ambiguous state. No production or test threshold was changed for that pre-existing timing sensitivity. -->
- [x] 3.2 Run Rust formatting and lint checks plus Edge acceptance, full test, and typecheck gates with bounded output.
  <!-- cargo fmt --check and clippy --all-targets --all-features -D warnings passed. Edge acceptance passed 30/30; full npm test passed 2453 with 1 gated E2E skip and 0 failures out of 2454; npm typecheck passed. The Native release build passed encoded-page-rule verification. -->
- [x] 3.3 Run `openspec validate repair-native-facebook-group-join-decoding --strict` and record repositories, commits, test counts, real-browser evidence, deviations, and delivery boundaries.
  <!-- Strict validation passed. Edge implementation commit c37ae9c and control artifact commit eef864e contain the repositories' changes. Counts and the real-browser result are recorded above. Delivery stops at source/default-branch integration: the installed client is still unchanged. -->
- [x] 3.4 Commit and push the isolated Edge and control branches, rebase and fast-forward integrate them into the current default branches, rerun required post-rebase gates, and leave packaging/install/release untouched.
  <!-- Edge rebased without overlap onto origin/master 20e1a09, then post-rebase TypeScript 104/104, Rust 88/88, Fake-CDP 3/3, acceptance 30/30, and typecheck passed before c37ae9c fast-forwarded master. The control artifact commit eef864e and this closeout commit fast-forward main. No package, signature, installer, installed app, Cloud deployment, or release was changed. -->
