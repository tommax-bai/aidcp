## ADDED Requirements

### Requirement: Facebook 启动期本人昵称采集经就地读取、由首个 feed 卡片触发

Facebook 账号的**启动期本人昵称采集** SHALL 复用平台统一的采集时机（完整浏览器启动后首批 `page.cards{startupId}` 触发、同代号只采一次、采空有界重试、超时兜底——见 `account-identity-resolution`）。当云端在该时机对某 Facebook 连接下发本人采集命令（`profile.open{direct}`）时，边缘 MUST **仅就地**读取本人身份与昵称（id 锚定头像标签，与本 capability「就地、绝不为取昵称导航」的既有要求一致），MUST NOT 为本人采集导航到 `profile.php` / `/me` 或任何其他页面。

边缘 SHALL 按**就地读到的**数字 id 与昵称上报本人 `profile.detail`（`authorId` 用就地读到的 id，自校验——读到不匹配的 id 时云端按「非本人」安全忽略、绝不写错账号）。就地读到非空昵称且与库内不同 → 云端差异持久化；就地读空 → 上报空昵称，计一次采空、进有界重试，MUST NOT 猜测、MUST NOT 回落页面标题、MUST NOT 导航。采集完成后的回 feed（`back`）SHALL 经幂等 feed 校准实现——已在 feed 时不重新导航、不整页重载。

hello 握手附带昵称的既有路径（见「Facebook 昵称经握手持久化」）保持不变，作为幸运时更早写入的机会主义路径；可靠且与 XHS 统一的采集时机由本要求的「首个 feed 卡片」触发承担。

#### Scenario: 云端本人采集命令 → 边缘就地读、绝不导航
- **WHEN** 云端在首批 `page.cards` 时机对某 Facebook 连接下发 `profile.open{direct}` 本人采集命令
- **THEN** 边缘就地读取本人 id + 昵称并上报 `profile.detail`，MUST NOT 发起任何 `Page.navigate`（对 `profile.php` / `/me` 或任何页）

#### Scenario: 就地读到非空昵称 → 差异写库
- **WHEN** 边缘就地读到与本账号数字 id 绑定的非空昵称、且与系统库内昵称不同
- **THEN** 云端将账号昵称更新为该已验证昵称，账号 id 与任务归因不变

#### Scenario: 就地读空 → 诚实空、有界重试、不导航
- **WHEN** 首批 feed 时机就地读不到本人昵称（顶栏未水合 / 语言未覆盖等）
- **THEN** 边缘上报空昵称、云端计一次采空并保留原昵称，MUST NOT 写页面标题类垃圾、MUST NOT 为取昵称导航；留待下一个浏览器启动代号在有界预算内重试

#### Scenario: 采集完回 feed 不重载
- **WHEN** 本人就地采集完成后云端派发回 feed 的 `back`
- **THEN** 边缘经幂等 feed 校准处理——因就地读从未离开 feed，`back` 不触发整页重载
