## 1. Edge Renderer

- [x] 1.1 Replace vague minute/hour labels and derive active-session remaining time plus supplied start/end range with honest fallbacks. <!-- aidcp-edge 92e77a8 -->
- [x] 1.2 Render capped detail rows as confirmed count plus secondary `最多 N`, while uncapped rows omit false slash/cap/progress semantics. <!-- aidcp-edge 92e77a8 -->
- [x] 1.3 Change expanded quota-window details to a normal-width 2×2 grid and a narrow one-column layout without changing the collapsed daily summary. <!-- aidcp-edge 92e77a8 -->

## 2. Tests

- [x] 2.1 Update the focused Electron companion test for the four labels, session timing, capped/uncapped row copy, release copy, and 2×2/one-column CSS contract. <!-- aidcp-edge 92e77a8 -->
- [x] 2.2 Add focused fallback coverage proving inactive or missing session timing does not fabricate a countdown or end time. <!-- aidcp-edge 92e77a8 -->

## 3. Validation

- [x] 3.1 Run the focused Electron companion UI test and any directly affected renderer tests. <!-- aidcp-edge focused: ./node_modules/.bin/tsx --test test/electron/companion-ui.test.ts, 74/74 pass -->
- [x] 3.2 Run `npm run typecheck` in the isolated Edge worktree. <!-- aidcp-edge pass -->
- [x] 3.3 Run `openspec validate client-quota-window-copy --strict` in the isolated control worktree. <!-- strict validation pass -->

## 4. Delivery

- [x] 4.1 Commit the Edge implementation and control artifacts with repo SHAs and validation evidence recorded in this task file. <!-- aidcp-edge 92e77a8; aidcp 3abf828; focused 74/74; edge typecheck pass; openspec strict pass -->
- [x] 4.2 Rebase/refresh against latest defaults, rerun required validation, fast-forward integrate, and push Edge `master` plus control `main` without packaging an installer. <!-- aidcp-edge master 92e77a8 pushed; aidcp main 744d889 pushed; no installer built per packaging boundary -->

## 5. Completion Visual Hierarchy

- [x] 5.1 Make browsing completion the only condition that applies completion styling to an entire quota-window card and its completed row. <!-- aidcp-edge 86091a2 -->
- [x] 5.2 Keep completed non-browsing rows neutral while showing the completion-colored `完成 N 项` state for every completed action. <!-- aidcp-edge 86091a2 -->
- [x] 5.3 Derive near-limit card tone only from incomplete capped actions so a completed supporting action does not create a false near-limit state. <!-- aidcp-edge 86091a2 -->

## 6. Follow-up Validation

- [x] 6.1 Add focused DOM and CSS coverage for non-browsing completion, browsing completion, and the completion state text. <!-- aidcp-edge 86091a2 -->
- [x] 6.2 Run the focused Electron companion UI test and Edge typecheck. <!-- focused 76/76 pass; edge typecheck pass -->
- [x] 6.3 Run `openspec validate client-quota-window-copy --strict` in the isolated control worktree. <!-- strict validation pass -->

## 7. Follow-up Delivery

- [x] 7.1 Commit the Edge implementation and control artifacts with repo SHAs and validation evidence recorded in this task file. <!-- aidcp-edge 86091a2; aidcp ce14d43; focused 76/76; edge typecheck pass; openspec strict pass -->
- [ ] 7.2 Refresh against latest defaults, rerun required validation, fast-forward integrate, and push Edge `master` plus control `main` without packaging an installer.
