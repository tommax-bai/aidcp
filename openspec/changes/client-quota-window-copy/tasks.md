## 1. Edge Renderer

- [x] 1.1 Replace vague minute/hour labels and derive active-session remaining time plus supplied start/end range with honest fallbacks. <!-- aidcp-edge b0b3259 -->
- [x] 1.2 Render capped detail rows as confirmed count plus secondary `最多 N`, while uncapped rows omit false slash/cap/progress semantics. <!-- aidcp-edge b0b3259 -->
- [x] 1.3 Change expanded quota-window details to a normal-width 2×2 grid and a narrow one-column layout without changing the collapsed daily summary. <!-- aidcp-edge b0b3259 -->

## 2. Tests

- [x] 2.1 Update the focused Electron companion test for the four labels, session timing, capped/uncapped row copy, release copy, and 2×2/one-column CSS contract. <!-- aidcp-edge b0b3259 -->
- [x] 2.2 Add focused fallback coverage proving inactive or missing session timing does not fabricate a countdown or end time. <!-- aidcp-edge b0b3259 -->

## 3. Validation

- [x] 3.1 Run the focused Electron companion UI test and any directly affected renderer tests. <!-- aidcp-edge focused: ./node_modules/.bin/tsx --test test/electron/companion-ui.test.ts, 74/74 pass -->
- [x] 3.2 Run `npm run typecheck` in the isolated Edge worktree. <!-- aidcp-edge pass -->
- [x] 3.3 Run `openspec validate client-quota-window-copy --strict` in the isolated control worktree. <!-- strict validation pass -->

## 4. Delivery

- [ ] 4.1 Commit the Edge implementation and control artifacts with repo SHAs and validation evidence recorded in this task file.
- [ ] 4.2 Rebase/refresh against latest defaults, rerun required validation, fast-forward integrate, and push Edge `master` plus control `main` without packaging an installer.
