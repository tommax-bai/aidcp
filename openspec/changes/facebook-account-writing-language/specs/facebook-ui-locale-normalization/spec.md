## ADDED Requirements

### Requirement: 浏览器界面 locale 与账号写作语言保持正交
Facebook 浏览器界面 SHALL 继续固定规范 `en-US`；账号 soul 的 `writing_language` 只约束 Cloud 生成的公开帖子/评论文本。改变写作语言 MUST NOT 修改 AdsPower 指纹语言、启动参数、cookie locale、Facebook 账号 UI 语言、代理、时区或 DOM 识别词表。

#### Scenario: 越南语写作账号仍使用英文界面
- **WHEN** Facebook 账号配置 `writing_language=vi`
- **THEN** 该账号生成越南语公开文本，但浏览器界面仍按既有规范使用 en-US，Edge 继续以英文 UI 结构识别按钮

#### Scenario: 改写作语言不触碰指纹
- **WHEN** 用户在人设向导把写作语言从中文改为英文
- **THEN** 系统只更新 Cloud 账号 soul，MUST NOT 调用 AdsPower `user/update` 改 fingerprint_config 或改变 cookie/UI locale
