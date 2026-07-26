## MODIFIED Requirements

### Requirement: 边缘指令运行时逐条执行并每条后置校验如实回报

边缘 SHALL 以 `PublishCommandDispatcher` 逐条分发 `publish.command`：每个 `kind` 对应一个参数化处理器，处理器 MUST 复用既有定位/执行原语与后置校验完成「定位 + 原子操作 + 后置校验」，MUST NOT 在发布层另起一套无校验的整页流程。小红书 `fill_field(content)` MUST 把普通文字与换行拆为不同输入原语：`Input.insertText` 的 `text` MUST NOT 含 CR/LF，每个正文换行 MUST 独立派发真实 Enter；Enter 后 MUST 在有界窗口内确认截至当前 Enter 的段落结构数、已写前缀和 selection 均稳定，并使 selection 连续位于正文编辑器末端，随后才可输入下一段。段落或光标无法稳定 MUST 清空字段并回 `ok:false`，MUST NOT 继续到 `submit_publish`。正文最终回读 MUST 在移除 URL 后只以 Unicode 字母和数字组成的语义文字比较，忽略 DOM 标签、空白/换行、标点与 emoji；按 Unicode code point 计算的 Levenshtein 相似度 MUST `>= 0.90` 才可放行，语义投影为空时 MUST 回退非空的既有精确校验。每条指令执行后边缘 MUST 按真实结果回报一条对应 `recordId+seq` 的 `publish.command.result`：成功带 `ok:true` 与 `value`，失败带 `ok:false` 与真实 `error`（如 `no_target` / `post_validate_failed` / `engine_error: content_newline_unstable`），`details` 带可得的 `actionId/outcome/attempts`。

#### Scenario: 逐条执行逐条回报
- **WHEN** cloud 依次下发 `navigate_entry`、`fill_field(title)`、`fill_field(content)`
- **THEN** 边缘 `PublishCommandDispatcher` 逐条分发到对应处理器，每条经定位、操作与后置校验后回一条带相同 `recordId+seq` 的 `publish.command.result`，`ok/value/error` 反映该条真实结果

#### Scenario: 小红书多段正文换行独立输入
- **WHEN** `fill_field(content)` 正文包含单换行、连续空行及换行后的普通文字
- **THEN** 每个换行各对应一次 Enter，所有 `Input.insertText` 参数均不含 CR/LF；Enter 后确认段落结构数、前缀与末端 selection 才继续，最终正文段落与字符顺序等于输入语义

#### Scenario: 换行后旧 selection 回退时归尾再继续
- **WHEN** 小红书 ProseMirror 在 Enter 后把 selection 恢复到上一段尾字之前
- **THEN** 边缘检测到光标不在末端并显式归尾，至少连续两次确认末端稳定后才输入下一段，上一段尾字不会被后续文字顶到文末

#### Scenario: 末段段落内 caret 视为编辑器语义末端
- **WHEN** Enter 已创建新的末段 `<p>`，selection 折叠在该段落内且 caret 之后没有实际文本，但其 Range boundary container 与外层 `.ProseMirror` 不同
- **THEN** 边缘 MUST 将其判为正文末端；若需归尾 MUST collapse 到末段内部，MUST NOT 因跨容器边界不严格相等而误报 `content_newline_unstable`

#### Scenario: 段落或光标无法稳定则清场失败
- **WHEN** Enter 被页面吞掉、已写前缀丢失、编辑器消失或 selection 在有界窗口内持续无法稳定到末端
- **THEN** `fill_field(content)` 清空已写正文并回 `ok:false` 与真实错误，云端停在该步且不下发 `submit_publish`

#### Scenario: 处理器复用而非无校验整页脚本
- **WHEN** 实现 `fill_field` 处理器
- **THEN** 它复用既有 CDP 输入、清场、轮询与 validator 原语并保留后置校验，而非新增一条不读回结果的整页脚本

#### Scenario: 后置校验失败如实回报
- **WHEN** `fill_field` 执行后读 DOM 校验不到刚填入的内容（后置校验失败）
- **THEN** 边缘回报 `publish.command.result {ok:false, error:'post_validate_failed'}` 及可得 details，MUST NOT 回报 `ok:true`

#### Scenario: 富文本附加内容不参与正文比较
- **WHEN** 小红书将正文中的 URL、emoji、换行或富文本标签改写/移除，但归一化后的中文、英文和数字语义文字保持一致
- **THEN** 最终正文回读 MUST 视为 100% 语义一致并允许 `fill_field(content)` 成功

#### Scenario: 正文 90% 相似度边界放行
- **WHEN** 最终回读的归一化语义文字与输入正文的 Levenshtein 相似度恰好为 90%
- **THEN** `fill_field(content)` MUST 放行；若相似度低于 90% 则 MUST 清场并回 `ok:false`

#### Scenario: 英文和数字仍属于语义文字
- **WHEN** 正文包含 `SenseNova`、`7B`、`MoT`、`OCR` 等英文或数字且页面吞掉其中超过容差的内容
- **THEN** 最终回读 MUST 把这些字符计入差异，MUST NOT 因汉字仍完整而误报成功

#### Scenario: 红线反例——谎报成功（禁止）
- **WHEN** 某指令找不到目标元素、换行后光标未稳定或最终后置校验失败
- **THEN** 边缘 MUST NOT 伪造 `ok:true` 或用兜底值掩盖失败；MUST 回报 `ok:false` 与真实 `error`，自愈不自残
