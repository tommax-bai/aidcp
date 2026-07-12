## ADDED Requirements

### Requirement: Facebook 排期发帖复用 review 待审路径并检查素材池

内容排期触发 Facebook 发帖 SHALL 复用既有发布管线的生成、待审草稿、授权信号与发布派发器。MVP 中 Facebook 排期发帖 MUST 使用 `review` 路径：到点只生成待审草稿并发审批卡，真发仍只在人审批准后执行。触发前 MUST 检查该账号具备 Facebook publish 能力、风险状态允许、排期闸通过、且素材池有 `available` 图片组；素材不足时本槽 SHALL 不生成草稿并发送诚实结果卡。`auto_approve` 对 Facebook publish 在本 change 中 MUST 保持禁用或 fail-closed，除非后续 change 明确开启。

#### Scenario: 排期命中且素材充足生成待审草稿
- **WHEN** Facebook 账号命中排期发帖时段、风险状态 normal、publish 能力可用、且素材池有 `available` 图片组
- **THEN** 内容调度器 SHALL 触发 Facebook 发布草稿生成，锁定素材池图片组，落待审草稿并发送审批卡，MUST NOT 直接提交

#### Scenario: 素材不足返回诚实结果卡
- **WHEN** Facebook 账号排期发帖命中但素材池没有 `available` 图片组
- **THEN** 内容调度器 SHALL 不生成草稿、不调用 edge，并回一张结果卡说明图片素材不足

#### Scenario: Facebook auto_approve 保持关闭
- **WHEN** 运营或配置尝试让 Facebook 排期发帖走 `auto_approve`
- **THEN** 系统 SHALL fail-closed 或降级为需要 review 的待审路径并明确提示，MUST NOT 在本 change 中免审自动提交 Facebook 帖子
