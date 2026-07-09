# publish-pipeline Delta

## MODIFIED Requirements

### Requirement: 审批通过即下发，下发从落库草稿重建、绝不重生成

人审授权信号到达即 SHALL 触发对应草稿进入该账号的下发队列（授权是发布的必要条件；出队时刻受 `publish-dispatch-pacing` 的最小间隔与熔断状态约束，延后 MUST 如实可见）。下发 MUST 从落库草稿重建发布输入（标题 / 正文 / 标签 / 图 / 元数据），下发上线的内容 MUST 与审批卡上所审的那份草稿一致；MUST NOT 在下发时重新生成内容、MUST NOT 用生成与下发之间变化后的人设 / 配置回灌或改写已定稿草稿（陈旧草稿如实照发，所见即所发）。下发时若该账号无在线边缘节点，SHALL 按零副作用失败处理：草稿回 `pending_approval`、作废该次授权信号并通知重批，MUST NOT 伪造成功、MUST NOT 静默丢弃授权、MUST NOT 把可重批的离线失败烧成终态。

#### Scenario: 授权到达即入队下发该草稿
- **WHEN** 某 `pending_approval` 草稿的人审授权信号（`approved === true`）到达且该账号无间隔 / 熔断约束
- **THEN** 云端即触发该草稿的下发段（让位 → 重建发布输入 → 驱动指令序列 → 回写结果），不等待自然空档

#### Scenario: 下发即所审、不重生成
- **WHEN** 一份草稿在 T0 生成定稿、T1（数小时后）才被批准
- **THEN** 下发上线的标题 / 正文 / 配图 / 元数据为 T0 定稿的那一份（与审批卡一致），MUST NOT 在 T1 重新生成或按 T1 的人设 / 配置改写

#### Scenario: 下发时边缘离线回待审可重批
- **WHEN** 授权到达、进入下发段，但该账号此刻无在线边缘节点
- **THEN** 云端不发任何指令，草稿回 `pending_approval`、该次授权信号被作废、运营被如实通知；边缘恢复后重批即可下发，MUST NOT 伪造成功或静默吞掉授权

#### Scenario: 红线反例——下发时重生成或回灌新配置（禁止）
- **WHEN** 有实现在下发时重新调用生成、或用当前人设 / 配置覆盖已落库草稿后再发
- **THEN** MUST 视为违规、不予合入；下发 MUST 忠于审批卡所审的冻结草稿（陈旧亦照发），重生成等于绕过人审所认可的内容

### Requirement: 下发段按账号单飞且每账号至多一份待下发草稿

下发段 SHALL 按账号串行（同一账号同一时刻至多一次下发在跑），授权到达时若该账号已有下发在跑，本次 MUST
排队或被忽略而 MUST NOT 并发抢同一边缘。生成候审段的堆积 SHALL 由每账号在途帽约束（「生成中 + 待审」合计
有界，见 `publish-generation-concurrency`），同账号多份 `pending_approval` 草稿在帽内合法并存（多候选挑选
场景）；同一参照稿在途时 MUST NOT 并发重复生成。下发段对同一 `recordId` MUST 幂等：已 `published` 或
正在下发的 `recordId` 重复授权 MUST NOT 触发二次发布。

#### Scenario: 同账号下发串行
- **WHEN** 某账号一份草稿正在下发，另一份草稿的授权同时到达
- **THEN** 第二份的下发 MUST 排队或被跳过、MUST NOT 与第一份并发向同一边缘下发指令

#### Scenario: 帽内多候选合法并存
- **WHEN** 某账号已有两份 `pending_approval` 草稿（未达在途帽），运营对另一篇参照稿触发洗稿
- **THEN** 新一轮正常生成并落第三份待审草稿；三份草稿各自独立可批 / 可驳，下发仍按账号串行推进

#### Scenario: 下发对 recordId 幂等
- **WHEN** 同一 `recordId` 的授权信号被重复投递（重复点击 / 兜底扫描与事件双触发）
- **THEN** 已 `published` 或正在下发的 `recordId` MUST NOT 二次下发 / 二次提交，结果保持单次发布

#### Scenario: 红线反例——并发下发抢同一边缘（禁止）
- **WHEN** 有实现允许同账号两份草稿同时进入下发、并发向同一边缘下发发布指令
- **THEN** MUST 视为违规、不予合入；同账号下发 MUST 串行，杜绝两条发布序列在同一 Chrome 上交错撞页
