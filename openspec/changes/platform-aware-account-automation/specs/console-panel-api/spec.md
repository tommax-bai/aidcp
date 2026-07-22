## ADDED Requirements

### Requirement: 内容排期目录返回规范化平台与权威自动化动作投影

Cloud `GET /api/content-schedule` SHALL 为每个账号目录行增量返回规范化 `platform` 与服务端权威 `availableActions`。每个可用动作描述 MUST 至少包含稳定动作 id、该平台允许的非关闭模式和服务端日上限；该投影 MUST 来自有真实消费者的平台注册声明，而不是复用仅供指标显示的 `group_join` capability，也不得由 Console 维护第二份平台动作矩阵。旧平台别名 SHALL 按既有规范化规则归一；未知平台 MUST NOT 被伪装成任一已知平台的可配置动作。

#### Scenario: 小红书目录行返回规范化动作能力
- **WHEN** 目录包含平台原始值为 `xhs` 的账号
- **THEN** 返回行的 `platform` 为 `xiaohongshu`，且 `availableActions` 精确描述当前小红书排期支持的动作、模式与上限

#### Scenario: 视频号无内容自动化动作
- **WHEN** 目录包含当前只支持互动收件箱工作流的视频号账号
- **THEN** 返回规范化平台 `wechat_channels` 和空 `availableActions`，不得因通用内容排期字段存在而声称可自动发帖或评论

#### Scenario: Facebook 发帖模式诚实受限
- **WHEN** 目录包含 Facebook 账号且当前 Facebook 自动发帖只支持待审模式
- **THEN** 其发帖动作只声明 `review`，不得把运行时会跳过的 `auto_approve` 投影为可配置模式

