## ADDED Requirements

### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 在扫码登录、握手完成（账号身份已确立、真实 userid 而非 env-label）后提供人设向导：客户选择封闭枚举的关键词（垂类/兴趣/语气/互动偏好），点击生成即由**边缘发起**一条 `persona.generate` WebSocket 请求。请求 MUST 携带握手绑定的 `accountId`（不由请求体自报覆盖）、关键词勾选、idempotency key，并以 `timeoutMs ≥ 185s` 显式覆盖默认超时。触发 MUST 发生在账号身份已确立之后（`accounts` 行已存在，满足人设落库外键前提）。

#### Scenario: 握手后触发生成

- **WHEN** 客户在客户端新建环境扫码登录、握手完成后于向导选定关键词并点击生成
- **THEN** 边缘发出 `persona.generate` 请求（携握手绑定 `accountId`、关键词勾选、idempotency key、`timeoutMs ≥ 185s`），云端据此生成

#### Scenario: 身份未确立不触发

- **WHEN** 环境已建但尚未扫码登录 / 未拿到真实 userid / 未握手
- **THEN** 向导 MUST NOT 发起生成请求（此刻无可落库的 `accountId`），仅可本地暂存关键词勾选

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
