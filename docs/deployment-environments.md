# AIDCP Deployment Environments

本文是 aidcp 当前部署目标的权威口径。历史文档里“cloud 只部署在 `121.89.85.150`”的表述是单 ECS 阶段遗留；从 `split-dev-ol-deploy-targets` 起，ECS 操作必须先明确目标环境。

## Targets

| Target | Host | SSH key | Purpose |
| --- | --- | --- | --- |
| `dev` | `121.89.85.150` | `~/codes/isales-4.pem` | **不稳定主干测试位**：主干开发（含实验性/FB 分支合并回的内容）高频部署、真机验证。 |
| `ol` | `123.56.253.183` | `/Users/baitianxing/Downloads/ol.pem` | **稳定生产环境**：只从 `release/<yyyymmdd>-<scope>` 分支部署；**edge 安装包默认云端目标** + **`aidcp.tommax.cc` 域名宿主**。 |

## 角色与发布模型（主干开发 / 分支上线，2026-07-11 定）

- **主干开发**：`master`（各 sub-repo）是开发主干，落地即部署到 `dev` 做测试；`dev` 允许承载不稳定内容（实验特性、刚合并回主干的隔离分支工作）。
- **分支上线**：`ol` 是稳定生产环境，其 ECS cloud/console 运行时**只从 release 分支部署**（edge 安装包是分发工件、走构建期选择，是此强制的**例外**，见下 edge 条）。稳定版 = 从选定的干净已提交 master commit（分支尖 / tag / SHA）切 `release/<yyyymmdd>-<scope>`；该 release 分支是 `ol` 的部署 ref of record，**在役期间保留不删**。**历史 append-only、只进不退**：向前推按 append-only——热修是 release tip 严格后代时可 fast-forward（如 console 0.3.18 下载页 bump `6bce66d→0c8db0c`），否则（trunk 已合入 `ol` 须排除的内容、热修非严格后代）以追加提交 / cherry-pick 落到 release 分支、**绝不把被排除内容拖进 `ol`**；**任何情形都绝不 force-push / rebase / reset 重写已发布历史**。被新 release 取代且不再是部署 ref 后方可归档 / 删除。
- **隔离分支合并纪律**：把某隔离 feature 分支合并回主干时，**若要同时保 `ol` 干净**，必须先从「合并前的 master」切好 `ol` release 分支并部署，再把 feature 合并进 master（推进 dev）。合并只推进 master，钉死的 release 分支不受影响。
- **edge 安装包默认云环境 = 构建期注入**：master 保持 dev-default（缺省或 `cloud_default_env=dev`，零回归）；OL 安装包用 `gh workflow run build-desktop.yml -f cloud_default_env=ol` 构建（electron-builder `extraMetadata.aidcpCloudDefaultEnv=ol` 烘进包内 `package.json`，shell 启动读取后注入 `AIDCP_CLOUD_URL=ol`、芯片显示=实际连接）。**同一份 master 源码构建 dev 或 ol 安装包，靠构建 flag 区分，不靠长命 release 分支** —— 不再需要为默认环境保留分支源码分叉。OL 包分发到域名所指主机的 `/opt/aidcp/downloads/`。
- **飞书**：dev 与 ol **各自拥有独立飞书 bot**（各自 `.env` 的 `FEISHU_APP_ID/SECRET` + `AIDCP_FEISHU_WS_ENABLED=true`），互不争用、无双消费问题；不再需要「共享单 app 时只开一端」的交接（该约束仅在退回共享单 app 时才适用，见下）。
- **域名 `aidcp.tommax.cc`（tommax.cc 已 ICP 备案通过）**：已切至 `ol`（2026-07-11 完成）。经 Cloudflare 橙云代理 fronts `aidcp.tommax.cc`→OL；OL nginx `listen 80 + server_name aidcp.tommax.cc`→反代 `/api`+`/ws` → ol 本地 `127.0.0.1:8090`、`/downloads/` alias；Cloudflare 提供边缘 TLS、源站 HTTP-only。OL 安装包已上架（`AIDCP-0.3.18-arm64.dmg`/`AIDCP-0.3.18.dmg` + Windows 仍 `AIDCP Setup 0.3.5.exe`）。**残留待办**：从 dev nginx 撤已 inert 的 `server_name aidcp.tommax.cc` 块（Cloudflare 已只回 OL）。

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

**Status 2026-07-11 (ol turned stable-production while still sharing dev PG — split deferred by user decision).** `ol` production and `dev` unstable-trunk both read/write `121.89.85.150/aidcp`, isolated only by `account_id`. Until `ol` gets its own PostgreSQL boundary, two guardrails are MANDATORY:

1. **Freeze destructive/incompatible dev schema migrations.** `dev` runs the unstable trunk (incl. freshly merged feature work) against the *same* schema `ol` production reads. Additive DDL (`ADD COLUMN IF NOT EXISTS`) is tolerable (ol just ignores the new column); DROP/RENAME/type-narrowing is NOT — it would corrupt ol production reads. Before landing any change that introduces such a migration, split the ol DB first.
2. **Tighten dev PostgreSQL `pg_hba`** away from `0.0.0.0/0` to local-dev + the ol source only (still pending as of 2026-07-11).

Verify at every dev deploy that the batch introduces no destructive migration (`migrations/*.sql` additions are the tell). The 2026-07-11 `feature/fb-full-integration → master` merge added no migration.

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
AIDCP_CLIENT_AUTH_PORT=
AIDCP_CLIENT_JWT_SECRET=
AIDCP_CLIENT_JWT_TTL_SECONDS=
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

**对外客户鉴权（change edge-client-customer-auth）**：`AIDCP_CLIENT_AUTH_PORT` 未设则整个客户鉴权服务禁用（默认，零回归）。设了才启用；`AIDCP_CLIENT_JWT_SECRET` **必须非空且 ≠ `AIDCP_PANEL_JWT_SECRET`**（否则启动断言拒启该服务——密钥即边界）；`AIDCP_CLIENT_JWT_TTL_SECONDS` 缺省 900。服务绑 `127.0.0.1:<port>`（dev 现用 8091），经 Nginx 反代对外。**dev 已启用并接线**：`aidcp-console.conf`（8088 + 80/`aidcp.tommax.cc`）加了 `location /capi/ → 127.0.0.1:8091/`（带 `X-Forwarded-For` 供限流取真实客户 IP），客户端可达地址 = `http://121.89.85.150:8088/capi` 或 `http://aidcp.tommax.cc/capi`（经公网 nginx 完整登录往返已验证）。**edge 侧配** `AIDCP_CLIENT_AUTH_URL=<该 /capi 地址>` 即连；密钥在 ECS `.env`、不入库。ol 上线应走独立 TLS 子域 + 独立 ol 密钥（不复用 dev）。

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
5. If the batch changes `package.json`/`package-lock.json`, run a FULL `npm ci` on the ECS (`--registry=https://registry.npmmirror.com` as fallback). Never use `--omit=dev`: the service runs source via `npx tsx`, and `tsx`/`typescript` live in devDependencies — omitting them bricks the restart. Runtime asset dirs (e.g. `assets/fonts/`) travel with rsync automatically.
6. Restart only `aidcp-cloud.service`.
7. Health-check service state, `8787`, panel `8090`, PostgreSQL, Feishu if enabled, and console if touched. If the batch touches the text-card renderer (`src/render/`, `assets/fonts/`, satori/resvg deps), also run the render smoke: instantiate the renderer on the ECS and assert a golden card renders at 1728x2304 with non-zero bytes (verifies napi prebuilds against the host glibc).

### Ol

1. Proceed only after the user explicitly requests `ol`/online deployment.
2. Create or select a release branch named `release/<yyyymmdd>-<scope>` from the chosen clean committed trunk commit (branch tip, tag, or SHA). Retain it as the ol ref of record while it backs a live ol runtime; advance it only append-only (fast-forward when the fix is a strict descendant, otherwise a cherry-picked commit appended to the branch) and never force-push, rebase, or reset it.
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
