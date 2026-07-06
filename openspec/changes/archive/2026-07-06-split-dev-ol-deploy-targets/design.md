## Context

The current deployment model was built around one ECS host: `121.89.85.150` runs cloud, console, PostgreSQL, and unrelated isales services. The control docs and helper scripts reflect that assumption. A new ECS host `123.56.253.183` is available and should become the online/stable aidcp environment (`ol`), while the original host becomes the development/high-frequency deployment environment (`dev`).

Read-only probes on 2026-07-06 established:

- `dev` runs Alibaba Cloud Linux 3, `aidcp-cloud.service`, `/opt/aidcp/cloud`, `AIDCP_PORT=8787`, panel API on `127.0.0.1:8090`, and nginx for console on `8088/80`.
- `dev` PostgreSQL listens on all addresses and currently allows `aidcp/aidcp` from `0.0.0.0/0`; SSL is off.
- `ol` runs Alibaba Cloud Linux 4 and is otherwise clean: only SSH/system services are listening, and Node.js/npm/nginx/rsync/PostgreSQL are not installed.
- `ol` can reach `dev` ports `5432`, `8787`, and `8088`.

Cloud startup performs many idempotent store initializers (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ADD COLUMN IF NOT EXISTS`, constraint rewrites, index creation). That is convenient for single-environment deployment but makes shared dev/ol databases unsafe as a long-term boundary: whichever code starts first can mutate the shared schema, config rows, schedules, risk counters, and provider settings for both environments.

## Goals / Non-Goals

**Goals:**

- Make `dev` and `ol` explicit deployment targets with distinct SSH keys, ECS hosts, runtime directories, service names, and validation checklists.
- Preserve the existing fast dev loop: validated default-branch commits deploy to `dev` automatically after completed production-facing development work.
- Make `ol` deployment explicit and release-branch-based: it runs only after the user requests `ol`/online deployment, and the deployed ref is a release branch.
- Define the database boundary so `ol` does not silently share mutable runtime state with `dev`.
- Provide a safe first-run path for preparing `ol`, including system dependencies, service files, nginx, env loading, backup/rollback, and health checks.
- Keep secrets outside git, docs, OpenSpec tasks, command arguments, and durable memory.

**Non-Goals:**

- Implement a full CI/CD platform or remote GitHub deploy-key based pull deployment.
- Move unrelated isales services off `dev`.
- Change edge/cloud protocol semantics.
- Introduce blue/green load balancing or automatic traffic switching.
- Perform destructive database changes or production data deletion.

## Decisions

**D1. Name the environments `dev` and `ol`.**

`dev` maps to `121.89.85.150` and `~/codes/isales-4.pem`. `ol` maps to `123.56.253.183` and `/Users/baitianxing/Downloads/ol.pem`. The old nickname `isales-4` should be treated as an SSH-key/host legacy name only; future operator-facing docs should call the host `dev`.

Alternative considered: keep the old “production ECS” wording and add a second IP ad hoc. Rejected because the existing docs already hide too much target selection in prose, and two hosts make implicit target choice dangerous.

**D2. `ol` should use a dedicated PostgreSQL database boundary.**

Preferred state is either PostgreSQL on `ol` or managed RDS for ol. The database may use the same schema and app role names, but it must not share mutable runtime rows with dev. This isolates config, schedules, risk state, account rows, curated content, token usage, provider credentials, and cloud self-healing DDL.

Temporary bridge: `ol` may point to `dev` PostgreSQL only for bootstrap or smoke testing, and only after `dev` PostgreSQL network access is restricted to local + ol. While bridged, only one cloud should process real edge/Feishu traffic unless the operator deliberately accepts duplicate scheduling/risk/config side effects.

Alternative considered: use dev PostgreSQL permanently to avoid data migration. Rejected because it turns release deployment into a code-only illusion; schema and state remain shared with dev.

**D3. Release promotion is branch-based, not worktree-based.**

Development can continue through the existing OpenSpec + worktree model. After a production-facing change lands, validates, commits, and pushes, it deploys to `dev` by default. `ol` deployment must wait for an explicit user request, then create or select a clean release branch such as `release/<date>-<scope>` and deploy by that branch. A tag or exact commit SHA may be the source used to create the release branch, but it is not a substitute for the branch-based deployment record. The release branch and exact SHAs are recorded in the relevant tasks/deployment note.

Alternative considered: deploy arbitrary feature branches to `ol` when needed. Rejected because it breaks the stable online contract and makes rollback/version audit harder.

**D4. Runtime credentials stay target-local.**

Each target has its own `/opt/aidcp/cloud/.env` loaded through systemd `EnvironmentFile`. Docs and tasks may record env key names and file paths but must not record values. Feishu credentials should be target-specific where possible; using the same Feishu app from two cloud processes risks event ingestion ambiguity and duplicate command handling.

Alternative considered: copy dev `.env` wholesale to ol. Rejected because it would copy secrets without review and can bind ol to dev chat/bot/database settings.

**D5. Edge and console target selection must be visible.**

Edge defaults currently point to `ws://121.89.85.150:8787`; dev/ol selection must be made explicit through `AIDCP_CLOUD_URL`, release packaging config, or operator docs. Console uses same-origin `/api` and `/ws` through nginx, so ol needs its own nginx config and static deploy path rather than reusing the dev host.

Alternative considered: leave edge default unchanged and rely on manual env overrides. Rejected for ol release because packaged clients or operator scripts can silently connect to dev.

**D6. First ol deployment is a controlled bootstrap, not a normal rolling deploy.**

Because `ol` is clean, first deployment must install runtime dependencies, create `/opt/aidcp` layout, install and enable nginx, install and enable `aidcp-cloud.service`, create target-local env, rsync committed artifacts, and then health-check cloud, panel, console, Feishu, and PostgreSQL. Later deploys can reuse the normal backup/rsync/restart/check flow.

## Risks / Trade-offs

- [Risk] `ol` temporarily sharing `dev` PostgreSQL lets different cloud versions mutate the same schema/state. → Mitigation: prefer dedicated ol DB; if bridging, restrict network/pg_hba first, mark bridge as temporary, and avoid running two real traffic processors concurrently.
- [Risk] `dev` PostgreSQL currently accepts `aidcp` connections from any IP and SSL is off. → Mitigation: tighten security group and `pg_hba.conf`, rotate the app password if exposure duration is unknown, and avoid treating the current posture as acceptable for online use.
- [Risk] Two cloud processes using the same Feishu app can race or duplicate command handling. → Mitigation: use target-specific Feishu apps or disable Feishu ingestion on the non-active target during bridge/smoke tests.
- [Risk] Alibaba Cloud Linux 4 package names and Node.js install path may differ from dev. → Mitigation: probe packages during implementation, install Node.js 20/npm/nginx/rsync explicitly, and verify `npx tsx src/server.ts` under systemd before marking ol ready.
- [Risk] Release branch and dev mainline drift can make console/cloud DTOs incompatible. → Mitigation: deploy cloud+console together for API shape changes, validate `/api/version`, and record exact SHAs.
- [Risk] Existing docs/scripts hard-code `121.89.85.150`. → Mitigation: update the control repo and sibling repo docs/scripts in this change so future operators cannot miss target selection.

## Migration Plan

1. Update docs/specs/tasks for the two-target deployment contract.
2. Add or update helper scripts with explicit target metadata and preflight checks:
   - target exists and key has `0600` permissions;
   - target hostname/IP matches requested environment;
   - deployment source is clean and eligible for target.
3. Harden `dev` PostgreSQL before any bridge:
   - backup config;
   - restrict `pg_hba.conf` from `0.0.0.0/0` to `127.0.0.1/32` plus an ol-specific source if bridging;
   - verify local dev cloud still works;
   - optionally rotate `aidcp` password and update env atomically.
4. Bootstrap `ol`:
   - install Node.js 20/npm/nginx/rsync;
   - create `/opt/aidcp/cloud`, `/opt/aidcp/console`, and optional `/opt/aidcp/downloads`;
   - install `aidcp-cloud.service`;
   - create `/opt/aidcp/cloud/.env` manually/atomically with target-local values;
   - deploy committed cloud and console artifacts;
   - start/restart services and health-check.
5. Configure edge/operator flows:
   - dev edge uses `ws://121.89.85.150:8787`;
   - ol edge uses `ws://123.56.253.183:8787` or the future ol domain.
6. Cut ol from bridge to dedicated DB as soon as the dedicated DB is ready.
7. Rollback:
   - restore target code backup and env backup;
   - restart only `aidcp-cloud.service`;
   - for ol first deployment failure, stop/disable ol service without touching dev or isales.

## Open Questions

- Should `ol` run PostgreSQL locally first, or should it use Aliyun RDS from the beginning?
- Will `ol` use a distinct Feishu app/chat, or should Feishu ingestion be disabled on ol until a production bot is configured?
- Should ol expose console on raw `:8088`, a domain, or both during initial rollout?
- Should edge desktop releases keep one build with configurable `AIDCP_CLOUD_URL`, or produce dev/ol-specific release channels?
