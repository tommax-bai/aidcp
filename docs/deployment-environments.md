# AIDCP Deployment Environments

本文是 aidcp 当前部署目标的权威口径。历史文档里“cloud 只部署在 `121.89.85.150`”的表述是单 ECS 阶段遗留；从 `split-dev-ol-deploy-targets` 起，ECS 操作必须先明确目标环境。

## Targets

| Target | Host | SSH key | Purpose |
| --- | --- | --- | --- |
| `dev` | `121.89.85.150` | `~/codes/isales-4.pem` | 默认部署目标；主干开发、高频部署、真机验证 |
| `ol` | `123.56.253.183` | `/Users/baitianxing/Downloads/ol.pem` | 稳定上线环境；仅在用户明确要求时从 release 分支部署 |

运行时目录约定：

| Path | Meaning |
| --- | --- |
| `/opt/aidcp/cloud` | cloud runtime |
| `/opt/aidcp/cloud/.env` | target-local runtime env, loaded by `aidcp-cloud.service` |
| `/opt/aidcp/console` | console static files served by nginx |
| `/opt/aidcp/downloads` | optional edge installer download fallback |

## Invariants

- Any SSH or `rsync` to ECS MUST name a target: `dev` or `ol`.
- If a completed production-facing development task needs deployment and the user did not name a target, the target defaults to `dev`.
- `ol` MUST NOT be deployed by default. It is allowed only after an explicit user request for `ol`/online deployment.
- Before SSH or `rsync`, run `scripts/deploy-target <target> --check` or manually verify the same facts: host IP, key path, and key permissions.
- Local cloud is not a production substitute. Run cloud tests locally, but runtime cloud lives on ECS.
- Deploy only from a clean main checkout/default branch for `dev`, and from a clean release branch checkout for `ol`. A tag or clean SHA may be used to create the release branch, but the deployed ref is the branch.
- Never deploy from an arbitrary dirty worktree.
- Never record secrets in git, OpenSpec tasks, docs, shell history snippets, or memory. Record only env key names, paths, services, and validation commands.
- Do not touch unrelated `isales` services, directories, ports, or databases on `dev`.

## Database Boundary

`ol` SHOULD use its own production PostgreSQL boundary, either local PostgreSQL on `ol` or managed RDS. That boundary may use the same app schema and role names, but it must not share mutable runtime rows with `dev`.

A temporary `ol -> dev PostgreSQL` bridge is allowed only for bootstrap or smoke testing. Before using that bridge:

1. Back up dev PostgreSQL config.
2. Restrict dev PostgreSQL access away from `0.0.0.0/0`.
3. Allow only local dev access plus the ol source.
4. Record the bridge as temporary in the OpenSpec task notes.
5. Avoid letting both dev and ol cloud processes process real edge/Feishu traffic against the shared database.

As of the 2026-07-06 probe, dev PostgreSQL was reachable from ol, listened on `*`, allowed `aidcp/aidcp` from `0.0.0.0/0`, and had SSL off. That posture is acceptable only as a finding to fix, not as a final online architecture.

## Target Selection

### Cloud

Both targets use `aidcp-cloud.service` with:

```ini
WorkingDirectory=/opt/aidcp/cloud
EnvironmentFile=/opt/aidcp/cloud/.env
ExecStart=/usr/bin/npx tsx src/server.ts
```

Each target owns its own `/opt/aidcp/cloud/.env`. Do not copy dev `.env` to ol blindly; review database, Feishu, model/provider, OSS, panel, and scheduling settings as target-local runtime config.

Minimum env inventory for ol bootstrap, listing key names only:

```dotenv
AIDCP_PORT=
AIDCP_PANEL_PORT=
AIDCP_PANEL_JWT_SECRET=
AIDCP_PANEL_USERS=
AIDCP_PANEL_FORBIDDEN_PORTS=
DASHSCOPE_API_KEY=
PGHOST=
PGPORT=
PGUSER=
PGPASSWORD=
PGDATABASE=
AIDCP_CRED_KEY=
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_CHAT_ID=
AIDCP_FEISHU_WS_ENABLED=
```

Optional feature flags such as `AIDCP_CONTENT_SCHEDULE_AUTO`, `AIDCP_COMMENT_APPROVAL`, `AIDCP_COMMENT_LIKE`, image-provider settings, and timeout overrides should be reviewed per target. If dev and ol temporarily share the same Feishu app, keep `AIDCP_FEISHU_WS_ENABLED=false` on the non-active target so only one cloud process receives real Feishu command traffic.

### Console

Console is same-origin: nginx serves `/opt/aidcp/console` and proxies `/api` and `/ws` to that target's local panel API, normally `127.0.0.1:8090`.

`ol` console must proxy to the ol panel API. It must not proxy operators to dev by accident.

### Edge

Development edge instances use:

```bash
AIDCP_CLOUD_URL=ws://121.89.85.150:8787
```

Online edge instances use:

```bash
AIDCP_CLOUD_URL=ws://123.56.253.183:8787
```

or a future ol domain. Packaged edge releases intended for ol must not silently use the dev default endpoint.

## Deployment Flow

### Dev

1. Land code to the relevant default branch after the required tests/typecheck.
2. If the changed service or artifact is production-facing, deploy `dev` automatically after commit/push unless the user explicitly pauses deployment or a safety gate fails.
3. From the clean main checkout, back up cloud/env on `dev`.
4. `rsync` excluding `.env`, `node_modules`, and `.git`.
5. Restart only `aidcp-cloud.service`.
6. Health-check service state, `8787`, panel `8090`, PostgreSQL, Feishu if enabled, and console if touched.

### Ol

1. Proceed only after the user explicitly requests `ol`/online deployment.
2. Create or select a release branch such as `release/<yyyymmdd>-<scope>` from the chosen clean default-branch commit, tag, or SHA.
3. Verify all affected artifacts are built from matching release branch sources.
4. Back up the existing ol runtime if present.
5. `rsync` committed cloud files and built console static files to ol.
6. Restart only ol `aidcp-cloud.service` and reload ol nginx when needed.
7. Health-check cloud, panel, console, database, and Feishu if enabled.
8. Record the release branch, deployed SHAs, database mode, and validation notes in the OpenSpec task.

## Preflight Helper

Use:

```bash
scripts/deploy-target dev --check
scripts/deploy-target ol --check
```

The helper is intentionally read-only. It prints target metadata and fails if the key is missing or has group/other permissions.
