## ADDED Requirements

### Requirement: Facebook 启动握手昵称刷新不依赖 feed 卡片产出

Facebook 完整浏览器启动时，边缘 SHALL 在握手前完成一次有界的页面就绪身份读取：稳定数字 id 仍按登录态确立，昵称仅接受与该 id 绑定的本人信号。若读到已验证昵称，边缘 SHALL 通过既有 hello 可选昵称字段上报，云端 SHALL 按既有平台校验与差异写规则刷新系统显示名；该路径 MUST NOT 以 `page.cards` 产出作为前置条件。

Cloud 在完整浏览器启动后首个 `page.cards` 武装的昵称采集 SHALL 继续作为二次机会，并保持同一浏览器代次去重、Cloud reconnect/cold-standby 不触发及 Facebook 就地不导航语义。XHS 的既有首卡采集时机不变。

#### Scenario: Facebook 新 feed 布局无卡片事件仍经 hello 刷新昵称
- **WHEN** Facebook 启动页已出现与稳定 id 绑定的本人昵称，但当前 feed 布局未被边缘卡片选择器识别、没有首个 `page.cards`
- **THEN** 边缘仍经 hello 上报已验证昵称，云端可刷新系统显示名而不等待首卡触发

#### Scenario: 空昵称不覆盖系统值
- **WHEN** Facebook 启动页面就绪读取只确立稳定 id、没有读到与该 id 绑定的昵称
- **THEN** hello 不携带有效昵称，云端保留原系统昵称且不猜测

#### Scenario: XHS 与 Cloud 二次采集时机保持不变
- **WHEN** XHS 启动或 Facebook 后续产生首个 `page.cards`
- **THEN** 既有 Cloud 首卡武装、浏览器代次去重与有界重试语义保持不变
