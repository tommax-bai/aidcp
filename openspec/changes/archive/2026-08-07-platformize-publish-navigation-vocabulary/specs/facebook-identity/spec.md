## MODIFIED Requirements

### Requirement: Facebook 启动期本人昵称采集经就地读取、由首个 feed 卡片触发

Facebook 账号的启动期昵称刷新 SHALL 优先由**启动 `identity.bootstrap`** 完成：当前 tab 尚非 Facebook 页面时，边缘 MAY 一次性引导到 Facebook 消费端首页并有界等待，再从与稳定数字 id 绑定的本人锚点就地读取昵称；读到非空昵称后经 hello 附带，云端按既有平台校验与差异写规则持久化。该主路径 MUST NOT 依赖 `page.cards` 是否产生。

完整浏览器启动后首批 `page.cards{startupId}` 触发的 Cloud 本人采集 SHALL 保留为**二次就地机会**。Cloud 在该时机只可下发 `identity.read_current_page{captureId}`；边缘 MUST 仅就地读取本人身份与昵称，MUST NOT 导航到 `profile.php`、`/me` 或任何其他页面。边缘 SHALL 通过 `identity.observed` 回传 captureId、绑定账号 id、可选昵称、`source=current_page` 与 `pageEffect=none`。读到不匹配 id 时云端 SHALL 安全忽略；就地读空 SHALL 保留原系统昵称，MUST NOT 猜测或用页面标题覆盖。Cloud 收到匹配结果后 MUST NOT 下发 Feed 恢复命令。

#### Scenario: 页面就绪后的 hello 昵称不依赖 feed 卡片
- **WHEN** Facebook 启动首读在消费端页面读到与稳定 id 绑定的昵称，但当前 feed 布局没有产出 `page.cards`
- **THEN** 边缘仍在 hello 附带该昵称，云端按既有差异写路径更新显示名

#### Scenario: 云端本人采集命令严格就地读
- **WHEN** 云端在首批 `page.cards` 时机对某 Facebook 连接下发 `identity.read_current_page`
- **THEN** 边缘就地读取本人 id + 昵称并上报匹配的 `identity.observed`
- **AND** MUST NOT 发起任何 `Page.navigate`

#### Scenario: 就地读到非空昵称后差异写库
- **WHEN** 启动 hello 或二次就地采集读到与本账号数字 id 绑定的非空昵称、且与系统库内昵称不同
- **THEN** 云端将账号昵称更新为该已验证昵称，账号 id 与任务归因不变

#### Scenario: 就地读空诚实保留原昵称
- **WHEN** 有界预算内仍读不到与本人 id 绑定的昵称
- **THEN** 系统保留原昵称，MUST NOT 写页面标题类垃圾、MUST NOT 猜测或为昵称跳转个人主页

#### Scenario: 二次采集完成不发页面恢复
- **WHEN** `identity.read_current_page` 就地采集完成并返回 `pageEffect=none`
- **THEN** Cloud 不发送 `facebook.navigation.back`、`facebook.feed.scroll` 或 Feed refresh
