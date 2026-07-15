## MODIFIED Requirements

### Requirement: 循环内真人审批——暂停态 + 短超时 + 未授权不发

因评论 MUST 在详情页打开时发出，审批 SHALL **循环内等待**：`CommentApprovalGate` 下发评论命令前 MUST 经飞书人审授权。

评论支线在途期间系统 MUST 进入**被看门狗认得的「评论支线在途」暂停态**（复用按-edge 暂停通道）。该暂停态：

- **覆盖范围为评论支线在途全程**：从该笔记进入评论支线（互动完成后开始评估/撰写）起，到该笔记评论支线终局（`comment.done` 或 `comment.skipped`）止；MUST NOT 只覆盖 `comment.cleared` 之后的审批等待段，因为评估 / 撰写 / 去 AI 味阶段（数秒到数十秒）内账号同样 MUST 停在待评论帖上。
- **经统一命令出口生效**：暂停 MUST 由发命令的统一出口（软暂停闸）扣住一切会离开当前待评论帖的浏览 / 互动命令——包括并行互动回执触发的 stale-target 重扫滚屏、idle 看门狗的恢复滚屏、换帖 `open_note`、`refresh`、feed 续滚。MUST NOT 退化为只在单个 idle-nudge 翻译点做门控（该退化会漏掉上述其余出口）。
- **看门狗按"有意暂停"处理**：暂停期间 idle 计时 MUST 冻结（不因无浏览上报累积 idle 而 nudge / 结束会话）。
- **窗内不提前结束会话**：暂停期间由动作数 / 时长 / 配额上限触发的 `session.should_end` MUST 推迟到评论支线终局后再评估，MUST NOT 在评论支线在途时结束会话而废掉一条正在人审 / 已授权的评论；但 `session.end` 本身 MUST 仍可达（暂停不得阻塞真正需要的结束）。
- **终局解除顺序严格**：`comment.approved` / `comment.skipped` 终局 MUST 先解除暂停态并恢复看门狗计时，再下发已授权评论命令或（读评 surface 不等时的）`open_note{purpose:'navigate'}` 迁移命令——否则评论 / 迁移命令会被自己设的暂停态扣住。

MUST 设**硬性短超时**（可信停留上限）；超时 / 拒绝 MUST 视为本篇不评、记审计、emit `comment.skipped` 进"是否进主页评估"。
审批 MUST 复用既有 `/tmp` 先到先得审批信号机制、用**评论专属 requestId 命名空间**（与发帖 `publish-<recordId>` 区分）；**未获授权 MUST NOT 下发评论命令**。

该暂停态跨平台一致：小红书（读评同为详情面）与 Facebook（读 feed、评论 detail，`comment.approved` 后经 `open_note{navigate}` 两步迁移）均适用。

#### Scenario: 授权后下发、超时则跳过
- **WHEN** 飞书人审在超时窗口内写入评论 requestId 的授权信号
- **THEN** `CommentApprovalGate` MUST emit `comment.approved` 触发评论命令下发；若窗口内未授权 / 被拒，MUST emit `comment.skipped{reason:'approval_timeout'|'rejected'}`、退出暂停态、进"是否进主页评估"

#### Scenario: 撰写窗内并行互动回 no_target 不得把目标帖滚走
- **WHEN** 评论支线已进入（评估 / 撰写 / 去 AI 味在途、`comment.cleared` 尚未发出），同一笔记的并行互动（点赞 / 收藏）回执带 `ok:false, reason:'no_target'`
- **THEN** 系统 MUST NOT 因该回执下发 stale-target 重扫滚屏（或任何离开当前待评论帖的命令）；账号 MUST 停在待评论帖上直到评论支线终局；该互动如实记为失败（不假成功、不重扫）

#### Scenario: 审批窗内 stray 边缘上报不得下发移动命令
- **WHEN** 浏览会话处于"评论支线在途"暂停态，其间到达任一边缘上报（迟到的 `page.cards` / feed 上报 / 互动回执等）
- **THEN** 系统 MUST NOT 经统一命令出口下发 `open_note` 换帖 / `scroll` / `refresh` 等会离开当前待评论帖的命令；仅 `session.end` 与暂停通道放行的命令可达

#### Scenario: 审批窗内不因动作数/时长/配额提前结束会话
- **WHEN** 浏览会话处于"评论支线在途"暂停态，其间一条边缘回执使动作数 / 时长 / 配额触及会话结束阈值
- **THEN** `session.should_end` MUST 推迟到评论支线终局（`comment.done` / `comment.skipped`）后再评估，MUST NOT 在评论在途时结束会话废掉在审 / 已授权评论

#### Scenario: 等待审批期间不卡死会话、不误判 idle
- **WHEN** 浏览会话处于"评论支线在途"暂停态
- **THEN** 看门狗 MUST 按"有意暂停"处理、MUST NOT 因 idle 重启或结束会话；该 edge 的其他浏览 / 互动命令 MUST 在暂停期间不下发，`session.end` MUST 仍可达

#### Scenario: 终局先解除暂停再下发评论/迁移命令
- **WHEN** 评论支线到达终局（`comment.approved` 或 `comment.skipped`）
- **THEN** 系统 MUST 先解除暂停态并恢复看门狗计时，再下发已授权评论命令或 `open_note{purpose:'navigate'}` 迁移命令；MUST NOT 让评论 / 迁移命令被残留的暂停态扣住而静默丢弃

#### Scenario: 红线反例——未授权或超时仍发评论（禁止）
- **WHEN** 有实现在无授权信号 / 超时后仍下发评论命令，或为绕开"页面久留"把评论改成无人审自动直发
- **THEN** MUST 视为违规、不予合入；评论 MUST 在授权信号存在时才下发（AC-PUB），未授权 / 超时一律 `comment.skipped` 不发
