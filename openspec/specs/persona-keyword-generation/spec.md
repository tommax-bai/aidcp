# persona-keyword-generation Specification

## Purpose
TBD - created by archiving change edge-persona-keyword-generation. Update Purpose after archive.
## Requirements
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

### Requirement: 云端生成经 JSON 序列化校验，生成失败硬 fail-closed 绝不回落默认人设

云端 SHALL 用登记进 role-catalog 的 persona 生成器角色调云端唯一文本大模型出口（按角色配模型、按 `accountId` 记账），输出 **JSON** → 经确定性序列化器转成 soul YAML → 过 `loadSoulFromValue` 结构校验。大模型超时 / 输出不可解析 / 校验不过时 MAY 修复重试 1–2 次；仍失败 MUST 诚实回 `generation_failed` / `persona_invalid`，该账号维持「缺人设」，MUST NOT 回落任何模板 / 默认人设、MUST NOT 静默返回半成品（守「绝不静默假成功」+「无默认人设」）。密钥 MUST 只在云端、只从启动期预载取。

#### Scenario: 生成成功回草稿

- **WHEN** 大模型输出经序列化 + `loadSoulFromValue` 校验通过
- **THEN** 云端回 `persona.generate` 响应，携草稿 soul YAML 与身份摘要；该草稿此刻 MUST NOT 落库

#### Scenario: 生成失败诚实拒绝不兜底

- **WHEN** 大模型超时或输出经重试仍不可解析 / 校验不过
- **THEN** 云端回 `generation_failed` / `persona_invalid`，账号维持「缺人设」，MUST NOT 回落任何模板 / 默认人设、MUST NOT 假成功

### Requirement: 生成调用幂等，重连或重试不产生双份付费

`persona.generate` MUST 幂等：云端对同一 idempotency key 的重复请求 MUST 命中缓存结果、MUST NOT 重复调大模型、MUST NOT 重复记账。仅 `persona.persist` 成功 SHALL 翻转账号「已绑人设」状态；`persona.generate` 本身 MUST NOT 改变绑定状态。

#### Scenario: 同幂等键命中缓存

- **WHEN** 同一 idempotency key 的 `persona.generate` 请求重复到达（客户端重发 / 网络重投）
- **THEN** 云端返回缓存的首次生成结果，MUST NOT 再次调用大模型、MUST NOT 二次记账

#### Scenario: 长在途遇自动重连不双计费

- **WHEN** 生成在 ≥185s 在途窗口内遭遇边缘自动重连（挂起请求被 reject）、客户端据幂等键重试
- **THEN** 幂等去重护住，MUST NOT 产生双份付费调用；账号绑定状态在 `persona.persist` 成功前保持不变

### Requirement: 草稿经客户确认后走现有已校验写入通道落库，边缘不本地判成功

客户确认草稿后 SHALL 由边缘发起 `persona.persist` 请求，携确认后的 soul YAML；云端 MUST 复用现有人设单写通道（`loadSoulFromValue` 校验 + 外键守护 + 写库成功才刷内存镜像 + 绑定即热加载唤醒在线节点 + 诚实回执），MUST NOT 新造绕过校验的写路径。边缘 MUST 仅透传云端诚实 `reason`、MUST NOT 本地判定成功。落库前的账号身份 MUST 取握手绑定 `accountId`。

#### Scenario: 确认落库并绑定

- **WHEN** 客户点击确认，soul YAML 经现有写入通道校验通过
- **THEN** 云端落 `persona_config`、刷镜像、绑定即唤醒该账号在线节点，回成功回执；边缘据真回执刷新，不乐观假成功

#### Scenario: 账号行缺失优雅回诚实失败

- **WHEN** `persona.persist` 命中外键守护（`accounts` 行因握手期 `ensureAccount` 尽力而为失败而缺失），回 `unknown_account`
- **THEN** 边缘按诚实失败处理、MUST NOT 判成功，向导可重驱使账号行落定后重试；付费 `generate` 前 SHOULD 先确认账号行到位

#### Scenario: 空或非法人设被拒不落库

- **WHEN** 确认提交的 soul 为空 / 结构非法
- **THEN** 云端回 `persona_required` / `persona_invalid`，MUST NOT 落库、MUST NOT 刷镜像

### Requirement: 大模型与密钥留云端，边缘只做交互

大模型调用、密钥、校验、序列化、落库、记账 MUST 全部在云端。边缘 SHALL 只做三件事：收关键词勾选、显示云端返回的草稿、捕获客户确认。边缘 MUST NOT 嵌入大模型、MUST NOT 持有大模型密钥、MUST NOT 直连 PG、MUST NOT 复制 soul 序列化器 / 校验器。

#### Scenario: 边缘不承载生成能力

- **WHEN** 审视边缘在本流程的职责
- **THEN** 边缘只收勾选 / 显示草稿 / 回确认；大模型、密钥、校验、序列化、落库、记账均在云端，边缘无其一

### Requirement: 生成 prompt 内置每账号差异化，差异化落在 seed_keywords

云端生成 SHALL 在 prompt 内置每账号差异化（如每账号差异化种子 + 采样温度），使跨账号产物有区分度；差异化 MUST 重点作用于 `seed_keywords` / 搜索词这条被平台当同质信号的链路，而非仅 `identity` / `tone` 文案字段。

#### Scenario: 同垂类不同账号产物有区分

- **WHEN** 同一垂类的两个不同账号以相近关键词生成
- **THEN** 两者 `seed_keywords` 呈现差异化、MUST NOT 逐字雷同

### Requirement: 新增协议消息走边缘发起的请求响应，不经主动命令白名单，两份 protocol.ts 逐字同步

新增的 `persona.generate` / `persona.persist` 及其响应 MUST 设计为**边缘发起的请求/响应**，回包走 pending-id 命中路径，MUST NOT 依赖 cloud→edge 主动命令下发、MUST NOT 需要 onMessage 主动命令白名单放行（规避静默丢弃 footgun）、MUST NOT 改动 command-bridge 动作映射。edge 与 cloud 两份 `protocol.ts` 的消息类型 MUST 逐字一致，`docs/protocol.md` 计数与消息表 MUST 同步更新，AC-PROTO 漂移哨兵 MUST 通过。

#### Scenario: 回包走 pending-id 不触白名单

- **WHEN** 云端回 `persona.generate` / `persona.persist` 的响应
- **THEN** 边缘按 pending-id 命中处理，MUST NOT 经主动命令白名单，MUST NOT 落入「其他主动消息暂忽略」被静默丢弃

#### Scenario: 两份 protocol.ts 不漂移

- **WHEN** 运行协议漂移哨兵（AC-PROTO）
- **THEN** edge 与 cloud 两份 `protocol.ts` 的 `MessageType` 穷举一致、校验通过

### Requirement: 适用范围仅新号 onboarding 一次性

本能力 SHALL 仅用于新号 onboarding（该账号首次绑定人设）。老号事后重建人设 MUST NOT 由本期能力承载（留待后续变更，届时须配套一次性令牌 / 配额等防重复触发设计）。

#### Scenario: 仅新号首次绑定走此流程

- **WHEN** 一个从未绑过人设的新号在 onboarding 触发向导
- **THEN** 允许生成 + 确认落库；对已绑人设的老号，本期不提供经此流程的重建入口

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

### Requirement: 生成 gate 判据不放宽但引导透明

生成 gate 判据 `auth === 'logged in' && cloud === 'connected'` MUST 保持不变（红线：persona 命令必须经运行中 core 子进程 WS 打到云端、握手后账号才在云端存在；放宽 gate = 点了发不出去 = 静默假成功）。未满足时边缘 MUST NOT 允许发起生成，但 SHALL **分别**如实告知未满足的前置（未登录 / 未连云）并给出指向「启动」的可操作引导，MUST NOT 只给一句无差别的灰置提示。

#### Scenario: 未登录时分态引导

- **WHEN** core 未运行或未扫码登录（`auth !== 'logged in'`）
- **THEN** 生成按钮 disabled，且提示明确指向「请先点启动并在浏览器扫码登录」，而非笼统灰置

#### Scenario: 已登录未连云时分态引导

- **WHEN** 已登录但云端未连接（`cloud !== 'connected'`）
- **THEN** 生成按钮 disabled，且提示明确指向「等待云端连接」，与「未登录」态区分

