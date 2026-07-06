# AGENTS.md

This file is the Codex-facing mapping of `CLAUDE.md`. Keep `CLAUDE.md` as the legacy Claude reference; use this file as the active Codex development guide.

## 0. Repo Role

- `aidcp` is the control repo for the `aidcp*` family. It owns contracts, architecture docs, product design, OpenSpec changes, and test/deploy orchestration.
- This repo carries docs and contracts only: `docs/`, `openspec/`, `README.md`, and helper scripts. Business code lives in sibling repos.
- Do not treat this repo as a buildable app repo. Root `npm test`, `npm run build`, or `npm run lint` are not the normal validation path here.
- Control-repo validation is OpenSpec-centric: `openspec list`, `openspec list --specs`, and `openspec validate <change> --strict`.

## 1. Path Preflight

- Sibling repo layout:
  - `.`: `aidcp`, control repo, default branch `main`
  - `../aidcp-edge`: edge runtime, default branch `master`
  - `../aidcp-cloud`: cloud runtime, default branch `master`
  - `../aidcp-console`: admin console frontend, default branch `master`
- Before touching edge/cloud/console code, tests, or deployment, confirm the sibling repo exists on this machine. Do not blindly reuse stale paths from older docs.
- Before any SSH or `rsync` to ECS, name the deployment target and verify it with `scripts/deploy-target <dev|ol> --check`.
  - `dev`: `121.89.85.150`, key `~/codes/isales-4.pem`
  - `ol`: `123.56.253.183`, key `/Users/baitianxing/Downloads/ol.pem`
  If the target is unclear or the key check fails, stop and report it.

## 2. Architecture Invariants

- Decide first whether a change belongs in edge, cloud, console, or the control repo. Use `docs/architecture.md`, `docs/protocol.md`, and `docs/risk-control.md` as the main architecture references.
- Edge stays light: atomic browser actions such as click, input, and scroll belong on edge. Planning, element selection strategy, orchestration, risk control, and persistence belong in cloud.
- Account risk state has a single writer: cloud `RiskController`. Other systems may emit events or read projections, but must not directly mutate final risk state.
- Red-line invariant: never silently fake success. Missing targets return honest failures such as `no_target`; measured movement/counts must be reported truthfully; bad pages and missing data must not be swallowed as success.
- DOM-first locating has three gates: post-action validation, bounded retry with escalation, and anti-pollution cache promotion only after repeated success. Do not weaken these gates.
- Protocol v2 changes must be synchronized across edge/cloud protocol definitions, cloud command mapping, `docs/protocol.md`, and edge active-command routing. Typecheck catches some drift, but not all routing omissions.
- Treat protocol message counts and role counts in docs as manually maintained hints. Code enumerations and registered runtime behavior are authoritative.
- Cloud is event-driven multi-agent orchestration, not the old monolithic planner path. Prefer the current v2 event-driven browse loop; avoid reviving deprecated browse/card-filter paths or deleted legacy files.
- Command pacing belongs primarily in cloud. Cloud computes central `thinkMs`/`dwellMs`; edge may apply jitter, enforce dwell, and handle disconnect fallbacks.

## 3. OpenSpec Workflow

- Default rule: functionality, behavior contracts, cross-repo/cross-module work, protocol, risk, publish, deployment-flow, or user-facing behavior changes go through OpenSpec first.
- Current Windows environment has OpenSpec CLI on PATH; verified `openspec --version` is `1.3.1`.
- Start by running `openspec list`; run `openspec list --specs` when you need baseline specs.
- Do not edit `openspec/specs/` directly for new behavior. Create or update `openspec/changes/<change-name>/` with proposal, tasks, optional design, and spec deltas.
- For complex or extensible features, first ground the current implementation with file/line evidence, compare mature design patterns, propose a pragmatic design, and review it adversarially before implementation.
- Before implementation, read the active change tasks and use OpenSpec CLI context such as `openspec status --change <name>` or `openspec instructions apply --change <name> --json` when useful.
- During implementation, code lands in the relevant sibling repo; progress, commits, and deviations are recorded back in this repo's change `tasks.md`.
- Mark completed tasks with `[x]` and include concise HTML comments with repo, commit SHA, and any deviation/deployment note.
- Finish by running `openspec validate <change-name> --strict`; archive only after tasks and required validation are complete.
- Trivial typo, formatting, or comment-only changes that do not affect behavior contracts may skip creating a change, but still confirm they do not alter product, protocol, risk, publish, or deployment semantics.

## 4. Testing

- Run tests in the sibling repo that owns the code.
- Edge: `cd ../aidcp-edge && npm test`, plus `npm run test:acceptance` and `npm run typecheck` when relevant.
- Cloud: `cd ../aidcp-cloud && npm test`, plus `npm run test:acceptance` and `npm run typecheck` when relevant.
- For protocol, risk, or publish changes, run acceptance first, then full tests, then typecheck.
- Safety suites such as protocol drift, unauthorized publish, risk-state honesty, and end-to-end checks must remain green for related changes.
- Local validation is code-level only for cloud. Production cloud runs on ECS; do not start the production cloud locally as a substitute for deployment checks.

## 5. Deployment

- Cloud runtime runs only on named ECS targets; local cloud is not the production runtime. See `docs/deployment-environments.md`.
- `dev` is the high-frequency development/validation target; `ol` is the stable online target and must deploy only release branches/tags or exact clean SHAs.
- `dev` also hosts unrelated `isales` services. Never touch unrelated services, directories, ports, or systemd units.
- Deployment sequence, when deployment is actually required: sibling-repo tests pass, back up ECS cloud and env, `rsync` excluding secrets/deps/git metadata, restart `aidcp-cloud.service`, then healthcheck service state, port, Feishu connection, and PostgreSQL.
- On deployment failure, roll back. Do not improvise against production.
- Deployment must come from a clean eligible checkout: default branch/main checkout for `dev`, release branch/tag or exact clean SHA for `ol`, never an arbitrary dirty shared worktree or feature worktree.

## 6. Git, Communication, Security

- Preserve user and other-session changes. Do not revert unrelated dirty files.
- Default closeout for code changes is automatic: after implementation, run the relevant validation, commit, push to the default branch, and deploy/publish when the changed service or artifact is production-facing.
- Confirm before force-push, non-fast-forward pushes, or pushing to non-default/protected branches.
- If the working tree has unrelated changes, use explicit pathspecs and/or a clean worktree/archive snapshot for final verification and deployment packaging.
- Default prose language is Chinese. Code, comments, commit messages, PR text, commands, and file names stay in English unless the surrounding file establishes otherwise.
- Explain problems by function and mechanism first, not by dumping internal identifiers. Use exact files/lines when they help implementation or review.
- Never record secrets in docs, commits, or tasks. Record paths, service names, commands, and config-loading methods instead.
- End user-facing work with a plain-language summary of what changed, system impact, and next step.

## 7. Automatic Closeout

- For code-bearing changes, the default finish line is: implementation complete, tests/typecheck appropriate to the touched repo pass, commit, push, and deploy/publish if runtime behavior changes.
- For OpenSpec-backed work, update the relevant `tasks.md` with commit SHA, validation notes, deployment/publish notes, and any deviation from the proposal.
- Deploy/publish only through the documented safe path for the affected artifact and target: cloud ECS deployment, console static release, edge desktop/package release, or docs/spec-only no-op.
- Stop and ask before destructive database changes, secret/key changes, production data deletion, tests failing but user still wants release, unclear publish target, force-push, non-fast-forward push, or any action that may affect unrelated `isales` services.
- Documentation-only or spec-only changes are still committed and pushed by default, but they do not trigger runtime deployment unless they are part of a release procedure.

## 8. Parallel Development

- Parallel work convention: one Codex session = one OpenSpec change = one branch = one worktree, all sharing the same change name.
- Sibling repo worktrees live at `../<repo>.wt/<change-name>`. Control-repo OpenSpec changes are mostly additive and may share the main checkout when safe.
- Prefer manual `git worktree add` or the repo helper scripts over environment-specific worktree switching that only affects the current repo.
- If assigned an existing change, treat it as owned by this session: read proposal/design/tasks, work in the matching worktree/branch, update tasks, validate, and help archive when complete.
- First determine where you are with `git worktree list` and `git rev-parse`. Worktree means branch-local implementation and validation; main checkout means integration/deployment coordination.
- Hotspots are single-writer during parallel work: protocol files and command mapping, role registration/catalog, and risk-state machine. Mark such changes as serial when they must be touched.
- Development may be parallel; integration is serial. Before merging back to default branch, fetch, rebase onto latest default, resolve conflicts, run required tests/typecheck, and fast-forward merge. On non-fast-forward push, rebase and retry; do not force.
- After deployment and validation, archive the change and remove obsolete worktrees/branches. A worktree without a matching active change is an orphan.
- See `docs/parallel-dev-worktrees.md` and helper scripts such as `scripts/new-change`, `scripts/spawn-change`, and `scripts/land-change` for operational details.

## 9. Codex Mapping Notes

- Claude slash commands in `CLAUDE.md` such as `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/impl`, and `/claim` are historical shortcuts. In Codex, perform the same workflow through natural-language intent, OpenSpec CLI, file edits, and repo helper scripts.
- Do not install an OpenSpec skill just to follow this process. The source of truth is this repo plus the OpenSpec CLI.
- If this file and `CLAUDE.md` diverge, prefer this file for Codex behavior and inspect `CLAUDE.md` for background/detail before making a risky change.
