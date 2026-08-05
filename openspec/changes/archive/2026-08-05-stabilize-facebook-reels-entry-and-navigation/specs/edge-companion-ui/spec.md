## MODIFIED Requirements

### Requirement: 开发者详情展示安全且阶段诚实的引擎命令诊断

客户端 SHALL 在“开发者详情”中为当前环境展示 Cloud 主动下发到 Edge 的命令诊断。每条诊断 SHALL 包含接收时间、命令类型、当前可证明阶段、安全摘要和短关联标识，并 MUST 明确区分已收到、已拒绝、已交给执行器及 Edge 接收层能够直接观测的步骤结果。`received` 或 `dispatched` MUST NOT 被表述为命令已经执行成功、业务已经完成或平台已经确认。

命令摘要 MUST 由逐命令字段白名单生成。`page.scroll{reason:'facebook_reels_primary'}` 与 `page.scroll{reason:'empty_feed_reels_fallback'}` SHALL 使用“进入 Reels”命令名称，并分别使用固定的主入口或 Feed 结束回退摘要；其它 `page.scroll` SHALL 保留“页面滚动 / 滚动当前页面”。正文、标题、评论、私信、搜索词、群聊码、Cookie、Token、二维码、截图内容、完整 URL、浏览器调试地址、账号身份字段、任务永久键和原始 payload MUST NOT 进入命令诊断事件、renderer 状态或可见诊断行。文本字段只可展示有界字符数，URL 只可展示是否存在，安全枚举和有界计数可按需展示。未知命令或新增 payload 字段 MUST 默认不展示内容。

诊断 SHALL 仅保存在 Edge 本机内存中，按环境隔离并具有数量与时间双重上限；它 MUST NOT 进入普通活动流、Cloud 数据库或自动化回执。旧客户端状态缺少诊断字段时界面 MUST null-safe 降级。

#### Scenario: 已登记命令显示接收与交付边界

- **WHEN** 当前环境收到一条已登记、通过校验且存在本地处理器的主动命令
- **THEN** 开发者详情出现该命令，并将阶段更新为“已交给执行器”
- **AND** 界面明确该阶段不表示执行成功或平台确认

#### Scenario: Reels 主入口显示导航意图

- **WHEN** Edge 收到 `page.scroll{reason:'facebook_reels_primary'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的主浏览入口摘要
- **AND** 阶段仍只显示 Edge 已收到或已交付的事实，不宣称已经进入 Reels

#### Scenario: Feed 结束回退显示导航意图

- **WHEN** Edge 收到 `page.scroll{reason:'empty_feed_reels_fallback'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的 Feed 结束回退摘要
- **AND** 不把该命令显示为普通页面滚动

#### Scenario: 普通页面滚动保留原文案

- **WHEN** `page.scroll` 不携带任一 Reels 入口 reason
- **THEN** 开发者详情继续显示“页面滚动 / 滚动当前页面”

#### Scenario: 非法或未协商命令诚实显示拒绝

- **WHEN** Edge 收到未登记、能力未协商、payload 非法或没有本地处理器的主动命令
- **THEN** 诊断阶段显示“已拒绝”及固定安全原因，不显示已执行或成功
- **AND** 诊断行为不得改变原有 fail-closed 路由结果

#### Scenario: 只有可直接观测的步骤才显示结果

- **WHEN** `plan.response` 的顺序步骤在 EdgeClient 内完成并得到逐步结果
- **THEN** 对应诊断可更新为“步骤已完成”或“步骤失败”
- **AND** 该结果不得表述为整项业务完成或平台结果已确认

#### Scenario: 异步处理器不猜测终态

- **WHEN** 命令已经交给一个返回 `void` 或自行异步执行的业务处理器
- **THEN** 诊断停留在“已交给执行器”，直到未来有显式结果事件
- **AND** 客户端不得依据交付动作自行补造成功或失败

#### Scenario: 敏感 payload 只产生白名单摘要

- **WHEN** 评论、回复、发布、搜索、验证码或导航命令携带文本、账号标识、任务键、图片、坐标或完整 URL
- **THEN** 命令诊断只展示固定动作说明、允许的枚举、有界数量或文本字符数
- **AND** renderer 状态和可见诊断行中不存在上述原始内容或完整 payload

#### Scenario: 多环境命令诊断不串号

- **WHEN** 环境 A 与环境 B 同时收到不同命令且用户在二者之间切换
- **THEN** 开发者详情只展示当前选中环境的命令诊断
- **AND** 每个环境分别执行最多 50 条且最长 30 分钟的保留规则

#### Scenario: 普通活动流不展示接收噪声

- **WHEN** Edge 收到、拒绝或交付一条引擎命令
- **THEN** 该接收诊断只出现在开发者详情
- **AND** “今天做了这些”不得因此新增一条动作成功、失败或处理中记录
