## ADDED Requirements

### Requirement: Facebook 账号以结构化枚举保存唯一写作语言
系统 SHALL 为 Facebook 账号保存一个结构化 `writing_language`，只允许中文 `zh-CN`、英文 `en`、越南语 `vi`。该字段 SHALL 是账号 soul 的一部分并由 Cloud 校验、持久化和热加载；MUST NOT 从语调、昵称、代理国家、Facebook UI locale、历史内容或目标帖语言推断。

#### Scenario: Facebook 人设保存越南语
- **WHEN** 已验证为 Facebook 的账号确认 `writingLanguage=vi` 的人设草稿
- **THEN** Cloud 将 `writing_language: vi` 写入该账号 soul，后续按账号读取均返回越南语

#### Scenario: 非法语言被拒绝
- **WHEN** Facebook 人设生成请求携带不在 `zh-CN/en/vi` 内的值
- **THEN** Cloud 以具名拒因失败，MUST NOT 调模型、落库或回占位人设

#### Scenario: 非 Facebook 不接受写作语言字段
- **WHEN** 小红书或视频号会话提交 `writingLanguage`
- **THEN** Cloud 拒绝该平台不适用字段，MUST NOT 把它写入账号 soul 或改变既有流程

### Requirement: Facebook 公开文本从首次生成起使用账号写作语言
Facebook 帖子正文、评论正文和会改变正文的后续重写 SHALL 从首次产文起使用账号 `writing_language`。目标帖可用任意语言作为理解语境，但 MUST NOT 覆盖账号写作语言。审核后到 Edge 提交之间 MUST NOT 翻译或改写，真实下发文本 SHALL 与审核文本一致。

#### Scenario: 越南语账号评论英文帖子
- **WHEN** `writing_language=vi` 的 Facebook 账号对英文帖子生成评论
- **THEN** 评论以越南语生成，英文帖子仅作语境，MUST NOT 让输出改为英文

#### Scenario: 审核后不做语言转换
- **WHEN** 一条 Facebook 稿件或评论已以目标语言进入审核并获准
- **THEN** 发布执行层逐字使用已审正文，MUST NOT 在提交前再次翻译、转写或按当前配置重生成

### Requirement: 缺配置或语言不确定时自动公开写入 fail-closed
Facebook 文本生成 SHALL 在审核/自动授权前验证目标语言。缺少 `writing_language`、输出明显不匹配或无法可靠确认时 SHALL 返回可诊断的非成功结果，MUST NOT 自动提交或记录为已发布/已评论。小红书和视频号不受此 Facebook-only 守卫影响。

#### Scenario: 存量 Facebook 人设缺语言
- **WHEN** 存量 Facebook soul 可解析但没有 `writing_language`，并触发帖子或评论产文
- **THEN** 系统以 `writing_language_required` 类具名原因停止产文/提交，MUST NOT 猜测默认语言

#### Scenario: 输出语言明显不匹配
- **WHEN** 英文账号的生成正文含明确中文主体文本，或越南语账号输出无法确认是越南语
- **THEN** 语言守卫返回 mismatch/uncertain 并停止自动公开写入，MUST NOT 把错误语言文本继续送往 Edge

### Requirement: Facebook 灵感创作范围保持关闭
本能力 MUST NOT 开放 Facebook 灵感池或 `publish_from_inspiration`。写作语言只服务 Facebook 已有普通稿件/候选稿产文与评论产文；小红书灵感创作行为 SHALL 保持不变。

#### Scenario: Facebook 选择语言后仍不能灵感创作
- **WHEN** Facebook 账号已配置任一合法写作语言
- **THEN** Edge 仍隐藏 Facebook 灵感创作入口，Cloud 仍拒绝 `publish_from_inspiration`，MUST NOT 因语言配置完成而扩展能力范围
