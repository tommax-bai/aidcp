## MODIFIED Requirements

### Requirement: 暂停期间只允许 captcha assist 恢复命令穿透

当某 edge 因验证码处于暂停态时，cloud 传输层 SHALL 继续阻止普通浏览、互动、发布页面动作等命令下发；但 SHALL 允许该 edge 绑定 incident 的截图与人工点击协助命令穿透暂停闸。穿透白名单 MUST 精确限定为 captcha assist 恢复路径与既有 `session.end` / 纯 UI 状态消息，MUST NOT 泛化为所有控制命令。

#### Scenario: 普通命令仍被暂停闸拦截
- **WHEN** edge `edge-1` 处于 captcha 暂停态且 cloud 尝试下发 `xiaohongshu.feed.scroll`
- **THEN** 该普通浏览命令仍被暂停闸拦截

#### Scenario: assist capture 可穿透暂停闸
- **WHEN** edge `edge-1` 处于 captcha 暂停态且操作者请求刷新协助截图
- **THEN** cloud 可向 `edge-1` 下发该 incident 的 `captcha.assist.capture` 命令
