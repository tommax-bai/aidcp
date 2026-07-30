# ⏸ 本轮不做（2026-07-30，用户裁定）

> **剩余任务已划出本轮范围，但本 change 未被废弃。** 立论仍然成立，缺陷仍然存在，只是不在这一轮做。
>
> 用户口径：**这些是此前 JS 侧没做完的功能，与「迁移到 Rust 引擎」这批工作没有关系**，
> 不应该混在这一轮里排期。
>
> **进度快照（划出时）：已做 0/23，剩余 23 项本轮不做。**
>
> **与「废弃」的区别**：本节不否定立论。下面每条未勾项都标了「本轮不做」，
> `- [ ]` 在这里表示「没做，本轮也不打算做」，**不表示这条已经不成立**。
> 重新排期时把本节与各条标注删掉即可，任务原文未改动。
>
> **MUST NOT 把本节读成「问题已解决」或「立论已作废」。** 该 change 描述的缺陷在生产上依然存在。

# Tasks — wechat-store-and-circuit

> 台账格式：每条完成后按 `<!-- <repo> <commit-sha> 备注 -->` 标注（部署后追加 `<!-- <date> deployed -->`）。
> **绝不编造 commit sha**：sha 必须取自**已推送**的提交（判据 `git merge-base --is-ancestor <sha> origin/master`）。

## 1. 前提重验（第一条，必须先做）

- [ ] **【本轮不做 2026-07-30】** 1.1 在当前 aidcp-cloud master 上重验本 change 每条发现的前提是否仍成立（文件/行号可能已漂移，按行为而非行号核对）。任一条已被他人修复或已失去前提 → 在本文件如实登记「已失效 + 依据」并跳过，**绝不为了勾选而重复实装**。
  - 复验基线（撰写时实测于 cloud master `c2f25c8`，四条全部成立）：
    - **H10**：`interaction-store.ts` 的 `noteSendOutcome` 中 `consecutive_failures=0, circuit_opened_at=NULL` 只在 `confirmed` 分支；`updateRuntimeControls` 的 UPDATE 字段列表**不含** `circuit_opened_at` / `consecutive_failures`；`send-orchestrator.ts` 两处门禁含 `controls.circuitOpenedAt !== null`；`interaction-internal-api.ts` 的 `publicControls()` 返回字段**不含**熔断相关字段。
    - **M4**：`ingestBatch` 中对每条 `direction==='inbound' && lifecycle==='active'` 的消息**无条件**执行 `UPDATE interaction_threads SET status='waiting_review'`，与「回复 job 是否真的新建（`ON CONFLICT (inbound_message_id) DO NOTHING` 是否 RETURNING 到行）」无关。
    - **M5**：`recoverStalledClassifyingJobs` 只在 `server.ts` 启动段被调用一次；30s 周期的 `drainInteractionRecovery` 只扫 `state='new'` 与 `state='queued'`。
    - **M6**：`purgeDueOffboards` 的 WHERE 硬性要求 `state='tombstoned'`；`tombstoned` 只由边缘回执路径写入。
  - [ ] 1.2 确认并行 change `wechat-send-failure-semantics` 是否已改动 `send-orchestrator.ts` 的门禁语义；若已改，登记其结论并据此调整本 change 的 2.2（避免两侧对「熔断态是否拒绝发送」的理解分叉）。

## 2. aidcp-cloud — H10 写熔断复位与透出

- [ ] **【本轮不做 2026-07-30】** 2.1 `updateRuntimeControls`：当本次请求把 `writePaused` 从 `true` 置为 `false` 时，在**同一条 UPDATE**（同一事务）内一并 `consecutive_failures=0, circuit_opened_at=NULL`。乐观锁版本校验语义不变；审计事件如实记录本次操作同时清除了熔断。
- [ ] **【本轮不做 2026-07-30】** 2.2 保持「熔断态拒绝发送」的门禁不变（属并行 change 的文件）。本条只需确认：清除熔断后再次发送不再被门禁拒绝，且 MUST NOT 出现「解除暂停返回 200、发送仍被拒」的界面-行为相反态。
- [ ] **【本轮不做 2026-07-30】** 2.3 `publicControls()`（`interaction-internal-api.ts`）与运行控制对外视图透出熔断状态：至少含「是否熔断」「熔断起始时刻」「连续失败次数」。字段命名与既有驼峰风格一致。
- [ ] **【本轮不做 2026-07-30】** 2.4 熔断跳闸时既有的 `write_paused=true` 副作用保留（跳闸即暂停写入），但**熔断本身**必须是可独立观测的状态，MUST NOT 与运营手动暂停混为一个布尔。
- [ ] **【本轮不做 2026-07-30】** 2.5 单测（克制）：① 熔断态下运营解除暂停 → 计数与时间戳双清零、后续发送门禁放行；② 版本冲突时不清熔断（409 路径无副作用）；③ `publicControls` 含熔断字段。

## 3. aidcp-cloud — M4 摄取不打回已处理会话

- [ ] **【本轮不做 2026-07-30】** 3.1 `ingestBatch`：把会话置 `waiting_review` 的条件收紧为「本次**确实新建了**回复 job」（即 `ON CONFLICT DO NOTHING` 真的插入了行）。`last_message_at` / `last_synced_at` 的推进照旧对所有入站消息执行——时间戳推进与状态回退是两件事。
- [ ] **【本轮不做 2026-07-30】** 3.2 单测：同一批次重复摄取（内容寻址批次 ID 因新增一条评论而变化、旧消息原样重来）→ 已 `ignored` / `escalated` / `replied` 的会话状态保持不变；新增的那条消息仍正常建 job 并把会话置待审。

## 4. aidcp-cloud — M5 分类中 job 周期恢复

- [ ] **【本轮不做 2026-07-30】** 4.1 `server.ts` 的 30s 周期恢复 `drainInteractionRecovery` 中，先执行一次卡住的 classifying 恢复（复用 `recoverStalledClassifyingJobs`，staleBefore 沿用启动段口径），再扫 new / queued。启动段那次调用可保留（幂等）。
- [ ] **【本轮不做 2026-07-30】** 4.2 确认 40s 盲区随之消失：部署重启前 40 秒内进入 classifying 的 job，最迟在重启后一个恢复周期内被拨回可重跑态，MUST NOT 永久停在「处理中」。
- [ ] **【本轮不做 2026-07-30】** 4.3 单测：一个 `classifying` 且 `updated_at` 早于阈值的 job，在周期恢复跑过后回到可重跑态且 version 递增；未超阈值的 classifying job 不被误动（避免打断正在跑的 AI 调用）。

## 5. aidcp-cloud — M6 云端清理与边缘回执解耦

- [ ] **【本轮不做 2026-07-30】** 5.1 解绑的**云端侧**内容清除（消息正文、附件元、草稿文本、参与者昵称/头像、会话标题）不再以「边缘已回执」为前提：到达 `purgeDueAt` 时，无论边缘是否回执，云端 SHALL 执行自己那份清除并把记录推进到终态。
- [ ] **【本轮不做 2026-07-30】** 5.2 边缘清理结果单独记账：边缘回执仍照常更新其自身状态与审计，但 MUST NOT 成为云端清除的阻塞条件。云端已清、边缘未回执的情形必须可区分地表达（审计 / 状态字段），不得表述为「边缘已清理完成」。
- [ ] **【本轮不做 2026-07-30】** 5.3 单测：offboard 请求到期而边缘从未回执 → 云端正文/昵称/头像/会话标题被清除、记录进终态；审计如实体现「边缘未回执」。

## 6. aidcp-console — 熔断与暂停分开渲染

- [ ] **【本轮不做 2026-07-30】** 6.1 运行控制类型（`src/types/interactionReplyConfig.ts`）补熔断字段，与 cloud 的对外视图逐字对齐（枚举/字段漂移会白屏）。
- [ ] **【本轮不做 2026-07-30】** 6.2 视频号回复设置页：熔断态下 MUST NOT 显示为「允许写入」。写总闸开关与熔断状态分开呈现；熔断中明确告知运营「解除写暂停即会清除熔断并恢复发送」这一恢复路径。
- [ ] **【本轮不做 2026-07-30】** 6.3 单测：熔断态 + `writePaused=false` 的快照 → 页面不出现「允许写入」的单一结论，熔断提示可见。

## 7. 验证与收口

- [ ] **【本轮不做 2026-07-30】** 7.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
- [ ] **【本轮不做 2026-07-30】** 7.2 console：`npm test` → `npm run typecheck` 全绿。
- [ ] **【本轮不做 2026-07-30】** 7.3 合回各自 master（rebase 后 ff，遇 non-ff 一律 rebase 重来、绝不 force）。
- [ ] **【本轮不做 2026-07-30】** 7.4 部署 dev（按 CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。
- [ ] **【本轮不做 2026-07-30】** 7.5 桩验不了的转真机：熔断跳闸→运营解除→真发送恢复的端到端闭环、解绑 30 天兜底的真实到期路径，登记到 `docs/real-machine-acceptance-backlog.md`（并入视频号真机簇）。
- [ ] **【本轮不做 2026-07-30】** 7.6 `openspec validate wechat-store-and-circuit --strict` 通过后归档。
