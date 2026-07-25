## MODIFIED Requirements

### Requirement: 昵称采集只在完整浏览器启动后的首个 feed 卡片触发

For XHS **and Facebook** accounts, cloud SHALL treat platform nickname capture as a startup-time browser readiness step. It MUST arm nickname capture only after a full browser startup or full browser restart reaches feed readiness and the first `page.cards` for that browser generation is observed. Cloud MUST NOT arm nickname capture on cloud hello, cloud WebSocket reconnect, cold-standby cloud recovery, or other transport-only lifecycle events. Each browser generation SHALL trigger nickname capture at most once.

采集**时机**跨平台统一（同一「首个 feed 卡片 / 浏览器代号」触发点、同一去重与有界重试）；采集**命令与副作用**由 Cloud 平台注册表穷举选择——XHS 下发 `identity.read_self_profile` 并在匹配结果后恢复 Feed，Facebook 下发 `identity.read_current` 且完成后保持当前页。两者 SHALL 经专用、可关联的 `identity.observed` 完成同一非空昵称差异持久化路径，MUST NOT 复用普通作者 `profile.open` / `profile.detail`。触发后的命令差异 MUST NOT 改变时机、去重、重试上界或超时兜底。

#### Scenario: 完整浏览器启动后首个 page.cards 触发一次采集
- **WHEN** a full browser startup or full browser restart reaches the feed and edge reports the first `page.cards` for that browser generation
- **THEN** cloud arms and runs nickname capture once for that browser generation

#### Scenario: Facebook 与 XHS 同一时机触发不同命令
- **WHEN** 一个 Facebook 或 Xiaohongshu 连接在完整浏览器启动后报出该代号的首批 `page.cards`
- **THEN** cloud 在同一时机按平台注册策略武装一次本人昵称采集
- **AND** Facebook 只可收到 `identity.read_current`，Xiaohongshu 只可收到 `identity.read_self_profile`

#### Scenario: cloud reconnect 不触发昵称采集
- **WHEN** an existing browser/core session only reconnects the cloud WebSocket
- **THEN** cloud MUST NOT arm nickname capture solely because of hello/reconnect

#### Scenario: 冷待机内部恢复云连接不触发昵称采集
- **WHEN** an environment remains in cold standby and only cloud connectivity is recovering
- **THEN** cloud MUST NOT arm nickname capture and MUST NOT send identity navigation or recovery commands for nickname capture

#### Scenario: 同一浏览器代次只采一次
- **WHEN** multiple `page.cards` events arrive for the same browser generation
- **THEN** nickname capture is armed at most once for that generation

### Requirement: Facebook 启动握手昵称刷新不依赖 feed 卡片产出

Facebook 完整浏览器启动时，边缘 SHALL 在握手前完成一次有界的 `identity.bootstrap`：稳定数字 id 仍按登录态确立；仅当当前 tab 为 `about:blank` 或非 Facebook 页面时，bootstrap MAY 一次性引导到 Facebook 消费端首页，MUST NOT 进入数字 profile URL 或作者主页。昵称仅接受与稳定 id 绑定的本人信号。若读到已验证昵称，边缘 SHALL 通过既有 hello 可选昵称字段上报，云端 SHALL 按既有平台校验与差异写规则刷新系统显示名；该路径 MUST NOT 以 `page.cards` 产出作为前置条件。

Cloud 在完整浏览器启动后首个 `page.cards` 武装的昵称采集 SHALL 继续作为二次机会，并保持同一浏览器代次去重、Cloud reconnect/cold-standby 不触发。该二次机会 MUST 使用禁止导航的 `identity.read_current` 并经匹配的 `identity.observed` 收尾；它 MUST NOT 发送 `profile.open`、本人主页读取或完成后的 Feed 恢复命令。XHS 的既有首卡采集时机不变，但命令改为显式 `identity.read_self_profile`。

#### Scenario: Facebook 新 feed 布局无卡片事件仍经 hello 刷新昵称
- **WHEN** Facebook 启动页已出现与稳定 id 绑定的本人昵称，但当前 feed 布局未被边缘卡片选择器识别、没有首个 `page.cards`
- **THEN** 边缘仍经 hello 上报已验证昵称，云端可刷新系统显示名而不等待首卡触发

#### Scenario: 空昵称不覆盖系统值
- **WHEN** Facebook 启动页面就绪读取只确立稳定 id、没有读到与该 id 绑定的昵称
- **THEN** hello 不携带有效昵称，云端保留原系统昵称且不猜测

#### Scenario: XHS 与 Cloud 二次采集时机保持不变
- **WHEN** XHS 启动或 Facebook 后续产生首个 `page.cards`
- **THEN** 既有 Cloud 首卡武装、浏览器代次去重与有界重试语义保持不变
- **AND** Cloud 按各自平台策略下发固定副作用命令

