## 1. Edge implementation

- [x] 1.1 Create a shared local arm64 OL macOS build implementation with deterministic Rust, dependency staging, credential handling, artifact isolation, and final DMG validation
- [x] 1.2 Add executable signed-only and signed-plus-notarized entry scripts that select the shared implementation mode
- [x] 1.3 Document environment variables, invocation, output paths, and the signed-only versus notarized trust boundary
<!-- Edge implementation: aidcp-edge 23351cd. No installer was built, notarized, uploaded, or published by this change. -->

## 2. Validation

- [x] 2.1 Add packaging contract tests for both entrypoints, shared gates, secret handling, arm64-only targeting, and sequential App/DMG notarization
- [x] 2.2 Run shell syntax checks, focused Edge packaging tests, typecheck, and desktop build-input validation
<!-- Validation at 23351cd: Bash 3.2 syntax PASS; focused packaging tests 56 passed/1 skipped; typecheck PASS; verify:desktop-build-input PASS; build:dist PASS (reachable=79, legacy_page_rules=absent, source_maps=absent). -->
- [x] 2.3 Validate the OpenSpec change strictly and record implementation evidence

## 3. Integration

- [x] 3.1 Commit and push the Edge implementation branch, fast-forward it into `master`, and push `master`
- [x] 3.2 Commit and push the control OpenSpec artifacts with final Edge commit and validation evidence
<!-- Edge branch codex/add-local-macos-release-scripts and master both point to pushed implementation commit 23351cd. -->
<!-- Control OpenSpec artifacts and strict-validation evidence were committed and pushed in aidcp f05dd5d; this follow-up records final task completion. -->
