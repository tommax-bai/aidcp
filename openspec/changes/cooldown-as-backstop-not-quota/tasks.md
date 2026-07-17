# Tasks — cooldown-as-backstop-not-quota

## 1. aidcp-cloud — 冷却值与语义

- [x] 1.1 <!-- aidcp-cloud b995207 --> <!-- 2026-07-17 deployed dev --> `src/risk/action-cooldown.ts`：`COOLDOWN_MS` 四值统一 `15_000`；文件头注释从「压稀节奏、更拟人、延缓配额触顶」**改写为兜底定位 + 不变量 + 15 的推导**（`60 ÷ MINUTE_BURST_CAP.like`）
- [x] 1.2 <!-- aidcp-cloud b995207 --> <!-- 2026-07-17 deployed dev --> `src/server.ts`（实际 `:2601-2609`，非文档写的 `:2547`）：`AIDCP_RESTART_QUIET_MS` 默认 `180_000 → 15_000`；注释同步改写（原立论已被 PG 持久化配额抽空）。两处魔数收敛为单个 `RESTART_QUIET_DEFAULT_MS` 常量（读默认 + 非法回落共用，防两处漂移）；`ActionCooldownGate` 的 `restartQuietMs` 选项文档也一并改写（那段旧立论原样活在那里）
- [x] 1.3 <!-- aidcp-cloud b995207 --> 单测：写死 2/5/10/30 的断言改为四动作统一 15s；**新增不变量回归**——对四动作断言 `COOLDOWN_MS[a] <= 60_000 / MINUTE_BURST_CAP[a]` 且 `<= 3_600_000 / HOUR_BURST_CAP[a]`，另加「15 的推导」与「分钟窗是唯一可能 binding 的窗口」两条前提断言（后者钉住 2.1「为什么只夹 perMinute」的算术前提）。**这几条测试就是不变量本身**（typecheck 抓不到，只能靠它）
      顺带修一条**被旧值掩盖的测试自身缺陷**：`remainingMs` 用写死的 `T0 + 60_000` 当窗口内探点，隐含假设「comment 冷却 ≫ 1min」；统一 15s 后该点已过窗，断言变成期望 `-45000`（生产代码正确地夹在 0）。探点改为窗口相对位置，并补一条「远过点也不为负」
- [x] 1.4 `npm run test:acceptance`（55/55）→ `npm test`（**2427 pass / 0 fail**，含新增回归）→ `npm run typecheck`（exit 0）
      🔴 红线已守：`typecheck` 未接 `| tail`，退出码取自 tsc 本身

## 2. aidcp-cloud — 主闸取值路径夹 cap（不变量 → 算术）

- [x] 2.1 <!-- aidcp-cloud b995207 --> <!-- 2026-07-17 deployed dev --> `src/config/quota-config-store.ts` 的 `windowQuotasFor`：`perMinute` 夹 `MINUTE_BURST_CAP[action]`。**单点夹**（`canDo` 与面板 catalog 读同一函数 ⇒ 显示＝生效，且覆盖已落库老行）
      🔴 **红线已守：只夹 `perMinute`，未夹 `perHour` / `daily`**——浏览行 `perHour=80` > `HOUR_BURST_CAP.view=60` **正在生效**（dev 库实测确认，见 2.3），夹了当场把浏览量从 80 砍到 60
      ⚠️ **顺带修一个隐形地雷（本 task 之外、但正是本文件）**：`cacheKey` 的分隔符在源码里嵌的是**裸 NUL 字节**（offset 2526），导致 git / grep **把整个文件当 binary**——`grep windowQuotasFor` 命中不到本文件（实装开场即撞：主闸取值路径搜不出来）、`git diff` 显示 `Bin 7483 -> 8680 bytes`（**本 change 那处红线敏感改动在 diff 里根本看不见**）。已改为等价转义 `\u0000`（运行时同一字符，全量测试与 typecheck 复跑通过），并留红线注释。**注**：本次提交的 diff 仍会显示 `Bin`（git 只要任一侧二进制就这么标，旧侧 NUL 在历史里），从下次起恢复文本
- [x] 2.2 <!-- aidcp-cloud b995207 --> 单测：`perMinute` 超 cap 被夹（like 6→4 / follow 5→1）；cap 内原样不动（夹只降不升）；**红线一防回归**——`perHour=80`（超 cap 60）与 `daily=300` 原样不被夹，且断言前置条件「80 确实超 cap」以防该测试哪天变成空转；**红线二防回归**——`dm_reply` / `view` / `join_group` 的 `perMinute` 不被夹（见 2.4）；另测「夹在取值口而非写路径」（库里原样留运营填的值、生效值被夹 ⇒ 回滚只需去掉那行夹、已落库行从不被改写）
      两条红线测试均已做**变异验证**（把 bug 改回去 → 当场红；修好 → 绿），不是摆设

- [x] 2.3 **部署前先探 dev 库** —— 已探，**门禁通过**：`quota_config` 共 9 行覆盖，**无任何 `per_minute` 超 cap** ⇒ 本 task 在 dev 上**零行为变化**。三条设计事实同时坐实：`normal` 档四个冷却动作确无覆盖行 ✓；`normal view per_hour=80` > cap 60 **正在生效** ✓（红线来源）；`normal view per_minute=4` ≤ cap 8 ✓（夹了也不动）
      偏离记一笔：原文「确认四个冷却动作无覆盖行」——`conservative comment` **有**覆盖行（1/1/1），但 `per_minute=1` = cap 1 ⇒ 不被夹、零行为变化，门禁的实质判据（无 per_minute 超 cap）仍成立。proposal 表格只声称 `normal` 档，故其表述无误
      ⚠️ 5.6 那条存疑数字**已被实测坐实**：`aggressive view per_hour=24`（daily=500 / per_minute=5），比 `normal` 档的 80 还慢 3.3 倍，确需运营核实

- [x] 2.4 <!-- aidcp-cloud b995207 修复 + b36acca 注释更正 --> **红线二：夹的作用域＝`COOLDOWN_ACTIONS`，MUST NOT 夹 `RISK_ACTIONS` 全集**（本条为实装期新增，propose 阶段未预见；由对抗性复核 4 个独立视角撞出、两名专职反驳者均推翻不了）
      **初版实装的真 bug（已修）**：夹无条件作用于全部 9 个动作，而 `MINUTE_BURST_CAP.dm_reply = 0` —— 那是「旧浏览曲线没有 dm_reply 语义」的**占位**、不是真爆发上限 ⇒ `Math.min(任何值, 0) = 0` ⇒ 运营在面板显式配的 dm_reply 额度被**永久压成 0**，而 `explain` 是 `count >= quota` 即拒 ⇒ `canDo('dm_reply')` 恒假 ⇒ **视频号入站回复静默停摆**。且 `dm_reply` 的三档 `DAILY_QUOTAS` 全为 0 ⇒ **`quota_config` 覆盖是它唯一的启用路径**，正是被夹掉的那条
      **下游没有任何一道闸救得回来**：`windowQuotasFor` 位于取值链**最上游**（`risk-controller.riskScaledQuotas` 从它取基准），慢启动 clamp 对视频号直接 early-return（`wechat_channels` 不在 `SLOW_START_PLATFORMS` 内）⇒ 它压根不参与、无从纠正上游夹出来的 0
      ⚠️ **实装期间 master 移动了**：复核发现该 bug 时，`risk-controller.ts:288-293` 尚有一条专为此开的 dm_reply 豁免（注释逐字写着「不能把运营明确配置的非零额度再次夹成 0」——**它正是「此处不该夹」的仓内既有判例**）；land 时 rebase 并入的 `780f104` 已用更干净的平台闸（`supportsSlowStart`）取代并删除了它。**结论不变、且更强**：判例没了，红线二成了唯一的防线。首版注释引用那条豁免、随 `b995207` 落到 master 后即成失效引用，已由 `b36acca` 更正为现行机制（纯注释、零行为变化）
      **这正是本 change 要根除的病、只换了个动作**（旋钮被焊死、无日志无告警），且是设计 §8 警告的「被『对称性』诱发的回归」——设计只提了**窗口轴**（别夹 perHour），我在**动作轴**上踩了同一个陷阱
      **修法**（＝复核提出的最小修法）：夹只作用于受冷却约束的动作；动作全集 `COOLDOWN_ACTIONS` 从 `COOLDOWN_MS` 的键**派生**并由 `action-cooldown.ts` 导出，`quota-config-store` 与不变量测试共用 ⇒ 将来加第五个冷却动作会自动纳入两处、不会漏
      🔴 **必须知道：全量测试对这个 bug 是瞎的**。`test/risk-cold-start-clamp.test.ts:192-207` 注入桩 `quotaProvider: { windowQuotasFor: () => override }`，**正好把被夹的那个函数替掉** ⇒ 初版 bug 在手时 `npm test` 仍 2424/0 全绿。别把「全绿」当这条路径的对账；新测试直连 store 才抓得到

## 3. aidcp（本仓）— spec 与台账

- [x] 3.1 `interaction-cooldown` spec delta——**最终为 MODIFIED ×5 + ADDED ×3**（原写 MODIFIED ×3 + ADDED ×2、proposal 头写 ADDED ×1，均低估；ADDED 第三条为实装期新增，见 2.4）。propose 阶段生成的 delta 有三处必须修正，`validate --strict` **全都抓不到**：
      ① 两条**新**要求（重启静默期、四条评论路径闸门表）被误置于 `## MODIFIED Requirements` 下，而主 spec 里并不存在它们 → 已移入 `## ADDED Requirements`
      ② MODIFIED「评论冷却前置到评估阶段」整段重写时**丢了 mandatory 例外段 + 「强制评论不被普通冷却否决」场景 + 「MUST NOT 进入撰写/人审」**——MODIFIED 是整条替换，归档即丢已声明行为，与 proposal「mandatory 例外保留」直接矛盾 → 已按主 spec 原文恢复，只改硬编码「30 分钟」
      ③ 漏了两条仍带旧值/旧语义的要求 → 补为 MODIFIED：「冷却时间戳在真实成功时落」（场景写死「后续 **2 分钟**内的 like 被抑制」，归档后会与 15s 直接矛盾）、「冷却闸只拦四类互动」（「附加只读**节奏闸**」＝被改判掉的旧定位 → 兜底闸）
      自检脚本已跑：主 spec 5 条要求 delta **全覆盖**、无旧秒数残留、每条 MODIFIED 的删除行都只是旧硬编码/旧理由
      ⚠️ **Purpose 本步填不了**：openspec delta **不支持** `## Purpose`（archive 目录里零先例；113 个 spec 中 110 个 Purpose 仍是 TBD）。历史上那 3 个填过的都是**在 archive 提交里手工写进主 spec** 的（如 `6235f07`）⇒ **Purpose 移到归档步骤执行**，见 4.4
- [x] 3.2 `comment-interaction` spec delta（例外理由句同源化）——已核 diff：**纯增补**，未丢原文任何行；`:81` Scenario 不动（新增一条场景，非改原场景）
- [x] 3.3 `interaction-appraisal` `:153` / `:156-157`（「跳过点赞冷却」）—— **核对后确认无需改**：三处提及冷却均**无秒数硬编码**，且理由与新语义一致（明写「该意图仍 MUST 经过 `RiskController.canDo('like')`」＝不跳主闸、「真实 `ok:true` 才落冷却」）。在此显式记一笔，别让下一个人以为漏了
- [x] 3.4 `openspec validate cooldown-as-backstop-not-quota --strict` → valid
      ⚠️ 记一笔：validate 对上述 ①②③ **全绿放行**（它不校验 MODIFIED 的目标要求是否真存在、也不校验整条替换是否丢内容）。**delta 正确性只能靠人肉对着主 spec 逐条 diff**，别把 valid 当对账
- [x] 3.5 tasks.md 回写 sha —— 两个提交均已 `merge-base --is-ancestor origin/master` 验证可达：
      `b995207`（主改动：四值 15s + 静默期 15s + 夹 cap + 测试 + NUL 转义）、`b36acca`（注释更正：失效的豁免引用 → 现行机制）

## 4. 部署与验收

- [x] 4.1 <!-- 2026-07-17 deployed dev --> 部署 dev —— 安全序列全过：`deploy-target dev --check` → 备份（`cloud.bak.20260717-165742.tar.gz` 4.9M + `.env.bak`）→ rsync（`--exclude .env/node_modules/.git`）→ restart → healthcheck。**无需回滚**
      healthcheck：服务 `active` / 8787 + panel 8090 均监听 / PG `select 1` 通 / 飞书长连接已建立（WSClient onReady）/ 上机核对三处改动均生效（冷却 15_000 ×4、`RESTART_QUIET_DEFAULT_MS = 15_000`、夹 cap 走 `COOLDOWN_ACTION_SET.has`）
      零行为变化已验：`quota_config` 仍 9 行、未被部署改动
      🔴 isales 红线已守：三进程（api / scheduler / worker）与 80 / 8000 端口部署前后原样
      ⚠️ 台账留痕：dev 上 cloud **不构建 dist、直接 `npx tsx src/server.ts` 跑源码** ⇒ rsync `src/` 即部署，无 build 步骤（别照 `dist/*.js` 的老假设去核对版本，那条路径根本不存在）
- [x] 4.2 dev 跑一天的三个验收信号 —— **已解耦登记到 `docs/real-machine-acceptance-backlog.md` 簇 97**（97.1-97.5），
      按本仓纪律「归档不 gate 在真机验收上，但真机项必须登记、不得随归档丢失」。三信号原文：
      `skip reason=cooldown` 趋零（**唯一能证伪本 change 的信号，仍有命中必须回头查**）／日总量向上限靠但不越过／
      `pacing_saturation` 频次上升（**主闸重新掌权的正信号，非故障**）
- [x] 4.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md` —— 新建**簇 97**（前置：dev 需真实浏览车队跑满
      **一整天且跨上海自然日**，因日窗是自然日硬清零、非滑动 24h）。含两条「别误判成冷却没生效」的良性现象（97.4）
      与运营核数项（97.6）
- [ ] 4.4 **归档时手工填写 `interaction-cooldown` 主 spec 的 Purpose**（自 `engagement-restraint` 归档日起逐字停留在
      `TBD - created by archiving change engagement-restraint. Update Purpose after archive.`）。
      **openspec delta 不支持 `## Purpose`**（archive 目录零先例；113 个 spec 中 110 个仍是 TBD），历史上填过的 3 个
      都是在 archive 提交里手工写进主 spec（如 `6235f07`）⇒ 只能在归档步骤做。Purpose 应写兜底定位：
      冷却＝只防意外爆发的兜底，数量单归风控配额主闸，「兜底必须比主闸松」为其存在前提


## 5. 登记 backlog（本 change 不做，但已挖出、必须留痕）

- [x] 5.1 静默期拒绝时日志打印「还需 0s」，与真冷却在日志里无法区分（`action-cooldown.ts` 的 `remainingMs` 无历史时返回 0）
      —— **注意它与 97.1 相互作用**：静默期拒绝也会记 `cooldown`，验收时别把它当成「15s 仍在 binding」的证据
- [x] 5.2 like/collect 失败的原地重试旁路不过主闸、也不过冷却（`role-dispatcher.ts` 重试段）——它证伪了「冷却是最坏形状唯一守门人」
- [x] 5.3 「收藏了但没点赞」：like 被拦时 collect 仍会发（循环对每个 action 独立判闸、无联动）——今天就有、与本 change 正交
- [x] 5.4 save/like 比例统一 15s 后会向上漂，系统内**无任何闸**在管这个比 —— 已并入 backlog 簇 **97.4(b)** 一起盯
- [x] 5.5 若未来要删 mandatory 冷却例外，**前置条件是冷却改成排队而非丢弃**（已写进 `interaction-cooldown` spec 的条件式不变量）
- [x] 5.6 **激进档浏览 `per_hour=24` 疑似把 240 打错** —— **已在 dev 库实测坐实**（`aggressive view: daily=500 / per_minute=5 / per_hour=24`，
      比正常档 80 还慢 3.3 倍）。已登记 backlog **97.6②** 请运营核实
- [x] 5.7 **（实装期新挖）源码里嵌裸 NUL 字节会让整个文件对 git / grep 隐形** —— 本次在 `quota-config-store.ts` 撞到并已修
      （改等价转义）。**同类风险仍在**：无任何机械手段阻止下一个人再嵌一个，`typecheck` / `validate` / 全量测试**全都抓不到**，
      只有「搜不到 / diff 显示 Bin」这种间接症状。若要根治，可加一条 CI 检查（源码目录禁裸 NUL）或 `.gitattributes`——本 change 不做
- [x] 5.8 **（实装期新挖）`openspec validate --strict` 不校验 spec delta 的正确性** —— 它对「MODIFIED 一条主 spec 里不存在的要求」
      「MODIFIED 整条替换时丢内容」均绿灯放行（本次三处全中，见 3.1）。**delta 只能靠人肉对着主 spec 逐条 diff**。
      可考虑加个脚本（比对 delta 的 MODIFIED/ADDED 与主 spec 实际要求集）——本 change 不做
- [x] 5.9 **（实装期新挖）桩注入会让测试对被桩掉的那条路径完全失明** —— `test/risk-cold-start-clamp.test.ts` 注入
      `quotaProvider: { windowQuotasFor: () => override }`，正好替掉本 change 要夹的那个函数 ⇒ dm_reply 那个 HIGH bug 在手时
      全量仍 2424/0 全绿（见 2.4）。**「全绿」≠ 该路径已对账**——本 change 不做，但值得作为通例记住

