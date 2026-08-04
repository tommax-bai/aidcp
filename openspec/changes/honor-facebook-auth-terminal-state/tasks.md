## 1. Terminal authentication exit

- [x] 1.1 Add a focused regression proving terminal Facebook authentication closes the owned browser before exit and reports closure only after confirmation.
- [x] 1.2 Route terminal Facebook authentication failures through the existing confirmed browser-close operation without adding retries or states.

## 2. Failure presentation

- [x] 2.1 Add a focused renderer regression proving `loginFlow.failed` does not display `待命中`.
- [x] 2.2 Prioritize the existing terminal login failure in `presenceView()`.

## 3. Validation and delivery

- [x] 3.1 Run focused Edge tests and typecheck.
- [x] 3.2 Run the required Edge acceptance/full suites and strict OpenSpec validation.
- [x] 3.3 Commit, push, and record delivery evidence without building an installer.

## Evidence

- Edge implementation: `aidcp-edge` commit `b9f9979f0d64af16a5ce02a22b511f13cfb6ec11`, fast-forwarded and pushed to `origin/master`.
- Focused validation on the rebased final source: 92 tests passed; `npm run typecheck` passed; `git diff --check` passed.
- Release validation on the rebased final source: `npm run test:acceptance` passed 39 tests; the full `npx tsx --test --test-reporter=dot test/**/*.test.ts` run exited 0. An earlier full run exposed one unrelated companion-UI timing failure; its isolated rerun passed, followed by repeated full-suite exit-0 runs.
- Control validation: `openspec validate honor-facebook-auth-terminal-state --strict` passed before implementation; final validation is recorded in the control commit.
- Delivery boundary: source and OpenSpec only. No real-account operation, Edge installer build/install, or Cloud/Console deployment was performed.
