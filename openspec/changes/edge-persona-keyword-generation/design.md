## Context

账号人设 = 按账号存 PG `persona_config` 的 soul（`identity` + `interests` + 可选 `behavior_guidelines`），写入经 `loadSoulFromValue` 严格结构校验、无默认/兜底人设、缺人设的账号被入口闸以 `needs_persona_setup` 拒绝运行。今天人设只能由运营在 console `/persona` 页手写 YAML。

真实账号在 Electron 客户端"新建 AdsPower 指纹环境 → 起浏览器 → 扫码登录 → 从登录后 DOM 读平台真实 userid → 该 userid 作 `accountId` 握手 → 云端物化 `accounts` 行"这条链里落地。人设落库外键指向 `accounts` 行，因此只能发生在**握手之后**。

边缘端已具备：一套 vanilla-JS Electron 伴随 UI（含"新建环境"向导作结构兄弟）、到云端的单条 WebSocket 通道（协议 v2，握手带 `accountId`）、`request()` 请求/响应原语（回包按 pending-id 命中、不经主动命令白名单）。边缘端今天基本不碰人设。

**关键约束**：① 边云握手**零鉴权**、`accountId` 客户端自报（运营模型靠"8787 只我方受控机可达"的隐性网络边界兜底）；② 云端唯一文本大模型出口按角色配模型 + 按 `accountId` 记账、180s 单次天花板、无原生 JSON 模式、无内建重试；③ soul 侧只有极简自写 YAML 解析器（对缩进 fail-fast）、无序列化器；④ 边缘自动重连已上线，断连会 reject 所有挂起请求。

## Goals / Non-Goals

**Goals:**
- 客户在客户端 onboarding 时选关键词 → 云端大模型生成人设草稿 → 确认 → 经现有已校验通道落库、绑定即开跑。
- 大模型/密钥/校验/序列化/落库/记账全留云端；边缘只做交互（收勾选 / 显示草稿 / 回确认）。
- 生成失败硬 fail-closed，绝不落任何模板/默认人设。
- 生成调用幂等，重连/重试不双计费。
- 生成产物在跨账号维度有差异化（差异化落在 `seed_keywords`/搜索词这条真封号链路上）。

**Non-Goals（本期明确不做，见 proposal 的 Deferred/Accepted Risks）:**
- 边缘身份鉴权（`accountId` 仍自报）。
- 限流/配额、重生成上限。
- 服务端关键词枚举复验、"只创建不覆写"写入守护。
- 跨账号语义去重、运营侧相似度报表/抽检（后续独立变更）。
- 老号事后重建人设（仅新号 onboarding 一次性）。
- console 侧任何改动。

## Decisions

### D1：大模型留云端，边缘只交互（否掉"客户端接入 LLM"字面方案）
边缘 = 客户自有机器，无百炼密钥、且"边轻云重"要求决策在云端。客户端直连大模型会泄露密钥、绕过按角色配置与按账号记账、把唯一出口散落。**决定**：边缘只收关键词、显示草稿、回确认；生成/校验/序列化/落库/记账全在云端。

### D2：通道 = WS"边缘发起的请求/响应"，否掉 Electron 直连 HTTP
两条备选：(A) WS 上新增 `persona.generate`/`persona.persist` 请求/响应；(B) Electron 直接 HTTP 调云端端点。
- 选 A。理由：边→云今天只有 WS 一条通道、零 HTTP 客户端；请求/响应回包走 pending-id、**永不经主动命令白名单**（规避静默丢弃 footgun）；落库直接复用云端成熟人设写入通道。
- 否 B。理由：客户 Electron 无运营 JWT、onboarding 期云端尚无该账号服务端凭据（鸡生蛋）；HTTP 要新暴露公网端点 + 新造鉴权；边缘要新增 HTTP 客户端，`accountId` 真相在"WS 握手"与"HTTP 自证"间 split-brain。
- **诚实标注**：选 A **不是**因为"WS 已被握手鉴权"——握手零鉴权。A 与 B 在自助模型下都缺边缘身份证明；本期按 Non-Goal 暂不补，接受该敞口。

### D3：大模型吐 JSON → 云端确定性序列化成 soul YAML（不让模型直接吐 YAML）
soul 侧解析器是极简自写、对缩进 fail-fast，高温中文模型直接吐 YAML 极易解析失败。**决定**：生成器 prompt 要求输出 JSON（对齐现有命令式生成器角色的既有做法）→ 云端写一个小的确定性 JSON→soul YAML 序列化器 → 再过 `loadSoulFromValue` 结构校验。YAML 语法层失败模式因此消失。

### D4：生成失败硬 fail-closed
大模型超时/输出不可解析/校验不过 → 修复重试 1–2 次仍失败 → 诚实回 `generation_failed`/`persona_invalid`，账号维持"缺人设"，**绝不回落模板/默认人设**（守"绝不静默假成功"+"无默认人设"）。备选"失败回模板"被否——直接破两条红线。

### D5：生成调用幂等
`persona.generate` 携客户端生成的 idempotency key；云端对同键去重 + 缓存结果，重连/重试命中缓存、不重复调大模型、不双计费；**只有 `persona.persist` 才翻转"已绑人设"状态**。配显式 `timeoutMs ≥ 185s`（对齐 180s 模型天花板；`request()` 默认仅 15s，必须覆盖）。

### D6：落库复用现有已校验写入通道
`persona.persist` 携确认后 soul YAML → 走现有人设单写通道（`loadSoulFromValue` 校验 + 外键守护 + 绑定即热加载唤醒在线节点 + 诚实回执）。不新造写路径，"校验后落库/无默认/写库成功才刷镜像"等不变量天然保留。边缘只透传诚实 `reason`、不本地判成功。

### D7：生成器角色仿现有命令式生成器 + 登记 role-catalog
新增 `PersonaGenerator`（注入按角色大模型客户端、`complete` 携角色键、按 `accountId` 记账），登记进 `role-catalog` 的 `RoleName` 枚举——白嫖按角色配模型/温度 + 按账号记账 + 后台 prompt 预览。**不在消息处理层裸调大模型**（会丢按角色配置与记账、把出口散落，有真机教训）。

### D8：每账号差异化打在 seed_keywords 上
生成 prompt 内置每账号差异化维度（如随机差异化种子 + 温度），**重点抖动 `seed_keywords`/搜索词**（这是被平台当同质信号、真封号的链路），而非仅 `identity`/`tone` 文案。跨账号语义去重（看得到全队的控制）后置为运营报表。

### D9：触发点 = 握手后（身份已确立）
向导触发键 = "账号身份已确立"事件（真实 userid、来源非 env-label），此刻 `accounts` 行应已存在（FK 前提）。AdsPower 模式无显式登录成功事件，身份行是唯一成功信号——不 hook cookie 轮询。

## Risks / Trade-offs

- **[零鉴权 + 不限量付费端点]** 公网可达、`accountId` 自报、无限流 → 免费大模型刷（成本敞口无上限）+ 给尚无人设账号抢先写人设。→ 本期唯一防护 = 幂等键（仅防重复计费）；**已知接受**，收口留后续独立变更（边缘身份鉴权 + 按连接/IP 限流 + 枚举复验 + 只创建不覆写）。
- **[FK post-handshake 是尽力而为]** 云端 `ensureAccount` 包在 try/catch、PG 抖动可能 welcome 已发但 `accounts` 行没建 → `persona.persist` 命中外键守护回 `unknown_account`。→ Mitigation：persist 必须把 `unknown_account` 当**正常分支**优雅处理、向导可重驱；付费 `generate` 前先确认 `accounts` 行到位，杜绝"先花钱后搁浅"。
- **[稀薄关键词 → 同质化]** 同垂类客户勾同样关键词，大模型均值回归 → 一批号 `seed_keywords` 雷同 → 跨号搜索词同质、可聚类。→ Mitigation：D8 每账号差异化 + 硬性重生成上限（饱和诚实回"需人工"、不无限烧）；跨账号语义去重后置运营报表（P1）。
- **[自写 YAML 解析器 fail-fast]** 模型直吐 YAML 易解析失败。→ Mitigation：D3 JSON + 确定性序列化器。
- **[185s 在途 × 自动重连]** 长在途窗口内重连 reject 挂起请求、云端可能已成功已记账 → 双计费/假失败。→ Mitigation：D5 幂等键 + 显式长超时。
- **[onMessage 白名单 footgun]** 若把"展示待确认草稿"设计成 cloud→edge 主动 push 命令，须在白名单放行否则静默丢弃（typecheck 抓不到）。→ Mitigation：坚持 D2"边缘发起请求/响应"，回包走 pending-id、天然不触白名单。
- **[协议热点并发]** 两份 `protocol.ts` + `role-catalog` 是并行开发单写者。→ Mitigation：本 change 独占改动、串行集成；请求/响应不碰 command-bridge。

## Migration Plan

- 协议为**新增消息、非破坏**：两份 `protocol.ts` 逐字同步新增 → 先部署 cloud（新处理器对旧 edge 不产生影响，旧 edge 不发这些消息）→ 再发 edge 安装包（新向导 + 新 `request()`）。
- 回滚：edge 回退到旧安装包即停用向导；cloud 新处理器无人调用时闲置、可保留或回退。
- dev 优先按默认部署序列上线验证；ol 待用户明确要求。

## Open Questions

- 向导触发方式：MVP 先"客户自发起"（省协议字段），还是"云端驱动提示缺人设"（需欢迎帧/快照帧加字段）？
- 关键词菜单的维度与每维选项清单由谁定枚举（默认 4 维：垂类/兴趣/语气/互动偏好）。
- 每账号差异化注入强度（`seed_keywords`/`identity`/`tone` 抖动幅度既差异化又不失真）。
- 硬性重生成上限的具体值（同垂类饱和判定与"需人工"话术）。
