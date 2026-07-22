## 1. Capability and protocol documentation

- [x] 1.1 Add the Edge `facebook_reel_follow_v1` hello capability and Cloud connection-version gate, documenting the optional capability value in `docs/protocol.md` without changing message types or payload fields.
- [x] 1.2 Add a distinct Cloud `reel_follow` platform capability while keeping Facebook profile `follow` and `profile_visit` unsupported; project the client `follow` metric when either normal follow or Reel follow is supported.

## 2. Cloud Reel follow policy

- [x] 2.1 Add the `0.10` follow probability and a session-local canonical Reel decision set, independently from the existing like policy.
- [x] 2.2 Dispatch the existing author + note-scoped follow command only after Edge capability, session budget, RiskController, cooldown, random threshold, and same-account dispatch gates pass; preserve receipt-driven budget and risk accounting.

## 3. Edge client presentation

- [x] 3.1 Emit one structured Facebook `follow` activity with a local `follows:1` fallback only for a verified new Reel follow; keep already-followed, shadow, and failed terminals silent.
- [x] 3.2 Give follow activity a distinct “关” marker and update Facebook “今日进展” coverage to show Cloud-supplied follow totals/quotas/windows while still hiding unsupported collect.

## 4. Focused and regression coverage

- [x] 4.1 Add Cloud policy tests for hit/boundary/duplicate/invalid/authorless/old-Edge behavior, independent like+follow draws, session budget, RiskController, cooldown/dispatch suppression, and receipt-only budget consumption.
- [x] 4.2 Add Cloud platform registry and usage projection tests proving Facebook exposes Reel follow metrics without enabling profile follow, while Xiaohongshu, Video Channels, and unknown-platform fail-safe behavior remain unchanged.
- [x] 4.3 Add Edge session/renderer tests proving verified follow activity and fallback count, no-op/failure silence, the `facebook_reel_follow_v1` declaration, the distinct marker, and Facebook follow KPI/window rendering.

## 5. Validation and delivery

- [x] 5.1 Run focused Cloud/Edge tests, protocol and relevant risk acceptance suites, both typechecks, and risk-proportionate full suites in isolated worktrees.
  <!-- Cloud focused 37/37, acceptance 65/65, full suite exit 0, typecheck exit 0. Edge focused 140/140 plus UI/data-plane 104/104, acceptance 29/29, full 2184/2184, typecheck exit 0. The worktree-local macOS Electron app was removed on first launch; the Electron-only assertion and full Edge suite were rerun with ELECTRON_OVERRIDE_DIST_PATH pointing to the canonical checkout's physical Electron 31.7.7 bundle after version and executable SHA-256 equality were verified. -->
- [x] 5.2 Run `openspec validate facebook-reels-random-follow --strict`; record Cloud/Edge/control commits, validation totals, deviations, and the no-installer boundary in this file.
  <!-- Implementation commits: aidcp-cloud b0135d3; aidcp-edge ca6df3b; aidcp control/spec 9d5401c. Strict OpenSpec validation passed. Validation totals and the Electron worktree deviation are recorded under 5.1. No Edge installer was built or published because packaging/release was outside the requested scope. -->
- [ ] 5.3 Fetch/rebase onto latest defaults, rerun required gates, fast-forward push Cloud/Edge/control default branches, deploy Cloud from a clean eligible default checkout to `dev`, and verify service/listeners/health/Feishu/PostgreSQL without touching `isales`.
