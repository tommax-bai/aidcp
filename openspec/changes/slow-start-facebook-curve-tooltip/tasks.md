## 1. Platform visibility

- [x] 1.1 Make slow-start rendering explicitly depend on the selected environment being Facebook, and fully hide/reset the row for Xiaohongshu or unknown platforms.
- [x] 1.2 Add renderer tests proving Facebook shows the row while Xiaohongshu hides the switch, status, copy, and help entry even when a slow-start snapshot exists.

## 2. Copy and curve help

- [x] 2.1 Replace the persistent slow-start explanation with the requested seven-day/account-tier copy.
- [x] 2.2 Add a focusable question-mark help button and responsive hover/focus panel containing the 7×6 Facebook curve-limit table.
- [x] 2.3 Add DOM/accessibility tests for the exact copy, table title, day-by-day values, keyboard focusability, and non-bubbling interaction.

## 3. Validation and closeout

- [x] 3.1 Run the focused slow-start UI logic and renderer smoke tests. <!-- PASS: 155/155 across ui-logic, renderer-smoke, companion-ui -->
- [x] 3.2 Run `npm run typecheck` in `aidcp-edge` and `openspec validate slow-start-facebook-curve-tooltip --strict` in the control worktree. <!-- PASS: typecheck exit 0; OpenSpec strict valid -->
- [x] 3.3 Review the diff for protocol/cloud scope creep, record validation and commit evidence, and prepare the completed change for integration. <!-- Scope: renderer HTML/CSS/JS + UI tests only; no protocol/cloud/dependency/package changes. aidcp-edge 3a1ffe4bde4ea05d683d39122cc90984f0f7fd91; installer/deploy not run because no client release was requested. -->
