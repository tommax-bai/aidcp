> **实装前必读**
> 1. 本 change **纯云端单边**——不改边缘、不改 console、不碰协议、不碰 DB 迁移、不碰配额数值。若你在改 `protocol.ts` / `quotas.ts` / `risk-state-machine.ts` / 任何迁移，**停手**：范围蔓延了。
> 2. **求值顺序是本 change 最容易写错的一行**：`canDo` 依赖计数器。**必须先取判定、再写入**。先写后判 ⇒ 刚写的这笔把自己算进去 ⇒ 撞顶那一次的返回值从 `true` 翻成 `false`（见 1.2）。
> 3. **`AC-RISK-*` 必须零改测试全过**。**任何一条需要改测试才能过 ⇒ 设计走错了，停手上报。** 这不是形式要求：已用执行证明过新语义下 4/4 原样全过（design D2）。
> 4. **别把这个 change 写成「求红线的例外」**。红线管的是**状态机**；`decouple-quota-hit-from-risk` 删掉自残时**把这句空壳留在了原地**，本 change 是把那场停在最后一行的拆迁做完。

## 0. 实装前必须先要到的裁决（**阻塞 3.x 与真机预期，不阻塞 1.x/2.x**）

- [ ] 0.1 **手动加群该不该吃自动预算？**（design Open Question 1）本仓对「操作员全权」有**两套互相矛盾的实现**：手动 `/comment` **根本不调 record**（`server.ts:1385` `skipRiskRecord`，刻意且有据）；手动 `/comment --join` 绕过预闸却照样把回执送进 record。`skipRiskRecord` 硬绑 `evt.action === 'comment'`，join 永远够不着。**若裁决是「不该吃」⇒ 正确修法是给 join 补一条豁免（本 change 的反面）**；本 change 仍需要（缝 2/3/4 依旧丢真实数），但真机预期小一圈。**两条不互斥**——可以「手动 join 豁免记账」且「凡进了 record 的就如实写」。**没要到裁决前不要写 3.x 的真机预期。**

## 1. aidcp-cloud — 记账只记既成事实

- [ ] 1.1 `src/risk/risk-controller.ts:179-191`：`record()` **无条件写入**计数 + 持久化，**返回值语义逐字不变**（被 `canDo` 拒时仍返 `false`）。改的是副作用，不是答案。
- [ ] 1.2 **求值顺序**：`const allowed = this.canDo(action);` **在写入之前**取，写完返回 `allowed`。加一条专门的测试钉死：**撞顶那一次仍返 `false`，且该次计数已写**（先写后判会让它返 `true`）。
- [ ] 1.3 **不碰** `canDo` / `explain` / `effectiveQuotas` / 状态机 / 配额数值。改完复核 `explain()` 的返回集**一字未动**。
- [ ] 1.4 更新 `record()` 上那段注释——它现在说「被拒只返 false（**canDo 已拦住动作**）」，**那个括号里的假设正是本 change 要拆的**（手动绕闸的裁决比这句注释还早）。写清新契约：返回值答「在不在策略内」，计数器答「发生过没有」。

## 2. aidcp-cloud — 同病第二处（**必须与 §1 同批，否则出真实重复计数**）

- [ ] 2.1 `src/interactions/interaction-inbox-service.ts:94-108`：微信入站回复在 `status === 'confirmed'`（**平台已确认发出**）时 `claimRiskRecord` → `record` → 被拒则**释放占位**。§1 之后写入已经发生，占位若仍释放 ⇒ **重放会再写一次 ⇒ 真实重复计数**。改为**只在真抛错时释放**（判据从「返回值是不是 false」改成「有没有抛」）。
- [ ] 2.2 `interaction_risk_record_total{status:'denied'}` **含义变了**：从「没记下」变成「记下了、但超策略」。显式登记（改注释 / 指标说明），别让读盘的人按旧义读。顺带：`denied` 与 `failed` 今天**收敛成同一种处理**、下游分不出「策略拒绝」与「PG 抛错」；改后 `denied` 分支消失，`failed` 只剩真故障 ⇒ 语义更干净。
- [ ] 2.3 **微信入站是活路径，必须单独跑测试**。`dm_reply` 三档配额都是 `0` ⇒ `canDo('dm_reply')` **恒 false**（`0 >= 0`）⇒ 今天每条已确认回复都被丢。改后计数器**首次**从 0 累加。坐实：`0` 是**占位而非真上限**（`quota_config` 覆盖是唯一启用路径）⇒ `canDo` 仍恒 false、门不变、**预期无行为变化**（design Open Question 2）。**若发现并非如此，停手上报。**

## 3. aidcp-cloud — 节奏告警改读 `explain()`（行为逐位不变）

- [ ] 3.1 `src/server.ts:1394` 一带：告警从 `!recorded` 改挂到**写入前的一次 `explain()`**。spec 那条要求（`spec:146`）**本来就是按 `explain()` 的 reason 措辞的**，且现码 `:1395` 当场就在重算它 ⇒ 行为逐位相同，成本一行。
- [ ] 3.2 **别把「保住这个告警」抬成设计约束**——它今天已经很脆：`:1395` 是第二次独立求值、窗口在滑，滑走就 `reason=undefined`、**本来就静默不发**；P2、20min 冷却去重、自陈「是提示、不是阻断」；**手动 `/comment` 早就完全不发它**（`skipRiskRecord` 跳过整块）⇒「运营绕闸把它弄瞎」是**已被接受的既有行为**。

## 4. 运营预期与安全红线

- [ ] 4.1 **部署前向运营打招呼**：**所有动作**的计数器都会变大（**变准**）⇒ 各闸更早拒绝，系统整体更保守。**这是目的，不是回归**。若真的过紧，正确动作是评估**配额数值**，**绝不是**把丢数改回去。
- [ ] 4.2 `AC-RISK-*` **零改测试全过**（design D2 已用执行证明可行）。**要改测试才能过 = 停手。**
- [ ] 4.3 复核**方向性**：计数器只增（`sliding-window-counter.ts:26` 只 push）、闸为 `count >= quota → deny` ⇒ 诚实记账**只可能更早拒绝**。**逐个确认没有任何路径因此放行今天会挡住的动作**——`view` 是唯一需要单独想的（见 5.5）。

## 5. 测试

- [ ] 5.1 **撞顶仍返 false，且该次已记**（1.2 的求值顺序）——本 change 最容易写反的一条。
- [ ] 5.2 **被限（`restricted` / `frozen`）时计数照写**、返回仍 `false`、**状态机纹丝不动**（`status` / `signal_count` / `last_signal_at`）。
- [ ] 5.3 **紧窗口的拒绝不得污染松窗口的账本**：小时配额 1、日配额 3，真实发生 3 次 ⇒ **日计数 = 3**（今天 = 1）。**这是「预算被打穿」那条的直接断言。**
- [ ] 5.4 **微信已确认回复被记且占位不释放**（§2）；重放不产生重复计数。
- [ ] 5.5 **`view` 记账后点赞比例规则真正生效**：`likeRatioAllowsNextLike()` 有 `if (views < minViewsForLikeRatio) return true;` ⇒ **view 被少记会跌破阈值、整条规则被跳过 ⇒ 今天更宽松**。诚实记 view 后该规则应真正开火（仍是收紧方向）。
- [ ] 5.6 **节奏告警行为不变**（§3）：突发窗饱和仍发、日窗饱和仍静默。
- [ ] 5.7 **零回归**：正常在额度内的动作，计数与返回值**逐位不变**。

## 6. 验证与部署

- [ ] 6.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`。**`typecheck | tail` 的退出码是 tail 的、会假绿——直接跑、看退出码**（上个 change 当场中过）。
- [ ] 6.2 提交 + push cloud master（末尾带 `Co-Authored-By`）。
- [ ] 6.3 部署 dev（安全序列照 §5：`deploy-target dev --check` → **先探 ECS 现状**（近 1h mtime + md5 对 master，防撞并发部署）→ 备份 → rsync `--exclude .env --exclude node_modules --exclude .git` → restart → healthcheck）。**多任务并行场景下从 `git archive <sha>` 出干净快照走，绝不从共享工作区 rsync。** 无迁移、无需出安装包。**红线**：绝不碰同机 isales。
- [ ] 6.4 **真机核 `view` / 浏览节奏是否更早撞窗**（design D5 + Open Question 3）——**本 change 影响面最大、最可能被当回归报回来的一项**。
- [ ] 6.5 **真机核加群**：运营一小时内手动加 3 个群（全部真点）⇒ 日计数 = 3（今天 = 1）；随后自动加群**不再多打 2 次**。**这是本 change 的正面验收。**（若 0.1 裁决为「手动不吃预算」，此项改为：核缝 2/3/4——飞行途中状态翻转的那次仍被记下。）

## 7. 回写与收口

- [ ] 7.1 tasks 标 `[x]` + commit-sha（`<!-- <repo> <sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`）。sha **必须取自已推送的提交**（判据 `git merge-base --is-ancestor`）。
- [ ] 7.2 真机项登记 `docs/real-machine-acceptance-backlog.md`（加群项与簇 90 共享 FB 环境；`view` / 浏览节奏项按实际环境归簇）。
- [ ] 7.3 `openspec validate risk-record-actuated-facts --strict` 通过。
- [ ] 7.4 design 的三个 Open Question 结论写回 design。
- [ ] 7.5 **登记（本 change 不修）**：① **`publish` 从不进 `record()`**——全仓零调用点，而 `record()` 是 `risk_counters` 唯一写入者 ⇒ **发布计数器恒 0、发布日配额是装饰品**；后台早已绕开它（`panel/types.ts:381` 注释自陈 publish 键用 `publish_log` 真实数覆盖同名键）——**有人把显示修好了，把计数器留在死地**。**这比本 change 的病更大**（不是回执被丢，是根本没有回执），值得单独 propose。② **`view` 在手动 `/comment` 路径上无预闸**（`comment-scheduler` 读帖不过 `explainView`，`skipRiskRecord` 只覆盖 `comment`）。
