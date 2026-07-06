## Why

aidcp currently treats the original ECS `121.89.85.150` as the only production cloud target, but a second ECS `123.56.253.183` is being introduced for online/stable service while the original machine becomes the high-frequency development target. Without an explicit dev/ol deployment contract, operators can accidentally deploy the wrong commit, point edges at the wrong cloud, or let dev and ol cloud processes share mutable runtime state.

The immediate risk is highest around PostgreSQL and runtime credentials: the current dev database is reachable from ol, but sharing one mutable database between a fast-moving dev cloud and a stable ol cloud would couple schema self-healing, schedules, risk state, model/provider config, Feishu ingestion, and panel writes across environments.

## What Changes

- Introduce named deployment targets:
  - `dev`: existing ECS `121.89.85.150`, key `~/codes/isales-4.pem`, used for mainline/high-frequency development deployment and real-machine validation.
  - `ol`: new ECS `123.56.253.183`, key `/Users/baitianxing/Downloads/ol.pem`, used only for stable online deployment from release branches/tags.
- Document and enforce that deployment target selection is explicit for cloud, console, and edge connection configuration.
- Define a safe first ol rollout path that prepares runtime dependencies, systemd, nginx, runtime env, and health checks without writing secrets into the repo.
- Define the database boundary:
  - Preferred: ol uses its own production PostgreSQL database or RDS instance.
  - Temporary bridge: ol may connect to dev PostgreSQL only with restricted network and `pg_hba.conf` allowlist, and only until a dedicated ol database is ready.
- Define release flow:
  - Development changes land to default branches and deploy to dev after validation.
  - Online deployment uses a release branch/tag or exact committed SHA, never an arbitrary dirty worktree.
  - Hotfixes start from the release line and are merged/cherry-picked back to mainline.
- Update docs and helper scripts so existing “cloud only deploys to `121.89.85.150`” wording no longer hides the new two-target reality.
- Keep secrets out of git: only env key names, paths, service names, and validation commands may be recorded.

## Capabilities

### New Capabilities

- `deployment-environments`: explicit dev/ol runtime target selection, promotion, database isolation, runtime credential handling, and deployment validation requirements.

### Modified Capabilities

- None.

## Impact

- Control repo docs and OpenSpec specs/tasks.
- Deployment helper scripts in `aidcp/scripts/` if implementation chooses to encode target metadata or preflight checks there.
- `aidcp-cloud` deployment documentation and possibly new target-specific deployment notes.
- `aidcp-console` deployment notes/nginx copy procedure for ol.
- `aidcp-edge` operator/release docs for choosing `AIDCP_CLOUD_URL` when connecting to dev vs ol.
- ECS runtime state:
  - dev: PostgreSQL exposure should be restricted before any ol database bridge is used.
  - ol: Node.js/npm, rsync, nginx, `/opt/aidcp/cloud`, `/opt/aidcp/console`, `aidcp-cloud.service`, env file, and health checks need first-time setup.
