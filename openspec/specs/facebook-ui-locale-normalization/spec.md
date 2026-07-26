# facebook-ui-locale-normalization Specification

## Purpose
TBD - created by archiving change facebook-locale-pin-en-us. Update Purpose after archive.
## Requirements
### Requirement: FB 互动号界面语言统一钉成规范 en-US、与代理 IP 派生语言及内容语言解耦

FB 互动号的浏览器**界面 chrome 语言**（按钮 / 菜单 / 系统级 UI 文案，如「Join / Pending / Write a comment / 同意 Cookie」）SHALL 统一钉成规范 locale `en-US`，与代理 IP 派生语言、所看群组 / 内容语言**解耦**，使下游按钮 / 状态的文字识别在跨国家 / 跨语言群组时稳定单语化。新号 SHALL 在建号阶段一次性钉定：指纹语言固定英文（`language_switch` 关闭 + 显式 `language=['en-US']`）、浏览器启动参数带 `--lang=en-US`（覆盖登出 / 未登录 chrome）、导入 FB cookie 时确保含 `locale=en_US`（缺则注入）。**内容语言 MUST NOT 被塌**——帖文、群名、评论正文、作者人名等内容一律保持原语言、仍归云端多语判定；本能力只统一界面 chrome。此 pin 为整套跨语言识别方案的必要非充分先手，MUST NOT 顺带引入 N 语关键词字典基础设施。

#### Scenario: 新建 FB 互动号钉定英文界面
- **WHEN** 程序化建一个 FB 互动号（指纹环境 + 启动 + cookie 导入）
- **THEN** 指纹语言为 en-US（非随代理 IP）、启动带 `--lang=en-US`、导入 cookie 含 `locale=en_US`，浏览器界面 chrome 渲染为英文

#### Scenario: 浏览非英文群组时内容语言不塌
- **WHEN** 已钉英文界面的账号浏览 / 加入一个越南语（或任一非英文）群组
- **THEN** 界面按钮与系统文案为英文（识别单语化），而帖文 / 群名 / 评论内容 / 人名仍为该群组原语言、不被翻译或塌为英文

#### Scenario: 语言 pin 不触发指纹一致性拒建
- **WHEN** 建号构造指纹时把语言钉成 en-US、同时时区 / 地理仍随代理 IP
- **THEN** `language` 不进「声明 OS == UA OS == 字体 OS == renderer 家族 OS」四者一致断言集，pin en-US 不触发 coherence 拒建；「英文界面 + 本地时区」为可接受的真实用户形态，不违反一 profile 一指纹一 IP 一账号绑定契约

### Requirement: 存量登录号经一次性账号服务端语言翻转达到规范 locale，写客户端结构性改不动存量号指纹语言

对已存在且已登录的 FB 互动号，其指纹语言 SHALL NOT 经受限写客户端改写——`user/update` 的放行**仅限改代理两键 body**、`fingerprint_config` 只在 `user/create` 设定，这是结构性边界、MUST NOT 为改语言而放宽。存量号达到规范 locale 的唯一有效路 SHALL 为**一次性登入后把 FB 账号服务端语言改为 English (US)**（该设置跨代理 / 跨会话存活、压过 Accept-Language 与启动参数）。此翻转 SHALL 以运维 runbook + 可选边缘自动化落地，并标记真机验证门（改语言的真实设置页导航路径待真机核实）。启动参数 `--lang` 与 cookie `locale` MUST NOT 被宣称能改登录态群面的界面语言——它们只兜登出 / 未登录 chrome。

#### Scenario: 存量号经账号语言翻转达到英文界面
- **WHEN** 一个长期以 IP 派生语言运行的存量登录号需要归一到英文界面
- **THEN** 经一次性登入把 FB 账号语言改为 English (US)，此后跨代理 / 跨会话界面 chrome 稳定英文；MUST NOT 依赖启动参数 / cookie 去改登录态群面语言

#### Scenario: 写客户端拒绝改存量号指纹语言
- **WHEN** 试图经受限写客户端 `user/update` 改一个存量环境的指纹语言字段
- **THEN** 该写口结构性只接受 `{ user_id, user_proxy_config }` 两键、拒绝透传 `fingerprint_config`，存量号指纹语言改不动；MUST NOT 静默改写指纹、MUST NOT 假成功

### Requirement: Existing Vietnamese Facebook sessions use bounded exact post-action labels

While en-US remains the normative interface locale for provisioned Facebook environments, Edge SHALL support the exact verified Vietnamese post-level controls needed by existing localized sessions: neutral like `Thích`, selected/unlike `Gỡ Thích` and `Bỏ thích`, reacted word `Thích`, and comment `Viết bình luận`. The shared localized-control classifier MUST combine exact labels with their same-card structure. A neutral/selected candidate MUST share a bounded post action bar with exactly one supported post-level comment control and MUST NOT be inside a reaction-summary toolbar. Numeric text rendered inside an otherwise exact action control MUST NOT by itself demote the control. Numeric reaction summaries such as `Thích: 27K người`, and reaction-word controls inside a summary toolbar, MUST remain distinct from the neutral like toggle and MUST NOT be clicked as the action target. Scan identity, action location, and post-action verification MUST use the same classification semantics. Missing or structurally ambiguous controls MUST continue to fail closed.

#### Scenario: Vietnamese neutral like is clicked and verified
- **WHEN** one exact target card contains neutral `Thích` and the same card changes to `Gỡ Thích` after the click
- **THEN** Edge confirms the existing like success for that card

#### Scenario: Vietnamese reaction count is not the toggle
- **WHEN** a card contains both `Thích` and a numeric summary `Thích: 27K người`
- **THEN** Edge targets only the post-level neutral control and may parse the numeric summary as a count

#### Scenario: Vietnamese neutral action may render its count inside the button
- **WHEN** the same-card post action bar contains one control with exact label `Thích` and visible text `866`, beside one `Viết bình luận` control, while a separate summary toolbar exposes `Thích: 825 người`
- **THEN** Edge classifies the exact action-bar control as the unique neutral like target, keeps the summary distinct, and permits the strict video card identity

#### Scenario: Shared structural semantics apply across supported locales
- **WHEN** the equivalent post-action and summary layout uses a supported Chinese, English, Spanish, or Vietnamese neutral label
- **THEN** the same shared classifier distinguishes the action from the summary without a locale-specific DOM-order fallback

#### Scenario: Numeric reaction word without unique action structure is ambiguous
- **WHEN** an exact reaction word with numeric text is not uniquely bound to a post-level comment control or is inside a reaction-summary toolbar
- **THEN** Edge does not use it as the like target or as the strict video action witness

#### Scenario: Vietnamese comment control anchors the post action boundary
- **WHEN** a lightweight video card contains `Viết bình luận` beside its like control
- **THEN** Edge may use it as the same-card action-boundary witness without interpreting caption text as a control

#### Scenario: Verbose Vietnamese accessibility labels recover the strict Feed card root
- **WHEN** a lightweight video card exposes visible `Thích` / `Bình luận` actions with accessibility labels `Bày tỏ cảm xúc Thích về bài viết của <author>` and `Bình luận về bài viết của <author>`
- **THEN** the shared classifier recognizes exactly one same-bar like/comment pair, permits the strict card root and video identity, and does not match the caption or reaction summary

#### Scenario: Reels reuses vocabulary but retains active-video proof
- **WHEN** a supported localized like or unlike word appears on the dedicated Reels surface
- **THEN** the Reels reader may reuse the normalized locale vocabulary but still requires the active Reel identity, constrained action geometry, and post-action selected-state proof rather than a Feed card selector

#### Scenario: Unknown localized state fails closed
- **WHEN** a localized card lacks every supported neutral/selected/comment witness or exposes multiple matching controls
- **THEN** Edge returns no target or ambiguous target and does not click by DOM order

### Requirement: 浏览器界面 locale 与账号写作语言保持正交
Facebook 浏览器界面 SHALL 继续固定规范 `en-US`；账号 soul 的 `writing_language` 只约束 Cloud 生成的公开帖子/评论文本。改变写作语言 MUST NOT 修改 AdsPower 指纹语言、启动参数、cookie locale、Facebook 账号 UI 语言、代理、时区或 DOM 识别词表。

#### Scenario: 越南语写作账号仍使用英文界面
- **WHEN** Facebook 账号配置 `writing_language=vi`
- **THEN** 该账号生成越南语公开文本，但浏览器界面仍按既有规范使用 en-US，Edge 继续以英文 UI 结构识别按钮

#### Scenario: 改写作语言不触碰指纹
- **WHEN** 用户在人设向导把写作语言从中文改为英文
- **THEN** 系统只更新 Cloud 账号 soul，MUST NOT 调用 AdsPower `user/update` 改 fingerprint_config 或改变 cookie/UI locale

