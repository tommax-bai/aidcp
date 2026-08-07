## MODIFIED Requirements

### Requirement: 小红书笔记访问限制弹窗不得作为账号级验证码事故上报

边缘 SHALL 识别小红书 Web 笔记访问限制弹窗（如 `access-modal`、`access-limit-app`、文案“当前笔记暂时无法浏览 / 请打开小红书App扫码查看”）为可恢复的笔记访问限制状态，而非账号登录墙、验证码或未知账号级阻断。该类弹窗出现时，边缘 MUST NOT 触发 `captcha.detected`、MUST NOT 将浏览命令队列长期暂停为 captcha/unknown；它 MAY 通过关闭浮层或直接导航回健康来源列表恢复。若访问限制发生在正在打开的笔记上，边缘仍须诚实失败或返回列表，MUST NOT 冒充已成功读取该笔记。

#### Scenario: 失效详情路由弹出 access-limit-app
- **WHEN** 小红书页面出现可见 `access-modal` / `access-limit-app`，并包含“当前笔记暂时无法浏览”或“请打开小红书App扫码查看”等文案
- **THEN** 边缘将其分类为非阻断可恢复弹窗，MUST NOT 上报为验证码或 unknown 阻断，后续 `{platform}.navigation.back` / 返回来源列表命令仍可执行

#### Scenario: 真验证码仍按账号级风控处理
- **WHEN** 页面出现验证码厂商 iframe、滑块/点选验证容器或“安全验证 / 滑动验证 / 请完成验证”等挑战文案
- **THEN** 边缘仍按 captcha 阻断处理并暂停高风险动作，MUST NOT 因 access-limit 兜底放宽真实验证码判断
