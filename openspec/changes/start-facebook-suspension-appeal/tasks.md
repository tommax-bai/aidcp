## 1. Native suspension-appeal contract

- [x] 1.1 Add exact suspension checkpoint recognition, visible/enabled/topmost Appeal binding, and loaded-successor postcondition logic to the Facebook auth router.
- [x] 1.2 Add the typed `suspension_appeal_start` signal and `facebook_auth_start_suspension_appeal` command across Native model/command/capability and TypeScript client registries, including command-postcondition evidence.
- [x] 1.3 Route the signal through the startup auth coordinator and retain the confirmed successor as an operator-required state that blocks identity/Cloud startup without broadening unsupported-checkpoint authority.

## 2. Regression coverage

- [x] 2.1 Add router tests for the observed hidden disabled clone plus visible target, exact page guards, loading, and accepted/rejected successor states.
- [x] 2.2 Add Native command tests for fresh signal binding, trusted pointer execution, confirmed advancement, ambiguous transition, cancellation/deadline, and replay refusal.
- [x] 2.3 Add coordinator and startup tests for the standalone action mapping, terminal manual handoff, contextual checkpoint deferral, authenticated recovery, and fail-closed unrelated states.

## 3. Validation and delivery

- [x] 3.1 Run focused auth/router/startup tests, required Edge acceptance/full tests and typecheck, Rust fmt/clippy/tests, command-postcondition validation, and `git diff --check`.
  - Evidence: focused TypeScript auth/router/startup/postcondition tests passed 75/75; on the rebased Edge source, acceptance passed 39/39 and full TypeScript passed 3099/3100 with one gated real-account E2E skip and zero failures; `npm run typecheck`, Rust fmt, clippy with warnings denied, the complete Native test gate, and `git diff --check` all passed.
- [x] 3.2 Run `openspec validate start-facebook-suspension-appeal --strict` and reconcile the task evidence with actual source/runtime boundaries.
  - Evidence: strict validation passed. Source validation did not package or install Edge, restart `Facebook import 5`, or click the real account's Appeal control; those remain separate runtime acceptance boundaries.
- [x] 3.3 Commit the Edge and control changes, rebase/fast-forward them onto current defaults, push both defaults, and record source SHAs plus the explicit no-package/no-install/no-live-click boundary.
  - Evidence: `aidcp-edge` master `0dc438fd5a7b94ecb218d8b35008dde0258ef6d8`; `aidcp` main OpenSpec source `24d6a92c2b2a7b7343b562a3bc29d0e267c46a3a`. Both were rebased and fast-forward pushed. No Edge package was built or installed, `Facebook import 5` was not restarted, and no live Appeal click was performed.
