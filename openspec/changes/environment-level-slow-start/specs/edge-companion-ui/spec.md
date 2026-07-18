## MODIFIED Requirements

### Requirement: 慢启动状态与开关在今日进展卡内如实呈现

客户端 SHALL 在「今日进展」摘要卡内以常驻脚注行呈现当前选中环境的慢启动状态与开关。该行 MUST NOT 位于默认收起区或会因窗口无数据而整块隐藏的容器内；慢启动允许在账号登录前按环境预先设置。

该行 MUST NOT 置于自定义标题栏内。标题栏空间与窄窗约束不变，环境级配置也不需要挤入标题区域。

`ui.snapshot` 或 env-scoped 读取的慢启动字段 SHALL 为权威环境配置；字段整体缺省仍表示未知。客户端 MUST NOT 把未知渲染为“未开启”。当投影同时包含 `binding_unknown` 与明确 `state` 时，`state` 表达环境配置，`binding_unknown` 表达当前没有账号执行对象；两者 MUST NOT 互相覆盖或被压成一个禁用态。

客户端 MUST NOT 把当前账号称为“新账号”或推断平台年龄，也 MUST NOT 暗示慢启动会使动作变慢、更像真人或改变节奏。慢启动只改变当前环境账号的每日额度上限，不进节奏系数。

#### Scenario: 字段未到时不渲染而非默认关闭

- **WHEN** 客户端尚未取得当前环境的慢启动字段
- **THEN** 该脚注行整行隐藏，MUST NOT 渲染为未勾选开关，无论经过多久

#### Scenario: 开启中显示天数与总天数

- **WHEN** 云端投影 `state=active`、`day=3`、`binding=true`
- **THEN** 客户端显示“慢启动 · 第 3/7 天”且开关为勾选态

#### Scenario: 曲线不比档位更严时如实说明

- **WHEN** 云端投影 `state=active`、`day=5`、`binding=false`
- **THEN** 客户端如实标注当前档位已更严、慢启动不额外限制
- **AND** MUST NOT 表述为正在压低配额

#### Scenario: 环境已配置但没有账号时保持开关真态

- **WHEN** 云端投影 `state=active`、`eligible=false`、`ineligibleReason=binding_unknown`
- **THEN** 客户端保持开关勾选且可操作，并说明设置属于该环境、登录账号后按曲线生效
- **AND** MUST NOT 显示为未开启、写入失败、待下发边缘或配额已被压低

#### Scenario: 毕业态显式告知而非静默消失

- **WHEN** 云端投影 `state=graduated`
- **THEN** 客户端显示已完成态并给出恢复日期，开关仍如实反映环境配置为开启
- **AND** 徽章 MUST NOT 静默消失、MUST NOT 显示为未勾选

#### Scenario: 平台或云端不适用时禁用并说明原因

- **WHEN** 云端投影 `eligible=false` 且原因为平台不支持、平台未知、客户接口未启用或云端全局停用，而非 `binding_unknown`
- **THEN** 开关禁用且按原因如实说明，MUST NOT 静默禁用

#### Scenario: 断连时降级而非清空

- **WHEN** 云端连接断开，客户端保留当前环境上一次慢启动状态
- **THEN** 客户端标注状态可能已过期并禁用开关
- **AND** MUST NOT 把停止更新渲染成已关闭或未知

#### Scenario: 开关点击不触发今日进展折叠

- **WHEN** 用户点击该脚注行内的开关或文字标签
- **THEN** 今日进展展开/收起状态保持不变，开关恰好切换一次

#### Scenario: 规则说明常驻可读且说清优先关系

- **WHEN** 该脚注行可见
- **THEN** 常驻说明明确该设置属于当前环境、每日额度按曲线逐日放开、第 7 天自动恢复，且实际额度取曲线与当前账号档位中更严的一个
- **AND** MUST NOT 依赖悬浮或额外交互才能看到

### Requirement: 未绑定账号的环境 SHALL 可预设并看懂慢启动

当云端就某环境返回明确环境 `state` 且 `ineligibleReason=binding_unknown` 时，客户端 SHALL 渲染慢启动整行并保持开关可操作。客户端 SHALL 将“环境配置已保存”和“当前没有账号可被 clamp”分开表达。

该状态 MUST NOT 表现为整行隐藏、开关禁用、写入失败或“已保存待下发”。开启时显示“已为此环境开启，登录账号后按曲线生效”；关闭时说明可以在登录账号前先为此环境开启。客户端 MUST NOT 展示 `binding`、当日上限或“已压低”等只有 controller 才能确认的内容。

客户端 MUST NOT 因环境从未连接而跳过该行；没有活快照时 SHALL 经不依赖边缘的 env-scoped 读取取得环境配置态。

#### Scenario: 未绑定且已开启时显示环境配置

- **WHEN** 用户选中自己拥有、未绑定账号且环境投影 `state=active` 的 Facebook 环境
- **THEN** 慢启动整行可见，开关勾选且可点击
- **AND** 文案说明登录账号后生效，MUST NOT 声称当前配额已被压低

#### Scenario: 未绑定且关闭时允许预先开启

- **WHEN** 用户选中自己拥有、未绑定账号且环境投影 `state=off` 的 Facebook 环境
- **THEN** 慢启动整行可见，开关未勾选且可点击
- **AND** 用户开启后客户端提交 env-scoped PUT，不要求先启动浏览器或完成登录

#### Scenario: 从未启动的环境经云端读取渲染出该行

- **WHEN** 用户选中一个边缘从未连接、因而没有活快照的 Facebook 环境
- **THEN** 客户端经 env-scoped 读取取得慢启动环境配置并渲染该行
- **AND** MUST NOT 因缺少边缘快照而隐藏或默认关闭

#### Scenario: 多来源不得逐字段拼接

- **WHEN** 同一环境同时存在活快照、env-scoped 读取结果与写入回执
- **THEN** 客户端按既定优先级整体采用其中一个来源
- **AND** MUST NOT 把不同来源字段合并成任何来源都未报告的混合状态
