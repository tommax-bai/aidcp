## 1. Edge interaction and validation

- [x] 1.1 Implement a 24-item content-preference counter and block the 25th preset selection without mutating the selected set.
- [x] 1.2 Add inline accessible limit messaging, a red attempted-control state, reduced-motion behavior, and immediate recovery after deselection.
- [x] 1.3 Apply the same limit to custom preferences while preserving the rejected input and focus.
- [x] 1.4 Raise the bounded Electron transport limit to 64 and return a specific `input_too_large` reason for capacity violations.

## 2. Edge regression coverage

- [x] 2.1 Add interaction tests for 24th success, 25th rejection, attempted-chip feedback, deselect-and-replace, and custom-input preservation.
- [x] 2.2 Add Electron IPC boundary tests proving a 50-entry derived request is accepted locally while 65 entries or a 41-character item are rejected before HTTP.
- [x] 2.3 Run focused Edge tests and `npm run typecheck`; record exact results.
  <!-- aidcp-edge validation: `npx tsx --test test/electron/fleet-console.test.ts test/electron/offline-persona-ipc-contract.test.ts` => 66 passed, 0 failed; `npm run typecheck` => passed. -->

## 3. Cloud compatibility boundary

- [x] 3.1 Raise the shared customer-auth persona transport limit and legacy WS compatibility limit to 64 while retaining the 40-character item limit.
- [x] 3.2 Add Cloud tests for 64-entry acceptance, 65-entry rejection, single-item length rejection, and zero model calls on rejection.
- [x] 3.3 Run focused Cloud tests and `npm run typecheck`; record exact results.
  <!-- aidcp-cloud validation: repository test script executed the full suite => 2,723 passed, 8 skipped, 0 failed; `npm run typecheck` => passed. -->

## 4. Integration, dev deployment, and closeout

- [x] 4.1 Rebase and fast-forward integrate Edge and Cloud branches into their latest default branches, then push without force.
- [x] 4.2 Deploy the committed Cloud default branch to dev and verify service, listeners, health, PostgreSQL, and persona generation boundary logs without touching unrelated services.
- [x] 4.3 Record repo commits, validation, deployment, deviations, and the explicit no-installer boundary in this task file.
  <!-- Repos: aidcp-edge `38f805e` and aidcp-cloud `81c29d1`, both fast-forwarded and pushed to `origin/master` without force. -->
  <!-- Dev deployment: Cloud `81c29d1` source delta deployed from clean master to `121.89.85.150:/opt/aidcp/cloud`; rollback backup `/opt/aidcp/cloud.bak.20260720-151918Z.tar.gz` plus target-local `.env.bak.20260720-151918Z`. Local and deployed SHA-256 hashes matched for all four transferred files. -->
  <!-- Dev verification: `aidcp-cloud.service` active since 2026-07-20 23:20:28 CST with `NRestarts=0`; listeners 8787/8090/8091/5432 present; internal and public panel/client-auth health returned `{ok:true}`; PostgreSQL `select 1` passed; Feishu `WSClient onReady` logged; deployed persona focused tests 24 passed, 0 failed; four `isales-*` services remained active/running. -->
  <!-- Validation: Edge focused tests 66 passed, Cloud focused tests 24 passed, Cloud full suite 2,723 passed with 8 gated skips, both typechecks passed. No Edge installer was built or published; the UI behavior reaches customers with a future normal Edge release. -->
- [x] 4.4 Run `openspec validate persona-preference-selection-limit --strict` and leave the completed change ready for archive.
  <!-- Strict OpenSpec validation passed after implementation and deployment evidence was recorded. Change intentionally remains unarchived for explicit archive follow-up. -->
