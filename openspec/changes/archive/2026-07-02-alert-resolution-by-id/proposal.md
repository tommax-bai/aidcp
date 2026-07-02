## Why

管理后台「告警（未解决）」列表当前**唯一**的解决途径，是验证码协调器收到边缘配对的 `risk.captcha_cleared` 后**按 edge** 解决其名下所有未解决告警。这条唯一通道使两类告警永远卡在列表里：

- **block（未知阻断弹窗）告警**：要靠边缘在同一个还活着的进程里送来与当初 `detected` 严格配对的 `cleared` 才会被解决。人工关弹窗、重启边缘、会话断线、误判自愈都不会送来这个配对事件；系统又无 TTL、无手动勾销，于是它永远留在列表（线上实例：edge `ads-k1e0awu5`，07-01）。
- **节奏过载（`pacing_saturation`）告警**：落库时不带 edge 标识，而「按 edge 解决」的匹配条件（`edge_id = $1`）永不匹配空 edge，**结构上无任何代码路径能解决它**（线上实例：07-01）。

运营已经处置了底层问题（清了弹窗、调了节奏/配额），面板却无法反映，产生「已处理但一直显示未解决」的假象。需要一个不依赖 edge、由运营主动触发的解决途径。

## What Changes

- 新增**按 `alert_id` 手动勾销单条告警**的写通道：云端告警存储加一个 by-id 解决方法、面板加 `POST /api/alerts/:id/resolve`、console 的监控页与首页告警列表每行加一个「解决」按钮。
- by-id 通道**天然不依赖 edge 标识**，一次性结构性解开上述两条卡死告警（绕开 block 的「边缘配对 cleared」依赖，绕开 pacing 的 `edge_id=NULL`）。
- **复用既有 `resolved_at` 列**：把某行 `resolved_at` 置为当前时刻即刻掉出「未解决」列表——无 schema 变更、无迁移、无新增状态列。
- 红线不变：手动解决**只闭合告警日志行**，MUST NOT 触碰风控状态单写（`applySignal` / `setQuotaLevel` / `risk_state`），MUST NOT 解除边缘暂停（`resumeEdge`）；**诚实回真实解决行数**（0 = 没这条/已解决，1 = 已解决），前端据此区分文案、绝不笼统报成功。
- 明确**不做**（YAGNI，记为纯追加式扩展缝）：TTL 自动过期清扫、`resolved_by`/来源审计列、按账号或一键批量解决。

## Capabilities

### New Capabilities

- `alert-manual-resolution`: 运营从管理后台按 `alert_id` 手动勾销单条运维告警的完整契约——by-id 解决语义与诚实行数、JWT 守护下的面板写路由、与边缘自动清除（按 edge）并存不冲突（同守 `resolved_at IS NULL`、行锁串行、后者命中 0 行）、以及「绝不联动风控状态单写 / 绝不解除边缘暂停」的隔离红线。

### Modified Capabilities

（无。本 change 遵守 `console-panel-api`（JWT 守护、面板故障不连累闭环）与 `console-write-operations`（owner 中介、诚实回真态、绝不 raw UPDATE）既有要求而不改动其 requirement；亦不改 `captcha-incident-handling` 的边缘暂停/恢复语义。）

## Impact

- **aidcp-cloud**：`src/alerts/alert-store.ts`（`AlertStore` 接口 + `PgAlertStore` 新增按 id 解决方法，SQL 镜像既有按 edge 解决）、`src/panel/panel-server.ts`（JWT 保护区内新增 `POST /api/alerts/:id/resolve` 写路由）、`src/panel/types.ts`（`PanelDeps` 注入可选 `alertStore`）、`src/server.ts`（把 `main()` 已构造的 `alertStore` 单例接进面板 deps）。**无协议改动、无 schema 改动、无迁移。**
- **aidcp-console**：`src/api/queries.ts`（共享 `useResolveAlert` mutation）、`src/pages/MonitorPage.tsx` 与 `src/pages/DashboardPage.tsx`（告警行「解决」Popconfirm 按钮）。
- **aidcp-edge**：无改动。
- **测试**：cloud 新增 `resolveById` 与路由用例 + 红线隔离断言（不触风控/不 `resumeEdge`）+ 与按 edge 解决共存无冲突；回归纪律走 `test:acceptance` → `test` → `typecheck`。
- **部署**：纯 cloud + console，按 CLAUDE.md §5 安全序列部署到 ECS（备份→rsync→restart→healthcheck→失败回滚），console 发 `/opt/aidcp/console` 且 rsync 不 `--delete`；**绝不碰同机 isales**。
