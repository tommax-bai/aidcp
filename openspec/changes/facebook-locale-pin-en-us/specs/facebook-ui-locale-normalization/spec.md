## ADDED Requirements

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
