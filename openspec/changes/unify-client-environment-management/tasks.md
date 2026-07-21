## 1. Shared proxy parsing and planning

- [x] 1.1 Move line splitting and safe `host:port[:user:password]` / `----` parsing into the shared proxy config module while preserving structured normalization as the single truth source.
- [x] 1.2 Refactor Facebook batch creation to consume the shared parser without changing its existing round-robin or safe-error behavior.
- [x] 1.3 Add pure helpers and unit tests for explicit ordered proxy reassignment plans, duplicate/empty targets, rotation, and safe partial-failure receipts.

## 2. Scoped main-process proxy writes

- [x] 2.1 Add a named parse IPC for single-line preview and expose it through preload without arbitrary channel or URL access.
- [x] 2.2 Harden the existing single proxy update IPC to fail closed outside the current customer-visible environment set when customer auth is enabled.
- [x] 2.3 Add a named batch proxy update IPC that validates all explicit targets and proxy lines before writes, rejects known active targets, executes serially, stops on first failure, and returns credential-free receipts.
- [x] 2.4 Add focused main/preload/write-boundary tests proving target scoping, prevalidation-before-write, two-key `user/update`, serial rotation, active-target refusal, and partial failure truth.
  <!-- Edge: pure scope/plan/executor tests plus named IPC and write-boundary contract tests cover stale/foreign scope, zero-write ordering, two-key user/update, single-flight serial stop, active races, and partial receipts. -->

## 3. Simple environment management UI

- [x] 3.1 Rename the left-rail entry and popover to “环境管理”, replace add-only icon semantics, and reduce primary tabs to “环境 / 新建环境”.
- [x] 3.2 Simplify environment membership copy to “已加入 / 未加入 / 加入 / 移出”, keep default rows free of checkboxes, and preserve refresh, manual-ID fallback, platform correction, single delete, and immediate roster persistence.
- [x] 3.3 Add single-environment quick proxy paste that fills the existing structured form through the shared parse IPC without displaying stored passwords in clear text.
- [x] 3.4 Add an on-demand batch proxy selection/form/preview state inside environment management, with explicit frozen targets, disabled active rows, round-robin reuse summary, cancel/reset behavior, and honest completion/partial-failure feedback.
- [x] 3.5 Update responsive styles so the wider management popover remains compact on ordinary desktop windows and falls back cleanly on narrow windows without creating a persistent detail page.
  <!-- Edge renderer: management stays a two-tab popover; batch selection is temporary, cancellation clears credentials, partial failure preserves them, and <=660px uses a compact wrapping layout. -->

## 4. Validation, integration, and delivery

- [x] 4.1 Extend renderer and fleet-console tests for the management entry/tabs, concise copy, default no-checkbox state, single-line paste, explicit batch selection, stable mapping, and failure preservation.
- [x] 4.2 Run focused proxy/environment tests and acceptance, then the full Edge test suite and `npm run typecheck`; record commands, counts, and any bounded flakes.
  <!-- Edge validation: focused proxy/management suites passed; `npm run test:acceptance` passed 28/28 tests (real-machine suite remained gated); final integration gate passed the full `tsx --test test/**/*.test.ts` suite at 2114/2114 and `npm run typecheck`. No flakes observed. -->
- [x] 4.3 Run `openspec validate unify-client-environment-management --strict`, commit the Edge worktree and control artifacts with validation evidence, and integrate by the documented fast-forward workflow without disturbing unrelated files.
  <!-- Edge integration: rebased onto the moving `origin/master`, preserved the concurrent scoped password-retention change with a masked password input, reran all gates, fast-forwarded and pushed `c484ed9`, synchronized the canonical checkout, and removed the feature worktree. Unrelated control-repo paths remained untouched. Control strict validation is rerun before its final commit. -->
- [x] 4.4 Push both default branches, run the dev deployment precheck, deliver every applicable runtime artifact, and record health evidence or an explicit non-applicable boundary.
  <!-- Delivery: Edge `master` was pushed at `c484ed9`; `scripts/deploy-target dev --check` passed for host `121.89.85.150` with readable key and configured Cloud/Console paths. This change has no Cloud/Console/server runtime artifact, and an Edge installer was not requested, so SSH/rsync/service health and installer publication are not applicable. The control `main` push is completed after this evidence commit. -->
