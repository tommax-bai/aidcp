# client-draft-refinement Specification

## Purpose
TBD - created by archiving change client-xhs-content-value-home. Update Purpose after archive.
## Requirements
### Requirement: 客户 SHALL 能直接编辑待审稿

客户 SHALL 能在稿件审核页编辑当前待审稿的标题、正文和话题。提交 MUST 带页面所见 `contentVersion`，Cloud MUST 校验环境归属、绑定账号、稿件账号和 `pending_approval` 状态，并以单写 CAS 回写后真态。客户端 MUST NOT 提交 `accountId` 或发布凭据。

#### Scenario: 直接编辑成功
- **WHEN** 客户修改标题和正文并提交仍为当前版本的待审稿
- **THEN** Cloud 原子写入允许字段、版本加一并返回写后稿件，页面刷新为新版本且仍处于待确认

#### Scenario: 编辑版本过期
- **WHEN** 稿件已被另一端更新而客户提交旧版本
- **THEN** Cloud 返回版本冲突和当前版本，不覆盖新稿，客户端提示刷新后重新编辑

### Requirement: AI 调整 SHALL 支持五种精确范围

调整任务 SHALL 支持 `whole`、`body`、`images`、`selected_image` 和 `selected_text`。Cloud MUST 只允许对应范围内字段变化：正文范围不得改标题、话题或图片；图片范围不得改文字；单图只替换所选位置；选中文字只替换经位置与内容双重校验的片段；整篇才可同时调整标题、正文、话题和图片。

#### Scenario: 只调整正文
- **WHEN** 客户以 `body` 提交指令且任务成功
- **THEN** 新版本只有正文允许变化，标题、话题、图片顺序和 URL 全部保持原样

#### Scenario: 只调整一张图片
- **WHEN** 客户以 `selected_image` 提交当前稿中一张图片 URL 和指令
- **THEN** 成功结果只替换该索引的图片，其余图片与全部文字逐字保持不变

#### Scenario: 只调整选中文字
- **WHEN** 客户提交 `selected_text`、UTF-16 起止位置和选中文字且与所见版本完全一致
- **THEN** 成功结果只替换该范围，前后正文逐字保持不变

### Requirement: AI 调整 SHALL 是持久、可观察的任务

创建调整 SHALL 返回持久 job id 和 `queued` 真态；状态读取 SHALL 返回白名单阶段、客户摘要、结果版本或失败原因。任务 SHALL 按服务端注入的 `execution_target` 领取，dev/ol worker MUST 只处理本目标任务。客户端关闭、浏览器停止或自动化 WebSocket 断开 MUST NOT 丢失已创建任务。

#### Scenario: 创建后客户端暂时关闭
- **WHEN** 客户成功创建调整任务后关闭客户端，Cloud worker 完成任务
- **THEN** 客户重新打开同一环境可通过 job id 或稿件状态读到完成结果和新版本

#### Scenario: 部署目标隔离
- **WHEN** shared PostgreSQL 同时存在 execution_target 为 dev 与 ol 的调整任务
- **THEN** dev worker 只领取 dev，ol worker 只领取 ol；缺失或非法部署目标的 worker 不运行

### Requirement: 过程消息 SHALL 是安全的客户投影

调整任务过程只允许 `计划/判断/生成/检查/确认` 阶段、状态和经过设计的客户摘要。响应 MUST NOT 包含原始 prompt、模型完整输出、chain-of-thought、provider 密钥、账号 id、内部堆栈或其它客户数据。

#### Scenario: 模型调用正在进行
- **WHEN** worker 正在生成正文或图片
- **THEN** 客户状态只说明正在处理的范围、保留边界和可核对进展，不返回模型隐藏推理或原始请求响应

### Requirement: 调整完成 SHALL 原子写入且不会自动发布

worker MUST 在最终写入时重新校验稿件仍为原账号、`pending_approval` 且版本等于任务 expectedVersion；整篇和图片任务的所需结果不完整时 MUST 不落部分修改。成功 SHALL 一次增加版本并刷新待审预览，旧审批版本失效；创建、执行或完成调整 MUST NOT 自动批准、调度或发布内容。

#### Scenario: 生成期间稿件被编辑
- **WHEN** 调整任务生成完成前稿件版本已经变化
- **THEN** 任务以版本冲突失败，原稿保持较新的版本，生成结果不覆盖也不自动重试写入

#### Scenario: 一组图片只生成成功一部分
- **WHEN** `images` 或 `whole` 所需的图片有任一张未得到真实 URL
- **THEN** 任务失败且稿件任何字段都不变化，不复用旧图伪装完整成功

#### Scenario: 调整成功后仍待确认
- **WHEN** 调整任务成功写入新版本
- **THEN** 稿件仍显示待客户确认，必须由客户后续显式批准才可能进入发布
