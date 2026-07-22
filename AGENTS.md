# AGENTS.md

Codex guide for `aidcp*`; keep it below 8 KiB. Details belong in task references; `CLAUDE.md` is legacy.

## 1. Repo role and task admission

- `aidcp` owns contracts, architecture, OpenSpec, product docs, and orchestration. Business code lives in `../aidcp-edge`, `../aidcp-cloud`, and `../aidcp-console` (`master`; control uses `main`). Confirm siblings before use.
- Do not run root `npm test`, `npm run build`, or `npm run lint`; this is not an app checkout. Validate control changes with OpenSpec.
- Before task/worktree/helper use, run `& "$env:ProgramFiles\Git\bin\bash.exe" ./scripts/task-preflight` in Windows PowerShell or `./scripts/task-preflight` in Bash. Use that Git Bash prefix for extensionless `scripts/*`. Failure blocks admission; do not switch, stash, clean, remove worktrees, or override it.
- Canonical checkouts stay on defaults. Feature work uses `../<repo>.wt/<change-name>` and `codex/<change-name>`. Never put `main` in an `aidcp.wt` worktree or switch the control checkout.
- Preserve unrelated dirty/untracked files. Use isolated worktrees and explicit pathspecs.

Read on demand:

- Architecture/protocol/risk work: `docs/architecture.md`, `docs/protocol.md`, `docs/risk-control.md`.
- Worktree/integration work: `docs/parallel-dev-worktrees.md`.
- Any SSH, `rsync`, or deployment: `docs/deployment-environments.md`.
- Edge Electron launch/packaging: active `aidcp-edge/CLAUDE.md` packaging section and `docs/release-desktop.md`.
- Assigned OpenSpec change: read its proposal, optional design, tasks, spec deltas, and apply instructions when useful.
- Read root `CLAUDE.md` only for legacy gaps.

## 2. Architecture invariants

- Decide first whether work belongs in edge, cloud, console, or control docs/contracts.
- Edge stays light: browser actions belong on edge; planning, selection strategy, orchestration, persistence, and primary pacing belong in cloud.
- Cloud `RiskController` is the single writer of final account risk state.
- DEV and OL share PostgreSQL long-term. Durable async work scanned, claimed, retried, or recovered by background code stores server-injected `execution_target=dev|ol`; all lifecycle reads/writes filter the local target. Missing/invalid `AIDCP_DEPLOY_ENV` disables that worker. Shared business data/config is excluded.
- Never fake success; report missing/ambiguous targets, bad pages/data, movement, and counts honestly.
- Add cooldowns, retries, fallbacks, compatibility branches, or knobs only for an observed failure or explicit contract; state why a simpler path fails and keep them observable/testable. Fail closed only at safety-sensitive irreversible writes; never turn unknown/failure into success.
- DOM-first locating keeps post-action validation, bounded retry/escalation, and cache promotion only after repeated success.
- Protocol v2 changes stay synchronized across cloud/edge types, cloud command mapping, edge active-command routing, and `docs/protocol.md`.
- Prefer the current event-driven v2 browse loop; do not revive deleted legacy planner/card-filter paths.

## 3. OpenSpec workflow

- Behavior contracts, cross-repo/module work, protocol, risk, publish, deployment-flow, and user-facing behavior changes go through OpenSpec first. Start with `openspec list`; use `openspec list --specs` only when baseline discovery is actually needed.
- Do not edit `openspec/specs/` directly for new behavior. Work in `openspec/changes/<change-name>/`, then implement in the owning sibling repo.
- Record progress in `tasks.md`; completed items include repo, commit SHA, validation, deployment, and deviations in concise HTML comments.
- Finish with `openspec validate <change-name> --strict`; archive only after required tasks and validation are complete.
- Typos, formatting, comments, and development-guide/config-only edits may skip a new change after confirming that product, protocol, risk, publish, and deployment semantics are unchanged.

## 4. Context and command-output budget

- Project `.codex/config.toml` caps retained output from an individual tool call at 4,000 tokens. Treat this as a ceiling, not a target.
- Default output budgets: 1,000-2,000 tokens for discovery/status and at most 4,000 for tests, builds, deploy checks, or focused failures.
- Use `rg`/`rg --files`, targeted ranges/tests, and concise reporters. Do not dump full files/suites/logs, `journalctl`, SSH output, database results, or repeated polls.
- On success, retain command, exit status, relevant duration, and a short pass/count summary. On failure, retain failing checks, primary error, and at most 120 relevant tail lines; narrow before expanding.
- If output is truncated, do not infer success. Check the exit code and inspect smaller slices until the cause and validation result are supported.
- Run independent repo tests/builds in parallel; serialize contention-related retries. Full suites remain risk/final-integration only.
- For long-running commands, use a background session and report only new state or bounded deltas on each poll.
- See `docs/codex-output-budget.md` for noisy-command examples and the failure-expansion ladder.

## 5. Testing and closeout

- Run tests in the sibling repo that owns the code. Edge/cloud normally use focused tests plus `npm run typecheck`; protocol, risk, or publish changes require acceptance first, then full tests, then typecheck.
- Keep protocol-drift, unauthorized-publish, risk-honesty, and relevant end-to-end safety suites green.
- Cloud local validation is code-level only; live cloud verification happens on the named ECS target.
- Default code finish line: implement, run proportionate tests/typecheck, update OpenSpec, commit, push the default branch, and deploy/publish to `dev` when runtime behavior changes and no gate fails.
- Documentation/config-only changes are committed and pushed but do not deploy. Do not build an Edge installer unless the user explicitly asks to package/release.

## 6. Deployment boundaries

- `dev` is the default development target; `ol` is opt-in only and deploys from an explicit `release/<date>-<scope>` branch.
- Before SSH or `rsync`, state the target, read `docs/deployment-environments.md`, and run `scripts/deploy-target <dev|ol> --check`. Stop if the target or key is unclear.
- Deploy only from a clean eligible default/release checkout, never an arbitrary feature worktree. Back up cloud/env, exclude secrets/dependencies/git metadata, restart only the documented AIDCP service, then check service, listener, health, Feishu, and PostgreSQL. Roll back on failure.
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
