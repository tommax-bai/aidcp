## MODIFIED Requirements

### Requirement: 浏览只在独占任务队列收敛后恢复

系统 SHALL 以 edge 协调器的当前租约与等待队列为浏览写入准入事实源。任一发布/评论自己的 `finally` MUST NOT 无条件导航或滚动；仅当没有当前独占租约且没有应立即接续的独占任务时，edge 才解除普通浏览写入冻结。解除冻结只表示可以接收浏览命令，MUST NOT 假装已经回到目标浏览面。Cloud 在完整工作流收敛并确认最终 release 回执后，才 SHALL 下发一次统一 `resume_redrive`；Edge 以新鲜页面探测执行它并重新上报结构化结果。

#### Scenario: 发布结束时评论已排队不闪回 feed
- **WHEN** 发布释放时评论 commit 已在等待队列
- **THEN** edge 直接把租约授予评论，不在两者之间恢复普通浏览或执行一个滚动

#### Scenario: 中间任务段释放只解除所有权
- **WHEN** 加群观察段释放后仍要进行加入点击段，或评论准备段释放后仍在等待最终提交段
- **THEN** Edge 释放该段所有权但不导航离开当前任务页
- **AND** Cloud 不为该中间 release 下发 `resume_redrive`

#### Scenario: 最后一个任务结束才恢复
- **WHEN** 工作流最后一个独占任务得到终局执行回执且其 release 得到 Edge 确认
- **THEN** Cloud 下发一次统一 `resume_redrive`，Edge 恢复到请求的浏览面并重新上报

## ADDED Requirements

### Requirement: Terminal group or comment workflow SHALL request one immediate browse redrive

The Cloud workflow owner SHALL distinguish an execution receipt from platform success. After a group/comment action chain obtains a terminal receipt—success, failure, or `submitted_unknown` after bounded confirmation—and its final page-task release is acknowledged, it MUST request exactly one browse redrive for the account on the Edge connection named by that release. `submitted_unknown` MUST remain ambiguous for accounting but SHALL release page ownership. A missing release acknowledgement MUST NOT authorize an immediate browse command.

#### Scenario: Comment verification times out

- **WHEN** comment submission was dispatched but bounded verification ends as `submitted_unknown`, and the final lease release is acknowledged
- **THEN** Cloud preserves the ambiguous action outcome, releases the action owner, and immediately requests one browse redrive
- **AND** it does not retry the comment or count it as confirmed success

#### Scenario: Comment fails before submission

- **WHEN** the page task returns a terminal failure and the final lease release is acknowledged
- **THEN** Cloud requests one browse redrive without promoting the failure to success

#### Scenario: Release acknowledgement is missing

- **WHEN** the final task body ends but Cloud has not received the matching Edge release acknowledgement
- **THEN** Cloud does not issue the immediate redrive
- **AND** idempotent release recovery, lease expiry, and the existing idle recovery remain available

#### Scenario: Chained actions redrive once

- **WHEN** settlement creates a next join/comment action in the same consumption chain
- **THEN** intermediate action settlement and lease release do not redrive
- **AND** the root chain requests exactly one redrive after its final action and release acknowledgement, targeted to the Edge that released the final page lease
