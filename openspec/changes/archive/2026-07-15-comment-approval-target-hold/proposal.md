## Why

浏览闭环内触发评论、进入人审时，账号本应"停在待评论的帖上等审批"，实测却会被滚走/换帖、甚至会话被提前结束。多 agent 对抗性核验确认：边缘在静默期完全静止、hot-lead 解耦路径对 FB 结构性不触发，根因**全在云端**——现有 `comment-interaction` Requirement 106 已明文要求"等待期间 MUST 进入被看门狗认得的暂停态、复用按-edge 暂停通道、暂停期间不发其他浏览/互动命令"，但实现漂移成一个只在 idle_nudge 一处被查的进程内布尔（`approvalInFlight`），既没进命令统一出口、又开得太晚，导致评论人审窗形同虚设。

## What Changes

- 把"评论支线在途"做成**真正的暂停态**：复用既有软暂停通道（`SessionContext.setBrowseSuspended`）+ 看门狗 `pauseClock`，让命令统一出口 `sendCommand` 自动扣住一切会离开当前待评论帖的 browse/互动命令（stale-target 重扫滚屏、idle_nudge 滚屏、`open_note` 换帖、`refresh`、feed 续刷），只放行 `session.end` 与 bypass。
- **前移保护窗**：从"仅 `comment.cleared` 之后的审批段"扩到"评论支线在途全程"（从互动完成/评估起，到 `comment.done` / `comment.skipped` 止），覆盖此前完全裸奔的撰写窗——治住"并行点赞回 `no_target` → 立即重扫滚屏把目标帖滚走"这条最主要的真实滚走源。
- **人审窗内推迟会话结束判定**：连同 `pauseClock` 一起冻结动作数/时长/配额触发的 `session.should_end`，`comment.done`/`skipped` 后再判，避免一条点赞回执把已人审通过的评论连同会话一起废掉；`session.end` 在真正需要时仍可达（不破坏红线）。
- **终局严格顺序**：`comment.approved`/`comment.skipped` 先解除暂停 + resume clock，再下发 approved 评论/`open_note{navigate}` 迁移命令（镜像 `nickname-enricher` 的成熟先例，避免评论/迁移命令被自己设的暂停态扣住）。
- 跨平台一致：XHS（读评同为详情面）与 FB（读 feed、评论 detail 两步迁移）均适用。
- 非目标 / 不改：**AC-PUB 红线（未授权绝不下发评论）保持不变**——本 change 只改"人审期间是否停在帖上"，绝不放松"未授权不发"；边缘无需改动；两步 surface 迁移与其 fail-closed 双验证保持不变。

## Capabilities

### New Capabilities
<!-- 无新增能力：这是对既有 comment-interaction 能力的行为修正与覆盖扩展。 -->

### Modified Capabilities
- `comment-interaction`: 收紧并扩展"循环内真人审批——暂停态"要求：暂停态覆盖范围从"仅审批等待段"扩到"评论支线在途全程"；暂停 MUST 经统一命令出口（复用按-edge 暂停通道）生效，MUST NOT 退化为只门控 idle_nudge；显式抑制 stale-target 重扫与 idle-nudge 滚动；人审窗内推迟 `session.should_end`；终局先解除暂停再下发评论/迁移命令。

## Impact

- **代码（cloud-only，`aidcp-cloud`）**：`src/orchestrator/role-dispatcher.ts`（评论支线暂停态置/清、`sendCommand` 出口复用、no_target 重扫与 idle_nudge 抑制、should_end 推迟、终局解除顺序）、`src/agents/comment-approval-gate.ts` 与评估/撰写/去味角色的暂停态进入点、`src/agents/session-monitor-role.ts`（`pauseClock`/resume 接线）、`src/agents/session-context.ts`（复用 `setBrowseSuspended`）。**边缘 `aidcp-edge` 无改动**。
- **热点单写约束**：`role-dispatcher.ts` 为热点单写文件，活跃 change `lease-strict-preemption` 同区在改——本 change 标记"集成串行"，合入 master 前先 rebase 到最新、解冲突、跑 `test:acceptance` + `typecheck`。
- **安全红线**：AC-PUB（未授权绝不静默发布/评论）必须全过；新增暂停态不得阻塞 `session.end` 的可达性。
- **测试**：新增 acceptance 场景覆盖撰写期 no_target 不滚走、审批窗 stray 上报不下发移动命令、审批窗不因配额/时长提前结束会话、终局解除顺序。真机灰度项归入 `docs/real-machine-acceptance-backlog.md`。
