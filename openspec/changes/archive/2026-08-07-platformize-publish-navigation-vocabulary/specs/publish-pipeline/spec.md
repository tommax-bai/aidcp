## RENAMED Requirements

- FROM: `### Requirement: 通用参数化发布指令协议与三处同步`
- TO: `### Requirement: 平台段参数化发布指令协议与同步`

## ADDED Requirements

### Requirement: 发布平台缺失必须 fail-closed 而非缺省小红书

发布调度与命令构造链（automation 侧）MUST NOT 以 `?? 'xiaohongshu'` 类静默缺省补齐缺失的平台：计划构造入参平台 MUST 必填；dispatcher / scheduler / 委托任务装载点在 draft 无平台时 MUST fail-closed 并给出独立原因（如 `draft_platform_missing`），MUST NOT 猜平台后继续。唯一允许的缺省在 api 发布记录 DB 读取层（早于平台列的历史行事实上均为小红书，属事实缺省而非猜测），MUST 就地注释坐实。

#### Scenario: draft 无平台不下发
- **WHEN** 发布调度器认领到一条 `platform` 缺失的 draft
- **THEN** 该 draft fail-closed 带 `draft_platform_missing` 类原因，不构造、不下发任何发布指令，MUST NOT 按小红书猜测执行

## MODIFIED Requirements

### Requirement: 平台段参数化发布指令协议与同步

系统 SHALL 按平台各以一对参数化消息驱动发帖执行层：`xiaohongshu.publish.command` / `facebook.publish.command`（cloud → edge，payload `{recordId, seq, kind, params, timeoutMs?, reason?}`）下发单条参数化原子指令，`xiaohongshu.publish.command.result` / `facebook.publish.command.result`（edge → cloud，payload `{recordId, seq, kind, ok, value?, error?, details?}`）回报单条执行结果。**平台维 MUST 只由消息名承载**：载荷 MUST NOT 携带 `platform` 字段，边缘 MUST 从消息名前缀解析平台并与本会话平台驱动核对、不符走既有 `platform_publish_executor_unavailable` 诚实失败，MUST NOT 以任何缺省平台执行。

`kind` MUST 为枚举 `PublishCommandKind`（共享词表），但**每条平台消息只接受该平台的合法子集**：xiaohongshu 形取全集（含 `set_cover` / `add_with_candidate` / `set_option` / `set_schedule` / `capture_scheduled` / `reconcile_scheduled` 等 XHS-only kind）；facebook 形只取 `navigate_entry` / `select_mode` / `upload_image` / `fill_field` / `submit_publish` / `capture_postId` 六词，非法组合 MUST 在云端类型面不可表示、在边缘 fail-closed 拒收。协议 MUST 保持「平台一条参数化消息 + `kind` 参数」，MUST NOT 为每个 `kind` 各立一条消息。两份 `src/comm/protocol.ts` MUST 逐字一致并与 `docs/protocol.md`（头部计数 + §2 表 + kind 枚举说明）同步登记，漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护暴露。

视频号（`wechat_channels`）MUST NOT 拥有发布消息名：其发布路径经 IM 回复协议、由 kernel 平台 profile 结构性拒绝，协议层不得出现零生产者的占位名。

#### Scenario: 平台一条参数化消息承载该平台全部 kind
- **WHEN** cloud 需要让 XHS 边缘执行 `fill_field` 与随后的 `submit_publish`
- **THEN** 两步都用同一条 `xiaohongshu.publish.command` 下发、靠 `kind` 与 `params` 区分，`MessageType` 不为每个 kind 各加一条，`npm run typecheck` 的穷举守护通过

#### Scenario: 载荷不再携带平台维
- **WHEN** 云端构造任一发布原子指令
- **THEN** 载荷无 `platform` 字段；平台由消息名声明，边缘按名路由到对应发布执行器；名与本会话平台不符时回 `platform_publish_executor_unavailable`，MUST NOT 静默按小红书执行

#### Scenario: 平台非法 kind fail-closed
- **WHEN** 一条 `facebook.publish.command` 携带 XHS-only 的 `set_schedule`（如经序列化边界绕过类型面）
- **THEN** 边缘拒收并回 `ok:false` 带格式/能力原因，MUST NOT 落到任何执行器，MUST NOT 回报成功

#### Scenario: 后续新增 kind 不动消息定义
- **WHEN** 后续阶段需支持一个新的执行原子（如某新表单控件）
- **THEN** 只扩 `PublishCommandKind` 枚举、对应平台合法子集与 `PublishCommandParams` 联合类型，消息定义与计数不动

#### Scenario: 协议同步缺一即失败
- **WHEN** 只改了 cloud `protocol.ts`，未同步 edge `protocol.ts` / `docs/protocol.md`
- **THEN** `npm run typecheck` 的 `Record<MessageType,true>` 穷举守护与 `AC-PROTO-*` 报漂移、构建失败，MUST NOT 合并

### Requirement: 边缘指令运行时逐条执行并每条后置校验如实回报

边缘 SHALL 以 `PublishCommandDispatcher` 逐条分发 `{platform}.publish.command`：每个 `kind` 对应一个参数化处理器，处理器 MUST 复用既有定位/执行原语与后置校验完成「定位 + 原子操作 + 后置校验」，MUST NOT 在发布层另起一套无校验的整页流程。小红书 `fill_field(content)` MUST 把普通文字与换行拆为不同输入原语：`Input.insertText` 的 `text` MUST NOT 含 CR/LF，每个正文换行 MUST 独立派发真实 Enter；Enter 后 MUST 在有界窗口内确认截至当前 Enter 的段落结构数、已写前缀和 selection 均稳定，并使 selection 连续位于正文编辑器末端，随后才可输入下一段。段落或光标无法稳定 MUST 清空字段并回 `ok:false`，MUST NOT 继续到 `submit_publish`。正文最终回读 MUST 在移除 URL 后只以 Unicode 字母和数字组成的语义文字比较，忽略 DOM 标签、空白/换行、标点与 emoji；按 Unicode code point 计算的 Levenshtein 相似度 MUST `>= 0.90` 才可放行，语义投影为空时 MUST 回退非空的既有精确校验。每条指令执行后边缘 MUST 按真实结果回报一条对应 `recordId+seq` 的 `{platform}.publish.command.result`：成功带 `ok:true` 与 `value`，失败带 `ok:false` 与真实 `error`（如 `no_target` / `post_validate_failed` / `engine_error: content_newline_unstable`），`details` 带可得的 `actionId/outcome/attempts`。

#### Scenario: 逐条执行逐条回报
- **WHEN** cloud 依次下发 `navigate_entry`、`fill_field(title)`、`fill_field(content)`
- **THEN** 边缘 `PublishCommandDispatcher` 逐条分发到对应处理器，每条经定位、操作与后置校验后回一条带相同 `recordId+seq` 的 `{platform}.publish.command.result`，`ok/value/error` 反映该条真实结果

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
- **THEN** 边缘回报 `{platform}.publish.command.result {ok:false, error:'post_validate_failed'}` 及可得 details，MUST NOT 回报 `ok:true`

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

### Requirement: 指令与结果按 recordId+seq 关联

系统 SHALL 以 `recordId + seq` 作为指令与结果配对的**业务级永久关联键**：`{platform}.publish.command` 与其对应 `{platform}.publish.command.result` MUST 携带相同的 `recordId` 与 `seq`，`CommandSequencer` MUST 以 `recordId:seq` 为键维护 pending map 并据此配对回报、推进序列。`envelope.id` 仅供日志追踪、MUST NOT 用于业务关联。`CommandSequencer` MUST 在结果到达时按键 resolve 并删除 pending 项；结果在 `timeoutMs`（缺省 30s）内不到达时 MUST reject 并自动清理该 pending 项、记 error 日志，pending map MUST NOT 泄漏。

#### Scenario: recordId+seq 配对请求与结果
- **WHEN** cloud 下发 `{platform}.publish.command {recordId:100, seq:3, kind:'fill_field'}`，边缘回报 `{platform}.publish.command.result {recordId:100, seq:3, ok:true}`
- **THEN** `CommandSequencer.onResult` 以 `recordId:seq`（`100:3`）找到对应 pending 项并 resolve，推进到下一条指令

#### Scenario: envelope.id 不用于关联
- **WHEN** 同一发布的多条指令复用或重发导致 `envelope.id` 变化、但 `recordId+seq` 不变
- **THEN** 配对仍以 `recordId+seq` 为准、不受 `envelope.id` 影响；`envelope.id` 仅落日志用于追踪单次请求

#### Scenario: 结果到达即释放 pending 项
- **WHEN** 某 `seq` 的结果正常到达
- **THEN** `onResult` 按 `recordId:seq` 找到 pending 项 resolve 后将其从 map 删除，不残留

#### Scenario: 超时清理不泄漏
- **WHEN** 边缘崩溃 / 断连使某 `seq` 结果在 `timeoutMs`（缺省 30s）内不到达
- **THEN** 该 pending 项超时 reject、自动从 map 清理并记 error 日志，pending map MUST NOT 泄漏

### Requirement: 边缘实装配图与元数据 kind 处理器并逐条后置校验

边缘 SHALL 实装 stage-1 预留为 `kind_not_implemented` 的处理器：`upload_image`（图 URL → 下载到 `/tmp` → CDP 文件输入桥 →
后置校验图已进入 → 清理临时文件）、`set_cover`、`set_option`（按 `optionKind` 路由 `visibility` / `permissions` / 各声明开关/单选）、
`set_schedule`（定位时间选择器填 `publishTime`）。每个处理器 MUST 复用既有 `LocatingEngine` 三道闸做「定位 + 原子操作 + 后置校验」，
MUST 在执行后按真实结果回报 `{platform}.publish.command.result`（成功 `ok:true` + `value`，失败 `ok:false` + 真实 `error` 如 `no_target` /
`post_validation_failed` / `upload_failed`）。同时 SHALL 放开 v1 整页路径的带图硬拒。MUST NOT 谎报成功、MUST NOT 在无法定位时回 `ok:true`。

#### Scenario: upload_image 走下载+CDP 桥并后置校验
- **WHEN** 边缘收到 `upload_image {imageUrl}`
- **THEN** 处理器下载图到 `/tmp`、经 CDP 文件输入桥喂给上传控件、后置校验图已出现在编辑区、清理临时文件，回报 `{platform}.publish.command.result {ok:true, value}`；定位/上传/校验任一失败回 `ok:false` + 真实 `error`

#### Scenario: set_option 按 optionKind 路由并校验
- **WHEN** 边缘收到 `set_option {optionKind:'visibility', optionValue:'self_only'}`
- **THEN** 处理器经 `LocatingEngine` 定位对应开关/单选、设置后后置校验当前选中态等于期望值，回报 `ok:true`；校验不符回 `ok:false, error:'post_validation_failed'`

#### Scenario: 放开 v1 带图硬拒
- **WHEN** v1 整页路径收到带图 payload（`images.length > 0`）
- **THEN** MUST NOT 再返回 `images are not supported in phase one` 硬拒，而是走配图流程（或经指令驱动路径处理），带图发布端到端可达

#### Scenario: 红线反例——配图失败谎报有图（禁止）
- **WHEN** 下载失败 / CDP 上传桥失败 / 后置校验不到图，但处理器回 `ok:true` 或伪造一个 `value` 掩盖失败
- **THEN** MUST 视为违规、不予合入；MUST 回 `ok:false` + 真实 `error`（`upload_failed` / `no_target` / `post_validation_failed`），由云端降级纯文字，绝不静默假成功
