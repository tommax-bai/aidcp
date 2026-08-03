# AGENTS.md

Codex guide for `aidcp*`; keep below 8 KiB. Put details in task references.

## 1. Repo role and task admission

- `aidcp` owns contracts, architecture, OpenSpec, product docs, and orchestration. Business code lives in `../aidcp-edge`, `../aidcp-cloud`, and `../aidcp-console` (`master`; control uses `main`).
- Do not run root `npm test`, `npm run build`, or `npm run lint`; this is not an app checkout. Validate control changes with OpenSpec.
- Before task/worktree/helper use, run `./scripts/task-preflight` in Bash or `& "$env:ProgramFiles\Git\bin\bash.exe" ./scripts/task-preflight` in PowerShell. Use Git Bash for extensionless `scripts/*`. Failure blocks admission; do not switch, stash, clean, remove worktrees, or override it.
- Canonical checkouts stay on defaults. Feature work uses `../<repo>.wt/<change-name>` and `codex/<change-name>`. Never put `main` in `aidcp.wt` or switch control.
- Preserve unrelated dirty/untracked files. Use isolated worktrees and explicit pathspecs.

Read on demand:

- Architecture/protocol/risk work: `docs/architecture.md`, `docs/protocol.md`, `docs/risk-control.md`.
- Worktree/integration work: `docs/parallel-dev-worktrees.md`.
- Any SSH, `rsync`, or deployment: `docs/deployment-environments.md`.
- Edge Electron launch/packaging: active `aidcp-edge/CLAUDE.md` packaging section and `docs/release-desktop.md`.
- Assigned change: read its proposal, design, tasks, spec deltas, and relevant apply instructions.

## 2. Architecture invariants

- Decide first whether work belongs in edge, cloud, console, or control docs/contracts.
- Edge stays light: browser actions belong on edge; planning, selection strategy, orchestration, persistence, and primary pacing belong in cloud.
- Cloud `RiskController` is the single writer of final account risk state.
- DEV and OL share PostgreSQL long-term. Durable async work handled by background code stores server-injected `execution_target=dev|ol`; lifecycle reads/writes filter the local target. Missing/invalid `AIDCP_DEPLOY_ENV` disables that worker. Shared business data/config is excluded.
- Never fake success; report missing/ambiguous targets, bad pages/data, movement, and counts honestly.
- Fail closed at irreversible writes; never promote unknown/failure to success.
- DOM-first locating keeps bounded retries and checks. DOM `click()` is not proof: progress/write controls require a fresh target, Native CDP mouse events, and verified post-state; cache after repeated success.
- Protocol v2 changes stay synchronized across cloud/edge types, cloud command mapping, edge active-command routing, and `docs/protocol.md`.
- Prefer the current event-driven v2 browse loop; do not revive deleted legacy planner/card-filter paths.

## 3. Design admission and OpenSpec

- State the outcome, evidence, minimum delta, and non-goals. Reuse one current path; unknown stops visibly.
- Retry, fallback, compatibility, knobs, or authority/schema/repo/platform expansion need observed evidence/contract and approval after stating the owner, observability, exit/postcondition, cost/risk, and narrower alternative. Otherwise defer. Split work that cannot ship independently; delete branches not required by the outcome.
- Behavior contracts, cross-repo/module work, protocol, risk, publish, deployment flow, and user-facing behavior changes use OpenSpec: start with `openspec list`, work in `openspec/changes/<name>/`, and never edit `openspec/specs/` directly. Guide/config-only edits may skip it when behavior and deployment are unchanged.
- Reconcile `tasks.md` with source/deployment evidence; completed items record repo, SHA, validation, deployment, and deviations. Finish with `openspec validate <name> --strict`; archive only when required work is complete. Validation proves consistency, not necessity or feasibility.

## 4. Context and command-output budget

- `.codex/config.toml` caps retained output per call at 4,000 tokens. Default to 1,000-2,000 for discovery and at most 4,000 for validation/failures.
- Use `rg`/`rg --files`, targeted ranges/tests, and concise reporters. Do not dump full files/suites/logs, `journalctl`, SSH output, database results, or repeated polls.
- Retain command, exit, duration, and pass/count on success; on failure retain the primary error and at most 120 relevant tail lines, then narrow before expanding.
- If output is truncated, do not infer success. Check the exit code and inspect smaller slices until the cause and validation result are supported.
- Run independent repo checks in parallel; serialize contention retries. Full suites remain risk/final-integration only. For long commands, use a background session and report bounded deltas.
- See `docs/codex-output-budget.md` for noisy-command examples and the failure-expansion ladder.

## 5. Testing and closeout

- Run tests in the sibling repo that owns the code. Edge/cloud normally use focused tests plus `npm run typecheck`; protocol, risk, or publish changes require acceptance first, then full tests, then typecheck.
- Keep protocol-drift, unauthorized-publish, risk-honesty, and relevant end-to-end safety suites green.
- Cloud local validation is code-level only; live cloud verification happens on the named ECS target.
- Default code finish line: implement, run proportionate tests/typecheck, update OpenSpec, commit, push default, and deploy/publish runtime changes to `dev` when gates pass.
- Documentation/config-only changes are committed and pushed but do not deploy. Do not build an Edge installer unless the user explicitly asks to package/release.

## 6. Deployment boundaries

- `dev` is the default development target; `ol` is opt-in only and deploys from an explicit `release/<date>-<scope>` branch.
- Before SSH or `rsync`, state the target, read `docs/deployment-environments.md`, and run `scripts/deploy-target <dev|ol> --check`. Stop if the target or key is unclear.
- Deploy only from a clean eligible default/release checkout, never a feature worktree. Back up cloud/env, exclude secrets/dependencies/git metadata, restart only the documented AIDCP service, then check service, listener, health, Feishu, and PostgreSQL. Roll back on failure.
- `dev` hosts unrelated `isales` services; never touch them.

## 7. Git, parallel work, and communication

- One change session = one named change, one branch, and one worktree; use the matching OpenSpec change when required. Development may be parallel; integration and deployment are serial.
- Protocol/command mapping, role registration/catalog, and risk-state machine are single-writer hotspots.
- Before integration, fetch/rebase onto the latest default, resolve conflicts, rerun required validation, then fast-forward merge. Never force-push or use non-fast-forward history without explicit approval.
- Within an explicitly requested deployment, database changes may proceed after backup, read-only impact checks, and a rollback plan. Stop when the target or rows are unclear, rollback is uncertain, or scope expands. Still stop before secret/key changes, unrelated production deletion, failed-test releases, or unrelated-service impact.
- Default user-facing prose is Chinese; code, comments, commits, PR text, commands, and filenames remain English unless the file establishes otherwise.
- Comments explain non-obvious rationale, external quirks, or invariants; use names/types/tests for the rest.
- Explain mechanism first, preserve honest validation boundaries, never record secrets, and close with what changed, impact, and next step.

## 8. Codex mapping

- Historical Claude slash commands map to natural-language intent, OpenSpec CLI, and repo helpers. Do not install an OpenSpec skill just to follow this workflow.
- Prefer this file when it conflicts with `CLAUDE.md`; use the latter only for explicitly needed legacy background.
