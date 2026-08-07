## MODIFIED Requirements

### Requirement: 页面命令具有跨平台固定副作用

每个 Cloud-to-Edge 页面命令 SHALL 具有不随平台变化的页面副作用合同。`identity.read_current_page` MUST 仅从当前页面读取会话绑定账号身份，禁止导航、重载、历史跳转或打开任何主页；`identity.read_self_profile` MAY 仅进入该会话绑定账号的规范本人主页并读取身份，MUST NOT 接受调用方提供的任意账号或作者 id；作者主页访问命令（`xiaohongshu.profile.open`，仅存在于 xiaohongshu 平台段下）SHALL 仅用于普通作者主页访问，MUST NOT 承担本人身份采集，也 MUST NOT 再接受改变其语义的 `direct` 字段。

#### Scenario: Facebook 当前页身份读取没有导航
- **WHEN** Cloud 对已协商 `identity.read_current_page` 的 Facebook 会话下发运行期本人身份采集
- **THEN** Edge/Native 从当前 Facebook 页面读取身份并返回结果
- **AND** MUST NOT 执行 `Page.navigate`、reload、history back/forward 或作者主页打开

#### Scenario: 本人主页读取只使用绑定账号
- **WHEN** Cloud 对支持 `identity.read_self_profile` 的会话下发本人身份采集
- **THEN** Edge/Native 只可从会话绑定身份推导规范本人主页并读取
- **AND** 命令 payload MUST NOT 接受可改写目标的账号 id、作者 id 或 URL

#### Scenario: profile open 不再兼任本人采集
- **WHEN** Edge 收到携带遗留 `direct` 字段的 `xiaohongshu.profile.open`
- **THEN** Edge 在浏览器/CDP 派发前返回显式不支持或协议错误
- **AND** MUST NOT 丢弃该字段后把命令当普通作者主页访问

### Requirement: 平台身份采集策略穷举且无默认回落

Cloud 平台注册表 SHALL 为每个 `PlatformId` 穷举声明本人身份采集策略：`identity.read_current_page`、`identity.read_self_profile` 或带非空原因的 unsupported。新增平台在未声明策略时 MUST 产生编译或严格合同校验失败；运行时缺少、未知或不一致的平台策略 MUST 显式拒绝或跳过采集，MUST NOT 默认使用 Xiaohongshu、Facebook 或其他平台的命令。

#### Scenario: 现有平台选择各自命令
- **WHEN** Xiaohongshu、Facebook 与 WeChat Channels 注册表被加载
- **THEN** Xiaohongshu 选择本人主页读取、Facebook 选择当前页读取、WeChat Channels 为该浏览器采集链声明 unsupported

#### Scenario: 新平台未声明策略
- **WHEN** 开发者向 `PlatformId` 增加新平台但未补身份采集策略
- **THEN** 类型检查或严格合同测试失败
- **AND** 系统 MUST NOT 在运行期以任一现有平台策略代替

### Requirement: 本人身份结果独立、可关联且决定恢复动作

运行期本人身份命令 SHALL 返回专用 `identity.observed` 结果，至少携 Cloud 生成并由 Edge 原样回传的 `captureId`、会话绑定 `accountId`、可选已验证昵称、读取来源与真实页面副作用。Cloud 仅接受与当前在途 captureId、accountId 和平台匹配的结果；当前页读取完成 MUST NOT 下发 Feed 恢复命令，仅本人主页读取产生离开 Feed 的副作用后才可执行恢复。

#### Scenario: 迟到或错账号结果被忽略
- **WHEN** Cloud 收到 captureId 不匹配、accountId 不匹配或平台不匹配的 `identity.observed`
- **THEN** 该结果不写昵称、不完成当前采集，也不触发页面恢复

#### Scenario: Facebook 就地读取完成
- **WHEN** Facebook `identity.read_current_page` 返回匹配结果且 `pageEffect=none`
- **THEN** Cloud 按非空昵称差异写规则处理结果
- **AND** MUST NOT 下发 `navigation.back`、`facebook.feed.scroll` 或 Feed refresh

#### Scenario: Xiaohongshu 本人主页读取完成
- **WHEN** Xiaohongshu `identity.read_self_profile` 返回匹配结果且页面已进入本人主页
- **THEN** Cloud 按非空昵称差异写规则处理结果并恢复 Feed
