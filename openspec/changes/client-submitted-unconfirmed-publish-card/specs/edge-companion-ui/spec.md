## ADDED Requirements

### Requirement: 发布卡显式展示已提交但公开结果未确认

Electron 陪伴界面收到当前环境的 `publish.state = submitted` 时 SHALL 将本次发布显示为独立的“已提交，平台确认中”卡片状态，并 SHALL 以本次稿件的标题、编号与提交时间覆盖发布卡主体；即使同一环境仍保存更早的 `lastPublish`，旧历史也 MUST NOT 盖住本次提交。该状态 MUST NOT 使用“已发布”文案，MUST NOT 把公开结果未确认的稿件写入已发布历史，并 MUST 保留真实 `lastPublish` 供后续失败回退或已确认发布替换。

#### Scenario: 新提交优先于旧的上次发布

- **WHEN** 当前环境已有一条历史 `lastPublish`，随后收到标题、编号和时间齐全的 `publish.state = submitted`
- **THEN** 发布卡自动展开并显示本次稿件及“已提交，平台确认中”，不继续把旧稿标题作为卡片主体
- **AND** 卡片 MUST NOT 显示“已发布”或把四个旅程节点全部标为完成

#### Scenario: 没有历史发布时仍展示提交真态

- **WHEN** 当前环境没有 `lastPublish`，但收到 `publish.state = submitted`
- **THEN** 发布卡显示本次提交而非“还没有发布过内容”空态
- **AND** 文案说明发布请求已经提交、公开结果仍待确认且无需用户重复操作

#### Scenario: 公开结果确认后转为上次发布

- **WHEN** 同一稿件在 `submitted` 后收到 `publish.state = published`
- **THEN** 发布卡按既有逻辑转为“上次发布”并以该稿件更新历史态
- **AND** 只有此时卡片才显示“已发布”并将四个旅程节点全部标为完成
