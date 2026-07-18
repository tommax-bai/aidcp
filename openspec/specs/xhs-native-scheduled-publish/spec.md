# xhs-native-scheduled-publish Specification

## Purpose
TBD - created by archiving change xhs-native-scheduled-publish. Update Purpose after archive.
## Requirements
### Requirement: 小红书定时时间具有严格窗口与平台边界

系统 SHALL 只为小红书待审草稿接受原生定时发布，目标时间 MUST 为权威校验时刻后至少 1 小时且不超过 14 天，并按北京时间分钟精度下发。`immediate` MUST 清空 `publishTime`；Facebook 或其它平台请求 `scheduled` MUST fail-closed，绝不静默改成立即发布。

#### Scenario: 合法定时时间被接受
- **WHEN** 审核人把一条小红书待审草稿设为当前时刻后 2 小时的定时发布
- **THEN** 系统保存 `mode='scheduled'` 与对应 epoch 时间，并把它作为新内容版本供后续审批

#### Scenario: 越界或不支持平台被拒绝
- **WHEN** 目标时间不足 1 小时、超过 14 天，或 Facebook 草稿请求 `scheduled`
- **THEN** cloud MUST 返回可区分的非法字段拒因，草稿保持原版本与原发布方式，MUST NOT 改成立即发布

### Requirement: 定时设置是提交关键步骤并具有正证据校验

edge SHALL 使用专用处理器设置小红书定时发布：开启定时控件、写入北京时间 `YYYY-MM-DD HH:mm`、再同时验证开关选中、显示值等于目标分钟、提交按钮为“定时发布”。任一验证失败 MUST 返回 `ok:false`；cloud MUST 停止在 `submit_publish` 之前，MUST NOT 把 `set_schedule` 当 best-effort 或退化成立即发布。

#### Scenario: 定时控件完整生效后才允许提交
- **WHEN** 三项正证据均与目标时间一致
- **THEN** `set_schedule` 回 `ok:true`，sequencer 才能继续下发 `submit_publish`

#### Scenario: 页面只有定时文案但开关未生效
- **WHEN** 页面可见“定时发布”标签、但复选框未选中或时间回读不一致
- **THEN** `set_schedule` MUST 回 `post_validation_failed`，后续提交指令 MUST NOT 下发

### Requirement: 定时稿按内容完成后设置并与立即发布分流

小红书定时序列 SHALL 依次完成配图、标题、正文、话题与其它选项，再执行 `set_schedule → submit_publish → capture_scheduled`。定时模式 MUST NOT 在同一提交序列中强求 `capture_postId`；立即发布仍执行 `submit_publish → capture_postId`，两者不得混淆。

#### Scenario: 定时稿指令顺序
- **WHEN** 已批准稿件包含标题、正文、话题和合法定时时间
- **THEN** `set_schedule` 位于全部写稿/话题/选项之后且位于提交之前，提交之后只执行 `capture_scheduled`，不执行 `capture_postId`

### Requirement: 平台接受定时任务与公开发布是两个持久化事实

定时提交成功，或提交点击已经派发但回执不确定时，cloud SHALL 将记录置为 `scheduled`、保存目标时间与可选内部定时 id，并禁止自动重投。内部 id MUST NOT 写入 `platform_post_id`、MUST NOT 被渲染为公开链接。`scheduled` MUST NOT 消耗发布风控次数或已发布日配额。

#### Scenario: 提交成功但无公开链接
- **WHEN** 平台接受定时任务且 `capture_scheduled` 找到内部 id，但当场没有公开 post id/link
- **THEN** 记录状态为 `scheduled`、内部 id 单独保存、`platform_post_id/post_url` 保持空，发布计数不变

#### Scenario: 提交点击后回执不确定
- **WHEN** `submit_publish` 回 `ok:false` 但 `submitDispatched=true`，且之前 `set_schedule` 已成功
- **THEN** 记录仍进入 `scheduled` 并等待对账，MUST NOT 自动重投或记为 `failed`

### Requirement: 到期对账确认公开后才完成发布与记账

cloud SHALL 在目标时间后有界扫描 `scheduled` 记录，通过账号绑定 edge 的 task lease 下发只读 `reconcile_scheduled`。edge SHALL 优先以内部定时 id、再以精确标题与目标分钟无歧义匹配已发布笔记；只有取得真实公开 post id 与平台可用 URL 才回成功。cloud MUST 以原子状态转换首次写 `published`，且只有该首次转换记一次发布风险账。

#### Scenario: 对账确认真实公开
- **WHEN** 目标时间后平台已发布列表出现唯一匹配笔记并给出真实 post id 与 URL
- **THEN** 记录原子转为 `published`、回写 `platform_post_id/post_url`，并且发布计数恰好增加 1

#### Scenario: 重复对账不双计数
- **WHEN** 同一 `scheduled` 记录因并发或重启收到重复的公开确认
- **THEN** 只有首个 `scheduled → published` 原子更新成功者记账，后续调用幂等跳过

#### Scenario: 尚未公开时有界退避
- **WHEN** 目标时间已过但平台仍显示定时中、edge 离线或没有无歧义匹配
- **THEN** 系统保持 `scheduled`、记录真实错误并按有界退避重试；达到最多 8 次后转 `needs_review`，MUST NOT 声称已发布或自动重投原稿

### Requirement: 客户端批准动作可在同一版本闸内设置发布计划

客户端对 `pending_approval` 小红书稿件执行批准时 SHALL 可携带 `publishMode/publishTime`。Cloud MUST 以活会话账号校验稿件归属、比对客户端所见内容版本、按权威时刻校验发布计划；计划变化 MUST 经既有 `editDraft` 单写方法和内容版本 CAS 深合并同一 `publish_log.publish_metadata`，随后重读真实稿件并以更新后的内容版本写审批授权。任一账号、状态、版本、时间或 CAS 校验失败 MUST 整体拒绝，不得写批准、不得静默改成立即发布、不得部分修改。计划未变化 MUST NOT 无谓增加版本。旧客户端未提供新字段时 SHALL 沿用稿件当前发布计划。

#### Scenario: 批准时设置合法定时发布

- **WHEN** 客户对版本 v3 的待审小红书稿选择合法定时值并批准，且稿件当前为立即发布
- **THEN** Cloud 以 v3 CAS 把同一稿件改为 scheduled/目标时间、得到 v4，再以 v4 写批准授权并触发下发

#### Scenario: 批准时切回立即发布

- **WHEN** 客户把待审定时稿切为立即发布并批准
- **THEN** 同一 CAS 写入 `mode=immediate/publishTime=null`，保留其它元数据，审批签名绑定修改后的新版本

#### Scenario: 发布计划未变化不增版本

- **WHEN** 客户批准时提交的模式与时间等于草稿当前真态
- **THEN** Cloud 直接以当前版本授权，不执行空编辑、不增加内容版本

#### Scenario: 时间在批准时已失效

- **WHEN** 客户提交 scheduled 目标时间在 Cloud 权威校验时已不足未来 1 小时或超过 14 天
- **THEN** Cloud 返回时间拒因，稿件元数据和审批信号均不改变，绝不改成立即发布

#### Scenario: 版本冲突不部分批准

- **WHEN** 客户所见 v3 在批准前已被其它编辑更新为 v4
- **THEN** Cloud 返回 `version_stale` 与当前版本，不修改发布计划、不写审批授权

#### Scenario: 取消不修改发布计划

- **WHEN** 客户取消一条待审稿
- **THEN** Cloud 按既有取消语义写拒绝，忽略或拒绝任何发布计划字段，不编辑稿件元数据
