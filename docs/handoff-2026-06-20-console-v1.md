# 交接：管理后台 aidcp-console-panel-mvp — V1 续做（2026-06-20）

> 给**新会话接手者**：先读本文件 → `CLAUDE.md`（§1 四仓、§5 部署）→ `openspec/changes/aidcp-console-panel-mvp/`（proposal/design/design-ui/specs/**tasks.md**）。
> tasks.md 是权威进度（每个 task 带 commit-sha + 偏离说明），本文件补充「续做 V1 的上下文与注意」。

## 0. 一句话现状

管理后台 **MVP 已上线生产 ECS**（2026-06-20），**V1 风控写核心已端到端可用**（手动调风控状态/档位）。进度 **37/44**，剩 **7 个 V1 增量 task**：9.2 / 9.3 / 9.4 / 9.5 / 9.6 / 10.2 / 10.3。

## 1. 三仓 tip（接手时先核对，可能已被并发会话推进）

| 仓 | tip（截至交接） | 备注 |
| --- | --- | --- |
| `aidcp`（中控） | `77e56b1` main | openspec change + CLAUDE.md(四仓) + 进度 |
| `aidcp-cloud` | `32a664e` master | 面板后端 `src/panel/` + 风控写。**工作区长期有并发会话的 publish-agent dirty（非 V1，勿碰、勿提交）** |
| `aidcp-console` | `8d21677` master | 前端（private 仓 `tommax-bai/aidcp-console`） |

> ⚠️ **并发会话**：这台机器有另一个会话长期在 `aidcp-cloud` 做 publish-agent 重构（publish-log/concept/role-dispatcher/server.ts/command-sequencer 等），持续 commit+push 到 master、工作区常 dirty。详见 memory `precise-git-add-concurrent-sessions`。**铁律：提交前 `git status` 看清，精确 `git add <自己的文件>`，绝不 `git add -A`；`git diff --cached --name-only` 确认 staged 只含自己的。**

## 2. 已完成

**MVP（task 1–7，31 个）+ 部署**：面板 API 层（`src/panel/`：jwt/auth/version/panel-store 只读聚合/panel-ws 事件流/panel-server 路由）、accounts 主表 + 暂停态持久、accountId 归因、写操作（审批 first-writer-wins + pause/resume command）、edge 心跳、console 全套页面 + 红线组件 kit。**已部署 ECS**（详见 §6）。

**V1 风控写核心（task 8.1–8.4 / 9.1 / 10.1）**：
- `e967f36` mutation queue（`RiskController.enqueue`，每账号串行化、无丢更新）+ `setQuotaLevel`（档位单写）+ 枚举运营信号（`manual_restrict`/`manual_freeze`/`operator_override_recover`，后者**强制 normal+清零、需审计理由**——design 开放问题已确认=要）。
- `32a664e` `RiskControllerRegistry`（`src/risk/risk-controller-registry.ts`，懒加载、共享 PgRiskStore、单写 PER ACCOUNT）；server.ts 现役用 registry 的 default controller（单一来源）、record 按 `evt.accountId` 路由；panel 路由 `POST /api/accounts/:id/risk/status`（枚举种类、override 需 reason、返回 `{state, statusBefore, changed}`，refused 可辨）+ `/risk/quota`（setQuotaLevel）。
- `8d21677`（console）`RiskControls` 组件：status 迁移 Dropdown + quota Select（**两个独立控件**）、override Modal 填理由、非乐观 round-trip、refused 区别于成功；接进 Accounts 页操作列。

## 3. 剩余 V1（7 task）— 实现要点 + 风险 + 文件

> 全部走 `openspec/changes/aidcp-console-panel-mvp/tasks.md` 第 9/10 节定位；落 cloud/console，进度回写本仓。

- **9.3 `ALTER publish_log + concepts ADD COLUMN account_id TEXT NOT NULL DEFAULT 'default'`**（最简，但**碰并发热点** `publish-log-store.ts`/`concept-store.ts`）。建议：用独立 migration（`migrations/` + `scripts/run-migration.ts`）或幂等 `ADD COLUMN IF NOT EXISTS`，**避免改并发正在动的 store 文件**。概念查询保持账号无关。
- **9.5 `alerts` 表 + `GET /api/alerts`**（独立、低风险，**推荐先做**）。新 `src/...alerts-store.ts`（alert_id PK/severity P0-P3/account_id/type/ts/resolved_at）；在飞书卡发送点（captcha-coordinator）写入、验证码清除点 set resolved_at；panel-store/路由读；dashboard summary 的 `alerts:[]` 接真数据。复用 P0–P3 枚举（risk-control §7 / product-exception §1）。
- **9.2 noteId + 接线孤儿 `risk_interactions` + `GET /api/monitor/interactions`**（中风险，碰 `handler.ts` emit 点 — 并发偶尔动）。`interaction.occurred` 的 `noteId?` 已声明（types.ts:123），在发射点（handler.ts 的 action.completed case，~line 242，已填 accountId）填 noteId；把从未实例化的 `InteractionDedup`/`risk_interactions` 接进互动完成路径；panel 加 monitor/interactions 读路由。
- **9.6 去 attribution-pending**：accountId 已流通（task 3）、risk_counters 已按账号记（`appendCounter(accountId,...)`）。让 panel-store 支持按账号聚合，dashboard 按账号切片去掉 `attributionPending` 标（或保留全局 totals 标注、新增按账号视图）。语义见 design D3/D4 + interaction-attribution spec。
- **10.2 dispatch 控件** + **10.3 Monitor/Alerts 页**（console，零并发）：dispatch 启停按钮接 9.4 的 `POST /api/accounts/:id/dispatch`；Monitor 页接 9.2 的 monitor/interactions + 9.5 的 alerts。
- **⚠️ 9.4 per-edge dispatcher（最高风险，建议最后/最小做）**：design 说「**非** god-object」「运行中的单账号闭环在此落地前不被触碰」「highest-touch、deferred」。`role-dispatcher.ts` 是单全局实例（one sessionContext/currentNote/sessionActive）+ **并发会话热点**。**单账号现实下风险 >> 收益**。建议：`POST /api/accounts/:id/dispatch {start|stop}` 先用**现有单 RoleDispatcher** 的 startSession/endSession（回报真实 edge-online 数 via `server.edgeCount()`/`onlineEdgeCount()`），**per-edge 多路复用拆分留到真多账号场景**，并在 tasks.md 标注偏离。**改 role-dispatcher 前务必确认它不在并发 dirty 列表 + 不破坏现役浏览闭环。**

## 4. 关键约束与红线（必读，违反即翻车）

- **风控单写**：account 风控最终态只由 `RiskController` 写（已串行化 enqueue）；status 经 `applySignal`(枚举种类)、档位经 `setQuotaLevel`，**绝不 raw UPDATE**。
- **不静默假成功**：写回真态；refused 用 `changed=false` 渲染；审批返 `written`/`alreadyDecided` **绝不 published**；归因落地前按账号切片标 attribution-pending。
- **边-云隔离**：panel WS 纯只读 EventBus 扇出，**绝不碰 edge**、与 `:8787` 物理隔离。
- **协议 v2 不被面板层触碰**：accountId 已在协议线上、noteId 已声明字段，都是云内改动，**不动两份 `protocol.ts`**。
- **ECS 绝不碰 isales**（80/8000/api/engine/scheduler/worker + `isales.conf`）；面板独立端口 8090，Nginx `aidcp-console.conf` 8088。

## 5. 续做流程

- **测试**（cloud）：`node --import tsx --test --test-force-exit test/<file>.test.ts`（`--test-force-exit` 防 panel 测试因 fetch keep-alive 不退出）；`npm run typecheck`。**全量 typecheck 含并发噪声**——`grep "error TS" | grep <自己的文件>` 判读自己的错误。
- **隔离验证**：要在干净 master 上验证，`git stash push <并发的文件>` 临时隔离、验证后 `git stash pop`；或 `git archive master` 导出干净副本（软链复用 node_modules）。
- **提交**：精确 `git add` 自己的文件 → `git diff --cached --name-only` 确认 → commit（英文，末尾 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`）→ ff push。回写本仓 tasks.md（`[x]` + `<!-- <repo> <sha> 备注 -->`）。
- **npm install**（若需，console）：本机内部源 `npm.zhaopin.com` 常挂，`@types` scope 被强制指向它；用 `npm install --registry=https://registry.npmjs.org/ "--@types:registry=https://registry.npmjs.org/"`，必要时禁沙箱。
- **部署**（§6 + CLAUDE.md §5）：**从干净 git master 用 `git archive` 部署**（绕开并发 dirty 工作区）；`rsync` **不用 `--delete`**（会误删 ECS 的 `.env.bak`/zip）；先 dry-run 暴露范围；备份→rsync→（package.json 变才 npm install）→`systemctl restart aidcp-cloud.service`→healthcheck（active + 8787 + 8090 + 飞书长连 + PG + console 8088 + **isales 仍在**）→失败回滚。console 改了则 `vite build` + rsync `dist/`→`/opt/aidcp/console`。

## 6. 部署形态 + 部署后 TODO

- **ECS** `121.89.85.150`（私钥 `~/codes/isales-4.pem`，chmod 600）：cloud `/opt/aidcp/cloud`（systemd `aidcp-cloud.service`，边-云 8787，面板 `127.0.0.1:8090`）；console `/opt/aidcp/console`；Nginx `/etc/nginx/conf.d/aidcp-console.conf`（listen **8088**、serve console、反代 `/api`+`/ws`→8090）。面板 env 在 cloud `.env`：`AIDCP_PANEL_PORT=8090` / `AIDCP_PANEL_JWT_SECRET` / `AIDCP_PANEL_USERS=admin:<部署时生成的临时密码>` / `AIDCP_PANEL_FORBIDDEN_PORTS=8000,80,443`。
- **TODO**（见 memory `aidcp-console-mvp-deployed`）：① 改 admin 临时密码（ECS `.env`）；② 确认 ECS 安全组开放 8088（仅验证过机器内 http=200）；③ 续做 V1 后重新部署（带上当前 V1 风控写，需 dry-run 暴露范围）。

## 7. 续做第一步建议

接手后：`cd ../aidcp-cloud && git pull`（拿并发最新）→ `openspec show aidcp-console-panel-mvp` / 读 tasks.md 第 9/10 节 → **先做 9.5（alerts，独立低风险）→ 9.3（account_id 列，用独立 migration 避开并发 store 文件）→ 9.2 → 10.2/10.3 → 9.6 → 最后 9.4（最小 dispatch 路由，慎碰 role-dispatcher）**。每步精确提交、回写 tasks.md。全部 done 后 `openspec validate aidcp-console-panel-mvp --strict` → 部署 → archive。
