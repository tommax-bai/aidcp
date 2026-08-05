# Design — unblock-facebook-consumption-comment-segment

## 1. 现状坐实（带落点）

- 单槽阻塞在 `aidcp-cloud/src/orchestrator/facebook-consumption-mode-runtime-store.ts:557`：
  `if (progress.active_action_id) { ... return { kind: 'action_active', action } }` —— 槽位非空时**连 view_fact 都不插**，`views_since_like` 恒不动。
- 评论闸在 `aidcp-cloud/src/orchestrator/facebook-consumption-mode-coordinator.ts:221`：策略取不到即
  `waiting_gate / facebook_group_comment_policy_unavailable`，经 `waitAndRelease` 落回等待态但**槽位仍指向它**。
- 自动化进程的显式缺席在 `aidcp-automation/src/automation-main.ts:952`（覆盖评论调度器）与 `:992`（消费协调器）。
- 唯一解冻路径在同文件 `:1590`：只有 `policy_revision` 变更时的 supersede 会清空 `active_action_id`。
- 生产证据（2026-08-05 18:47 查 dev 库）：12 行 `facebook_consumption_progress` 的 `active_action_id`
  全部指向 `action_type=comment / state=waiting_gate / blocker=facebook_group_comment_policy_unavailable`。

## 2. 为什么选「让位」而不是「超时作废」

现有 spec（`facebook-consumption-mode`）明写：无合规群时义务 SHALL 持久留存为 `waiting_target`，
**不还信用、不造重复机会**。那是刻意的——义务作废等于悄悄少做一次运营动作。

所以本 change 不动「义务是否留存」，只动「义务要不要占住推进槽位」。这也正是用户的表述：解耦。

超时作废方案另有一处硬伤：`no_target` 这个 outcome 在 TS 枚举里有、在库的 CHECK 约束里**没有**，
写进去会直接违反约束。要走作废就得先补一次迁移，而它换来的只是「把义务丢掉」——方向本身也不对。

## 3. 槽位语义的重新定义

**槽位 = 当前唯一可下发 / 在途的动作**，不再是「当前唯一未终结的动作」。

判据（三条同时成立才算「让位型义务」）：

- `action_type <> 'like'`（点赞段自己就是被保护的那一段，不参与让位）；
- `state IN ('waiting_target','waiting_gate')`；
- `dispatch_phase = 'not_started'`。

第三条是**红线「提交点是最外层前置」的落点**：只有一次都没派发出去的动作才可能让位。
已 `dispatched` 的一律照旧占槽，绝不允许在有在途写的情况下再起新动作。

让位时把 `active_action_id` 置空，义务行本身保持非终态——它仍会被 `listActiveActions`
（判据是 `state <> 'terminal'`，不是槽位指针）扫到并驱动，所以「让位」不等于「丢失」。

## 4. 积压上限（防止让位换来无限义务堆积）

让位之后点赞段恢复，下一轮 J 次确认加群又会到点造评论义务。若不设上限，
一个长期评论不成的账号会积压出成百上千份义务（正是当前 12 个账号的处境的另一种形态）。

规则：**同账号同策略号下，同类型未终结义务至多一份。** 到点时若已有一份，
MUST NOT 再造第二份，MUST 打一行具名日志（本轮的评论机会并入已有那份），
MUST NOT 静默吞掉——「悄悄少做一次」与「合并进已有义务」在运维视角必须可分辨。

## 5. 一次浏览至多一个边缘动作

让位后，同一次 `facebook.rule.view.confirmed` 有可能既产生点赞、又想去驱动等待中的义务。
评论 / 加群走 edge-task 租约、会打断浏览，与在途点赞叠加会让点赞回执落空。

规则：本次浏览产生了点赞动作，就**不在同一轮驱动等待义务**；义务留到下一次浏览或在途扫描。
这条不是性能考虑，是「别让两条边缘动作在同一时刻抢同一个浏览器」。

## 6. 策略接线为什么走 `content_schedule` 流

三选一：新开一条流 / 挂 `facebook_operation_policy` 流 / 挂 `content_schedule` 流。

选第三条，唯一理由是**游标已经覆盖载荷**：`FacebookGroupCommentPolicyStore.write()` 落库时
bump 的就是 `content_schedule` 这个 mirror key，单体里读它的闸也正是 `isStale('content_schedule')`。
挂第二条流要额外把 `content_schedule` 塞进那条流的游标键，挂新流要再手抄一遍流清单
（本仓已为「手抄流清单漂一条」付过一次代价：消费方永远拿不到那条流 ⇒ 边缘一台都连不上）。

镜像陈旧 / 载荷缺失时**返回 null**，与单体缺配置时逐位一致：协调器照旧报
`facebook_group_comment_policy_unavailable`，MUST NOT 塞默认 24 小时顶替——
顶替会让「策略还没同步过来」和「运营就是这么配的」变成同一件事。

## 7. 验收判据（防止改完看不出来）

- 变异验证：把让位判据改成恒 false（即恢复旧行为），承重用例 MUST 精确变红。
- 生产验收：dev 部署后，`facebook_consumption_progress` 里指向 `waiting_*` 评论义务的
  `active_action_id` MUST 归零，且被冻结账号 MUST 重新出现 `action=like sent=1`。
