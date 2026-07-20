# persona-keyword-generation Specification

## Purpose
TBD - created by archiving change edge-persona-keyword-generation. Update Purpose after archive.
## Requirements
### Requirement: 客户端 onboarding 关键词向导经边缘发起的 WS 请求触发云端生成

Electron 客户端 SHALL 在客户已登录、环境归属与账号绑定已由 Cloud 权威解析后提供人设向导：客户按维度选择关键词——**垂类（枚举快捷选 + 「自定义」自由文本兜底长尾，单选）、兴趣（少量高频标签多选 + 自由文本兜底长尾）、语气（枚举单选）**；并在“语气调性”面板下提供**点赞倾向（正常 / 喜欢 / 更喜欢，单选，默认正常）**。点赞倾向 MUST 有真实输出映射：客户端 SHALL 以受控标记随 `keywordSelections` 发送，云端 SHALL 在生成兴趣关键词前剥离该标记，并把档位写入人设 `behavior_guidelines.like_affinity` 与匹配账号兴趣的 `like_principle`；MUST NOT 把内部标记当作兴趣词或原样写入身份文案。除该有明确映射的点赞倾向外，客户端 MUST NOT 提供对生成产物零影响的互动偏好输入。

点击生成 SHALL 由 Electron 主进程经 customer-auth 窄接口发起；请求只携带 `envKey`、关键词勾选（含自由文本项与受控点赞倾向标记）及 idempotency key，Cloud MUST 从客户会话逐请求校验环境归属并解析权威 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。生成 MUST NOT 要求环境浏览器已启动、页面登录态在线、CDP 可用、浏览器槽位可用或 Edge 活 WS 会话存在。云端 MUST 对 `keywordSelections` 做轻量输入校验（单项长度上限 + 条数上限），超限诚实拒绝、绝不把超长/超量文本原样喂进生成 prompt。旧客户端仍经 Edge WS 发起时 SHALL 保持原协议兼容，且两条传输 MUST 复用同一生成领域方法、校验、幂等和记账。

#### Scenario: 浏览器关闭时触发生成

- **WHEN** 客户已登录且环境归属/绑定可信，在浏览器关闭、CDP 缺席或槽位为零时选定关键词与点赞倾向并点击生成
- **THEN** Electron 主进程经 customer-auth 请求携 `envKey`、关键词、受控标记与 idempotency key，Cloud 解析权威账号后生成，MUST NOT 启动浏览器或等待槽位

#### Scenario: 默认正常并在预览中可核对

- **WHEN** 客户首次打开人设初始化向导且未主动调整点赞倾向
- **THEN** “正常”档被选中，预览摘要显示“点赞倾向：正常”，生成的人设以 `like_affinity=normal` 持久化

#### Scenario: 点赞倾向标记不污染人设兴趣

- **WHEN** 云端收到 `like_affinity:like_more` 或 `like_affinity:like_most` 受控标记
- **THEN** 生成器在构造身份/兴趣 prompt 前移除该标记，并只把其映射到 `behavior_guidelines`，MUST NOT 把内部 token 写入 identity、interests 或 seed keywords

#### Scenario: 旧客户端无标记保持兼容

- **WHEN** 旧客户端的 `persona.generate` 请求没有点赞倾向标记
- **THEN** 云端按 `normal` 处理并生成合法人设，MUST NOT 因字段缺失拒绝请求

#### Scenario: 绑定未确立不触发

- **WHEN** 客户未登录、环境不属于该客户或 Cloud 无法权威解析账号绑定
- **THEN** 向导 MUST NOT 发起可落库的生成请求，仅可本地暂存选择，并 SHALL 显示可区分的客户鉴权/绑定拒因而非引导启动浏览器

#### Scenario: 超长或超量输入被诚实拒绝

- **WHEN** `keywordSelections` 某项超单项长度上限或总条数超上限（含经自由文本注入的超量内容）
- **THEN** 云端诚实拒绝该次生成、MUST NOT 把超长/超量文本原样喂进 prompt，客户端显示真实失败原因

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

Cloud SHALL 在客户鉴权环境状态中返回该环境绑定解析状态及账号“是否已绑人设”的权威结果。客户端 SHALL 按“绑定待解析 / 已解析且已绑 / 已解析且未绑”三态渲染；该真态来自客户拥有环境与账号绑定的服务端解析，MUST NOT 依赖浏览器、CDP、页面登录态或 Edge WS hello。为了避免 stale-true 泄漏，环境切换、客户切换或归属刷新时客户端 MUST 先清除上一账号投影，待目标环境的新权威响应重建。

浏览器无关 core 的 `ui.snapshot.personaBound` MAY 在兼容窗口继续下发，但只能作为同一权威结果的辅助同步，MUST NOT 成为新客户端判断人设绑定的唯一来源。旧客户端仍可按既有 WS 快照语义工作。

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

### Requirement: 生成 gate 判据不放宽但引导透明

新客户端的人设生成 gate SHALL 为“客户会话有效、环境归属通过、账号绑定已权威解析且 Cloud 请求通道可用”；判据 MUST NOT 包含 core 子进程存在、页面 `auth === logged in`、Edge WS 已连接、浏览器已启动、CDP 或槽位。未满足时客户端 MUST 禁止提交并分别显示客户登录、环境归属、绑定解析或 Cloud 可用性的真实前置，MUST NOT 提示“请先启动浏览器”。旧客户端在兼容窗口仍 MAY 使用既有 `auth && cloud` gate。

#### Scenario: 客户未登录时分态引导

- **WHEN** 客户会话无效
- **THEN** 生成按钮 disabled，提示客户登录，不得引导打开平台浏览器扫码

#### Scenario: 绑定已解析且 Cloud 可用时不看浏览器状态

- **WHEN** 客户会话有效、环境归属和绑定可信且 Cloud 请求通道可用，但浏览器关闭、CDP 缺席或 Edge WS 重连中
- **THEN** 生成按钮可用，提交不进入浏览器调度链

#### Scenario: Cloud 请求不可用时诚实失败

- **WHEN** 客户鉴权有效但 Cloud 人设接口不可达
- **THEN** 客户端显示 Cloud 请求失败/可重试状态，MUST NOT 把失败改写为“浏览器未启动”

### Requirement: 人设向导使用吉祥物功能色并保留多平台身份

Edge 客户端账号人设向导 SHALL 使用 AIDCP 吉祥物色系建立局部视觉层级：青绿蓝作为通用功能交互色，金黄作为待确认/待更新状态色，珊瑚色可作为小红书平台点缀。选择项文字 SHALL 与区块标题形成可辨层级，MUST NOT 依赖过重字重表达选中状态；选中状态 SHALL 主要由指示器、边框、浅底和文字颜色共同表达。

平台身份与功能交互色 MUST 正交：当前环境为 `xiaohongshu` 时，人设浮层 SHALL 显示“小红书”及其平台点缀；当前环境为 `facebook` 时 SHALL 显示“Facebook”及 Facebook 平台蓝。通用选择、步骤和 CTA MUST NOT 因平台切换而改变功能语义或被写死为单一平台样式。

未选内容项和自定义入口的加号 SHALL 使用不依赖字体字形基线的几何绘制，确保跨 PingFang、Microsoft YaHei、Segoe UI 等系统字体时保持视觉居中。

#### Scenario: Facebook 环境显示平台身份但沿用通用功能色

- **WHEN** 当前环境平台为 `facebook` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“Facebook”并使用 Facebook 平台蓝，而步骤、选择项和主 CTA 仍使用吉祥物青绿功能色

#### Scenario: 小红书环境显示小红书平台身份

- **WHEN** 当前环境平台为 `xiaohongshu` 且用户打开账号人设向导
- **THEN** 浮层平台标签显示“小红书”并使用珊瑚平台点缀，MUST NOT 残留 Facebook 文案或平台类

#### Scenario: 加号跨字体保持居中

- **WHEN** 未选内容项或自定义入口在任一受支持系统字体栈下渲染
- **THEN** 加号由几何线条居中绘制，不依赖 `+` 字符的字形基线

