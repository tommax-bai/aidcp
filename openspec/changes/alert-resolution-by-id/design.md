## Context

管理后台的告警是一条 append-only 事件日志（`alerts` 表），首页与监控页用 `GET /api/alerts`（过滤 `WHERE resolved_at IS NULL`）只读展示「未解决」列表，**列表无任何解决/勾销动作**。

全系统写 `resolved_at` 的**唯一**路径是验证码协调器的清除点：边缘送来配对的 `risk.captcha_cleared` → 协调器按 `edgeId` 调「按 edge 解决」（`UPDATE alerts SET resolved_at=now() WHERE edge_id=$1 AND resolved_at IS NULL`），同时解除该 edge 的传输层暂停（`resumeEdge`）。

告警只有两个写入点：
- **验证码/未知阻断**（`captcha`/`block`，P0/P1），带 `edgeId` 与 `accountId`。
- **节奏过载**（`pacing_saturation`，P2），只带 `accountId`、**不带 `edgeId`**（`edge_id=NULL`）。

由此产生两条永远解决不掉的告警（均为线上实测，07-01）：block 告警要靠边缘在同一活着的进程里送来配对 `cleared` 才解决（人工处置/重启/断线/误判自愈都不送）；pacing 告警 `edge_id=NULL`，「按 edge 解决」的 `edge_id=$1` 永不匹配空值，**结构上无解**。且系统无 TTL、无手动勾销兜底。

本设计经一轮多角度设计 + 对抗性评审收敛（见变更历史）：最小面、复用现列、把红线写成显式断言。

## Goals / Non-Goals

**Goals:**
- 给运营一个**不依赖 edge、主动触发**的解决途径，一次性结构性解开上述两条告警。
- 复用既有 `resolved_at` 列，零 schema 变更、零迁移。
- 诚实回真实解决行数，前端可区分「已解决 / 已被解决或不存在」，绝不假成功。
- 把「手动解决绝不联动风控状态单写、绝不解除边缘暂停」固化为可测断言。

**Non-Goals:**
- 不做 TTL 自动过期清扫（对仍活跃饱和账号不降稳态噪声；按 severity 触发是 footgun；新增常驻定时器是新失败面）。
- 不加 `resolved_by` / `resolution_source` 审计列（当前无 `includeResolved` 历史审计视图这个消费者）。
- 不做按账号 / 一键批量解决（会误清同账号仍活跃的真告警，是钝器）。
- 不引入新状态列 / 告警状态机（`resolved_at` 已足够表达「不再活跃」）。
- 不改协议、不改边缘、不改验证码事件的按 edge 自动清除与暂停/恢复语义。

## Decisions

### D1：按 `alert_id` 手动勾销（而非按 edge / 按账号 / TTL）
新增存储方法「按 id 解决」，SQL 精确镜像既有「按 edge 解决」，只把 `WHERE edge_id=$1` 换成 `WHERE alert_id=$1`，保留 `AND resolved_at IS NULL` 守卫，回真实 `rowCount`。
- **为何 by-id**：列表里一行一个 `alert_id`，逐条勾销是最贴合 UI 的诚实单元；且 by-id **天然不依赖 `edge_id`**——这正是 `edge_id=NULL` 的 pacing 告警**唯一**能被解决的路径，同时也绕开 block 告警对「边缘配对 cleared」的依赖。**一条通道同解两根因。**
- **弃 by-account**：会连带清掉同账号上仍活跃的其它告警（如把该账号一条真 block 一起 over-resolve）。
- **弃 TTL**：见 Non-Goals。

### D2：复用 `resolved_at`，不新增状态列
全系统「未解决」判据只有一处谓词 `resolved_at IS NULL`（存储 `list` / 面板 `listAlerts` / 首页 summary / 那条部分索引）。加第二状态轴（`dismissed_at`/`status` 枚举）会把这一处谓词裂成多处 AND、每个读点都要改，是纯漂移面；且运营视角「已解决」与「已勾销」无行为差异（都只是「掉出未解决列表」）。故复用 `resolved_at`：把行 `resolved_at` 置当前时刻即刻消失，正是想要的 UX。

### D3：HTTP 用 `POST /api/alerts/:id/resolve`（软闭合，非 `DELETE`）
告警是事件日志，需保留行供 `?includeResolved=1` 历史查看；`POST` 软闭合（改 `resolved_at`）保留 `created_at` 与行本体，语义自洽。`DELETE` 会删行、丢历史，不符。路由复刻既有「按 id 删除精选内容」路由的 `Number` 校验 + 依赖未注入 503 + 诚实回真实行数模式，但**不加 `accountId` 越权闸**（见 D5）。存储单例经面板 deps **可选注入**，未注入即路由 503，沿用「面板故障不连累闭环」既有降级。

### D4：红线隔离——手动解决只闭合日志行
手动解决**只** `UPDATE alerts.resolved_at`。MUST NOT 调 `applySignal` / `setQuotaLevel` / 写 `risk_state`（账号风控终态仍由风控 controller 单写，与告警解决完全解耦）；**MUST NOT 调 `resumeEdge`**。这是本设计最关键的实装护栏：验证码清除点（`onCleared`）恰好会 `resumeEdge`，实装者极易「顺手」把解决 block 告警接上恢复边缘——那会把仍卡在验证码后的 edge 误恢复。故独立于协调器实现，并写成必过断言。

### D5：不加 `accountId` 越权闸（基于单租户，非「无账号」）
按全局 `alert_id` 解决，路由不校验 `accountId`。事实澄清（吸收评审）：block 告警**确带** `accountId`；不加越权闸的正确理由是「单租户运营控制台 + 按全局 id 解决 + 两条卡死告警分属不同账号」，**不是**「block 无账号语义」。若 console 日后多租户化，需重评 by-id 全局解决的越权面。

### D6：诚实回真实行数
路由回 `{resolved: 0|1}`（0 = 没这条/已被解决，1 = 本次解决）。前端据此出文案：`1`→「已解决」、`0`→「该告警已解决或不存在」，绝不笼统报成功（符合 `console-write-operations` 的「拒绝/无效与成功可区分」契约）。

### D7：console 侧共享一个 resolve mutation
告警列表同时出现在监控页与首页，抽一个共享的 resolve mutation（`POST` + 成功后同时失效 `['alerts']` 与 `['dashboard','summary']` 两个 query key），两页各在告警行加一个二次确认的「解决」按钮，复用既有页内 mutation 写法；仅加动作，不改其余只读渲染。前端类型已含 `id`，无需改类型。

## Risks / Trade-offs

- **[勾销仍活跃的 block 告警]** → 手动解决只闭合日志行：不 `resumeEdge`、不改风控态。边缘仍暂停在验证码后、账号风控态仍为迁移后的姿态，由恢复窗口/人工恢复命令驱动降级。以断言固化「解决不 resumeEdge / 不碰风控单写」。
- **[pacing 打地鼠]** → 勾销后若账号仍饱和，节奏告警器在其内存冷却窗（约 20min）后会再 raise 一条**新**行。这是活状况如实复现、非 bug；勾销与告警器解耦，不重置冷却、不静默抑制（更诚实）。
- **[手动勾销 × 验证码去重冷却盲区]** → 手动解决不走 `onCleared`，故不清协调器的 per-edge 冷却记录；若同一 edge 在冷却窗（约 10min）内出现**真的新** block，会被既有冷却压制不再发卡/落库，而旧告警已被人工勾销 → 运营短暂「两头空」。低概率、窄窗、且是既有冷却属性；固化为已知语义 + 一条回归断言，不在本 change 改动冷却逻辑。
- **[未解决列表 100 行显示天花板]** → 列表有上限（监控页 100 / 首页 summary 更小）。若 pacing 长期堆积超过上限，纯 by-id 就够不到窗外的行。今日累积极慢（约一天一条），近期非问题；真逼近时用**限制 pacing raise 量**（按 type 清理/去重）解决，与本方案正交。（记为已知限制、非本次。）
- **[多租户越权面]** → 见 D5，单租户下安全；多租户化需重评。

## Migration Plan

- **无 schema 变更、无迁移文件、无协议改动、无新端口/新服务。** 核心修复完全复用现有 `resolved_at` 列。
- **cloud** 按 CLAUDE.md §5 安全序列部署到 ECS `121.89.85.150`：① sub-repo 测试通过（`test:acceptance` → `test` → `typecheck`）→ ② ECS 先备份（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ ③ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ ④ `systemctl restart aidcp-cloud.service` → ⑤ healthcheck（`active (running)` + 8787 监听 + 飞书长连接已建立 + PG `select 1`）→ ⑥ 失败即回滚。
- **console** 构建后发到 `/opt/aidcp/console`（`rsync` **绝不** `--delete`——目录混着非构建的 `intro.*` 文件），Nginx `aidcp-console.conf` 在 8088 serve 静态、反代 `/api`。
- 执行前先做 §0 私钥（`~/codes/isales-4.pem`，`chmod 600`）与 sub-repo 存在性检查。**红线：绝不碰同机 isales**（不同 systemd 服务/目录/端口）。
- **回滚**：restart 后 healthcheck 任一项不过即用备份 `.tar.gz` 覆盖回滚并重启；本改动无数据结构变更，回滚无残留。
- **上线后**：线上两条卡死告警（block `ads-k1e0awu5`、pacing）在运营点「解决」后即掉出列表——本 change 就是为它们提供出口。

## Open Questions

- `includeResolved=1` 历史视图是否要展示「谁于何时以何来源解决」？——若将来需要，才是追加 `resolved_by` 列的信号（届时优先只加 `resolved_by`、路由处 `verified.payload.sub` 现成、且**不动**按 edge 自动清除这条验证码安全路径）。本次不做。
