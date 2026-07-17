> **实装前必读**：本 change **纯云端单边**——不改边缘、不改 console、不碰协议、不碰 DB。
> 若你发现自己在改 `protocol.ts` / `main.cjs` / `renderer.js` / 任何迁移，**停手**：不是改错了地方，就是范围蔓延了（见 design D1/Non-Goals）。

> **实装后更正两条（2026-07-17）——本文件原文有两处错，读者以此为准**：
> 1. **上限面是 4 个不是 3 个**（见 design D8）。除 minute / hour / day 三份 quotas 外，还有 **session「本轮计划」窗口**（数据源是全局单例 `session_config_global`，`collects:5` / `follows:3`，与 `quota_config` 是两套配置）与**慢启动开关回执**（`PUT /environments/:envKey/slow-start` 的 `dayQuotas`，`renderer.js:1923-1934` 现读并**直接覆盖** `dailyUsage.quotas` 与 `windows.day.quotas`）。判据是 spec 原文「MUST NOT supply **a client-facing usage cap**」——**面无关**，漏掉它们才是违规。两者已一并摘，spec delta 已补一条 scenario 把这点写进法条。
> 2. **过滤点是 `pickDailyUsageCounts` 之后、不是之前**。原 2.2 / proposal Impact / design Migration 写的「之前」是**会造成事故的错**（详见 design.md Migration 步骤 1 下的更正框）：`pickDailyUsageCounts` 把六键无条件物化（缺失 → `0`），先摘再 pick 会把摘掉的键补回 `0`，`quotaSaturation` 算出 `totals(0) >= cap(0)` ⇒ 标成 saturated ⇒ 客户端渲染「收藏 0/0 今日计划已完成」——正是本 change 要除掉的那个谎、早一行原样重来，且 **typecheck 全绿**。design D3 正文「**最后一步**」才是对的口径，已按其实装。

## 1. aidcp-cloud — 平台感知的上限投影（纯函数）

- [x] 1.1 在 `src/platform/surface.ts` 新增纯函数（与既有 `isNoteActionSupported` / `isOrchestrationCapabilitySupported` 同处），入参 `(platform, quotas)`、出参过滤后的 quotas。**同步、纯、永不抛**：内部自兜 try/catch，任何 registry 查询失败即原样返回入参 quotas（design D4——fail-open 由函数自证，不依赖调用点记得包 try）。 <!-- aidcp-cloud 6122083 函数名 omitUnsupportedUsageCaps；barrel src/platform/index.ts 已 `export *`，无需另加导出 -->
- [x] 1.2 函数**两张矩阵都查**：note-scoped 动作（如 `collect`）查 `noteActions`，编排动作（如 `follow`）查 `capabilities`。**只查一张是缺陷不是取舍**——`follow` 的不支持声明在 `capabilities:307` 而非 `noteActions`，只查后者会结构性看不见它（design D2）。 <!-- aidcp-cloud 6122083 用全覆盖 Record<UiDailyUsageAction, UsageCapSupportSource> 表态每个客户端指标键读哪张矩阵；新增第七个 KPI 键时 typecheck 逼当场表态（载荷类型是宽松 Partial<Record<…>>，漏键 typecheck 一声不吭）。view→noteActions.read_content、follow→capabilities.follow、publish→'none' -->
- [x] 1.3 只摘**显式声明为 `supported: false`** 的动作。缺失声明 / 平台解析不到 / 查询抛异常 ⇒ **不摘**（照发）。**MUST NOT** 用「限额=0」表达不支持，**MUST NOT** 给 `quota_config` 加 platform 维度（design D6）。 <!-- aidcp-cloud 6122083 quota_config 零 diff；publish 两张矩阵都无声明 → 映射表显式写 'none'（永不摘），而非靠「查不到」碰巧不摘 -->
- [x] 1.4 单测（纯函数层）：FB 入参含 `collect`/`follow` ⇒ 出参恰好少这两项、其余逐位不变；XHS ⇒ 出参与入参**逐位相同**；platform 传 `null`/`undefined`/未知串 ⇒ 出参与入参逐位相同；registry 查询 throw ⇒ 出参与入参逐位相同（fail-open）。 <!-- aidcp-cloud 6122083 test/platform-surface.test.ts +6 用例，全部覆盖；另加「入参不被就地改写」「0 是真上限须原样保留、undefined 是无上限须保持缺席」「session 四键子集同规则」三条 -->

## 2. aidcp-cloud — 接入点（位置即正确性）

- [x] 2.1 **先逐点分类 `pickDailyUsageCounts` 的调用点**，写明分类结论。 <!-- aidcp-cloud 6122083 偏离：原文说 4 个，实际 8 个（proposal 写作后 account-level-slow-start 又加了一处）。分类：server.ts:2199/2200/2201 = quotas 侧（已摘）；:2141/2143/2145 = totals 侧（零 diff）；completeSessionUsageCounts:423 内部 = session totals 侧（零 diff）；:4167 = 慢启动回执 quotas 侧（已摘，见上方更正 1）。另 pickSessionUsageCounts:2146 = session quotas 侧（已摘）。四者入参均为宽松 Partial<Record<string, number>>，typecheck 一个都不提醒 -->
- [x] 2.2 接入点：`effectiveQuotas()` **之后**、`pickDailyUsageCounts` **之后**（见上方更正 2）。 <!-- aidcp-cloud 6122083 偏离：原文「pickDailyUsageCounts 之前」错误，已按 design D3「最后一步」实装并在 surface.ts 函数注释 + 调用点各留一条在码内警告。另：session 侧调用点在 :2186 那个 try 之外——D3 立「try 块内」的唯一理由是 fail-open，而 D4 已把该保证收进函数自身（自兜 try/catch、永不抛），平台读取 platformFor 也只是 Map.get（契约「同步、零 IO、永不抛」）⇒ 该点零 fail-closed 风险；D3 实质满足、字面不必，正是 D4 存在的目的 -->
- [x] 2.3 过滤对 minute / hour / day **三份 quotas 都生效**，不是只治 day。 <!-- aidcp-cloud 6122083 三份 + session 窗口 + 慢启动回执，共 4 个上限面（见上方更正 1） -->
- [x] 2.4 确认 `totals` 段**零 diff**。摘 totals 键是无效功——`main.cjs:1604` 的 `cleanRequiredCounts` 会把六键无条件物化回 0，改动会 land、会全绿、会部署，**屏幕上一格都不会变**（design D1）。 <!-- aidcp-cloud 6122083 已确认零 diff。补记：该不对称只在**顶层** totals 成立——windows[*].totals 走的是 cleanOptionalCounts（main.cjs:1648），摘那里的键**会**survive；本 change 两者都不碰 -->

## 3. aidcp-cloud — 载荷级验收测试

- [x] 3.1 **小红书载荷逐位不变**（回归判据，非善意期待）。 <!-- aidcp-cloud 6122083 桩层：test/platform-surface.test.ts 断言 XHS 六键 deepEqual 入参。真环境：见 4.4，dev 实测 XHS 下发六项逐位不变 -->
- [x] 3.2 **FB 载荷恰好少两项**：quotas 无 `collect`、无 `follow`，其余上限逐位不变；**totals 六项齐全且不变**。 <!-- aidcp-cloud 6122083 桩层 + dev 真实数据实测（4.4）。**偏离（诚实登记）**：3.1/3.2/3.3 无法在「载荷级」落测——buildTodayUsageForAccount 是 main() 内的未导出闭包（server.ts:2096），全仓无任何 test import src/server.ts，UiSnapshotService 把它整个当依赖桩掉且其 deps 不含 platform 字段。故断言压在**唯一可测的层**（纯函数 + 真环境实测），未为此重构 server.ts（范围蔓延）。缺口：无载荷级测试会抓到「有人把过滤挪到 pickDailyUsageCounts 之前」——已用 surface.ts 函数注释 + 调用点注释两处在码内警告代偿 -->
- [x] 3.3 **fail-open 断言**：平台解析失败 / 查询抛异常时，payload 仍带**完整六项上限**（不是空 quotas、不是整行消失）。 <!-- aidcp-cloud 6122083 桩层四条（undefined/null/''/未知串抛异常）+ dev 真实数据实测未知平台照发六项 -->
- [x] 3.4 确认 `AC-PROTO-*` **无变化**——本 change 不碰协议，若这组断言有任何变动，即说明改错了地方。 <!-- aidcp-cloud 6122083 AC-PROTO 仍 19 条、零改动；两份 protocol.ts 零 diff -->

## 4. 验证与部署

- [x] 4.1 `npm run test:acceptance` → `npm test` → `npm run typecheck`。 <!-- aidcp-cloud 6122083 acceptance 55/55、test 2402（0 fail，7 skip）、typecheck 干净。注意：typecheck 直接跑取真退出码，`| tail` 的退出码是 tail 的、会假绿 -->
- [x] 4.2 提交 + push cloud master。 <!-- aidcp-cloud 6122083 已推 origin/master（判据 git merge-base --is-ancestor，非 cat-file） -->
- [x] 4.3 部署 dev。 <!-- aidcp-cloud 6122083 2026-07-17 deployed。安全序列：deploy-target dev --check → 探 ECS 现状（部署树 md5 逐位等于 c701988 = 本提交父提交，确认并发方部署的就是我的基线、本次为纯 ff 叠加）→ 备份 cloud.bak.20260717-150822.tar.gz + .env.bak → rsync（--exclude .env/node_modules/.git）→ restart → healthcheck 全绿（active、8787+8090 在听、PG 就绪、飞书长连接已建立）。**未碰同机 isales**。两条纪律：① 主 checkout 有他人残渣（未跟踪文件 `1`）+ 并行场景 ⇒ 按 §6 从目标提交 `git archive` 建干净快照再 rsync，绝不从脏工作区上线；② 首次 rsync 误带 `--delete-excluded`（该标志会**删除目标上被排除的文件**，即会删掉服务器 .env 与 node_modules），rsync 恰好先报错中止、无损，已改回只排除不删除 -->
- [x] 4.4 dev 上取 FB 与 XHS 账号的实际用量载荷比对，坐实 3.1 / 3.2 在真环境成立（**不是只在单测里成立**）。 <!-- aidcp-cloud 6122083 2026-07-17 用部署上去的那份代码 + dev 库真实平台值 + 真实 deriveWindowQuotas('normal') 实测。dev 库平台普查：xiaohongshu 9 / facebook 7 / wechat_channels 2（7 个 FB 账号 platform 列真是 'facebook'，不受「NULL 回落小红书」天花板影响）。真实 day 档 = {view:150,like:50,collect:25,comment:8,follow:15,publish:1}（与 proposal 引用的「收藏 0/25」「关注 0/15」数字对上）。结果：facebook 摘掉 [collect,follow]、其余逐位不变；xiaohongshu 摘掉 []（六项逐位不变）；wechat_channels 摘到只剩 publish（D7 预测形状，其整行不渲染由 wechat-channels-interaction-management 决定）；未知平台照发六项（fail-open）。注：quota_config 表只存 9 条**覆盖项**（六键里只有 view），真实上限是代码默认档 + 覆盖合并——直接查该表当夹具会验错，已改走真实 deriveWindowQuotas 路径 -->

## 5. 回写与收口

- [x] 5.1 本文件标 `[x]` + commit-sha + 偏离说明。 <!-- aidcp 本次提交；sha 取自已推送提交（判据 merge-base --is-ancestor） -->
- [x] 5.2 真机项登记 `docs/real-machine-acceptance-backlog.md` **簇 90**。 <!-- aidcp 本次提交，登记为 90.7 -->
- [x] 5.3 `openspec validate platform-honest-usage-caps --strict` 通过。 <!-- aidcp 本次提交，含新增 scenario 后复验通过 -->
- [x] 5.4 与 `account-level-slow-start` 对账。 <!-- 无需对账：该 change 已于 2026-07-17 land + deploy + archive（早于本 change）。本 change 直接叠在其之上——平台过滤排在 effectiveQuotas（含慢启动 min(曲线,档位) 压低）**之后**，顺序即 design D3 要求的「最后一步」。反向影响一条：其新增的慢启动回执 dayQuotas 是本 change 第 4 个上限面，已一并摘（见上方更正 1） -->

## 6. 登记（不实装，仅记录）

- [x] 6.1 确认 design Open Question 2：dev 库是否有 FB 账号在风控流水里留有历史 `follow` 记录。 <!-- 结论：不阻塞、无需查。totals 段零 diff ⇒ 无论有无历史记录，数字本身不受影响，只是没了上限（客户端渲染「关注 N」无分母），仍诚实。且 registry 声明 FB 无 follow 执行器 ⇒ 云端结构上不下发 follow -->
- [x] 6.2 确认 design Open Question 1：视频号载荷形状是否需在过滤函数里显式短路。 <!-- 结论：**不短路**（与 design 倾向一致）。dev 实测视频号被摘到只剩 publish；该平台整行不渲染由 wechat-channels-interaction-management 决定、优先级更高，本 change 不接管其渲染决策，验收亦未依赖其载荷形状（Non-Goals 已写明不为其负责） -->
- [x] 6.3 把 proposal 的两条遗留登记进 backlog，**本 change 不治**。 <!-- aidcp 本次提交，登记为 backlog 簇 90 的 90.8（平台错标不可纠错，建议另立 change）与 90.9（spec:934 的 falsifiable 理由应改为引用四档模型，独立 nit） -->
