# Tasks — account-level-slow-start

> **并行纪律（CLAUDE.md §7）**：本 change 动两份 `protocol.ts` 与 `risk/risk-controller.ts`（明列的单写者热点文件）。**必须串行、不与其它 fleet session 并行**，否则 rebase 时两份 protocol.ts 漂移 → `AC-PROTO-*` 红。
>
> **分三阶段**：Phase 0（地基，云端可独立验证）→ Phase 1（可见，只读徽章）→ Phase 2（可改，勾选框）。若 Phase 2 的授权口径在评审中被否，Phase 0+1 加一个 console 侧写入口仍可独立交付（fallback，非目标——客户与运维零重叠，把唯一写入口放进客户进不去的后台等于把功能做成工单流程）。
>
> 台账格式：`<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha 必须取自**已推送**提交（判据 `git merge-base --is-ancestor`，见 memory `tasks-md-sha-must-be-pushed`）。

---

## Phase 0 — 地基（云端，可独立验证）

## 1. aidcp-cloud — 数据模型

- [x] 1.1 `src/account-store.ts` 的 `ACCOUNTS_SCHEMA_SQL`（:27-52）末尾，照 :44-50 已有三条自愈 ALTER 的先例追加 `ADD COLUMN IF NOT EXISTS slow_start_since TIMESTAMPTZ`（允许 NULL）。**必须走 IF NOT EXISTS**——本仓无迁移执行器（:44 注释自陈），只写进 CREATE TABLE 的话 dev/OL 那张早已存在的表永远拿不到它  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 1.2 配一份 `migrations/00XX_account_slow_start_since.sql` 作文档（不被执行，与 1.1 同义）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> 迁移 0044（文档性，实际靠 init() 幂等 ALTER 自愈）
- [x] 1.3 `AccountStore` 加第三个同步内存镜像 `slowStartCache`，照既有 `nicknameCache`(:164) / `platformCache`(:166) 的同款形状；启动时随账号加载回填  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 1.4 `AccountStore` 加写方法 `setSlowStart(accountId, enabled)`：enabled=true 写 `shanghaiDayStartMs(now)` 对齐后的时刻、false 写 NULL；写库成功后同步刷镜像（**顺序：先库后镜像，库失败不刷**）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 1.5 `AccountStore` 实现 provider 接口 `{ platformFor(id), slowStartSinceFor(id) }`——契约与已有 `quotaProvider` 逐字同款：**同步、零 IO、永不抛**（`effectiveQuotas` 是同步热路径，`canDo` 在浏览闭环每个动作都调，绝不能 await PG）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->

## 2. aidcp-cloud — 风控读侧（摘构造期快照）

- [x] 2.1 `src/risk/risk-controller.ts`：删掉构造期的 `createdAt` / `platform` 字段，改为注入 provider（照 :47 `quotaProvider` 的注入形状 + :178-179 在 `effectiveQuotas` 内每次现算）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 2.2 `src/risk/risk-controller-registry.ts`：删掉 `nurtureMetaResolver`（含 :59-60 那颗 `.catch(() => null)` 哑弹）与 `createdAt` 透传，改为只透传 provider。**做对之后 registry 不需要任何缓存失效机制**——「Map 永不驱逐」变成不再相关的事实  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 2.3 `src/account-store.ts` 删掉 `getNurtureMeta`（:133/:352-361）或保留但不再被风控调用（择一，勿留双源）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> 选择「删」：唯一消费者已换成 provider，留着即同一事实两个源
- [x] 2.4 新增私有 anchor 解析函数（clamp 与投影**共用同一个函数 + 同一次 `clock()`**）：① `slowStartSinceFor(id)` 非 NULL → 用它；② 否则 `coldStartRampEnabled && createdAt` → 用 `createdAt`（env 路径原样保留、一行不动）；③ 否则 null。**MUST NOT OR/AND/min 合成**——合成一次就把 FB 车队夹回 `view=70`（07-15 判为根因的那个上限）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> **偏离**：env 路径的 createdAt 也走 provider 现读（见文末偏离 A）
- [x] 2.5 `applyColdStartClamp`（:195）改用 2.4 的 anchor；平台经 `platformFor(id)` 现读  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 2.6 `src/risk/cold-start-planner.ts` 的 `coldStartDailyCap(ageDays, platform)`（:42-48）：平台未确认时**返回 null（不 clamp）**，MUST NOT 回落 XHS 曲线（:44 现状是 `platform === 'facebook' ? FB : XHS`，非 FB 一律 XHS）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 2.7 `src/server.ts:1259` 附近加全局停用闸 `AIDCP_SLOW_START_DISABLED === 'true'`：置真时无视所有账号级开关、全体不 clamp；启动日志如实打印（理由：raw SQL 改库不刷镜像，无此闸即无秒级止血手段）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> AIDCP_SLOW_START_DISABLED；启动日志仅在置真时打印
- [x] 2.8 `RiskController` 加 `slowStartView()`：返回 `{ state, day, totalDays, since, binding, eligible, ineligibleReason }`。`binding` = clamp 是否至少收紧一项（同一次组装内已有 clamp 前后两份数字，逐位比较即可）。**与 clamp 共用 2.4 的 anchor 与同一次 clock()**  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 2.9 单写红线自检：慢启动 MUST NOT 进 `risk_state` / `setQuotaLevel` / `applySignal` / mutationChain(:144-152)  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->

## 3. aidcp-cloud — Phase 0 测试

- [x] 3.1 **同源同格**：`slowStartView().day` 与 clamp 用的 day 逐格相等（day 1..8 + off）← 「显示的=生效的」的守卫  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.2 **单调性**（不是「必变小」）：同一 controller，慢启动开启前后 `effectiveQuotas()` 逐位 ≤。← design D6：「必变小」在可编辑的 `quota_config` 下为假，而单测用写死默认三档会稳过，那条守卫守不住它声称守的东西  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.3 **`binding=false` 用例**：XHS conservative 档 + D5-7 → view/like/comment/publish 逐位不变且 `binding=false`  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> **偏离**：原假设实测为假，binding 保持诚实（见文末偏离 B）
- [x] 3.4 **热加载**：改 store 值后，**同一个 controller 实例**的 `effectiveQuotas()` 立刻变（不重建 controller）← 正对着 Map 永不驱逐  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.5 **platform 诚实闸**：platform 未知时 `effectiveQuotas()` 与不开慢启动逐位一致，且 `eligible=false`、`ineligibleReason='platform_unknown'`  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.6 **两路径不合成**：env 开 + 账号级开且两者起点不同 → 按账号级起点，不取 `created_at`  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev --> 另加一条「env 旁路仍原样可用」正面用例
- [x] 3.7 **上海日对齐**：23:50 写入 → `since` 存当日 00:00；跨日 day 递增与计数窗口同相  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.8 **全局停用闸**：`AIDCP_SLOW_START_DISABLED=true` → 全体不 clamp 且 `ineligibleReason='globally_disabled'`  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.9 **零回归**：账号级全 off + env 关 → 与改动前逐位相同。原有「旁路关 → 逐位零回归」测试（`test/risk-cold-start-clamp.test.ts`）照旧保留、不改  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->
- [x] 3.10 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（**注意 memory `unified-card-routing`：`typecheck | tail` 的退出码是 tail 的、会假绿——不要管道**）  <!-- aidcp-cloud a80b9da --> <!-- 2026-07-17 deployed dev -->

## 4. Phase 0 验证（不依赖 UI）

- [x] 4.1 部署 dev（按 CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）  <!-- 2026-07-17 deployed dev --> 备份 cloud.bak.slowstart-20260717-124748.tar.gz + .env.bak.20260717；rsync 走 git archive a303157 干净快照（非脏工作区）
- [ ] 4.2 dev 上用 SQL/console 造态（写 `slow_start_since`），经后台仪表盘 `effectiveQuotas().day`（`panel-server.ts:646` 是天然观测点）验证 clamp 按新起点生效、且**不重启即生效**（正面验证 2.1-2.2 的 provider 现读）

---

## Phase 1 — 可见（只读徽章）

## 5. 协议（两份 protocol.ts 逐字一致 — 热点单写者）

- [x] 5.1 cloud `src/comm/protocol.ts:260` 的 `UiDailyUsagePayload` 加可选 `slowStart`（形状见 design D7）  <!-- aidcp-cloud a303157 --> <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> 两份逐字节比对 1157 chars 相同（land 后在 origin/master 上复核仍相同）
- [x] 5.2 edge `src/comm/protocol.ts:555-579` 同步加，**与 cloud 逐字一致**  <!-- aidcp-cloud a303157 --> <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> 两份逐字节比对 1157 chars 相同（land 后在 origin/master 上复核仍相同）
- [x] 5.3 `docs/protocol.md` 补 :56 表行与 :245-268 示例。**MessageType 数不变**（`AC-PROTO-02` 的计数不动）；command-bridge 不涉及（只映射角色命令）；edge onMessage 白名单已含 `ui.snapshot`（`edge-client.ts:680`）→ 协议四处同步的硬闸均不触发  <!-- aidcp (本仓) 见下方提交 --> 补 :56 表行 + dailyUsage 示例内 slowStart 块
- [x] 5.4 **两仓各写一条 AC-PROTO 往返断言**（照 `protocol-contract.test.ts:173/198/222` 的 `AC-PROTO-14`）。理由：两份 protocol.ts 的机械保障只覆盖 MessageType 穷举（:4-6/37），**payload 字段漂移 typecheck 完全抓不到——且已经漏过**：`inspirationSummary` 只活在 edge（`protocol.ts:566` + `ui-event-lines.ts:77/108` + `main.cjs:1683/1703`），cloud 全仓含 test 零命中，客户端在渲染一个云端从未发过的字段  <!-- aidcp-cloud a303157 --> <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> AC-PROTO-17（两仓各一条，含 binding=false / 三个 reason / 毕业态 / 字段缺省）

## 6. aidcp-cloud — 组装

- [x] 6.1 `src/server.ts` 的 `buildTodayUsageForAccount`（:2064）已有 try 块内、紧挨 :2160 `payload.quotaLevel = ...`，从**同一个 controller 实例**取 `slowStartView()`，**不得从 store 另读一次**（这是唯一能防「徽章说 D7、clamp 已按 D8 放行」的机制）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev --> 同一 controller 实例取 slowStartView()
- [x] 6.2 拿不到 controller → 诚实缺省（不带 slowStart 字段），照 :2160 附近既有的 catch 回落风格  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev --> 既有 catch 天然诚实缺省，未新增分支

## 7. aidcp-edge — 三道白名单（不进名单即静默丢弃、typecheck 抓不到）

> 与 memory 记的 C3残留2.1「FB 早带回却被未声明事件类型丢弃」逐位同型。症状是「云端发了、界面不显示、没有任何报错」。

- [x] 7.1 `src/flows/ui-event-lines.ts:100-120` 的 `sanitizeDailyUsage`：加 slowStart 分支且内部逐字段校验（`state` 必须命中三枚举、`day` 必须 1..7 整数），任一不合法 → **整个 slowStart 丢弃**（不渲染 > 渲染半真）。**注意 :100-104 的隐式耦合**：`totals` 为空即整块返 null，会把 slowStart 一起吞掉——需确认该路径下的期望行为  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> **已确认 7.1 提到的隐式耦合不咬**：pickDailyUsageCounts 恒发全 9 键（含 0）→ totals 实际永不为空；耦合仍在，若云端改成省略零值，slowStart 会随之被静默吞掉
- [x] 7.2 `src/electron/main.cjs:1675-1700` 的 `normalizeDailyUsage`：第二道白名单，校验风格照 :1701 的 `quotaLevel`  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 7.3 确认 `main.cjs:3512-3516` 透传无需改；`:3469-3473` 的 account 三字段重建**不涉及**（这是把字段挂 dailyUsage 而非 account 的附带收益）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> 已确认：:3512 透传无需改；bumpDailyUsage 用 ...usage 展开 → slowStart 在本地乐观加计数时存活

## 8. aidcp-edge — 只读徽章 UI

- [x] 8.1 `src/electron/renderer/index.html`：`#daily-summary` section（:259-303）内、`#quota-windows`（:302）之后、section 闭合前，加**静态**脚注行节点（JS 只切 hidden/textContent，不动态建元素）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.2 `src/electron/renderer/styles.css`：新建 `.acct-age` 类照 `.acct-p` 尺寸口径（:74，10px / 2px 6px）。**别复用 `.badge`**（:2008-2016，12px/4px 11px、为浮层行设计、会撑高行）。配色避开 `.acct-p` 已占的平台色，否则两个同尺寸色块并排会读成一个控件  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.3 `src/electron/renderer/ui-logic.js`：抽纯逻辑 `slowStartLine(dailyUsage, connState)`（照 `railDisplayName` :689-696 的抽法，:4 自陈无 DOM 无 Electron 依赖），返回 `{ visible, text, disabled, reason }`  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.4 `src/electron/renderer/renderer.js`：渲染该行。**渲染契约**：字段缺省 → 整行 hidden（**绝不默认 off**，照 personaBound 三态判例 `protocol.ts:624-631` 那段带血注释）；`active`+`binding=true` → 「慢启动 · 第 3/7 天」；`active`+`binding=false` → 「慢启动 · 第 5/7 天 · 当前档位已更严，不额外限制」；`graduated` → 「慢启动 · 已完成（X 月 X 日起上限已放开）」  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.5 **断连降级**：断连时字段不会变缺省、只是停止更新（`main.cjs:3512` 是 `if (evt.dailyUsage)` 不清空、:1728 bumpDailyUsage 展开保留）→ 按既有连接态灰化 + 「云端已断开，状态可能已过期」  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.6 规则常驻小字（照 `parking-hint` `index.html:770`，最长的先例就是两句）：「新号头 7 天按曲线逐日放开每日额度，第 7 天自动恢复正常。上限取慢启动曲线与账号档位中**更严的一个**。」**第二句必须有**——`#usage-source`（`renderer.js:621-623`）已在同屏显示「账号今日 · 稳妥节奏」，两个都表示「慢」的东西不说清关系，「我改了档位为什么没变」的工单会翻倍  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> **偏离**：所给文案违反本卡既有文案红线，改用同义措辞（见文末偏离 C）
- [x] 8.7 **两条文案红线自检**：全域不出现「新账号」三字（系统只知道它连上我们多少天）；不暗示「动作更慢 / 更像真人」（clamp 只返回 `WindowQuotas`、完全不进 pacing，`pacing.ts:206` 的 tempo 只认 status + quotaLevel）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 8.8 **不做 i 图标 / tooltip 基建**：客户端全库零 tooltip、零 i 图标、零 `aria-describedby`（index.html + styles.css 全文 grep 无命中）；现有两个浮层全是右对齐硬编码不锚定触发元素（`#health-pop` `styles.css:110-117`、`.delegated-popover` :2074），一个都不能复用。规则两句话，常驻小字即可  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->

## 9. Phase 1 测试

- [x] 9.1 edge ui-logic 单测：各态 + 字段缺省 + `binding=false` + 毕业态 + 断连降级 + 跨天  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 9.2 edge jsdom 断言徽章文案与显隐（`renderer-smoke.test.ts:1-25` 已加载真实 html + ui-logic + renderer）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> 含「点勾选框不触发展开」用例，**已做变异验证**（移掉 stopPropagation 该用例确实红）
- [x] 9.3 edge `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（不用管道，见 3.10）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> acceptance 23/23、npm test 1638 pass/0 fail、typecheck 0（均未用管道）

---

## Phase 2 — 可改（勾选框）

## 10. aidcp-cloud — 活映射解析

- [x] 10.1 `src/ws-server.ts` 加 `resolveAccountIdForEdge(edgeId)`：镜像已有的 `resolveEdgeIdForAccount(accountId, capability)`（:80，只认 OPEN + 非 stale）——同一循环、判据反过来、**多条即诚实失败**（MUST NOT 任取其一）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev --> resolveAccountIdForEdge + 4 条用例（含「同 edge 两账号 → null」）
- [x] 10.2 **绝不走 WS 写**：`ws-server.ts` 全文无鉴权，`session.accountId` 是边缘 hello 里自报的字符串（`edge-client.ts:271-279`）；`publish.approval_action` 的「鉴权」只是 `draft.accountId === session.accountId` 自证比对（`server.ts:2403`）——那对「本地在场的人审自己的稿」够用，对账号级风控配置不够  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev --> 已守：写走 client-auth HTTP，未新增任何 WS 写入口
- [x] 10.3 **不建 `edge_account_binding` 持久表**（理由见 design D9：爆炸半径 / 语义更差 / 信任链并不更强）；**不照抄 read-controls 那条链**——`withAuthorizedInteractionScope`(`client-user-store.ts:656-700`) 的 accountId 只能从 `interaction_auth_state` join 出来(:676-681)，而**那张表只有视频号有行**（唯一写入者链路终点 `aidcp-edge/src/wechat-channels/runtime.ts:104`），FB/XHS 走这条路 100% 返回 `not_authorized`(404) 且语义是「你没权限」→ 排查会先去查客户授权  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev --> 已守：未建绑定表、未碰 withAuthorizedInteractionScope

## 11. aidcp-cloud — client-auth 写路由

- [x] 11.1 加 `PUT /environments/:envKey/slow-start`，体 `{ enabled: boolean }` 严格 `onlyKeys` 校验（照 `interaction-customer-api.ts:277-282`）。**accountId 由云端解析、客户端永不提交**（红线已成文：`interaction-customer-api.ts:266-268` 的 `accountId is never accepted as an unverified cross-customer selector`）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.2 授权用已存在的 `ownsEnv(userId, envKey)`（`client-user-store.ts:632-648`），fail-closed  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.3 envKey→edgeId 确定性映射（`fleet.cjs` 的 `ads-${profileId}` ↔ `renderer.js:211` 的 `envKey = selected.profileId`）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.4 解析不出 → 409「该环境当前未连接」，如实说。**「边缘不在线就改不了」不是缺陷**：slowStart 状态本身就搭在 `ui.snapshot.dailyUsage` 上，边缘离线时这张卡本来就不更新、开关本来就该禁用——两者是同一件事  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.5 回执带写后真态 + 生效后的当日上限。**不做「已保存 vs 已下发本机」二态**（design D10：慢启动执行体在云端 `effectiveQuotas` 内，provider 现读做对了 PUT 200 = 本云端已生效；照抄一个不存在的状态同样是撒谎。**两者绑定**：若偷懒做成构造期读入，这个简化立刻变谎言）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.6 **不做 expectedVersion CAS**（单值 + 单写入口，last-write-wins 无丢失更新的实际危害；read-controls 需要 CAS 是因为两个独立开关共用一个版本号会互相覆盖，慢启动没有这个结构）  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->
- [x] 11.7 **信任边界写进 spec**（已在 `specs/client-customer-auth/spec.md`）：accountId 仍是边缘自报的（与现状风控计数、发布定向同源），但 ownership 是管理员授予的 env_key，且握手已有 platform 一致性校验（`connection-runtime.ts:143` 的 `platform_mismatch`）。客户只能改「自己环境上此刻正在跑的那个账号」  <!-- aidcp-cloud a303157 --> <!-- 2026-07-17 deployed dev -->

## 12. aidcp-edge — 勾选框

- [x] 12.1 `index.html` 脚注行内加 `.switch.inline-switch`（`styles.css:1529-1543`），照 `browser-cold-standby`（`index.html:775-779`）——它已被两个「行为策略」类开关占用、语义一致；裸 checkbox 在本客户端偏向临时/辅助选项，不匹配长期生效的账号策略  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 12.2 **必须 `stopPropagation`**（照 `renderer.js:1748-1750`）：`fields.dailySummary` 的整卡点击委托只认 `closest('button')`（:1744-1747），checkbox/label 不是 button → 点勾选框会连带展开/收起今日节奏。更难看的是 `<label>` 包 `<input>` 时点文字合成两次冒泡 → 切换两次 → 净效果为零；直接点滑块只冒泡一次 → 切换一次。**同一控件点在不同位置行为不同，人工点测会当「偶发」放过**。**不要**去放宽 :1745 的判据  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 12.3 preload / IPC 通道 + 主进程调 client-auth 路由  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 12.4 `eligible=false` → 禁用 + 按 `ineligibleReason` 如实说明原因；未连云端 → 禁用 + 「未连接云端，暂时无法更改」  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 12.5 **第一版平台闸只放 facebook / xiaohongshu**，视频号禁用勾选并如实说明（design D12：平台分叉因默认关在生产几乎从未执行过，开关一放开就是首次批量生效——零成本的风险削减）  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->
- [x] 12.6 jsdom 断言：**点勾选框不触发今日节奏展开**；各 disabled 态文案正确  <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev -->

## 13. Phase 2 测试与部署

- [x] 13.1 cloud + edge 两仓 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（不用管道）  <!-- aidcp-cloud a303157 --> <!-- aidcp-edge aeb235f --> <!-- 2026-07-17 deployed dev --> cloud 2390 pass/0 fail + acceptance 55/55；edge 1638 pass/0 fail + acceptance 23/23；两仓 typecheck 0
- [x] 13.2 部署 dev（§5 安全序列）  <!-- 2026-07-17 deployed dev --> 服务 active、8787 + 8090 在监听、飞书长连接已建立、PG select 1 通、isales 未被触碰

---

## 14. spec delta 与归档

- [x] 14.1 `openspec validate account-level-slow-start --strict` 通过  <!-- openspec validate --strict 通过 -->
- [x] 14.2 确认 `interaction-risk-gating` 的 MODIFIED 块保留了 07-15 决策的内核（「新号默认按安全配额浏览、不被冷启动压低」Scenario 原样保留、新设计满足它）  <!-- 已确认：MODIFIED 块保留 07-15 决策内核，新设计满足它（默认 NULL → 新号仍按安全配额浏览） -->
- [x] 14.3 **不在本 change 里删 `AIDCP_COLDSTART_RAMP` / `createdAt`**——那是 spec 明文保留的 MAY、是因生产事故才加的回滚拉杆，且往热点单写者文件塞不相关的删除只会白白放大 rebase 冲突面  <!-- 已守：AIDCP_COLDSTART_RAMP / createdAt 均未删；env 路径行为逐位保留并有正面用例 -->
- [x] 14.4 真机项登记 `docs/real-machine-acceptance-backlog.md`（新簇，见下）  <!-- 簇 94（簇 93 已被 client-content-workspace-navigation 于同日占用）；含两条硬前置 A/B + 9 项 -->
- [ ] 14.5 archive

## 15. 真机验收（新簇，登记 backlog）

- [ ] 15.1 **前置硬项 A（共库）**：验收账号与 OL 在跑账号显式排他核对。`docs/deployment-environments.md:62` ol 与 dev 共读写同一 PG——「新列默认 NULL 所以零回归」只证到了**部署那一刻**；只要验收账号同时在 OL 跑，dev 上一次勾选就会让 OL 生产上同一个号被夹到 FB D1 `view≤20`
- [ ] 15.2 **前置硬项 B（客户端构建）**：客户端必须是烘焙包或显式配 `AIDCP_CLIENT_AUTH_URL`。`main.cjs:551` 第一行 `if (!clientAuthEnabled()) return ... 503 '当前构建未启用 customer-auth API'`（:303-304 注释自陈「未配置（现有运营装机 / dev）行为与从前完全一致」）——否则会把 503 读成「provider 没现读」，去改一个没坏的东西
- [ ] 15.3 **用 FB 号 + normal/aggressive 档验收**（那里数字必变）
- [ ] 15.4 **XHS conservative 号另跑一条**，验的是 `binding=false` 文案正确出现（数字纹丝不动是**预期**，不是 bug）
- [ ] 15.5 勾选后后台仪表盘 `effectiveQuotas().day`（`panel-server.ts:646`）当场变 —— 同时验证 provider 现读真的绕过了 controller 缓存（**不重启**）
- [ ] 15.6 第 7→8 天跨天（dev 上把 `since` 改到 7 天前造态）+ 午夜对齐：day 递增与计数清零同时发生
- [ ] 15.7 Windows @640 窄窗：脚注行不破版（块级、不与标题区争空间，风险低但看一眼）
- [ ] 15.8 平台未知造态（临时让 provider 返 undefined）→ `eligible=false` + 不 clamp + UI 如实说明

---

## 16. 已知缺口（登记，不在本 change 做）

- [ ] 16.1 左栏 rail 行内不显示慢启动 → 多号并行时看不出哪个号在养（`.rail-name` 空间更紧 = 第二轮挤压）
- [ ] 16.2 视频号不支持慢启动（design D12）
- [ ] 16.3 完整 7 天曲线表不下发——规则说明只用静态措辞 + 今天生效的数字（数字来自已在推的 `dailyUsage.windows.day.quotas`，即 clamp 的实际结果 → 零漂移）
- [ ] 16.4 毕业时云端不自动清 `since`（那是替用户改他设的值，且丢失「谁什么时候养的」这段历史）
- [ ] 16.5 `platform_registered_at` + 运营录入口不做——要新造入口 + 改 4 段导入格式（`facebook-account-import.cjs:84-112` 无日期位）+ 依赖运营真知道注册日期（号从卡商买来时运营自己常常也不知道）。**「永远填不上」是稳态不是过渡态**；而新设计起点是勾选时刻，根本不需要它

---

## 17. 实装期偏离（三处，均为「照字面做会造出一个谎」而改）

### 偏离 A（task 2.2 ↔ 2.4 自相矛盾）：provider 多一个 `createdAtFor`

2.2 要求删掉 registry 的 `createdAt` 透传，2.4 又要求 env 路径继续用 `created_at`。而 `createdAt`
**只经 `nurtureMetaResolver` 一条路**到达 controller（原 `risk-controller-registry.ts:67`）——照字面实装，
`AIDCP_COLDSTART_RAMP=true` 会静默变成死代码：env 变量还在、日志照打「已开启」、clamp 永不发生。
那是 14.3 明文要保的**生产事故回滚拉杆**，坏掉且无人会发现。

→ provider 定为三个方法 `{ platformFor, slowStartSinceFor, createdAtFor }`（design 写的是两个）。
`createdAtFor` **仅**在账号级未开启时被查询，且注释写明 MUST NOT 用作慢启动起点。env 路径语义逐位不变，
并新增一条正面用例锁住（「账号级关 + env 开 → 按 created_at 现算，FB D7 view≤70」）。

附带：`ensureAccount` 同批回填 `createdAtCache`。原先 resolver 是**建 controller 时现读 PG**，
换成读内存镜像后，本进程 `init()` 之后新登记的账号若不回填，env 旁路会对它静默失效（少一半）。

### 偏离 B（task 3.3 的前提实测为假）：`binding` 保持诚实定义

3.3 要求「XHS conservative + D5-7 → `binding=false`」。**实测为 `true`**：view/like/comment/publish
四项确实逐位不变（80/20/3/1），但 `collect 10→5`、`follow 5→3`、`comment_like 3→2` 三项真被曲线压低了
——design D6 自己的表就是这么写的（「collect / follow / comment_like: 5 / 3 / 2 → 收紧」）。

`binding` 的定义是「clamp 是否至少收紧一项」（task 2.8）。对一个 collect 额度刚被砍半的号说
「当前档位已更严，不额外限制」是**假话**——为了让 3.3 通过而把 binding 缩小到只看四个头部动作，
等于用 UI 撒一个更精致的谎。

→ 保持 2.8 的定义。3.3 改为断言实测真值（四项不变但 binding=true，附「验收 MUST NOT 用 XHS
conservative 号看数字变没变」的理由）。`binding=false` 另用 D6 点名的**真实可达**场景覆盖：
档位被面板热编辑得比曲线还严时，慢启动一格都压不动。

### 偏离 C（task 8.6 文案违反本卡既有红线）：改用同义措辞

8.6 给的文案是「…逐日放开每日**额度**，…**上限**取…更严的一个」。但 `#daily-summary` 卡有一条既有
断言守着**全域不得出现「已达 / 上限 / 额度 / 释放 / 已满」**（`companion-ui.test.ts:891`，companion-ui
的陪伴式口径：用「计划」不用配额术语）。照抄即让既有用例红——已实测复现。

→ 用本卡自己的词写同一件事：「开启后头 7 天按曲线逐日放开每日**计划量**，第 7 天自动恢复正常。
每天实际执行的是慢启动曲线与账号档位中**更严的一个**。」两句都在、语义不变。毕业徽章同步改词
（「起按正常档位执行」而非「起上限已放开」——原措辞含「上限」，会在毕业态触发同一条红线）。
并把这条口径钉进 ui-logic 与 renderer-smoke 两处新断言，让下次违规在写文案的地方就红。

## 18. 未做 / 移交（如实登记）

- **4.2 / 15.x 全部真机项**：已登记 backlog 簇 93。代码级已验证到「部署那一刻」——dev 上列已自愈建出
  （`information_schema` 实查：`slow_start_since | timestamptz | nullable=YES`），**17 个账号全为 NULL**
  → 共库零回归在生产数据上成立。但「勾选后仪表盘天数当场变 / FB 号数字真变 / 窄窗不破版」这些需要
  真机 + 烘焙包客户端，未跑。
- **15.2 是硬前置**：现有运营装机 / dev 客户端 `clientAuthEnabled()` 为假时，勾选框会拿到 503
  「当前构建未启用 customer-auth API」。**那不是 provider 没现读**——验收前先确认客户端是烘焙包或
  显式配了 `AIDCP_CLIENT_AUTH_URL`，否则会去改一个没坏的东西。
- **未出安装包**：edge 改动已 land + 部署 dev 云端侧，但客户端 UI 要到运营机需出安装包（CLAUDE.md §6：
  打包默认不做，用户显式要求才执行）。**在出包之前，慢启动开关对运营不可见**——云端 Phase 0 已可用
  （可经 SQL 造态 + 仪表盘观测，即 4.2 的路径）。

### 偏离 D（task 4.2 / design Migration Plan 与 design Risks 自相矛盾）：raw SQL 造态**验不了**「不重启即生效」

4.2（与 design Migration Plan 第 4 步）说「用 SQL/console 在 dev 造态 → 经后台仪表盘
`effectiveQuotas().day` 验证 clamp 按新起点生效、**且不重启即生效**（正面验证 provider 现读）」。
但 design 自己的 Risks 段写着「**直接改库回滚不生效** → 内存镜像只在『服务写入的那个进程』里刷新，
`UPDATE accounts SET slow_start_since=NULL` 改了库但镜像不刷」。

两句不能同时为真。真相是：**raw SQL 造态 + 重启**能验「clamp 按新起点生效」（`init()` 会预热镜像），
但**验不了「不重启即生效」**——那恰恰需要走 PUT 路由（服务自己写 → 先库后镜像）。拿 raw SQL 去验
provider 现读，会看到「数字没变」并误判成「provider 没做对」，去改一个没坏的东西。

→ 4.2 保持未勾。真机项拆成两条登记进簇 94：94.1（raw SQL 路径，已注明其局限与判据边界）与
**94.2（勾选路径 —— 这才是 provider 现读的正面验证）**。
