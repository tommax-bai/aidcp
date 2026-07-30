## MODIFIED Requirements

### Requirement: 慢启动状态与开关在今日进展卡内如实呈现

客户端 SHALL 在「今日进展」摘要卡内以常驻脚注行呈现当前选中环境的慢启动状态、开关、active/next revision 与 Cloud 返回的固定七日策略。该行 MUST NOT 位于默认收起区或会因窗口无数据而整块隐藏的容器内；慢启动允许在账号登录前按环境预先设置。

该行 MUST NOT 置于自定义标题栏内。标题栏空间与窄窗约束不变，环境级配置也不需要挤入标题区域。

`ui.snapshot` 或 env-scoped 读取的慢启动字段与完整 policy revision SHALL 为权威环境配置；字段整体缺省仍表示未知。客户端 MUST NOT 把未知渲染为“未开启”，MUST NOT 回落本地七日常量。当投影同时包含 `binding_unknown` 与明确 `state` 时，`state` 表达环境配置，`binding_unknown` 表达当前没有账号执行对象；两者 MUST NOT 互相覆盖或被压成一个禁用态。active revision 与全局 current revision 不同时，客户端 SHALL 分别标为“当前七日使用”和“下次开启采用”，不得混拼数值。

客户端 MUST NOT 把当前账号称为“新账号”或推断平台年龄，也 MUST NOT 暗示慢启动会使动作变慢、更像真人或改变节奏。慢启动只改变当前环境账号的每日额度上限，不进节奏系数；实际额度继续取慢启动派生上限与当前风险档位中更严者。

#### Scenario: 字段未到时不渲染而非默认关闭

- **WHEN** 客户端尚未取得当前环境的慢启动字段
- **THEN** 该脚注行整行隐藏，MUST NOT 渲染为未勾选开关，无论经过多久

#### Scenario: 开启中显示天数版本与总天数

- **WHEN** 云端投影 `state=active`、`day=3`、`totalDays=7`、`binding=true` 且 active policy 完整
- **THEN** 客户端显示“慢启动 · 第 3/7 天”、active revision、Cloud 返回的当日数字且开关为勾选态

#### Scenario: 曲线不比档位更严时如实说明

- **WHEN** 云端投影 `state=active`、`day=5`、`binding=false`
- **THEN** 客户端如实标注当前档位已更严、慢启动不额外限制
- **AND** MUST NOT 表述为正在压低配额

#### Scenario: 环境已配置但没有账号时保持开关真态

- **WHEN** 云端投影 `state=active`、`eligible=false`、`ineligibleReason=binding_unknown`
- **THEN** 客户端保持开关勾选且可操作，并说明设置属于该环境、登录账号后按 active policy 生效
- **AND** MUST NOT 显示为未开启、写入失败、待下发边缘或配额已被压低

#### Scenario: 毕业态显式告知而非静默消失

- **WHEN** 云端投影 `state=graduated`
- **THEN** 客户端显示已完成态并给出恢复日期，开关仍如实反映环境配置为开启
- **AND** 徽章 MUST NOT 静默消失、MUST NOT 显示为未勾选

#### Scenario: 平台或云端不适用时禁用并说明原因

- **WHEN** 云端投影 `eligible=false` 且原因为平台不支持、平台未知、客户接口未启用或云端全局停用，而非 `binding_unknown`
- **THEN** 开关禁用且按原因如实说明，MUST NOT 静默禁用

#### Scenario: 断连时降级而非清空

- **WHEN** 云端连接断开，客户端保留当前环境上一次慢启动状态和完整 policy
- **THEN** 客户端标注状态与策略可能已过期并禁用开关
- **AND** MUST NOT 把停止更新渲染成已关闭、未知或当前最新

#### Scenario: 开关点击不触发今日进展折叠

- **WHEN** 用户点击该脚注行内的开关或文字标签
- **THEN** 今日进展展开/收起状态保持不变，开关恰好切换一次

#### Scenario: 规则说明常驻可读且说清优先关系

- **WHEN** 该脚注行可见
- **THEN** 常驻说明明确该设置属于当前环境、每日额度按 Cloud policy 逐日放开、第 7 天自动恢复，且实际额度取策略与当前账号档位中更严的一个
- **AND** MUST NOT 依赖悬浮或额外交互才能看到

### Requirement: 慢启动卡 SHALL 分别标注云端真态与本机用量的新鲜度

「今日节奏」卡上有两条来源不同的数据，客户端 SHALL 分别表达其新鲜度，MUST NOT 用其中一条的陈旧去否定另一条：

- **慢启动真态**（state / day / since / binding / active policy revision / 七日策略 / 当日上限）：由云端计算，写入回执当场刷新，边缘离线时**依然有效**。
- **用量计数**（今日已发生多少次动作）：由边缘上报，边缘离线时**确实陈旧**，SHALL 明确标注为可能已过期。

边缘离线 MUST NOT 被表述为慢启动状态不可信或开关不可用。慢启动真态 MUST NOT 被标注为「等待本机应用」「已保存待下发」或任何等价措辞——其执行体在云端，云端写入成功即为已生效，标注一个不存在的中间态与谎报成功同属不诚实。Cloud policy 响应超过声明 freshness 后，客户端 MAY 保留完整 last-good 供参考，但 MUST 单独标为 stale，MUST NOT 声称仍是全局当前。

#### Scenario: 离线时用量陈旧但开关真态照常呈现

- **WHEN** 当前选中环境的边缘未连接，且客户端持有该环境的新鲜慢启动真态
- **THEN** 客户端 MUST 照常呈现慢启动徽章、policy revision 与开关真态
- **AND** MUST 就地标注用量计数可能已过期
- **AND** MUST NOT 把整行呈现为不可用或状态不可信

#### Scenario: 离线写入成功不得标注为待应用

- **WHEN** 边缘离线时慢启动写入成功并返回写后真态与完整 policy
- **THEN** 客户端 MUST 呈现为已生效
- **AND** MUST NOT 显示「已保存，等待本机应用」或任何等价的二态措辞

#### Scenario: 陈旧用量 MUST NOT 被当作慢启动真态

- **WHEN** 客户端只持有该环境的陈旧用量计数
- **THEN** 客户端 MUST NOT 据此推算慢启动天数、版本、绑定性或当日上限

#### Scenario: 陈旧策略保留为参考但不冒充当前

- **WHEN** 客户端曾取得完整 policy 但其 freshness 已过期且刷新失败
- **THEN** 客户端 MAY 保留整份 last-good 表并显式标 stale/asOf
- **AND** MUST NOT 将其标为当前最新、拆字段与其它 revision 拼接或据此触发动作

### Requirement: 慢启动开关必须即时反馈提交过程并以云端真态收敛

客户端 SHALL 在用户拨动环境级慢启动开关后立即显示与目标动作一致的提交中样式，并在云端返回前明确说明正在等待确认。该临时态 MUST 只表达请求在途，MUST NOT 冒充慢启动已经生效，MUST NOT 本地推算天数、版本、绑定状态或计划量。

写入在途期间，客户端 MUST 禁止同一环境重复提交，且 MUST NOT 让旧的 `ui.snapshot` 把目标开关或提交中样式拨回。临时态及错误 MUST 按环境隔离。

#### Scenario: 开启请求立即进入等待确认样式

- **WHEN** 用户在一个可用的 Facebook 环境中将慢启动从关闭拨为开启，且云端请求尚未完成
- **THEN** 开关 MUST 在同一交互周期显示为目标开启态并被暂时禁用
- **AND** 同一行 MUST 显示“正在开启”及等待云端确认的可见反馈
- **AND** 客户端 MUST NOT 在此时显示“第 1/7 天”、policy revision 或任何本地推算的生效计划量

#### Scenario: 关闭请求立即进入等待确认样式

- **WHEN** 用户将慢启动从开启拨为关闭，且云端请求尚未完成
- **THEN** 开关 MUST 立即显示为目标关闭态并被暂时禁用
- **AND** 同一行 MUST 显示“正在关闭”及等待云端确认的可见反馈

#### Scenario: 在途旧快照不得覆盖目标样式

- **WHEN** 慢启动写入仍在途，客户端收到该环境写入前的旧 `ui.snapshot`
- **THEN** 客户端 MUST 保留当前目标开关与提交中样式
- **AND** 权威快照数据本身 MUST NOT 被本地临时态篡改

#### Scenario: 成功后立即采用完整写后真态

- **WHEN** 云端成功回包并携带该环境的写后 `slowStart`、完整 active/next policy `days` 与顶层 `dayQuotas`
- **THEN** 客户端 MUST 清除提交中样式，并立即按同一回执渲染慢启动徽章、revision、七日 `days[].dailyCaps` 和当日最终额度
- **AND** 客户端 MUST NOT 等待下一次周期性快照才显示已生效结果

#### Scenario: 失败后恢复原状态并保留原因

- **WHEN** 云端拒绝写入、请求异常或超时
- **THEN** 客户端 MUST 清除提交中样式并恢复点击前的权威开关、revision 与徽章状态
- **AND** 同一行 MUST 保留可读的失败原因，直至用户再次提交或该环境反馈被明确替换

#### Scenario: 环境切换不串写反馈

- **WHEN** 环境 A 的慢启动请求在途期间用户切换到环境 B
- **THEN** 环境 B MUST NOT 显示环境 A 的提交中样式、目标开关、policy 或失败原因
- **AND** 环境 A 的回执 MUST NOT 改写环境 B 的状态

## ADDED Requirements

### Requirement: 客户端模式数字只从完整 Cloud revision 动态渲染

Edge SHALL 从当前环境的 customer-auth HTTP 投影读取完整、同 revision 的规则模式摘要和慢启动七日策略。规则摘要 SHALL 分开使用 Cloud 返回的 owner current、execution-target applied current、account adopted policy envelope 及其 `viewThreshold`、`joinEveryNRounds`；慢启动 SHALL 分开使用 active 与 next-enable policy envelope 的 `days[7].dailyCaps`，并渲染固定七天和 `view`、`search`、`like`、`comment`、`follow`、`publish`、`join_group` 七个动作。顶层 `dayQuotas` 只渲染为有唯一绑定账号时的当日最终额度，MUST NOT 当作七日矩阵。renderer、preload、main 和本地模板 MUST NOT 保存或推断 `5/2` 与 Facebook 七日额度作为权威 fallback。

每份 policy MUST 整体验证 `envKey`、`kind`、`revision`、`schemaVersion`、`complete=true`、完整 typed payload、`asOf`、`freshUntil`、可选 digest 与固定范围。缺字段、重复/缺 day/action、非法值或 revision 混合时，数字详情整块 SHALL 为 unknown；现有 `enabled` 开关真态如果仍可证 MAY 独立显示，MUST NOT 因详情缺失被伪装为关闭。新 Edge 连接旧 Cloud 且 additive 字段缺失时仍可读取和关闭既有开关，但 SHALL 显示“当前规则详情暂不可用”，不得开启或采用 non-legacy policy。

支持该投影的新 Edge SHALL 在已认证的环境读取、写入和程序化创建完成请求上发送固定 header `X-AIDCP-Client-Capabilities: facebook_mode_policy_projection_v1`。该 token 只声明客户端能完整校验和诚实渲染动态数字，不赋予数字写权限，也不改变 Native/Protocol v2。Cloud 返回 capability missing/unsupported/stale blocker 时，Edge SHALL 保留最近一次权威开关真态并禁用 non-legacy enable/adoption，不得隐藏 blocker 或本地伪造兼容。

客户端 SHALL 在环境选择、页面重新进入、成功写回、Cloud 报告 revision 变化或声明的有界 freshness 到期时刷新 policy。last-good 只能整份缓存并携带 envKey+revision；环境 A 或 revision A 的晚到响应 MUST NOT 更新环境 B 或较新的 revision。

#### Scenario: 非默认规则数字无需 Edge 发版即可显示

- **WHEN** Cloud 为当前环境返回完整 revision 9，`viewThreshold=8`、`joinEveryNRounds=3`
- **THEN** Edge 显示“每 8 次确认浏览触发 1 次点赞；每 3 轮追加固定 join-contact”
- **AND** Edge 不按本地 `5/2` 触发、校验或替换这两个数字

#### Scenario: 非默认七日表包含 search

- **WHEN** Cloud 返回完整非默认 7×7 slow-start policy
- **THEN** Edge 逐格显示该 revision 的七日 daily caps 并包含 search 列
- **AND** 不使用 HTML 中复制的旧数值补任何单元格

#### Scenario: 旧 Cloud 缺少 additive policy 字段

- **WHEN** customer-auth 返回可证的模式开关真态但没有完整 policy 字段
- **THEN** Edge 保留开关真态并把数字详情显示为暂不可用
- **AND** MUST NOT 回落编译期规则摘要或七日表

#### Scenario: 新 Edge 以固定能力标记刷新环境观察

- **WHEN** 新 Edge 以已认证 customer-auth 请求读取或写入当前环境模式配置
- **THEN** 请求携带 `facebook_mode_policy_projection_v1`，Cloud 只为该 owned envKey 记录服务端观察时间
- **AND** Edge 不提交 revision、数字、动作或 Prompt，也不把 capability 当运行授权

#### Scenario: owner current 尚未传播到 execution target

- **WHEN** Cloud 返回 owner current revision 8、target applied current revision 7 与 propagation lag
- **THEN** Edge 分开显示“已发布 8”和“当前目标已应用 7”
- **AND** 不声称账号可采用 revision 8，也不把两份 envelope 的数字拼接

#### Scenario: 非法策略整块未知

- **WHEN** 七日策略缺少一个 action、混入两个 revision 或包含非法数字
- **THEN** 整份策略详情显示 unknown 并记录具名诊断
- **AND** 客户端不得渲染其余“看似有效”的单元格

#### Scenario: 有界刷新看到后台发布

- **WHEN** Edge 已缓存一次成功 policy，之后 Cloud 全局 current revision 变化且缓存到达刷新边界
- **THEN** Edge 重新读取权威投影，并按 active/adopted/next 语义更新显示
- **AND** 成功缓存不得在整个进程生命周期永久阻止刷新

#### Scenario: 晚到响应不串环境或倒退版本

- **WHEN** 环境 A revision 4 的读取在用户切换到环境 B 或 B 已取得 revision 5 后才返回
- **THEN** 该响应只可更新 A revision 4 对应缓存
- **AND** 不改变 B 的开关、数字、revision、freshness 或错误状态
