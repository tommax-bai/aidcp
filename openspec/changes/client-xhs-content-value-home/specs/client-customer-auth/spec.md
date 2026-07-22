## ADDED Requirements

### Requirement: 客户稿件编辑与调整接口 SHALL 按环境归属隔离

customer-auth SHALL 提供授权环境下的待审稿 PATCH、调整任务创建和任务状态读取端点。每次请求 MUST 在验签、撤销与客户启用检查后，以路径 envKey 重新解析当前归属和持久账号绑定；SQL/领域写 MUST 同时校验该账号与稿件。请求 MUST NOT 接受 `accountId`、任意 Cloud URL、token、provider 或模型凭据。

#### Scenario: 当前客户编辑自己的环境稿件
- **WHEN** 客户 A 对其授权环境绑定账号的待审稿提交合法版本编辑
- **THEN** 请求进入该账号范围内的稿件 CAS 写且响应不披露 accountId

#### Scenario: 跨客户稿件 id
- **WHEN** 客户 A 通过自己的 envKey 请求编辑或调整客户 B 的稿件 id
- **THEN** Cloud fail-closed 拒绝且不泄露稿件是否存在、正文、图片或任务状态

### Requirement: 调整请求 SHALL 使用显式最小 DTO

创建调整请求只允许 `expectedVersion`、`scope`、`instruction` 和该 scope 所需的 selection；直接编辑只允许标题、正文、话题和 expectedVersion。未知字段、空指令、超长指令、无效位置、非当前图片或不支持 scope MUST 以具名校验错误拒绝，不得静默放宽成整篇调整。

#### Scenario: 单图请求夹带其它图片
- **WHEN** `selected_image` 请求额外提交图片数组或正文
- **THEN** Cloud 以 DTO 校验错误拒绝，不把它升级为整图或整篇修改

### Requirement: 稿件与任务响应 SHALL 最小披露

编辑和调整响应 SHALL 只返回客户审核所需的稿件字段、版本、job 状态、白名单过程和客户可理解错误。响应 MUST NOT 返回原始来源快照、sourceReference 全量、LLM prompt/response、内部审批信号、accountId、execution lease 或数据库诊断。

#### Scenario: 客户读取调整任务
- **WHEN** 客户读取自己环境中一条调整任务
- **THEN** 响应包含 job id、scope、状态、过程摘要、结果版本或公开错误，不包含内部模型与账号字段

### Requirement: 客户内容数据面 SHALL 独立于环境运行状态

待审稿编辑、调整任务创建和任务状态读取 SHALL 通过 customer-auth HTTP 处理，不以浏览器、Edge 自动化进程或 WebSocket 在线作为客户身份与内容数据读写前置。只有图片或文本 provider 不可用、绑定未知、版本冲突等真实领域条件可以拒绝；不得返回伪造的“请先启动浏览器”替代 Cloud 真态。

#### Scenario: 环境停止时调整待审稿
- **WHEN** 客户环境停止但授权、绑定和待审稿版本均有效
- **THEN** 客户仍可创建 Cloud 调整任务，任务不会自动启动浏览器或执行平台写入

