## MODIFIED Requirements

### Requirement: 云端下发已绑人设信号，边缘按 onboarding 三态渲染

云端 SHALL 经既有 `ui.snapshot` 下行通道把该账号「是否已绑人设」如实告知边缘：`UiSnapshotPayload` 新增可选 `personaBound?: boolean`，云端在 hello 快照解析 `isPersonaBound(accountId)`（人设存储权威判据，与浏览/发布入口闸同源）后携带下发。为守「宁缺毋假 / 全空不发包」，`personaBound` MUST 仅在为真时下发（缺省=边缘按本地默认渲染）。该字段 MUST NOT 新增 `MessageType`（`ui.snapshot` 为既有消息，穷举计数不变、不碰 command-bridge 与 onMessage 主动命令白名单），但两份 `protocol.ts` MUST 逐字同步该可选字段、AC-PROTO 往返断言两端镜像。

边缘 SHALL 据 `personaBound` × 连接态渲染 onboarding 状态，其中「是否已绑」**仅在已连云（`auth==='logged in' && cloud==='connected'`）时判定为权威**——因为该账号在云端的真实 id 与人设绑定态只有握手连云后才可知：① 已绑（连云后 `personaBound=true` 或本会话确认成功）→ 显示「已设置」、跳过向导；② **未连云 / 未登录（尚不知道该账号是否已绑）→ 徽标 MUST 显示中立态（如「待启动」），MUST NOT 谎称「未设置」（宁缺毋假）**，并引导「先启动、扫码登录」，明确「连上云端后会显示该账号人设状态」；③ 未绑 + 已连云（权威可知未绑）→ 徽标「未设置」、启用向导。

边缘 MUST 在换会话时清除上一账号的已绑标记（core 重启清 `ui.snapshot` 派生的已绑态、断连清本会话确认标记），避免切环境 / 换账号后旧账号的「已设置」误染新账号——因云端只在为真时下发 `personaBound`（从不发 false），stale-true 会泄漏，故须本地在换会话时清零，待新会话权威信号重建。

#### Scenario: 已绑人设的账号连云后显示已设置

- **WHEN** 一个此前已绑人设的账号在客户端选环境、启动、扫码登录、握手连云后收到 hello 快照
- **THEN** 快照带 `personaBound=true`，边缘徽标显示「已设置」并跳过向导三步，MUST NOT 停在本地默认

#### Scenario: 未连云时中立态不谎称未设置

- **WHEN** 在设置页选 / 切换环境但尚未启动 / 未登录 / 未连云（边缘此刻不知该环境对应哪个真实账号、也未连云）
- **THEN** 徽标 MUST 显示中立态（如「待启动」）而非「未设置」，并引导先启动登录；连云后再据权威 `personaBound` 翻「已设置」/「未设置」

#### Scenario: 切环境不泄漏旧账号已绑态

- **WHEN** 在一个已绑账号运行后切换到另一个环境 / 账号（core 重启、断连重连）
- **THEN** 边缘 MUST 先清除上一账号的已绑标记（回中立「待启动」），MUST NOT 因 stale `personaBound=true` 把新账号误显示为「已设置」；新会话连云后据其真实 `personaBound` 重新判定

#### Scenario: 未绑人设不下发 personaBound

- **WHEN** 账号未绑人设，云端组 hello 快照
- **THEN** 快照 MUST NOT 带 `personaBound`（或带 false 而不因此破坏「全空不发包」）；边缘连云后按「未设置」渲染、进入向导流程
