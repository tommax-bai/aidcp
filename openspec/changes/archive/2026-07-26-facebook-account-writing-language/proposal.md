## Why

Facebook 账号目前没有独立、结构化的对外写作语言：人设向导只采集语调，评论会跟随目标帖语言，发布创作提示仍可能落入中文语境，导致同一账号的稿件与评论语言不稳定。需要把账号选择的中文、英文或越南语作为 Cloud 权威的人设配置，在文本首次生成与后续改写阶段始终生效，并保证审核后不再转换内容。

## What Changes

- **BREAKING（仅 Facebook 人设生成请求）**：在 Edge 人设向导的“语气调性”下增加仅 Facebook 环境可见的“发言语言”单选，支持中文、英文、越南语；新生成或更新 Facebook 人设时必须显式选择，旧客户端缺字段的 Facebook 生成请求将收到具名拒因。
- 以独立、受控的 `writingLanguage` 协议字段提交选择，并由 Cloud 按已验证的 Facebook 会话校验，不把语言伪装成自由关键词。
- 将写作语言确定性持久化进账号 soul，并通过 Cloud 权威快照回显到对应环境；存量未配置账号保持可识别的“待补充”状态，不从昵称、语调或历史内容猜测。
- Facebook 稿件正文、评论正文及会改变正文的重写角色从首次生成起使用账号写作语言；审核后的稿件/评论按已审文本原样下发，发布前不得再次翻译或转换。
- Facebook 评论不再默认跟随目标帖语言；目标内容可用于理解语境，但最终输出必须使用账号写作语言。
- 保持 Facebook 灵感创作不可用；本变更不开放 `publish_from_inspiration`，不改变小红书或视频号人设与创作流程。
- 在审核前增加写作语言一致性守卫；无法确认或明显不匹配时诚实拒绝自动公开写入，不以错误语言内容继续发布。

## Capabilities

### New Capabilities
- `facebook-account-writing-language`: Facebook 账号级写作语言的枚举、权威存储、平台边界、审核前一致性和存量兼容契约。

### Modified Capabilities
- `persona-keyword-generation`: Edge 人设向导和 `persona.generate` 请求增加 Facebook-only 的受控写作语言输入与回显。
- `account-persona-config`: 账号 soul 支持可校验、可热加载的结构化写作语言字段。
- `comment-interaction`: Facebook 评论首次撰写及去 AI 味/撞车重写使用账号写作语言，不再以目标帖语言覆盖账号选择。
- `publish-pipeline`: Facebook 稿件正文首次生成及正文重写使用账号写作语言，审核后仍保持所见即所发。
- `facebook-ui-locale-normalization`: 明确浏览器界面固定 en-US 与账号对外写作语言继续正交，写作语言不得改动指纹、cookie 或 Facebook UI locale。

## Impact

- Control repo：OpenSpec delta、`docs/protocol.md` 协议说明与跨仓验证记录。
- `aidcp-edge`：Electron 人设 UI、环境级回显/切换隔离、`persona.generate` 请求和 Edge 协议类型。
- `aidcp-cloud`：Soul 类型/加载/序列化、人设生成与快照、Cloud 协议类型、Facebook 发布/评论文本角色及语言一致性守卫。
- 不新增 Edge 端模型或翻译能力，不开放 Facebook 灵感池，不改变风险、审批、发布确认状态语义。
