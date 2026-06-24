## ADDED Requirements

### Requirement: 发布成功时捕获并持久化可用的详情页链接

发布执行端 SHALL 在发帖**真实成功**后，除裸笔记 id 外，额外尝试捕获一个**可用的**小红书笔记详情页链接——即带 `xsec_token`（及相应来源参数）的完整分享 URL，使该链接在登录态下可被点开。捕获到的完整 URL SHALL 经回执回报云端并持久化到 `publish_log.post_url`。该捕获 MUST 只含页面公开状态、不含任何密钥/令牌等敏感系统凭据。

#### Scenario: 抓到完整分享 URL → 持久化到 post_url
- **WHEN** 发帖成功且页面可取到带 `xsec_token` 的完整笔记分享 URL
- **THEN** 该完整 URL 经回执上报并写入 `publish_log.post_url`

#### Scenario: 链接捕获不影响成功判定
- **WHEN** 发帖已达真实成功信号，但分享 URL 暂未取到
- **THEN** 本次发布仍判成功（成功判定锚定平台真实成功信号），链接捕获是成功之后的附加动作、不反向否定成功

### Requirement: 详情页链接不可得时诚实置空、绝不伪造

当无法取到带 token 的完整分享 URL 时，系统 MUST 把 `post_url` 置为 NULL 并据实呈现「无链接」，MUST NOT 用裸笔记 id 拼一个缺 `xsec_token`、不一定能打开的链接去冒充可用详情页链接，MUST NOT 派生任何假链接。后台对 `post_url` 为空的记录 SHALL 禁用/隐藏「打开详情页」入口并明确标注无链接。

#### Scenario: 抓不到完整 URL → 存 NULL、标无链接
- **WHEN** 发帖成功但页面取不到带 `xsec_token` 的完整分享 URL
- **THEN** `publish_log.post_url` 为 NULL，后台该记录显示「无链接」、详情页入口不可点

#### Scenario: 红线反例——裸 id 拼假链接（禁止）
- **WHEN** 完整分享 URL 抓不到，有实现想用 `https://www.xiaohongshu.com/explore/<裸id>` 顶替写入 `post_url`
- **THEN** 这违反「不伪造打不开的链接」，MUST 被拒绝；正确行为是置 NULL、据实标无链接
