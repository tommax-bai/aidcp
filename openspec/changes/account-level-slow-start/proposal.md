## Why

2026-07-15 摘掉「按账号年龄冷启动配额爬坡」（change `disable-account-age-coldstart-ramp`）解决的是**粒度错**，不是机制错：一个进程级 env 开关（`AIDCP_COLDSTART_RAMP`）把老号和新号一起限死，Facebook 全车队浏览被封顶在曲线第 7 天的 `view=70`。摘除后新号从第一天起直接按安全限额跑——养号纪律随之整条消失，没有任何「只给这个新号压低」的手段。

真需求是**按账号 opt-in**：运营拿到一个真·新号时，能只给它开 7 天的逐日爬坡，不牵连同云端的其它账号。

但沿用旧机制的起点会造出一条新谎言：`accounts.created_at`（`aidcp-cloud/src/account-store.ts:41`，`DEFAULT now()`）记的是「该 accountId 第一次握手连上本云端库」的时刻，不是平台注册时间。FB 号在本项目主要靠 cookie 批量导入（`aidcp-edge/src/electron/main.cjs:4431`），导入与新建在云端走同一条路、握手侧零区分——**一个养了三年的号导入后会被算作「第 1 天」**。这是最主流的进号方式，不是边缘 case；反向亦错（号停用半年后复活，`ON CONFLICT DO NOTHING` 保留原 `created_at`，算作「第 180 天」而它只跑过 3 天）。本仓 spec 自己已诚实地把它叫「入库天数」（`openspec/specs/interaction-risk-gating/spec.md:430`）。

因此本 change 换锚点：**慢启动的起点 = 运营勾选那一刻**，由云端自己写下、100% 权威、零说谎面。同一个「第 3 天」，从推测账号年龄变成陈述我方策略状态。

决策人是养号的客户本人，而 console 后台是 `.env` 里 1–5 人内部账密（`aidcp-cloud/src/panel/auth.ts:1-8` 自陈「适配 1-5 人内部工具」）、客户进不去——所以开关必须落在客户端，否则功能退化成工单流程。

## What Changes

- **新增账号级慢启动开关**：`accounts` 表加一列 `slow_start_since TIMESTAMPTZ`（NULL = 关，默认；非 NULL = 开且为起点）。一列同时表达开关、起点与三态，无非法组合。写入时起点对齐上海日起点。
- **启用条件从「仅 env」扩为「env 全局 **或** 账号级」**：账号级用自己的起点；两者 MUST NOT 做 OR / AND / min 合成（合成一次就把 FB 车队夹回 `view=70`，即 07-15 判为根因的那个上限）。env 路径原样保留、缺省仍关。
- **`RiskController` 不再攥构造期快照**：`createdAt` / `platform` / `nurtureMetaResolver` 从构造期摘掉，改由 `AccountStore` 的同步内存镜像做 provider 现读（契约与已有 `quotaProvider` 逐字同款：同步、零 IO、永不抛）。这消灭「registry 的 controller Map 永不驱逐 → 勾了要重启才生效」的整类问题，而非绕过它。
- **平台未知 MUST NOT 静默回落小红书曲线**：现状 `coldStartDailyCap(ageDays, platform)` 对「非 facebook」一律走 XHS 曲线，而 `platform` 解析失败时传 `undefined` → FB 号按 XHS 曲线跑（D1 `view=50` 而非 `20`，差 2.5 倍）。改为平台解析不到即 `eligible=false`、不 clamp、如实说明。
- **新增全局停用闸** `AIDCP_SLOW_START_DISABLED=true`：无视所有账号级开关、全体不 clamp。理由：raw SQL 改库不刷内存镜像，没有此闸即无秒级止血手段。
- **协议加可选字段**（不新增消息类型）：`ui.snapshot` 的 `UiDailyUsagePayload` 内挂 `slowStart`，含 `state` / `day` / `binding` / `eligible` / `ineligibleReason`。
- **客户端「今日节奏」卡内新增常驻脚注行**：慢启动开关 + 「慢启动 · 第 N/7 天」状态徽章 + 两句规则小字。**不放标题区**（Windows 窄窗算术上挤爆昵称；标题区跟随选中环境而慢启动是账号级，作用域错）。
- **新增 env-scoped 写路由** `PUT /environments/:envKey/slow-start`：accountId 由云端经活会话映射解析，客户端永不提交。
- **诚实表达「勾了但没压」**：`effectiveQuotas = min(曲线, 档位)`，而档位数字面板可编辑——小红书 conservative 档在曲线 D5-7 下 view/like/comment/publish 逐位不变。UI MUST 如实标注该态，MUST NOT 宣称「正在压低配额」。

**非 BREAKING**：账号级默认全 NULL、env 缺省仍关 → 逐位零回归。

## Capabilities

### New Capabilities
（无）本 change 的三个面向都落在既有 capability 内，不新造 capability。

### Modified Capabilities
- `interaction-risk-gating`: 「配额闸默认不做账号年龄冷启动爬坡」要求的**启用条件**从「仅当 `AIDCP_COLDSTART_RAMP=true`」扩为「env 全局 **或** 账号级 `slow_start_since` 非 NULL」；新增「起点 MUST NOT 取 `created_at`」「平台未知 MUST NOT 回落 XHS 曲线」「两条启用路径 MUST NOT 合成」「全局停用闸」四条约束。原「新号默认按安全配额浏览、不被冷启动压低」的内核（07-15 决策）原样保留。
- `edge-companion-ui`: 新增「慢启动状态与开关在今日进展卡内如实呈现」要求——字段缺省 = 不渲染（照 `personaBound` 三态判例）、`binding=false` 时如实说明未额外限制、毕业态显式告知而非静默消失、MUST NOT 出现「新账号」措辞、MUST NOT 暗示节奏变慢。
- `client-customer-auth`: 新增 env-scoped `PUT /environments/:envKey/slow-start` 要求——accountId 由云端经活会话映射解析、客户端永不提交；边缘未连接即诚实 409。

## Impact

- **aidcp-cloud**：`src/account-store.ts`（加列 + 第三个内存镜像 + provider）、`src/risk/risk-controller.ts`（摘构造期快照、anchor 解析、`binding` 计算）、`src/risk/risk-controller-registry.ts`（删 `nurtureMetaResolver`）、`src/risk/cold-start-planner.ts`（平台未知不回落）、`src/server.ts`（组装 `slowStart` 视图、全局停用闸）、`src/comm/protocol.ts`、`src/ws-server.ts`（`resolveAccountIdForEdge` 活映射）、client-auth 路由。
- **aidcp-edge**：`src/comm/protocol.ts`（与 cloud 逐字一致）、`src/flows/ui-event-lines.ts` + `src/electron/main.cjs`（两道手写字段白名单，不进名单即静默丢弃、typecheck 抓不到）、`src/electron/renderer/`（index.html / renderer.js / ui-logic.js / styles.css）、preload/IPC。
- **协议**：MessageType 数不变（`AC-PROTO-02` 不动）；command-bridge 不涉及；edge onMessage 白名单已含 `ui.snapshot`。仅 `docs/protocol.md` 补表行与示例。
- **热点文件串行纪律**：本 change 动两份 `protocol.ts` 与 `risk-controller.ts`（CLAUDE.md §7 明列的单写者热点），MUST 标记串行、不与其它 fleet session 并行。
- **dev/OL 共库**（`docs/deployment-environments.md:62`）：验收账号与 OL 在跑账号的排他核对为前置硬项——dev 上一次勾选会夹住 OL 生产上的同一个号。
- **不在本 change 内**：删 `AIDCP_COLDSTART_RAMP` / `createdAt`（spec 明文保留的 MAY + 因生产事故加的回滚拉杆）；`platform_registered_at` 新列与运营录入口；i 图标 / tooltip 基建；持久绑定表；console 改动；左栏 rail 徽章；视频号支持。
