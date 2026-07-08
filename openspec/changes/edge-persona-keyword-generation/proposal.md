## Why

今天账号人设只能由运营在管理后台手写 YAML（`/persona` 页）。而真实账号是在 Electron 客户端"新建环境 + 扫码登录"时才落地的——新号落地后卡在 `needs_persona_setup`、必须等运营手动补人设才能开跑。这是一道人工瓶颈，也把"谁最了解这个号该是什么人设"（正在现场操作的客户）排除在外。

本变更让客户在客户端**扫码登录后就地自助建人设**：选几类关键词 → 云端用大模型生成人设草稿 → 客户确认 → 落库开跑。把 onboarding 的人设这一步从"运营事后手写"变成"客户当场自助"。

## What Changes

- **新增 edge onboarding 人设向导**：Electron 伴随 UI 在扫码登录、握手完成后弹出关键词选择向导（垂类/兴趣/语气/互动偏好，封闭枚举多选），一键触发生成，展示草稿，支持"重新生成"（不限次）与"确认落库"。
- **新增两对边→云 WebSocket 消息**（`persona.generate` / `persona.persist`，均为**边缘发起的请求/响应**）：回包走 pending-id 命中路径，**不经主动命令白名单**（规避静默丢弃 footgun）、**不碰 command-bridge**。协议两份 `protocol.ts` 逐字同步 + 补 AC-PROTO 穷举 + 更新 `docs/protocol.md` 计数与消息表。
- **新增云端 persona 生成器角色**：调云端唯一文本大模型出口（按角色配模型、按 `accountId` 记账）→ 输出 **JSON** → **云端确定性序列化成 soul YAML** → 复用 `loadSoulFromValue` 结构校验。生成 prompt 内置**每账号差异化**（差异化落在 `seed_keywords`/搜索词这条真封号链路上，而非仅 identity/tone 文案）。登记进 `role-catalog`。
- **生成失败硬 fail-closed**：大模型超时/输出不可解析/校验不过 → 修复重试 1–2 次仍失败则诚实回 `generation_failed` / `persona_invalid`，账号维持"缺人设"，**绝不回落任何模板/默认人设**（守"绝不静默假成功"+"无默认人设"红线）。
- **生成调用幂等**：`persona.generate` 带 idempotency key，云端对同键去重 + 缓存结果；配显式 `timeoutMs ≥ 185s`（对齐 180s 模型天花板）。防已上线的自动重连在 185s 在途窗口 reject 挂起请求导致的**双份付费调用/双计费**。
- **落库复用现有已校验写入通道**：`persona.persist` 携确认后的 soul YAML → 走现有人设单写通道（`loadSoulFromValue` 校验 + 外键守护 + 绑定即热加载唤醒在线节点 + 诚实回执）。边缘只透传诚实 `reason`、不本地判成功。
- **适用范围**：仅**新号 onboarding 一次性**（不含老号事后重建）。
- **大模型/密钥/校验/序列化/落库/记账全在云端**；边缘只做"收关键词勾选 / 显示草稿 / 回确认"三件事，不嵌大模型、不持密钥、不碰 PG。

### Deferred / Accepted Risks（本变更明确不做、已知接受、后续单独立项）

- **边缘身份鉴权**：边云握手今天零鉴权、`accountId` 由客户端自报（运营模型靠"8787 只我方受控机可达"的隐性网络边界兜住，自助模型把边缘搬到客户机后该边界失效）。本变更**不补**该鉴权。
- **限流/配额**：不做按连接/IP 限流，也不做重生成上限——即生成端点在公网上不限量。
- **服务端枚举复验**、**"只创建不覆写"人设写入守护**：本期不做。
- **跨账号语义去重 + 运营侧相似度报表/抽检**：后置为独立变更。

**接受后果记账**：本期 MVP 形态 = 一个公网可达、不鉴权、不限量、不校验输入枚举的付费大模型生成端点，唯一防护是幂等键（防重复计费）。存在"免费大模型刷调用（成本敞口无上限）"与"给尚无人设的账号抢先写人设"两类敞口，均已知并接受，留待后续变更收口。

## Capabilities

### New Capabilities
- `persona-keyword-generation`: 客户在 Electron 客户端 onboarding 时，选关键词 → 云端大模型生成人设草稿 → 确认 → 经现有已校验写入通道落库的自助建人设能力；含边→云 `persona.generate`/`persona.persist` 请求/响应契约、生成失败硬 fail-closed、幂等、每账号差异化，及大模型留云端的边云分工。

### Modified Capabilities
<!-- 无。现有 account-persona-config / mandatory-account-persona / persona-gated-session-start 的要求不变：
     新写入路径仍复用同一 soul 校验与"无默认人设/必填"不变量，本变更是新增一条 onboarding 生成+落库通道，
     不改这些既有 spec 的 requirement 级行为。 -->

## Impact

- **aidcp-edge**：`src/electron/renderer/`（新增关键词向导，vanilla DOM+JS、套现有 editingProvider/dirty latch 防周期性 status 推送重置进度）、`preload.cjs`/`main.cjs`（新增 IPC verbs + `ipcMain.handle`）、`src/client/edge-client.ts`（发 `persona.generate`/`persona.persist` 的 `request()`，显式长超时）、`src/comm/protocol.ts`（新增消息类型 + 载荷）。触发键 = 身份已确立事件（真实 userid，非 env-label）。
- **aidcp-cloud**：`src/comm/protocol.ts`（与 edge 逐字同步）、边云消息处理层（处理 `persona.generate`：生成器角色→差异化→JSON→YAML 序列化→校验；`persona.persist`：复用人设写入通道）、新增 `PersonaGenerator`（仿现有命令式生成器角色）、`role-catalog.ts` 加一个 persona 生成角色、新增 JSON→soul YAML 确定性序列化器、`server.ts` 装配把大模型客户端穿进该链路。
- **docs**：`docs/protocol.md` 头部消息计数 + 消息表同步。
- **测试**：补 AC-PROTO 漂移哨兵穷举；生成失败 fail-closed / 幂等去重的回归。
- **热点单写文件（须串行、不与他人并行改）**：两份 `protocol.ts`、`role-catalog.ts`（`RoleName` 枚举）。请求/响应不碰 command-bridge、不碰 onMessage 主动命令白名单。
- **不涉及**：风控状态机、发布链、console（跨账号报表在后续 P1 变更再碰）。
