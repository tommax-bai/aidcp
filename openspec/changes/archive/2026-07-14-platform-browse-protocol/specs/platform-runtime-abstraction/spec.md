## MODIFIED Requirements

### Requirement: 协议语义保持平台无关

平台抽象 SHALL 复用现有平台无关命令语义。新增平台 MUST NOT 引入以平台名命名的协议消息类型来表达通用动作；除非新增真实通用语义，否则 `docs/protocol.md` 的消息计数与两端 protocol 枚举 SHALL 保持不变。浏览 surface 与 open purpose、以及派生 `noteId` 与独立 `observation` 见证包 SHALL 作为既有消息上的**平台无关 optional 字段扩展**承载，不新增消息类型、不改变消息计数。

#### Scenario: 平台抽象不改变协议计数
- **WHEN** 完成 xhs driver 提取并运行协议契约验收
- **THEN** 两端 protocol 枚举和 `docs/protocol.md` 计数保持 Change 0 前一致，AC-PROTO 类检查通过

#### Scenario: surface 与 purpose 是平台无关字段扩展
- **WHEN** 为 `note.open` 增加 `surface`/`purpose`、为 `action.completed` 增加派生 `noteId`/`observation`
- **THEN** 两端 protocol 的 `MessageType` 枚举与计数不变，AC-PROTO 全绿
- **AND** 这些字段的语义不以任何平台名命名、缺省时逐位等于今天
