> **实装前必读**
> 1. 本 change **纯云端单边**——不改边缘、不改 console、不碰协议、不碰 DB 迁移。若你在改 `protocol.ts` / `join-executor.ts` / 任何迁移，**停手**：范围蔓延了。
> 2. **判据轴是 `clicked`，绝不是 `reason`**。两个 pending 返回点 reason 字符串**相同**但语义相反：`join-executor.ts:702`（点击**前**发现「之前就已待审批」，`clicked:false`，**不该计**）vs `:759`（点击**后**确认 pending，`clicked:true`，**该计**）。按 reason 判 = 过计。
> 3. 本 change 会让日限**第一次真正生效**。这是**目的**，不是回归（见 4.1）。

## 1. aidcp-cloud — 记账闸按 `clicked` 放行 join_group

- [ ] 1.1 读 `src/comm/handler.ts:558-560` 现文，确认 join_group 专属子句 `(result.clicked === true && result.reason !== 'already_member' && result.reason !== 'observation_only')` **已经是正确判据**。本 change 是**把它从 `result.ok` 的合取下解出来**，不是新写判据（design D1）。
- [ ] 1.2 改条件结构：join_group 走 `<join子句>`（不再要求 `ok`）；其余动作走 `result.ok && <既有条件>`，**逐位不变**。改完复核 `like`/`collect`/`follow`/`comment`/`comment_like` 的放行条件**一字未动**。
- [ ] 1.3 **不新增任何 reason 分支**。design D1 的表格已证：`clicked` 这条轴把边缘全部返回天然分对了边（点前 pending / already_member / shadow / 导航失败 全是 `clicked:false` ⇒ 自动继续不计）。

## 2. aidcp-cloud — 排查 `interaction.occurred` 的全部订阅者（**本 change 最可能出事的地方**）

- [ ] 2.1 逐个列出 `interaction.occurred` 的订阅者（起点：`server.ts:1391` / `:1412` / `:1424` 一带 + 全仓 grep），**逐个确认**没有消费者会把「计了配额的待审批加群」误当成功加群。结论写进 PR 描述。
- [ ] 2.2 确认展示账本**天然免疫、无需新增防护**：join_group 的 `targetId` 已被刻意置 `undefined`（`handler.ts:571-576`），入 `interaction_feed` 要求 targetId 为真且动作在四类白名单内（`server.ts:1422-1427`）⇒ 双重挡在外（design D6）。**若发现并非如此，停手上报**——那说明 D6 的前提错了，设计要重来。
- [ ] 2.3 确认 `curated-content-store.markBotAction`（`:781`）只认 `like`/`collect` ⇒ 不受影响。

## 3. aidcp-cloud — 统一分子

- [ ] 3.1 `src/server.ts:3434`：调度预筛分子从 `facebookGroupMembershipStore.countJoinedToday` 改接**风控流水日计数**（与 `:3198` 的 `canJoin` **同源**）（design D3）。
- [ ] 3.2 **`joinDailyCap`（`:3435-3438`）一个字不动**——它**兼作启用闸**（`if (!facebookGroupJoinAutoEnabled() && !facebookGroupJoinShadow()) return 0;`），改它会顺手开关自动加群（design D5）。
- [ ] 3.3 `countJoinedToday`（`facebook-group-store.ts:912`）**保留不动**。若因 3.1 失去全部调用点 ⇒ **显式登记、不顺手删**（design D4：它是「今天成功加进几个群」的正确度量，pending 回查一开工就要用）。结论写回 design Open Question 1。
- [ ] 3.4 **绝不**改成「成员账本也数 pending」。`markJoining`（`group-store.ts:741`）在**点击之前**就写 `last_attempt_at = now()` ⇒ 导航/登录失败也会被数进去 ⇒ **过计**（design D3 备选，已否决）。

## 4. 运营预期与安全红线

- [ ] 4.1 **部署前向运营打招呼**：日限将第一次真正生效，加群次数会下降——**这是之前超发被纠正，不是 bug**。若真的不够用，正确动作是评估日限**数值**（另一个问题），**绝不是**把分子改回去。
- [ ] 4.2 `AC-RISK-*` 全过（安全红线：绝不自残、被禁 `record` 返 false）。本 change 动的正是记账闸，**这组断言是主防线**。

## 5. 测试

- [ ] 5.1 点后 pending（`clicked:true, ok:false, reason:'pending'`）⇒ 风控 join_group 计数 **+1**；**且不产生任何成功加群记录**、不进展示账本。
- [ ] 5.2 点前已 pending（`clicked:false, reason:'pending'`）⇒ 计数 **不变**。**与 5.1 reason 字符串相同、结果相反**——这一对是本 change 的核心断言。
- [ ] 5.3 `already_member`（`clicked:false`）/ shadow `observation_only` ⇒ 计数不变。
- [ ] 5.4 点后 joined（`clicked:true, ok:true`）⇒ 计数 +1 **且**成功账本 +1（**今天的行为逐位不变**）。
- [ ] 5.5 **只下发、无边缘回执** ⇒ 计数不变（红线：下发是意图不是既成事实，spec:27 的「MUST NOT 凭下发即记」原样成立）。
- [ ] 5.6 **其余动作零回归**：`like`/`collect`/`follow`/`comment`/`comment_like` 在 `ok:false` 时仍**不计**。
- [ ] 5.7 **一个分子**：调度预筛与 `canJoin` 对同一账号读到**同一个数**。

## 6. 验证与部署

- [ ] 6.1 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`（顺序照 CLAUDE.md §4）。**注意**：`npm run typecheck | tail` 的退出码是 tail 的、会假绿——直接跑、看退出码。
- [ ] 6.2 提交 + push cloud master（commit message 末尾带 `Co-Authored-By`）。
- [ ] 6.3 部署 dev（安全序列照 §5：`scripts/deploy-target dev --check` → ECS 先备份 → rsync `--exclude .env --exclude node_modules --exclude .git` → restart → healthcheck）。**无 DB 迁移**、**无需出安装包**。**红线**：绝不碰同机 isales。
- [ ] 6.4 dev 上真发一次入群申请并停在待审批，坐实风控日计数 +1（**不是只在单测里成立**）。

## 7. 回写与收口

- [ ] 7.1 本文件按 §6 用 HTML 注释标 `[x]` + commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。sha **必须取自已推送的提交**（判据：`git merge-base --is-ancestor`，不是 `cat-file`）。
- [ ] 7.2 真机项登记 `docs/real-machine-acceptance-backlog.md` **簇 90**：发出 N 个入群申请（含待审批）后日计数 = N 而非批准数；额度耗尽后调度闸不再起加群。
- [ ] 7.3 `openspec validate fb-join-quota-counts-attempts --strict` 通过。
- [ ] 7.4 design 的 Open Question 1（`countJoinedToday` 是否还有调用点）与 2（shadow 模式是否恒 `observation_only`）结论写回 design。**若 Q2 发现 shadow 下存在 `clicked:true` 路径 ⇒ 那是独立 bug（影子模式点了真按钮），当场上报、不绕过。**
