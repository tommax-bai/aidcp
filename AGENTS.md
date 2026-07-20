# AGENTS.md

Active Codex guide for the `aidcp*` family. Keep this file at or below 8 KiB because Codex loads it into every task; move details to task-specific references. `CLAUDE.md` is legacy background and is not a default prerequisite.

## 1. Repo role and task admission

- `aidcp` is the control repo for contracts, architecture, OpenSpec, product docs, and orchestration helpers. Business code lives in sibling repos: `../aidcp-edge`, `../aidcp-cloud`, and `../aidcp-console` (default branches `master`; control repo default is `main`). Confirm a sibling exists before using it.
- Do not run root `npm test`, `npm run build`, or `npm run lint`; this is not an app checkout. Validate control changes with OpenSpec.
- Before opening a task, creating/reusing a worktree, or using task helpers, run `& "$env:ProgramFiles\Git\bin\bash.exe" ./scripts/task-preflight` in Windows PowerShell or `./scripts/task-preflight` in Bash. Use the same Git Bash prefix for every extensionless `scripts/*` entry. A failure blocks admission; do not switch branches, stash, clean, remove worktrees, or override it automatically.
- Canonical checkouts stay on their default branches. Feature work uses `../<repo>.wt/<change-name>` and `codex/<change-name>` branches. Never put `main` in an `aidcp.wt` worktree or switch the canonical control checkout to a feature branch.
- Preserve unrelated dirty/untracked files. Use isolated worktrees and explicit pathspecs.

Read on demand:

- Architecture/protocol/risk work: `docs/architecture.md`, `docs/protocol.md`, `docs/risk-control.md`.
- Worktree/integration work: `docs/parallel-dev-worktrees.md`.
- Any SSH, `rsync`, or deployment: `docs/deployment-environments.md`.
- Edge Electron process launch or packaging: the active `aidcp-edge` checkout's `CLAUDE.md` packaging section and `docs/release-desktop.md`.
- An assigned OpenSpec change: its `proposal.md`, `design.md` when present, `tasks.md`, spec deltas, and `openspec instructions apply --change <name> --json` when useful.
- Read root `CLAUDE.md` only when this guide and the references above do not resolve a material legacy detail.

## 2. Architecture invariants

- Decide first whether work belongs in edge, cloud, console, or control docs/contracts.
- Edge stays light: browser actions belong on edge; planning, selection strategy, orchestration, persistence, and primary pacing belong in cloud.
- Cloud `RiskController` is the single writer of final account risk state.
- Never fake success. Missing targets, bad pages, missing data, movement, and counts must be reported honestly.
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
- Default requested output budgets: 1,000-2,000 tokens for discovery/status commands and at most 4,000 for tests, builds, deploy checks, or focused failure evidence.
- Use `rg`/`rg --files`, targeted file ranges, focused tests, and concise reporters. Do not dump entire files, full test suites, build logs, `journalctl`, SSH output, database result sets, or repeated polling output into the task transcript.
- On success, retain the command, exit status, duration when relevant, and a short pass/count summary. On failure, retain the failing test/check names, primary error block, and at most the final 120 relevant lines; narrow and rerun before expanding.
- If output is truncated, do not infer success. Check the exit code and inspect smaller slices until the cause and validation result are supported.
- Run focused tests first. Run full suites only when required by the touched risk area or final integration, and summarize successful full-suite output.
- For long-running commands, use a background session and report only new state or bounded deltas on each poll.
- Detailed operating examples and the failure-expansion ladder live in `docs/codex-output-budget.md`; read it when a command may be noisy.

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
- Explain mechanism first, preserve honest validation boundaries, never record secrets, and close with what changed, impact, and next step.

## 8. Codex mapping

- Historical Claude slash commands map to natural-language intent, OpenSpec CLI, and repo helpers. Do not install an OpenSpec skill just to follow this workflow.
- Prefer this file when it conflicts with `CLAUDE.md`; use the latter only for explicitly needed legacy background.
