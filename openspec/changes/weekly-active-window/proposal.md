## Why

运营希望把「机器人允许活跃的时间」按**一周**精细排布——不只是「每天 08:00–24:00」这种单段日窗口（现有 `session-auto-resume` 的活跃时段窗口只能配单段、且只在续场处生效），而是**按天 × 按小时**各自开关（如工作日 09–22 活跃、周末只开晚上、深夜全休）。这既贴合真人作息（降低「7×24 不间断」的风控特征），也给运营一个直观的全局总闸。现有单段日窗口表达不了「周中/周末不同」「按小时挖空」，且不约束新开会话与运行中会话，故新增一个全局周历活跃时段闸。

## What Changes

- 新增**全局「可活跃时间」周历掩码**：7 天 × 24 小时 = 168 格，每格「活跃 / 休眠」。周一起头、按**服务器本地时间**判定（与现有日窗口同口径，单地域、无时区参数）。对**所有账号**生效。
- **落地复用全局单场配置单例**（`session_config_global` 单行 + `/api/session-limits` + 控制台 session-limits 查询）：只加**一列** `active_week_mask TEXT`（168 长 '0'/'1' 串）+ 一个取值口 + 一个面板字段，不另起存储 / 接口。列可空（NULL = 未配置 → 回落「全周全天活跃 = 不限」，严格零回归）。自愈加列（store init 幂等 ALTER）+ migration 0024，重启即自动补列。
- **三处闸**（读同一全局掩码、热加载）：① 不在活跃格时**不开新会话**（统一收口于会话(重)启动入口，覆盖边端 hello / 绑人设自启 / 续场 / 面板手动）；② 不在活跃格时**不自动续场**（续场闸新增一道，与既有日窗口/每日上限/风控并列）；③ 会话**运行中跨入休眠格 → 结束当前会话**（监测体每次现读，巡视暂停期不打断）。
- **管理后台「安全」页新增卡片「可活跃时间（全局）」**：7×24 网格点选（点格切小时、点「天」名切整天、点小时号切整列）+ 预设（全部活跃 / 全部休眠 / 工作时间周一–周五 9–22 / 反选）。改完下场会话即生效（热加载）。未配置显示「全天活跃（未配置）」。
- 校验：传则必须为长度 168、仅含 '0'/'1' 的串；非法整块拒（`invalid_value`/400），绝不落脏掩码、绝不部分落库。

## Capabilities

### New Capabilities
- `weekly-active-window`: 确立一道**全局周历活跃时段闸**——按周 × 天 × 小时配置允许活跃的时段，对所有账号生效；活跃时段外不开新会话、不自动续场，运行中会话跨入休眠时段须结束；配置作为全局单例落库、后台可改、热加载、缺值绝不 brick（未配置 = 全天活跃 = 零回归）。与既有 `session-auto-resume` 的单段日活跃窗口**并存且相互独立**（两道闸都过才活跃；本闸更细、且额外约束开场与运行中会话）。

## Impact

- **代码**：aidcp-cloud 为主——`risk/session-limits.ts`（掩码类型 + 纯函数 `isWeekActiveAt` / `mondayBasedDayIndex` + 提供者口 `weekActiveMask()`）、`config/session-config-store.ts`（加列 + 取值 + upsert）、`config/session-config-facade.ts`（校验 + 回显）、`panel/types.ts` + `panel/panel-server.ts`（契约 + PUT 解析）、`orchestrator/role-dispatcher.ts`（启动收口闸 + 续场闸 + 注入监测体现读口）、`agents/session-monitor-role.ts`（运行中跨入即结束）、`migrations/0024_weekly_active_window.sql`。aidcp-console 小改——`types/api.ts`（对齐 `SessionLimitView.activeWeekMask`）、`pages/QuotasPage.tsx`（新卡片 + 7×24 网格编辑）。
- **测试**：纯函数 + store 取值/写 + facade 校验 + 调度器启动/续场闸（全休眠不开/不续、全活跃正常、缺掩码零回归）全过；既有 `SessionLimitProvider` / `SessionConfigRow` 内联桩补一字段。
- **数据 / 部署**：一列自愈 ALTER（重启即补，无需手动 psql）+ migration 0024；走家族安全序列（备份 → 部署 → healthcheck → 失败回滚），绝不碰同机 isales。需用户放行生产 SSH。
- **协议**：零改（不动两份 `protocol.ts`）。
- **已知边界**：窗口**重开**后不主动唤醒——由边端重连 / 下一次 hello 驱动续上（与既有日活跃窗口同构，不新增定时唤醒）。时区为服务器本地（单地域）。
