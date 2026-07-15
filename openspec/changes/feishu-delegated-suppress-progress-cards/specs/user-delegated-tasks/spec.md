## RENAMED Requirements

- FROM: `### Requirement: 等待审批的无变化对账必须静默且不使控制卡过期`
- TO: `### Requirement: 委托层通知由底层业务结果卡承担、发帖失败兜底、无变化对账静默`

## MODIFIED Requirements

### Requirement: 委托层通知由底层业务结果卡承担、发帖失败兜底、无变化对账静默

委托层 MUST NOT 为任务的常规状态迁移（`queued`、`executing`、`completed`、`waiting_approval`）主动推送自有的任务进度卡。每个任务的执行结果 SHALL 由其底层动作的**正常业务结果卡**承担：评论由评论链的结果卡回报；发帖成功由发布人审卡自证（成功不重复报绿）；发帖等待人审由发布人审卡本身承担。

唯一例外：**发帖类终态失败**（`failed`，或仍有缺口的 `partially_completed`）没有独立业务结果卡，委托层 MUST 补发一张诚实的失败 / 部分完成结果卡（红线：绝不静默失败）。**评论类终态失败 MUST NOT 由委托层补发**（评论链已发结果卡，避免重复）。

精确旧 slash 写命令（`source=legacy_command`）直接排队时 SHALL **静默受理**——只保留已读表情，MUST NOT 发送队列提示卡；结果由该任务自身的业务结果卡回报。自然语言委托仍先展示结构化确认卡（不受影响）；用户主动请求的控制命令（查看 / 暂停 / 取消）与卡片按钮回卡不受影响。

委托任务处于 `waiting_approval` 时保留有界的审批结果对账，但当审批、真实进度、控制意图和终态结果均未变化时，MUST NOT 发送新的用户通知或递增用于卡片控制的 task version；内部 claim/lease MAY 更新，但不得把无变化心跳呈现为新的业务进度。审批通过 / 驳回 / 候选版本变化 / 真实计数变化 / 暂停 / 取消意图变化 / 终态收敛时，按上述通知归属发送对应反馈，MUST NOT 吞掉真实业务变化。

#### Scenario: 评论任务完成不再叠加委托进度卡
- **WHEN** 一个委托评论任务跑完（成功或失败），评论链已按账号发出正常结果卡
- **THEN** 委托层 MUST NOT 再叠加一张任务进度卡（`queued` / `failed` / `completed`）

#### Scenario: 发帖失败仍诚实通知
- **WHEN** 一个委托发帖任务达到最大尝试仍 0 成功 → `failed`
- **THEN** 委托层补发一张红色失败结果卡（含真实完成数 0/N），MUST NOT 静默

#### Scenario: 发帖成功不重复报绿
- **WHEN** 委托发帖经人审通过并发布 → `completed`
- **THEN** 委托层 MUST NOT 再发绿色成功卡（成功由发布人审卡自证）

#### Scenario: 精确命令静默排队
- **WHEN** 管理群发送 `/publish <昵称>` 且昵称唯一可解析
- **THEN** 命令直接入队且 MUST NOT 回任何队列提示卡（只保留已读表情）
- **AND** 结果由发帖的正常业务卡（人审卡 / 失败卡）回报

#### Scenario: 等待审批的重复对账不产生新卡
- **WHEN** 发布候选进入 `waiting_approval`，连续多轮对账都返回仍未审批
- **THEN** 委托层不发任何等待进度卡，后续静默对账也 MUST NOT 递增 task version、增加 attempt 或发重复飞书卡

#### Scenario: 审批结果变化仍正常通知
- **WHEN** 静默等待中的候选随后被批准、驳回或修改为影响任务收敛的新版本
- **THEN** 下一次对账 SHALL 按真实结果更新任务，并按通知归属发送反映该语义变化的反馈（评论链结果卡 / 发帖失败兜底 / 成功由人审卡自证）

#### Scenario: 静默对账不覆盖并发取消
- **WHEN** worker 持有等待审批 claim 时用户取消尚未执行的剩余部分
- **THEN** 静默 release MUST NOT 把已经取消的任务改回 `waiting_approval`
- **AND** 取消后的真实终态与已有计数保持不变
