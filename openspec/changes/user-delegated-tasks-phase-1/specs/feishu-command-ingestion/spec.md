## ADDED Requirements

### Requirement: Feishu 自然语言委托必须解析为昵称唯一绑定的确认卡

Feishu 管理群 SHALL 接受 Phase 1 可确定解析的自然语言委托，并要求可读账号昵称；系统 MUST 以昵称精确唯一解析真实账号，展示账号昵称、平台、动作、数量、尝试上限、时间、约束、人审和优先级的确认卡。昵称缺失、找不到或重名 MUST 澄清，MUST NOT 接收裸 accountId 作为面向用户的替代。

#### Scenario: 昵称唯一解析后展示确认卡
- **WHEN** 管理群输入“让小萝北今晚前完成 5 条有效评论，最多尝试 8 次”且昵称唯一
- **THEN** 系统返回结构化 `awaiting_confirmation` 卡片
- **AND** 点击确认前不得执行评论

#### Scenario: 昵称重名时不猜账号
- **WHEN** 两个账号昵称都为“小萝北”
- **THEN** 系统要求用户消除重名或提供可读区分
- **AND** MUST NOT 任意选择一个 accountId

### Requirement: 旧 slash command 语法保持兼容且写操作同样先确认

现有 `/publish`、`/comment`、`/status`、`/pause`、`/resume` 等命令 SHALL 保持语法兼容；只读命令可原路执行，`/publish` 与 `/comment` 等写命令 MUST 创建单次 DelegatedTask 并先展示结构化确认卡。确认后的单次任务 MAY 保留既有人工额度语义，但该语义 MUST NOT 被批量/异步任务继承。

#### Scenario: 旧单次评论命令继续工作
- **WHEN** 用户发送现有 `/comment <昵称>`
- **THEN** 路由器创建目标数为 1 的确认卡，确认后调用既有单次评论路径
- **AND** 该兼容语法不得绕过确认或被解释为 N 条批量任务
