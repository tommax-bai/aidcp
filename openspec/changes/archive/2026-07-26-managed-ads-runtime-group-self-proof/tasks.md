## 1. CLI session reset

- [x] 1.1 Extend the Ads runtime helper with an injectable reset-before-ensure option that runs bounded CLI `status`/`stop` before `start` and preserves honest stop errors.
- [x] 1.2 Add focused runtime tests for already-stopped, successfully-stopped, stop-failed, and stop-timeout ordering without launching a real daemon.

## 2. Managed routing and group self-proof

- [x] 2.1 Track successful first-session runtime reset in the Electron main process so warm-up and real actions share one single-flight reset and later ensures do not stop the healthy daemon again.
- [x] 2.2 Make `adsServiceBase` outrank renderer/settings API-base values once the managed runtime is established, while preserving form/settings fallback before establishment.
- [x] 2.3 Clarify the exact-`aidcp` missing-group error as a current runtime account/permission-space failure and keep `group/create`/`user/create` fail-closed.

## 3. Regression coverage and validation

- [x] 3.1 Add focused tests proving a managed fallback port wins over a stale `50325` form value and that session reset is committed only after successful runtime establishment.
- [x] 3.2 Run focused Electron provisioning/runtime tests, the full Edge test suite, and `npm run typecheck` in the isolated Edge worktree.
  <!-- validation="focused 49/49; acceptance 25/25; full Edge 1901/1901; npm run typecheck" result="pass" -->
- [x] 3.3 Run `openspec validate managed-ads-runtime-group-self-proof --strict` and record Edge commit, validation, packaging boundary, and deviations in this task file.
  <!-- repo="aidcp-edge" commit="19ee12b" openspec="strict pass" packaging="not requested; source-only" real-machine="not performed" deviations="none" -->

## 4. Integration

- [x] 4.1 Rebase and fast-forward the validated Edge change to `master`, push it, and leave desktop packaging/release explicitly unperformed.
  <!-- repo="aidcp-edge" landed="19ee12b on origin/master" post-rebase-validation="focused 49/49; typecheck pass" packaging="not performed" -->
- [x] 4.2 Rebase and fast-forward the validated OpenSpec change to control-repo `main`, push it, and report source-only completion without claiming real-machine validation.
  <!-- control="rebased to origin/main" validation="strict pass" delivery="source-only" real-machine="not performed" -->
