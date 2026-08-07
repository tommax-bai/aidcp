## MODIFIED Requirements

### Requirement: 云端下发已绑人设信号，边缘按 onboarding 三态渲染

Cloud SHALL 在客户鉴权环境状态中返回该环境绑定解析状态及账号“是否已绑人设”的权威结果。客户端 SHALL 按“绑定待解析 / 已解析且已绑 / 已解析且未绑”三态渲染；该真态来自客户拥有环境与账号绑定的服务端解析，MUST NOT 依赖浏览器、CDP、页面登录态或 Edge WS hello。为了避免 stale-true 泄漏，环境切换、客户切换或归属刷新时客户端 MUST 先清除上一账号投影，待目标环境的新权威响应重建。

浏览器无关 core 的 `ui.push_snapshot.personaBound` MAY 在兼容窗口继续下发，但只能作为同一权威结果的辅助同步，MUST NOT 成为新客户端判断人设绑定的唯一来源。旧客户端仍可按既有 WS 快照语义工作。

#### Scenario: 已绑人设且浏览器关闭时显示已设置

- **WHEN** 客户登录后获取一个绑定可信且此前已绑人设的环境状态，而该环境浏览器未启动
- **THEN** 客户鉴权响应返回已解析且 `personaBound=true`，客户端显示“已设置”并跳过向导，MUST NOT 要求启动环境

#### Scenario: 绑定待解析时中立态不谎称未设置

- **WHEN** 环境属于当前客户但 Cloud 尚未解析出可信账号绑定
- **THEN** 徽标显示中立“绑定待确认/状态加载中”，MUST NOT 谎称“未设置”，也 MUST NOT 把打开浏览器作为默认解析手段

#### Scenario: 切环境不泄漏旧账号已绑态

- **WHEN** 从一个已绑人设环境切换到另一个环境或客户 roster 发生变化
- **THEN** 客户端先清除旧 `personaBound` 投影，待目标环境权威响应后显示新状态，MUST NOT 把 stale true 泄漏给新账号

#### Scenario: 已解析且未绑时进入向导

- **WHEN** Cloud 已验证环境归属和账号绑定并确认该账号未绑人设
- **THEN** 客户端显示“未设置”并启用向导，浏览器关闭或槽位已满不得改变该判定
