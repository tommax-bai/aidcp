> **实装前必读**
> 1. 本 change **纯云端单边**——不改边缘、不改 console、不碰协议、不碰 DB 迁移。若你在改 `protocol.ts` / `join-executor.ts` / 任何迁移，**停手**：范围蔓延了。
> 2. **判据轴是 `clicked`，绝不是 `reason`**。两个 pending 返回点 reason 字符串**相同**但语义相反：`join-executor.ts:702`（点击**前**发现「之前就已待审批」，`clicked:false`，**不该计**）vs `:759`（点击**后**确认 pending，`clicked:true`，**该计**）。按 reason 判 = 过计。
> 3. 本 change 会让日限**第一次真正生效**。这是**目的**，不是回归（见 4.1）。

> **【实装收口 2026-07-17】最终范围比提案窄一半：只做 §1（记账闸），**不做 §3（统一分子）**。**
> §3 的前提（design D3：「风控流水的日计数**恰好就是**抵达 FB 的入群动作数」）在实装期被**证伪**——记账函数内部会再过一次判定并静默丢数，那个计数器只是**下界**。照 §3 改会让当天真实点击从 3 涨到 5（详见 design D3 的实装期证伪段与 5.7）。**最终 diff = `src/comm/handler.ts` 一个文件 + 一个新测试文件。**

## 1. aidcp-cloud — 记账闸按 `clicked` 放行 join_group

- [x] 1.1 读 `src/comm/handler.ts:558-560` 现文，确认 join_group 专属子句 `(result.clicked === true && result.reason !== 'already_member' && result.reason !== 'observation_only')` **已经是正确判据**。本 change 是**把它从 `result.ok` 的合取下解出来**，不是新写判据（design D1）。
  <!-- 已坐实：该子句 2026-07-09 由 commit 0a0f1ae7 加入，与 join_group 同批落地。今天的闸是 `ok` **且** `clicked` 两者都要；因 `ok` 是第一个合取项且会短路，clicked 那一条**只能减、永远不能加**——它作为「放行判据」今天不可达。 -->
- [x] 1.2 改条件结构：join_group 走 `<join子句>`（不再要求 `ok`）；其余动作走 `result.ok && <既有条件>`，**逐位不变**。改完复核 `like`/`collect`/`follow`/`comment`/`comment_like` 的放行条件**一字未动**。
  <!-- aidcp-cloud 293c4e5 `result.ok &&` → `(result.ok || result.action === 'join_group') &&`，其余三个合取项逐字未动。 -->
  <!-- **本 change 唯一真正危险的地方**：`ok` 是**六个动作共用**的第一个合取项。提案原话「把判据从 ok 换成 clicked」若照字面执行 = 整条删 `result.ok &&` = 失败的点赞/收藏/关注/评论/评论赞全被记成真互动，**直接踩「绝不静默假成功」红线，且 typecheck 一声不吭**。已按动作收窄，并补两条零回归绊线测试钉死（5.6）。 -->
- [x] 1.3 **不新增任何 reason 分支**。design D1 的表格已证：`clicked` 这条轴把边缘全部返回天然分对了边（点前 pending / already_member / shadow / 导航失败 全是 `clicked:false` ⇒ 自动继续不计）。
  <!-- 零 reason 分支。附带坐实：D1 表格漏了**第 5 个 `clicked:true` 返回点**（边缘 `join-executor.ts:763` 的 `join_failed` / `post_not_confirmed_slow`），两者改后都开始计——在「尝试」轴上是对的，但 `post_not_confirmed_slow` 是可重试瞬态、云端会重新下发并**重新真点**，故一个群可能烧掉 N 格配额。已写入 design 修正表。 -->

## 2. aidcp-cloud — 排查 `interaction.occurred` 的全部订阅者（**本 change 最可能出事的地方**）

- [x] 2.1 逐个列出 `interaction.occurred` 的订阅者（起点：`server.ts:1391` / `:1412` / `:1424` 一带 + 全仓 grep），**逐个确认**没有消费者会把「计了配额的待审批加群」误当成功加群。结论写进 PR 描述。
  <!-- 全量排查（含 grep 找不到的那类）。实际订阅者：`server.ts:1369` 一个具名订阅者内含 5 个分支（:1383 风控记账 / :1401 likedNoteStore / :1408 精选 markBotAction / :1429 risk_interactions 去重 / :1438 展示账本），后四个各自都按动作过滤（like/collect 或四类白名单）⇒ 均不受 join_group 影响。 -->
  <!-- **漏网的那个（提案完全没提）**：`src/panel/panel-ws.ts:135` 用 `onAny()` **通配订阅全部事件**、无动作过滤、无 targetId 要求，序列化后广播给已认证的后台浏览器。**全文 grep `interaction.occurred` 永远找不到它**。核后判定良性：它是原始事件中继，console 侧无 join_group 专属渲染、不构成「报成已加入」，故不改。教训记 design：**「grep 事件名 = 审计完毕」在本仓是错的。** -->
- [x] 2.2 确认展示账本**天然免疫、无需新增防护**：join_group 的 `targetId` 已被刻意置 `undefined`（`handler.ts:571-576`），入 `interaction_feed` 要求 targetId 为真且动作在四类白名单内（`server.ts:1422-1427`）⇒ 双重挡在外（design D6）。**若发现并非如此，停手上报**——那说明 D6 的前提错了，设计要重来。
  <!-- **前提两半均逐字属实**（实际行号 handler.ts:572-577 / server.ts:1438-1442），展示账本确实双重挡在外，已加测试钉住（emit 不带 targetId）。 -->
  <!-- **但 D6 的结论错了，已停手上报并取得裁决**：真正会被操作员看见的那一处**根本不走 `interaction.occurred`**——后台仪表盘按账号的用量表**直接读 `risk_counters`**（`panel-store.ts:389` → `/api/dashboard/summary` → console `AccountTotalsTable.tsx:35-53` 按 `RISK_ACTIONS` 铺列，`join_group` 标签「加群」，渲染 `用了/上限`）。沿「订阅者」这条轴审计永远审不到它。**裁决（用户 2026-07-17）：不改前端标签**——「在不同 tab 下代表的含义就是不一样」，那张表主语是配额用量，「加群 2/3」= 「加群配额用了 2 格」，新语义下是真话。已在 spec 补一段 + 一个 scenario 把「用量面 vs 成员面」的区分写死，防止下一个人照 D6 的误读去「修」前端。 -->
- [x] 2.3 确认 `curated-content-store.markBotAction`（`:781`）只认 `like`/`collect` ⇒ 不受影响。
  <!-- 属实。**路径提案写错**：实际在 `src/cache/curated-content-store.ts:784`，**不是** `src/comment-agent/`（照提案路径找会扑空）。 -->

## 3. aidcp-cloud — 统一分子

> **【整节不做 —— 前提被证伪，2026-07-17】** 详见 design D3 的实装期证伪段。摘要：`RiskController.record()` 在写计数前**再过一次 `canDo()`**，不过就静默丢弃（`risk-controller.ts:175-186`）⇒ 风控日计数的真实语义是「记账时策略恰好还允许的动作数」，是**下界**，不是「抵达平台的动作数」。加群小时配额算出来是 **1**，而手动 `/comment --join` **按产品裁决刻意绕过配额闸**、其回执却照走记账闸（`skipRiskRecord` 只豁免 `comment`）⇒ 运营一小时内手动加 3 个群全部真加进去，计数器只记 1。照 3.1 换分子后预筛读到 1<3 放行 ⇒ 自动加群再打 2 次 ⇒ **当天真实点击 5 次 / 预算 3**；而改之前预筛读成员账本=3 直接挡住 ⇒ 3 次。**认知反转：那两个分子是同一个量的两个独立下界，两闸 AND = 取较紧的那个；「统一」实为把紧的换成松的。** 已改 spec 的相应 MUST（原文「每个闸必须读同一个分子」本身是错的，它禁掉的正是这道保险）。

- [ ] 3.1 ~~`src/server.ts:3434`：调度预筛分子从 `facebookGroupMembershipStore.countJoinedToday` 改接**风控流水日计数**（与 `:3198` 的 `canJoin` **同源**）（design D3）。~~
  <!-- **刻意不做**（非遗漏）。实装期确曾改完并全绿（acceptance 55/55、全量 2401、typecheck 干净），随后被对抗性复核以上述场景证伪、**整条撤回**。绿的测试没能抓到它——因为它是个**语义**错误，不是逻辑错误。 -->
- [x] 3.2 **`joinDailyCap`（`:3435-3438`）一个字不动**——它**兼作启用闸**（`if (!facebookGroupJoinAutoEnabled() && !facebookGroupJoinShadow()) return 0;`），改它会顺手开关自动加群（design D5）。
  <!-- 一字未动（3.1 撤回后整个 server.ts 零 diff）。 -->
- [x] 3.3 `countJoinedToday`（`facebook-group-store.ts:912`）**保留不动**。若因 3.1 失去全部调用点 ⇒ **显式登记、不顺手删**（design D4：它是「今天成功加进几个群」的正确度量，pending 回查一开工就要用）。结论写回 design Open Question 1。
  <!-- 保留不动、且**根本没失去调用点**——3.1 撤回后它仍是调度预筛的分子、仍在生产路径上载荷。实装期确曾摘掉并坐实「全仓归零」（唯一生产调用点即 server.ts 那一处；`test/content-scheduler.test.ts:401/:434` 只注入自己的桩、从不碰 store 方法），随 3.1 一并撤回。已写回 design Open Question 1。 -->
- [x] 3.4 **绝不**改成「成员账本也数 pending」。`markJoining`（`group-store.ts:741`）在**点击之前**就写 `last_attempt_at = now()` ⇒ 导航/登录失败也会被数进去 ⇒ **过计**（design D3 备选，已否决）。
  <!-- 未做，成员账本零改动。 -->

## 4. 运营预期与安全红线

- [ ] 4.1 **部署前向运营打招呼**：日限将第一次真正生效，加群次数会下降——**这是之前超发被纠正，不是 bug**。若真的不够用，正确动作是评估日限**数值**（另一个问题），**绝不是**把分子改回去。
  <!-- **未做 —— 需人来做，不是代码任务**。dev 已于 2026-07-17 部署（默认授权），此项**仍欠**：需向运营口头/群内说明「加群变少 = 之前超发被纠正」。**另一个必须一起讲的**：`post_not_confirmed_slow` 重试会真点多次（见 1.3），FB 群页渲染慢时配额消耗比预期更快。**OL 上线前必须先完成此项。** -->
- [x] 4.2 `AC-RISK-*` 全过（安全红线：绝不自残、被禁 `record` 返 false）。本 change 动的正是记账闸，**这组断言是主防线**。
  <!-- `test:acceptance` 55/55 全过（含 AC-RISK-*）。坐实：AC-RISK-* 四条都在 `test/acceptance/risk-guard.test.ts`，只 import RiskController、测 record() 自身语义，从不碰 join_group / handler / 事件总线 ⇒ 本 change 不该动它们，也确实没动。 -->

## 5. 测试

<!-- **贯穿全节的实装期发现**：记账闸**里没有任何 record 调用**——它只决定 `emit('interaction.occurred')`；真正的 +1 在 `server.ts:1369` 的订阅者里（引导期接线，单测无缝可进）。故本节全部断言压在 **emit 决策**这一层，「日计数真的 +1」只能由真机坐实（6.4）。**「emit ≠ +1」不是措辞问题**：`record()` 内部还会再过一次 `canDo`（正是 §3 被证伪的根因）。 -->

- [x] 5.1 点后 pending（`clicked:true, ok:false, reason:'pending'`）⇒ 风控 join_group 计数 **+1**；**且不产生任何成功加群记录**、不进展示账本。
  <!-- `test/handler-join-quota.test.ts`：断言 emit 一条 join_group（含 accountId）+ 断言 `targetId === undefined`（⇒ 展示账本双重挡在外）。**偏离**：断言的是 emit，非计数器 +1（seam 见上）。 -->
- [x] 5.2 点前已 pending（`clicked:false, reason:'pending'`）⇒ 计数 **不变**。**与 5.1 reason 字符串相同、结果相反**——这一对是本 change 的核心断言。
  <!-- 已覆盖，两条测试 reason 逐字相同（'pending'）、仅 clicked 相反、结果相反。 -->
- [x] 5.3 `already_member`（`clicked:false`）/ shadow `observation_only` ⇒ 计数不变。
  <!-- 已覆盖。另加一条**防御性**断言：`observation_only + clicked:true`（谎称点过）仍不计——理由见 design Open Question 2：影子模式的安全**全靠云端上游两处 if(shadow) 守着，边缘对影子模式一无所知、没有能力拒绝点击**，边缘测试/typecheck/两份 protocol.ts 都抓不到。 -->
- [x] 5.4 点后 joined（`clicked:true, ok:true`）⇒ 计数 +1 **且**成功账本 +1（**今天的行为逐位不变**）。
  <!-- emit 侧已覆盖（成功账本由边缘 verdict 驱动、不经本闸，零改动）。 -->
- [ ] 5.5 **只下发、无边缘回执** ⇒ 计数不变（红线：下发是意图不是既成事实，spec:27 的「MUST NOT 凭下发即记」原样成立）。
  <!-- **未加测试 —— 结构上无可测之处**：记账闸只挂在 `action.completed` 分支上，「只下发」这条路径**根本到不了这个闸**。为它写测试等于断言「没调用就没发生」，是套套逻辑、抓不到任何回归。红线由结构保证而非断言保证，如实记此。 -->
- [x] 5.6 **其余动作零回归**：`like`/`collect`/`follow`/`comment`/`comment_like` 在 `ok:false` 时仍**不计**。
  <!-- 两条循环绊线（五个动作 × ok:false 不计 / ok:true 照计）+ 一条 already_followed 仍不计。**这是防 1.2 那颗雷的主绊线**：既有测试只覆盖 `like` 一个动作（`test/handler-attribution.test.ts:63`），另外四个动作此前**无任何守卫**。 -->
- [ ] 5.7 **一个分子**：调度预筛与 `canJoin` 对同一账号读到**同一个数**。
  <!-- **随 §3 一并作废**：结论已反转为「两个独立下界、两闸 AND 取较紧」，「同一个数」不再是目标，而是**被明确禁止**的（会开倒车，见 §3 头注）。spec 中相应 MUST 与 scenario 已改写。 -->

<!-- 测试真实性验证（防假绿）：把 handler.ts 改动 stash 掉后单跑本文件 → **12 条里恰好 3 条红**（正是编码新行为的那 3 条：点后待审批计入 / 不进展示账本 / group.join 归一后同判），9 条零回归绊线两边都绿。⇒ 新断言钉的是真行为，绊线钉的是真·未变行为。 -->

## 6. 验证与部署

- [x] 6.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序照 CLAUDE.md §4）。**注意**：`npm run typecheck | tail` 的退出码是 tail 的、会假绿——直接跑、看退出码。
  <!-- acceptance 55/55、全量 2408 中 2401 pass / 0 fail / 7 skipped、typecheck exit 0。**那条坑当场兑现**：首次 typecheck 真的 exit 2（新测试签名太松），正因为直接跑看退出码才抓到。 -->
- [x] 6.2 提交 + push cloud master（commit message 末尾带 `Co-Authored-By`）。
  <!-- aidcp-cloud master `293c4e5`（经 `scripts/land-change`：fetch + rebase 到 5ccd05b → 全量绿 → ff 推送 → 自动清理 worktree）。sha 已核 `git merge-base --is-ancestor 293c4e5 origin/master` 通过。 -->
- [x] 6.3 部署 dev（安全序列照 §5：`scripts/deploy-target dev --check` → ECS 先备份 → rsync `--exclude .env --exclude node_modules --exclude .git` → restart → healthcheck）。**无 DB 迁移**、**无需出安装包**。**红线**：绝不碰同机 isales。
  <!-- 2026-07-17 deployed dev。备份 `cloud.bak.20260717-154048.tar.gz`（4.9M）+ `.env.bak.20260717`。 -->
  <!-- **部署前探 ECS**：近 1h 有 292 个文件被改（并发方 15:08 刚部署过）；比对 md5 坐实 ECS 上的 handler.ts **恰等于我这个提交之前的 master**（5ccd05b）⇒ 我的改动干净地只叠一个提交上去，未覆盖他人工作。 -->
  <!-- **未从共享主 checkout 走**（当时其中有别的 session 撒下的残渣文件 `1`，且正处多任务并行）：按 CLAUDE.md §6 用 `git archive 293c4e5` 出干净快照后 rsync。本批不动 `package.json` ⇒ 无需 `npm ci`。 -->
  <!-- healthcheck 绿：service active、8787 边-云 ws 监听、8090 面板 API 监听、PG 锚点缓存就绪、飞书长连接已建立、「事件订阅已建立（RiskController）」。isales 未触碰。 -->
- [ ] 6.4 dev 上真发一次入群申请并停在待审批，坐实风控日计数 +1（**不是只在单测里成立**）。
  <!-- 真机项 → backlog 簇 90（见 7.2）。**这条不可省**：单测只能断言 emit，「emit → record → +1」那一跳全在引导期接线里，桩测无缝可进。 -->

## 7. 回写与收口

- [x] 7.1 本文件按 §6 用 HTML 注释标 `[x]` + commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha **必须取自已推送的提交**（判据：`git merge-base --is-ancestor`，不是 `cat-file`）。
  <!-- aidcp-cloud 293c4e5 · 2026-07-17 deployed dev -->
- [x] 7.2 真机项登记 `docs/real-machine-acceptance-backlog.md` **簇 90**：发出 N 个入群申请（含待审批）后日计数 = N 而非批准数；额度耗尽后调度闸不再起加群。
  <!-- 已登记簇 90（共享 FB 真机环境，同簇 82/88/91）。**同时修正了簇 90 既有的 90.5**——它的原验收判据「客户端说『申请加入…等待管理员通过』时云端**不**记 join_group」已被本 change 推翻，不改会让真机验收把正确行为当 bug 报回来。 -->
- [x] 7.3 `openspec validate fb-join-quota-counts-attempts --strict` 通过。
- [x] 7.4 design 的 Open Question 1（`countJoinedToday` 是否还有调用点）与 2（shadow 模式是否恒 `observation_only`）结论写回 design。**若 Q2 发现 shadow 下存在 `clicked:true` 路径 ⇒ 那是独立 bug（影子模式点了真按钮），当场上报、不绕过。**
  <!-- 两条均已写回 design。Q1：问题作废——它根本没被摘掉（3.1 撤回）。Q2：**问题本身问错了地方**——`AIDCP_FB_GROUP_JOIN_SHADOW` **在边缘仓根本不存在**，影子模式纯粹是云端调度器旗标，边缘对它一无所知。答案是「恒 observation_only/clicked:false」，**不是独立 bug、无停手条件**；但由此暴露的隐患已记 design：边缘既然不知道影子模式开着，就**没有能力拒绝点击**，整个不变量只靠云端点击调用点上游那两处 `if (shadow)` 守着，边缘测试/typecheck/两份 protocol.ts 全抓不到。已补一条防御性断言兜底（5.3）。 -->
