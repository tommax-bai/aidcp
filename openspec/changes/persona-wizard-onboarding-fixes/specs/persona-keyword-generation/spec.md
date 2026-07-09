## MODIFIED Requirements

### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 在扫码登录、握手完成（账号身份已确立、真实 userid 而非 env-label）后提供人设向导：客户按维度选择关键词——**垂类（枚举快捷选 + 「自定义」自由文本兜底长尾，单选）、兴趣（少量高频标签多选 + 自由文本兜底长尾）、语气（枚举单选）**；v1 的「互动偏好」维度 MUST 移除（它映射不到任何生成字段、对产物零影响，属误导性输入）。点击生成即由**边缘发起**一条 `persona.generate` WebSocket 请求。请求 MUST 携带握手绑定的 `accountId`（不由请求体自报覆盖）、关键词勾选（含自由文本项）、idempotency key，并以 `timeoutMs ≥ 185s` 显式覆盖默认超时。触发 MUST 发生在账号身份已确立之后（`accounts` 行已存在，满足人设落库外键前提）。云端 MUST 对 `keywordSelections` 做轻量输入校验（单项长度上限 + 条数上限），超限诚实拒绝、绝不把超长/超量文本原样喂进生成 prompt（纵深防御：弱注入面在自助模型下影响面仅为该用户自己的人设、且产物经 `loadSoulFromValue` 结构复验）。

#### Scenario: 握手后触发生成

- **WHEN** 客户在客户端新建环境扫码登录、握手完成后于向导选定关键词（含自定义垂类 / 自由文本兴趣）并点击生成
- **THEN** 边缘发出 `persona.generate` 请求（携握手绑定 `accountId`、关键词勾选、idempotency key、`timeoutMs ≥ 185s`），云端据此生成

#### Scenario: 身份未确立不触发

- **WHEN** 环境已建但尚未扫码登录 / 未拿到真实 userid / 未握手
- **THEN** 向导 MUST NOT 发起生成请求（此刻无可落库的 `accountId`），仅可本地暂存关键词勾选

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限 / 总条数超上限（含经自由文本注入的超量内容）
- **THEN** 云端诚实拒绝该次生成、MUST NOT 把超长/超量文本原样喂进 prompt，边缘透传失败原因

## ADDED Requirements

### Requirement: 云端下发已绑人设信号，边缘按 onboarding 三态渲染

云端 SHALL 经既有 `ui.snapshot` 下行通道把该账号「是否已绑人设」如实告知边缘：`UiSnapshotPayload` 新增可选 `personaBound?: boolean`，云端在 hello 快照解析 `isPersonaBound(accountId)`（人设存储权威判据，与浏览/发布入口闸同源）后携带下发。为守「宁缺毋假 / 全空不发包」，`personaBound` MUST 仅在为真时下发（缺省=边缘按本地默认「未设置」）。该字段 MUST NOT 新增 `MessageType`（`ui.snapshot` 为既有消息，穷举计数不变、不碰 command-bridge 与 onMessage 主动命令白名单），但两份 `protocol.ts` MUST 逐字同步该可选字段、AC-PROTO 往返断言两端镜像。

边缘 SHALL 据 `personaBound` × 连接态渲染 onboarding 三态：① 已绑（`personaBound=true`）→ 显示「已设置」摘要、跳过关键词→生成→确认三步，绝不再把已绑账号显示为「未设置」；② 未绑 + 未连云 → 引导「先启动、扫码登录」；③ 未绑 + 已连云 → 启用向导。

#### Scenario: 已绑人设的账号握手后显示已设置

- **WHEN** 一个此前已绑人设的账号在客户端选环境、启动、扫码登录、握手连云后收到 hello 快照
- **THEN** 快照带 `personaBound=true`，边缘徽标显示「已设置」并跳过向导三步，MUST NOT 停在本地默认「未设置」

#### Scenario: 未绑人设不下发 personaBound

- **WHEN** 账号未绑人设，云端组 hello 快照
- **THEN** 快照 MUST NOT 带 `personaBound`（或带 false 而不因此破坏「全空不发包」）；边缘按本地默认「未设置」渲染，进入向导流程

### Requirement: 生成 gate 判据不放宽但引导透明

生成 gate 判据 `auth === 'logged in' && cloud === 'connected'` MUST 保持不变（红线：persona 命令必须经运行中 core 子进程 WS 打到云端、握手后账号才在云端存在；放宽 gate = 点了发不出去 = 静默假成功）。未满足时边缘 MUST NOT 允许发起生成，但 SHALL **分别**如实告知未满足的前置（未登录 / 未连云）并给出指向「启动」的可操作引导，MUST NOT 只给一句无差别的灰置提示。

#### Scenario: 未登录时分态引导

- **WHEN** core 未运行或未扫码登录（`auth !== 'logged in'`）
- **THEN** 生成按钮 disabled，且提示明确指向「请先点启动并在浏览器扫码登录」，而非笼统灰置

#### Scenario: 已登录未连云时分态引导

- **WHEN** 已登录但云端未连接（`cloud !== 'connected'`）
- **THEN** 生成按钮 disabled，且提示明确指向「等待云端连接」，与「未登录」态区分
