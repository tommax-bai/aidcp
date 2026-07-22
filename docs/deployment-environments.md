# AIDCP Deployment Environments

本文是 aidcp 当前部署目标的权威口径。历史文档里“cloud 只部署在 `121.89.85.150`”的表述是单 ECS 阶段遗留；从 `split-dev-ol-deploy-targets` 起，ECS 操作必须先明确目标环境。

## Targets

| Target | Host | SSH key | Purpose |
| --- | --- | --- | --- |
| `dev` | `121.89.85.150` | `~/codes/dev-0722.pem` | **不稳定主干测试位**：主干开发（含实验性/FB 分支合并回的内容）高频部署、真机验证。 |
| `ol` | `123.56.253.183` | `~/codes/ol-0722.pem` | **稳定生产环境**：只从 `release/<yyyymmdd>-<scope>` 分支部署；**edge 安装包默认云端目标** + **`aidcp.tommax.cc` 域名宿主**。 |

2026-07-22 起，本机 ECS SSH 私钥路径使用上表记录；仓库只保存路径，私钥文件本身不得入库。

## 角色与发布模型（主干开发 / 分支上线，2026-07-11 定）

- **主干开发**：`master`（各 sub-repo）是开发主干，落地即部署到 `dev` 做测试；`dev` 允许承载不稳定内容（实验特性、刚合并回主干的隔离分支工作）。
- **分支上线**：`ol` 是稳定生产环境，其 ECS cloud/console 运行时**只从 release 分支部署**（edge 安装包是分发工件、走构建期选择，是此强制的**例外**，见下 edge 条）。稳定版 = 从选定的干净已提交 master commit（分支尖 / tag / SHA）切 `release/<yyyymmdd>-<scope>`；该 release 分支是 `ol` 的部署 ref of record，**在役期间保留不删**。**历史 append-only、只进不退**：向前推按 append-only——热修是 release tip 严格后代时可 fast-forward（如 console 0.3.18 下载页 bump `6bce66d→0c8db0c`），否则（trunk 已合入 `ol` 须排除的内容、热修非严格后代）以追加提交 / cherry-pick 落到 release 分支、**绝不把被排除内容拖进 `ol`**；**任何情形都绝不 force-push / rebase / reset 重写已发布历史**。被新 release 取代且不再是部署 ref 后方可归档 / 删除。
- **发布分支上的任何改动必须回流主干（铁律，2026-07-14）**：release 分支是「已上线」的，主干是「将上线」的。热修只落在 release 分支上，等于给下一次从主干切版埋一颗同样的雷，而且没有机械手段会提醒（控制仓对这些 sha 全文 grep 零命中）。**已付过两次代价**：`210f386`（人设弹窗竞态）只活在 `release/20260712-ol-recut`，用户跑的 master 客户端从来没拿到它 →「修了几次还复发」；打包 spawn cwd/asar 的 fix 只活在签名分支 → master 发版把同一个 regression 原样发出。
  - 验收口径＝**主干上有等价行为 + 有测试覆盖**，不是 patch-id 相同：cherry-pick / 冲突解决 / 在主干新代码上重新实现都算完成（`git cherry` 的 `+` 只是线索，不是判决）。
  - 回流不成（受阻 / 已被取代 / 需重写）**必须当场登记**（change 的 tasks.md + 真机 backlog，写清 sha 与原因），绝不静默留在 release 分支上。
  - **唯一例外＝发布态工件指针**（安装包版本号、下载页指向哪个包）：那是「哪台机器上放了哪个包」的部署状态，照搬会让主干指向另一台机器上并不存在的产物。必须显式对账，但不得机械照搬。
  - **切下一个 release 分支前**先跑 `git cherry -v origin/master origin/release/<上一个>`，凡 `+` 逐条给出「已回流 / 已被取代 / 工件指针」的结论。
- **隔离分支合并纪律**：把某隔离 feature 分支合并回主干时，**若要同时保 `ol` 干净**，必须先从「合并前的 master」切好 `ol` release 分支并部署，再把 feature 合并进 master（推进 dev）。合并只推进 master，钉死的 release 分支不受影响。
- **edge 安装包默认云环境 = 构建期注入**：master 保持 dev-default（缺省或 `cloud_default_env=dev`，零回归）；OL 安装包用 `gh workflow run build-desktop.yml -f cloud_default_env=ol` 构建（electron-builder `extraMetadata.aidcpCloudDefaultEnv=ol` 烘进包内 `package.json`，shell 启动读取后注入 `AIDCP_CLOUD_URL=ol`、芯片显示=实际连接）。**同一份 master 源码构建 dev 或 ol 安装包，靠构建 flag 区分，不靠长命 release 分支** —— 不再需要为默认环境保留分支源码分叉。OL 包分发到域名所指主机的 `/opt/aidcp/downloads/`。
- **飞书**：dev 与 ol **各自拥有独立飞书 bot**（各自 `.env` 的 `FEISHU_APP_ID/SECRET` + `AIDCP_FEISHU_WS_ENABLED=true`），互不争用、无双消费问题；不再需要「共享单 app 时只开一端」的交接（该约束仅在退回共享单 app 时才适用，见下）。期望绑定为 `dev -> Dev.A`、`ol -> Red.A`；若 `bot/v3/info` 查到相反名称，说明目标 `.env` 凭据串环境反了，必须先修正运行时凭据再排查消息发送。
- **域名 `aidcp.tommax.cc`（tommax.cc 已 ICP 备案通过）**：已切至 `ol`（2026-07-11 完成）。经 Cloudflare 橙云代理 fronts `aidcp.tommax.cc`→OL；OL nginx `listen 80 + server_name aidcp.tommax.cc`→反代 `/api`+`/ws` → ol 本地 `127.0.0.1:8090`、`/downloads/` alias；Cloudflare 提供边缘 TLS、源站 HTTP-only。OL 安装包已上架（`AIDCP-0.3.18-arm64.dmg`/`AIDCP-0.3.18.dmg` + Windows 仍 `AIDCP Setup 0.3.5.exe`）。**残留待办**：从 dev nginx 撤已 inert 的 `server_name aidcp.tommax.cc` 块（Cloudflare 已只回 OL）——该块会让本机带 `Host:` 头直连 dev 时返回 200，制造「域名还指向 dev」的假象，误导排查。
- **以域名为值的 `.env` 项必须按 target 分别配（2026-07-16 事故定）**：域名归 OL 之后，任何在 **dev** 上把 `aidcp.tommax.cc` 当自身基址的配置都会退化成**跨环境指针**——链接由 dev 签发、却把人送到 OL。已知实例：dev 的 `AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL` 原配 `http://aidcp.tommax.cc`（2026-07-07 配置时域名尚在 dev，属当时正确），2026-07-11 割接后无人复核，运营点开验证码协助链接即报 `captcha_assist_unavailable`（详见 §「验证码协助基址」）。**口径：dev 用自身可达基址 `http://121.89.85.150:8088`，ol 用 `http://aidcp.tommax.cc`。** 割接 / 迁移域名时，收尾清单必须包含「扫一遍两台 `.env` 里以域名为值的项」，不能只扫 nginx / 安装包 / 下载页。

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
- Before SSH or `rsync`, run `scripts/deploy-target <target> --check` or manually verify the same facts: host IP, key path, and that the key is a readable regular file. For both `dev` and `ol`, do not reject the key based on Git Bash's synthesized POSIX mode on Windows.
- Local cloud is not a production substitute. Run cloud tests locally, but runtime cloud lives on ECS.
- Deploy only from a clean main checkout/default branch for `dev`, and from a clean release branch checkout for `ol`. A tag or clean SHA may be used to create the release branch, but the deployed ref is the branch.
- Never deploy from an arbitrary dirty worktree.
- The automation writer (the cloud process that owns risk state) MUST run **exactly one instance per target**. Deployment MUST be stop-then-start. **Rolling and blue-green deployment MUST NOT be used for it** — the overlap window makes the single-writer invariant false while both builds are live. (change `risk-state-cross-process-integrity`)
- A cloud process that cannot acquire the automation writer lock MUST be treated as a correct refusal, not as an outage. Do not "fix" it by force-killing the current holder before confirming that holder is genuinely dead — that is exactly how a double-write window is created.
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

1. **Freeze destructive/incompatible dev schema migrations.** `dev` runs the unstable trunk (incl. freshly merged feature work) against the *same* schema `ol` production reads. Additive DDL (`ADD COLUMN IF NOT EXISTS`) is tolerable (ol just ignores the new column); DROP/RENAME/type-narrowing is NOT — it would corrupt ol production reads. Before landing any change that introduces such a migration, split the ol DB first. 该冻结在迁移期的延伸写在 `aidcp-cloud/migrations/README.md` §5（change `cloud-schema-migration-executor`）：每个迁移文件 MUST 声明 `-- aidcp:kind=expand|contract`；共库期执行器**默认拒绝**应用 `contract`，只在显式 `npm run migrate up --allow-contract` 时应用并把授权者写进账本。重命名 MUST NOT 用 `ALTER … RENAME`，MUST 改写为新增列 + 双写 + 影子读 + 切读 + 一次独立的 contract 删旧列（六步模板见 `aidcp-cloud/docs/table-ownership-migration.md`）。这不是新增护栏，是同一条冻结的机械化。
2. **Tighten dev PostgreSQL `pg_hba`** away from `0.0.0.0/0` to local-dev + the ol source only (still pending as of 2026-07-11).

Verify at every dev deploy that the batch introduces no destructive migration (`migrations/*.sql` additions are the tell). The 2026-07-11 `feature/fb-full-integration → master` merge added no migration.

**共库的一个已知副作用（change config-mirror-cross-process-invalidation 修复中）**：`quota_config`、`pacing_floor_config`、`session_config_global`、`resume_config_global`、`model_config`、`role_config`、`category_config`、`hot_lead_config` 这 8 张是**全局表、无 `execution_target` 列**。云端此前对配置只在启动与本进程写入时刷新内存镜像（全仓无 watch / 无定时刷配置 / 无 LISTEN/NOTIFY），因此在一个部署目标的后台改动这些配置，**另一个部署目标的进程到重启才可见**，中间没有任何日志、没有任何告警、后台还回显写入成功。本变更引入共享版本表 `config_mirror_version` + 消费侧有界轮询（默认 5s、硬上界 30s，env `AIDCP_CONFIG_MIRROR_POLL_MS`；整体开关 `AIDCP_CONFIG_MIRROR_REFRESH`，默认开、置 `false` 即秒级回滚到旧行为），把可见性延迟收敛到「轮询周期 + 一次查询耗时」。闸门类配置（人设、运营暂停态、环境出口闸、慢启动锚点、内容排期）副本超过 60s 陈旧上限即**停手**：不下发新的平台动作、已在跑的会话自然收敛，并落 `config_mirror_stale` 告警。（本段同时兑现定稿 §11.4「陈旧上限 T MUST 是部署文档中写死的一个具体值」= 60s）

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
OSS_REGION=
OSS_BUCKET=
OSS_INTERNAL=
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_CHAT_ID=
AIDCP_FEISHU_WS_ENABLED=
```

**对外客户鉴权（change edge-client-customer-auth）**：`AIDCP_CLIENT_AUTH_PORT` 未设则整个客户鉴权服务禁用（默认，零回归）。设了才启用；`AIDCP_CLIENT_JWT_SECRET` **必须非空且 ≠ `AIDCP_PANEL_JWT_SECRET`**（否则启动断言拒启该服务——密钥即边界）；`AIDCP_CLIENT_JWT_TTL_SECONDS` 缺省 900。服务绑 `127.0.0.1:<port>`（dev 现用 8091），经 Nginx 反代对外。**dev 已启用并接线**：`aidcp-console.conf`（8088 + 80/`aidcp.tommax.cc`）加了 `location /capi/ → 127.0.0.1:8091/`（带 `X-Forwarded-For` 供限流取真实客户 IP），客户端可达地址 = `http://121.89.85.150:8088/capi`（经公网 nginx 完整登录往返已验证）。**⚠️ 2026-07-16 更正**：本条原写「或 `http://aidcp.tommax.cc/capi`」，那是 2026-07-11 域名割接**之前**的事实——今天该域名只回 OL，拿它当 **dev** 的客户鉴权地址会连到 ol 的 `/capi`（若 ol 未启用则整个登录门不存在）。**dev 一律用 IP:8088**；`http://aidcp.tommax.cc/capi` 只对 **ol** 有效（OL 安装包烘焙的正是它，属正确）。**edge 侧配** `AIDCP_CLIENT_AUTH_URL=<对应 target 的 /capi 地址>` 即连；密钥在 ECS `.env`、不入库。ol 上线应走独立 TLS 子域 + 独立 ol 密钥（不复用 dev）。

**验证码协助基址（`AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL`）**：协助链接由「持有事故的那个云端进程」签发，事故只活在**该进程内存**里（不落库、不跨进程），点击指令也只能发给**连在该进程 8787 上**的边缘分身。因此基址必须指向**签发进程自己**，否则运营会被送到一台既没有该事故、也够不着该分身的机器上。**dev = `http://121.89.85.150:8088`（2026-07-16 由 `http://aidcp.tommax.cc` 更正，见 §域名条）；ol = `http://aidcp.tommax.cc`。** 缺该项则回退 `AIDCP_PANEL_PUBLIC_BASE_URL`；两者皆空时协助功能整体不可用（面板 API 直接 503 `captcha_assist_unavailable`，在鉴权之前）。**排错口径**：503 = 这台机器没开协助功能（多半是找错机器）；404 = 这台机器开着但没有该事故（同样是找错机器）；`edge_offline` = 分身不连在这台机器上。三者同一病根，都不是「在这台机器上把开关打开」能修的。

Product actions MUST NOT require a second hidden environment authorization after their account/channel/schedule configuration is enabled. `AIDCP_CONTENT_SCHEDULE_AUTO`, `AIDCP_PUBLISH_AUTO`, `AIDCP_COMMENT_LIKE`, `AIDCP_FB_COMMENT_AUTO`, `AIDCP_FB_COMMENT_SHADOW`, `AIDCP_FB_COMMENT_REVIEW_ALL`, `AIDCP_FB_GROUP_JOIN_AUTO`, `AIDCP_FB_GROUP_JOIN_SHADOW`, `AIDCP_INTERACTION_AUTO_ACCOUNT_ALLOWLIST`, and `AIDCP_INTERACTION_DM_AI_ENABLED` are retired and ignored; remove them opportunistically from target `.env` files, but stale values MUST be inert. `AIDCP_INTERACTION_WRITE_ENABLED` remains the projected environment-wide emergency stop for interaction writes. Integration ownership flags such as `AIDCP_COMMENT_APPROVAL`, image-provider settings, and timeout overrides should still be reviewed per target. If dev and ol temporarily share the same Feishu app, keep `AIDCP_FEISHU_WS_ENABLED=false` on the non-active target so only one cloud process receives real Feishu command traffic.

### OSS image relocation

发布配图会先由图片模型返回 provider 临时图，再由 cloud 抓取字节并转存到 `OSS_BUCKET`，供审批与下发使用稳定公网 URL。`OSS_INTERNAL=true` 只在 ECS 与 OSS bucket **同地域**时可用；跨地域打开内网 endpoint 会让上传不可达，不能作为提速手段。

当前目标地域口径：

| Target | ECS region | OSS bucket region | `OSS_INTERNAL` guidance |
| --- | --- | --- | --- |
| `dev` | `cn-wulanchabu` | `oss-cn-beijing` (`aidcp`) | 不要直接设 `true`；当前是跨地域，只能走公网上传，或改用同地域 bucket 后再开启内网。 |
| `ol` | `cn-beijing` | `oss-cn-beijing` (`aidcp`) | 应设 `OSS_INTERNAL=true`；同地域内网上传可避免大图转存超过 30s。 |

2026-07-12 OL 事故复盘：Wanxiang `wan2.7-image` 返回的单张结果图约 5.8 MB，公网 OSS 上传约 40s，触发 cloud `relocateImageToStore` 的 30s「抓字节+上传」闸并导致 `M=0` 诚实失败；同一文件在 OL 同地域内网 OSS 上传约 0.2s。OL 已在 `/opt/aidcp/cloud/.env` 设置 `OSS_INTERNAL=true` 并重启验证。

DEV 是否延长超时：如果 DEV 继续使用北京 bucket 且不改同地域 OSS，公网跨地域上传 5 MB 级别万相结果图仍可能超过 30s。当前 cloud 代码没有独立的 env 来调 `relocateImageToStore` 的 30s 内层闸；`AIDCP_PUBLISH_PER_IMAGE_TIMEOUT_MS` 只控制每图总预算，不能放宽这段转存超时。要提升 DEV 稳定性，优先选「DEV 使用同地域 OSS bucket + `OSS_INTERNAL=true`」；若必须沿用北京 bucket，则应新增专用转存超时 env（例如 `AIDCP_IMAGE_RELOCATE_TIMEOUT_MS`）并把 DEV 设到 90s 左右，而不是误调发布总预算。

### Feishu bot binding

每个目标的 `.env` 中 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 必须指向该目标自己的机器人，并且机器人必须在默认审批/通知群内。

期望绑定：

| Target | Expected bot app name |
| --- | --- |
| `dev` | `Dev.A` |
| `ol` | `Red.A` |

2026-07-12 运行态修正记录：此前两端 `.env` 中的飞书凭据反接（`dev -> Red.A`、`ol -> Dev.A`）。已交换运行时凭据并重启两端 cloud；备份分别为 `dev:/opt/aidcp/cloud/.env.bak.20260712-171830.feishu-swap2`、`ol:/opt/aidcp/cloud/.env.bak.20260712-171829.feishu-swap2`。交换后 `bot/v3/info` 验证为 `dev -> Dev.A`、`ol -> Red.A`。

发送能力不能只看 bot 名称，必须做实际发信探针。2026-07-12 验证结果：

- `ol`：`Red.A` 已在默认审批群 `AI运营`，文本探针发送并删除成功；飞书审批卡发送能力已恢复。同日因旧凭据未送达的 `publish-84` 已按当前 `content_version=2` 补发真实审批卡；`publish-83` 检查时已是 `published`，未重复补卡。
- `dev`：`Dev.A` 已加载且服务健康，但对当前默认群发送探针仍返回 `230002 Bot/User can NOT be out of the chat`。在 DEV 依赖飞书审批前，必须把 `Dev.A` 加入目标群并重新 `/bind` 默认群，随后用发送+删除探针确认。

只读核验命令（不要打印 secret）：

```bash
cd /opt/aidcp/cloud
set -a; . ./.env; set +a
node --input-type=module <<'NODE'
const tokenResp = await fetch('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json; charset=utf-8' },
  body: JSON.stringify({ app_id: process.env.FEISHU_APP_ID, app_secret: process.env.FEISHU_APP_SECRET }),
});
const tokenData = await tokenResp.json();
const token = tokenData.tenant_access_token;
const botResp = await fetch('https://open.feishu.cn/open-apis/bot/v3/info', {
  headers: { Authorization: `Bearer ${token}` },
});
console.log(JSON.stringify(await botResp.json(), null, 2));
NODE
```

如果发送审批卡、评论卡或参照创作回执时报 `HTTP 400`，先用当前目标凭据查 `bot/v3/info` 和 `im/v1/chats`。`230002 Bot/User can NOT be out of the chat` 表示当前机器人不在目标群；`232010 Operator and chat can NOT be in different tenants` 表示 chat_id 属于不同租户或旧机器人环境。修复顺序是：纠正目标 `.env` 凭据 -> 把对应机器人拉进目标群 -> 重新 `/bind` 默认群或更新 `bot_chats` / `FEISHU_CHAT_ID`。

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
6. **Apply and verify database migrations before restarting** (change `cloud-schema-migration-executor`). Run `npm run migrate status` on the ECS (read-only). It MUST report no anomalies. If it lists pending migrations, a human MUST review them and then run `npm run migrate up`. If `migrate status` or `migrate up` fails, **abort the deployment** — do not restart the service. Never restart with unapplied migrations: since the stores no longer self-create tables, a lagging schema now surfaces as a fail-closed capability with a named missing-object list instead of a silently recreated empty table.
7. Restart only `aidcp-cloud.service`.
8. Health-check service state, `8787`, panel `8090`, PostgreSQL, Feishu if enabled, and console if touched. If the batch touches the text-card renderer (`src/render/`, `assets/fonts/`, satori/resvg deps), also run the render smoke: instantiate the renderer on the ECS and assert a golden card renders at 1728x2304 with non-zero bytes (verifies napi prebuilds against the host glibc).

### Ol

1. Proceed only after the user explicitly requests `ol`/online deployment.
2. Create or select a release branch named `release/<yyyymmdd>-<scope>` from the chosen clean committed trunk commit (branch tip, tag, or SHA). Retain it as the ol ref of record while it backs a live ol runtime; advance it only append-only (fast-forward when the fix is a strict descendant, otherwise a cherry-picked commit appended to the branch) and never force-push, rebase, or reset it.
3. Verify all affected artifacts are built from matching release branch sources.
4. Back up the existing ol runtime if present.
5. `rsync` committed cloud files and built console static files to ol.
6. **Apply and verify database migrations before restarting** (change `cloud-schema-migration-executor`). Run `npm run migrate status` on the ol ECS (read-only). It MUST report no anomalies. If it lists pending migrations, a human MUST review them and then run `npm run migrate up`. If `migrate status` or `migrate up` fails, **abort the deployment** — do not restart the service. Never restart with unapplied migrations: since the stores no longer self-create tables, a lagging schema now surfaces as a fail-closed capability with a named missing-object list instead of a silently recreated empty table.
7. Restart only ol `aidcp-cloud.service` and reload ol nginx when needed.
8. Health-check cloud, panel, console, database, and Feishu if enabled.
9. Record the release branch, deployed SHAs, database mode, and validation notes in the OpenSpec task.

### Schema Contract Gate

(change `cloud-schema-migration-executor`) Cloud 启动时先读迁移账本的最高版本，与本构建声明的 `REQUIRED_SCHEMA_VERSION` / `KNOWN_MAX_SCHEMA_VERSION` 按复合版本序比较（`aidcp-cloud/src/schema/schema-contract.ts`）。

- 模式由 `AIDCP_SCHEMA_GATE=warn|enforce` 控制，**当前默认 `warn`**：判定照做、结论照打，暂不拒绝启动。跑满一个发布周期并覆盖一次 ol 部署后切 `enforce` 并把默认值改为 `enforce`。
- **`enforce` 之后，账本落后于代码会直接表现为服务启动失败。这是预期行为**，处置是**补跑迁移**；MUST NOT 关闭契约门、MUST NOT 回滚代码来掩盖。
- 账本**超前**于代码（回滚到旧构建的典型场景）同样拒绝启动。放行通道 `AIDCP_ALLOW_SCHEMA_AHEAD` **必须填具体版本 id**，布尔值 / 空串 / 通配值一律视为未放行；不存在「一次开启即永久生效」的形态。共库期 dev 应用一条新 expand 迁移后，ol 上的旧构建会观察到超前——这不是误报，是必须逐次显式放行并记录的事实。
- **部署验收信号新增一条**：restart 之后除服务状态、`8787`、panel `8090`、PostgreSQL、飞书之外，还 MUST 在启动日志里确认出现 schema 契约门的**通过行**（含账本最高版本 id，形如 `[aidcp-cloud] schema 契约门（warn） schema 契约门通过：账本最高版本 <version>`）。仅确认进程 `active (running)` MUST NOT 被视为通过。

## Automation Writer Lock

(change `risk-state-cross-process-integrity`) The cloud process that owns risk state takes a PostgreSQL session-scoped advisory
lock keyed by its `executionTarget` before enabling any risk write path. The lock
rides a dedicated long-lived connection, not a pooled one: a pooled connection can
be recycled, and the lock would be released with it.

**Startup logs.** A healthy start prints `自动化写者锁已持有（target=<dev|ol>）`.
A refused start prints `自动化写者锁获取失败` plus the reason, writes a P1 alert
naming the holder, and exits non-zero. The refusal is the designed behaviour —
refusing to start beats silently double-writing.

**Who holds it.** On the target host:

```sql
SELECT a.pid, a.application_name, a.client_addr, a.backend_start, a.state
  FROM pg_locks l
  JOIN pg_stat_activity a ON a.pid = l.pid
 WHERE l.locktype = 'advisory'
   AND l.classid  = hashtext('aidcp_automation_writer');
```

Match `pid` against the running service (`systemctl status aidcp-cloud.service`)
before concluding anything.

**Forcing a release.** Only after confirming the holder is genuinely dead — the
old process was `kill -9`'d and its TCP connection has not yet been reaped, so
PostgreSQL still counts the session as live:

```sql
SELECT pg_terminate_backend(<pid>);   -- terminates that backend; the advisory lock goes with it
```

MUST NOT terminate a backend that belongs to a *running* service. If the service
is up and holding the lock, the correct action is to stop it first
(`systemctl stop aidcp-cloud.service`), which releases the lock cleanly.

**Why rolling/blue-green is forbidden here.** Both shapes deliberately keep the
old and new builds alive at the same time. For a stateless HTTP tier that is the
whole point; for this process it means two copies simultaneously hold the
admission authority for real platform side effects. The mechanical lock turns that
into a loud startup failure rather than a silent double-write, but the deployment
shape must not create the situation in the first place. The current
`systemctl restart` is already stop-then-start, with a zero overlap window — this
section only records that as a hard constraint rather than an accident.

## Preflight Helper

Use:

```bash
scripts/deploy-target dev --check
scripts/deploy-target ol --check
```

The helper is intentionally read-only. It prints target metadata and fails only when the key is missing or unreadable. Neither target requires a POSIX `600` mode; Windows ACLs remain the workstation's native access control and SSH may still apply its own platform checks.
