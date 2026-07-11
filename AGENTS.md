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
- Default deployment target is `dev`: when a production-facing code/artifact change is complete and no target is specified, resolve the target to `dev`, state it, run the target check, and deploy `dev` after validation.
- `ol` is opt-in only: deploy `ol` only when the user explicitly requests `ol`/online deployment.

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
- `dev` is the default high-frequency development/validation target. After a production-facing change is implemented, validated, committed, and pushed, deploy `dev` automatically through the safe deployment sequence unless the user explicitly pauses deployment or a safety gate fails.
- `ol` is the stable online target and is never the default. Deploy `ol` only after an explicit user request, and create or use a release branch such as `release/<date>-<scope>` for the deployment. Tags or clean SHAs may seed that release branch, but the deployed ref must be the release branch.
- `dev` also hosts unrelated `isales` services. Never touch unrelated services, directories, ports, or systemd units.
- Deployment sequence, when deployment is actually required: sibling-repo tests pass, back up ECS cloud and env, `rsync` excluding secrets/deps/git metadata, restart `aidcp-cloud.service`, then healthcheck service state, port, Feishu connection, and PostgreSQL.
- On deployment failure, roll back. Do not improvise against production.
- Deployment must come from a clean eligible checkout: default branch/main checkout for `dev`, release branch checkout for `ol`, never an arbitrary dirty shared worktree or feature worktree.

### Edge desktop packaging red-lines (Electron / asar)

> This bug class is **invisible to `electron .`, `npm run typecheck`, and unit tests — it only surfaces in the packaged build**, so it tends to reach operator machines before anyone notices. Read before touching any process launch under `aidcp-edge/src/electron/**`; authoritative detail lives in `aidcp-edge/CLAUDE.md`.

- **A `spawn` `cwd` (or entry path) must never resolve inside `app.asar`.** In a packaged build (electron-builder defaults to `asar:true`), `app.getAppPath()` returns `.../Contents/Resources/app.asar`, which is a FILE, not a directory. Passing it as a `child_process.spawn` cwd makes macOS throw `spawn ENOTDIR`, so the edge core child never starts and the fingerprint browser never launches. Local dev is unaffected because `appRoot` is a real directory — this is a packaged-only regression.
- **Guard:** the core spawn uses `appRoot.endsWith('.asar') ? path.dirname(appRoot) : appRoot` (`dirname` = `Contents/Resources`, the historically-working value). Any new child-process launch must apply the same guard; sites that pass no `cwd` (inheriting the main-process cwd, never asar) are safe.
- **Packaging fixes must be forward-ported to `master`.** This fix first landed on branch `codex/edge-macos-developer-id-signing` (`20d3784`) but was never merged to master, so `0.3.5` shipped the regression again (re-fixed on edge master `3f578b9`, version bumped to `0.3.6`). A packaging fix that lives only on a feature branch recurs the moment master ships.
- **Before releasing, run the packaged artifact once on the build machine** (start the compiled core, confirm it reaches cloud connect / the AdsPower call) instead of discovering cwd/asar regressions on the operator machine. Desktop release flow: `aidcp-edge/docs/release-desktop.md`.

## 6. Git, Communication, Security

- Preserve user and other-session changes. Do not revert unrelated dirty files.
- Default closeout for code changes is automatic: after implementation, run the relevant validation, commit, push to the default branch, and deploy/publish to `dev` when the changed service or artifact is production-facing.
- Do not build the edge desktop installer by default (standing user authorization, 2026-07-08). `electron:build` / `electron-builder` (incl. `electron:build:mac` / `:win`) invoke remote GitHub services and Apple signing/notarization and are slow; build an installer only on an explicit user request to package/release. Default closeout for edge changes stops at commit/push (plus `dev` deploy and typecheck/tests where applicable) and never produces an installer on its own.
- Confirm before force-push, non-fast-forward pushes, or pushing to non-default/protected branches.
- If the working tree has unrelated changes, use explicit pathspecs and/or a clean worktree/archive snapshot for final verification and deployment packaging.
- Default prose language is Chinese. Code, comments, commit messages, PR text, commands, and file names stay in English unless the surrounding file establishes otherwise.
- Explain problems by function and mechanism first, not by dumping internal identifiers. Use exact files/lines when they help implementation or review.
- Never record secrets in docs, commits, or tasks. Record paths, service names, commands, and config-loading methods instead.
- End user-facing work with a plain-language summary of what changed, system impact, and next step.

## 7. Automatic Closeout

- For code-bearing changes, the default finish line is: implementation complete, tests/typecheck appropriate to the touched repo pass, commit, push, and deploy/publish to `dev` if runtime behavior changes.
- For OpenSpec-backed work, update the relevant `tasks.md` with commit SHA, validation notes, deployment/publish notes, and any deviation from the proposal.
- Deploy/publish only through the documented safe path for the affected artifact and target: cloud ECS deployment, console static release, edge desktop/package release, or docs/spec-only no-op. If no target is named for production-facing development work, use `dev`; require an explicit user request before any `ol` deployment.
- Stop and ask before destructive database changes, secret/key changes, production data deletion, tests failing but user still wants release, unclear publish target, force-push, non-fast-forward push, or any action that may affect unrelated `isales` services.
- Documentation-only or spec-only changes are still committed and pushed by default, but they do not trigger runtime deployment unless they are part of a release procedure.

## 8. Parallel Development

- Parallel work convention: one Codex session = one OpenSpec change = one branch = one worktree, all sharing the same change name.
- Sibling repo worktrees live at `../<repo>.wt/<change-name>`. Control-repo OpenSpec changes are mostly additive and may share the main checkout when safe — but "share the main checkout" always means "write additive change dirs on its default branch (`main`)", never "switch its branch".
- **Canonical checkout stays on its default branch (hard rule, added 2026-07-11).** The canonical control-repo checkout `/Users/baitianxing/codes/aidcp` must always be on `main`. Never run `git checkout <feature>` or `git checkout -b` in it; use a worktree for branch isolation. `main` must live only in the canonical checkout and must never be occupied by a `.wt/<change>` worktree. Codex change branches must be created via `git worktree add`, never by switching the canonical checkout. Session-start guard: run `git -C /Users/baitianxing/codes/aidcp branch --show-current`; if it is not `main`, stop and restore (when safe) or spin a worktree before working. Incident (2026-07-11): the canonical checkout was left on `codex/remote-captcha-assist` (already archived on origin/main) while `main` was squatting in `aidcp.wt/publish-queue-stage-overview`, silently 163 commits behind origin/main with nobody cleaning up — root cause was checking out a feature branch in the canonical dir plus checking `main` out into a worktree. To restore a mislocated canonical checkout: wait for any concurrent session to finish, free the squatted `main` (remove the orphan worktree), then `git checkout main` + `git merge --ff-only origin/main`; never `-f` over another session's WIP.
- Prefer manual `git worktree add` or the repo helper scripts over environment-specific worktree switching that only affects the current repo.
- If assigned an existing change, treat it as owned by this session: read proposal/design/tasks, work in the matching worktree/branch, update tasks, validate, and help archive when complete.
- First determine where you are with `git worktree list` and `git rev-parse`. Worktree means branch-local implementation and validation; main checkout means integration/deployment coordination.
- Hotspots are single-writer during parallel work: protocol files and command mapping, role registration/catalog, and risk-state machine. Mark such changes as serial when they must be touched.
- Development may be parallel; integration is serial. Before merging back to default branch, fetch, rebase onto latest default, resolve conflicts, run required tests/typecheck, and fast-forward merge. On non-fast-forward push, rebase and retry; do not force. Deploy `dev` only from the clean main/default checkout, and deploy `ol` only from the selected release branch.
- After deployment and validation, archive the change and remove obsolete worktrees/branches. A worktree without a matching active change is an orphan.
- See `docs/parallel-dev-worktrees.md` and helper scripts such as `scripts/new-change`, `scripts/spawn-change`, and `scripts/land-change` for operational details.

## 9. Codex Mapping Notes

- Claude slash commands in `CLAUDE.md` such as `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/impl`, and `/claim` are historical shortcuts. In Codex, perform the same workflow through natural-language intent, OpenSpec CLI, file edits, and repo helper scripts.
- Do not install an OpenSpec skill just to follow this process. The source of truth is this repo plus the OpenSpec CLI.
- If this file and `CLAUDE.md` diverge, prefer this file for Codex behavior and inspect `CLAUDE.md` for background/detail before making a risky change.
