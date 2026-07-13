## MODIFIED Requirements

### Requirement: UI 事件解析结构化优先、字符串兜底且状态形状兼容
主进程 SHALL 经独立可单测模块解析核心输出为带类型 UI 事件：`[ui-event] {json}` 结构化行优先采用，既有中文日志行经映射表兜底；status 对象 MUST 保持既有字段形状向后兼容（新增 presence / publish 字段不删旧字段），既有计数递增行为不变。

#### Scenario: 结构化事件行直接采用
- **WHEN** 核心输出带 `[ui-event]` 前缀的合法 JSON 行
- **THEN** 解析结果直接驱动活动流 / 在场感 / 发布卡，不再走字符串匹配

#### Scenario: 旧日志行兜底映射保持计数行为
- **WHEN** 核心仅输出既有中文日志行（无结构化事件）
- **THEN** 活动流与计数仍按映射表工作，与改版前的计数行为一致

#### Scenario: 渲染器收到旧形状 status 不崩溃
- **WHEN** status 推送缺失新增的 presence / publish 字段
- **THEN** 渲染器按待命态安全降级渲染，不抛错、不白屏

#### Scenario: Facebook confirmed browse actions produce structured desktop events
- **WHEN** a Facebook child has actually started its enabled browse session, successfully reported `note.detail`, or confirmed `action.completed` for a like
- **THEN** it emits a structured UI event that updates the activity stream and presence projection for that child
- **AND** a successful `note.detail` contributes exactly one local view fallback increment and a confirmed like contributes exactly one local like fallback increment
- **AND** shadow, failed, already-liked, or no-target paths MUST NOT produce a success increment

#### Scenario: Facebook read activity identifies the opened content without raw identifiers
- **WHEN** a Facebook `note.detail` has a readable author nickname and post body
- **THEN** its desktop activity and presence text show bounded, whitespace-normalized author and leading-content excerpts
- **AND** when either field is unavailable, the text MUST degrade to an honest generic description and MUST NOT show a permalink or raw note ID
