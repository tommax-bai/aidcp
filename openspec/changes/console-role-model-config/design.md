# Design — console-role-model-config

> 现状坐实来自两次全仓盘点 + 对抗评审（2026-06-21）。文件:行均为 `aidcp-cloud` / `aidcp-console`（子仓，本仓未 checkout）。

## 现状坐实（文件:行）

- **全进程单一文本客户端**：`server.ts:137` 只构造一个 `QwenClient`（不传 model → 代码默认 `qwen-turbo`；不传 temperature → 构造默认 `0`；不传 timeoutMs → 默认 30s）。`server.ts:139` 注入 `getModel` 闭包读 `modelConfigStore.getCached().textModel`。
- **温度构造期固化**：`qwen.ts:66` `this.temperature` 为 `private readonly`，`chat()`（:79）请求体 `:93` `model: this.getModel?.() ?? this.model`、`temperature: this.temperature`（无 per-call 入口）、超时用 `this.timeoutMs`（AbortController）。**模型名是唯一已热加载的参数；温度/超时要热加载必须改成 per-call 解析**（否则改了要重启，与现有范式不一致）。
- **LLM 接口当前只有 complete**：`qwen.ts:15-17` `LlmClient { complete(prompt): Promise<string> }`。
- **两套注入/调用约定**：
  - 浏览侧：`role-dispatcher.ts:260` `commonOptions = { eventBus, soul, llm }`，`llm` 是弱接口 `{ complete }`；基类 `base-role.ts:51/:58` 统一 `decide(prompt) → this.llm.complete(prompt)`。
  - 发布侧：`server.ts:474` 起逐个 `new XxxRole({ llmClient: llm })`，字段是**具体 `QwenClient` 类型**（`content-creator.ts:10,:28`），调用走 `this.llmClient.chat([system,user])`（`content-creator.ts:50`）。
  - → wrapper 必须同时覆盖 `complete` 与 `chat`；发布角色字段类型若不放宽为接口，传 wrapper 会 TS 编译失败。**借此统一到一个 `LlmClient` 接口**。
- **配置存储范式（须复刻）**：`model-config-store.ts` 单行表 `id=1`（`:26` schema），`set()`（:101）**先 INSERT/ON CONFLICT 写库成功、再 `this.cache = next`**；`getCached()` 同步返回内存镜像。回退**只在空/空白时触发**（`:73` `?.trim() || DEFAULT`）——**非空但无效的模型名不回退**。图片模型已在该表 `:18`。
- **角色名两套真源**：浏览 `RoleName` 联合类型（`event-bus/types.ts:416`，~34 项含条件注册的 `concept_extractor`），snake_case；发布 `RoleConfig.name`（publish 侧 `base-role.ts`），驼峰（如 `ContentCreator`）。
- **真正调 LLM 的角色（白名单基线）**：
  - 浏览文本（经 `complete`）：`content_curator`、`content_evaluator`、`search_evaluator`、`interaction_appraiser`、`follow_agent`、`author_evaluator`、`comment_appraiser`、`comment_composer`、`comment_reviewer`、`comment_de_ai_flavor`、`concept_extractor`（~11）。
  - 发布文本（经 `chat`）：`ContentScout`、`ContentCreator`、`ImagePlanner`、`QualityScorer`、`ApprovalGatekeeper`（确切 5）。
  - 发布图像：`ImageGenerator` 用 `wanxiangClient`（imageModel，**不在本期 per-role 配**）。
  - 其余几十个为纯规则角色，v1 遗留为 plan/anchor/select 兼容路径——**均不列入页面**。
- **安全闸（与本 change 解耦，纠正评审前误判）**：`publish-executor.ts:127-130, 209-222` 在下发任何发帖指令前查 `isApproved(requestId)`，未批一律 `needs_review`、绝不下发；`approval-gatekeeper.ts:66-77` 还有 LLM 失败时的代码兜底规则。**改模型/温度威胁不到发布安全**。
- **console 范本**：`SettingsPage.tsx`（模型配置页，非乐观写）、API client `client.ts`（`apiGet/apiPut`、401、Bearer、ApiError 现成）、`queries.ts`（useQuery + useMutation + invalidate）、路由 `App.tsx`、导航 `AppShell.tsx`、DTO `types/api.ts`（无 codegen，两端手动同步）。

## 业界方案取舍

| 业界模式 | 取/舍 | 落到本系统 |
| --- | --- | --- |
| LLM 网关 / 按调用方路由模型 | 取**思想**、舍独立进程 | 单 provider 单账号，不引 LiteLLM/Portkey；「路由表」= `role → model` PG 表，「路由器」= 扩展后的按角色解析。 |
| feature-flag 式带默认回退 | **取（安全底座）** | 完全复用 `ModelConfigStore` 范式：DB 存覆盖、缺/空/无效回落代码默认，绝不 brick。 |
| 配置即代码 vs DB + 热加载 | 分层 | 模型名/温度 → DB + 热加载（高频改、即时生效）；prompt/红线/JSON 契约 → 永远代码为真源（本期不进配置面）。 |
| Prompt 版本化/模板/灰度/RBAC | **本期全舍** | prompt 编辑后置为独立 change；灰度/A-B（单账号无意义）、RBAC（模型可秒回滚）不做。 |

## 角色目录（role-catalog.ts）

- 合并两套角色为统一形状：`{ roleId, displayName, group: 'browse' | 'publish', llmKind: 'text' | 'image' | 'none', tunable: { temperature: boolean } }`。
- `roleId` 加前缀防撞键：`browse:content_evaluator` / `publish:ContentCreator`。
- **白名单制**：只导出现役且 `llmKind !== 'none'` 的角色；纯规则、v1 遗留角色不进 catalog（从源头防止运营误把遗留路径当现役配）。
- `tunable.temperature = true` 仅给生成/改写类：`comment_composer`、`comment_de_ai_flavor`、`concept_extractor`、`ContentCreator`、`ImagePlanner`；判定类为 false。
- catalog 在 `server.ts` 装配后注入 panel（panel 层不直接 import 角色实现，保持薄）。
- **不照搬文档的「15 角色」**（计数滞后于代码），以代码 `RoleName` / 实例 `roles.map(r => r.roleName)` 为真源。

## 数据模型（migrations/000N_role_config.sql，幂等）

- `role_config`：`role_id text PRIMARY KEY`、`model text`（NULL = 用全局 textModel）、`temperature real`（NULL = 用代码默认 0）、`updated_at timestamptz`、`updated_by text`。
- 缺行 / 字段 NULL / 字段无效 = 回落。与 store `CREATE TABLE IF NOT EXISTS` 同源（沿用 `0007_model_config.sql` 风格）。

## 运行时解析（核心改造，最小化）

1. **`QwenClient` 开 per-call opts**（`qwen.ts:79`）：`chat(messages, opts?)` / `complete(prompt, opts?)`，`opts?: { role?, model?, temperature?, timeoutMs? }`。请求体：
   - `model`：`opts?.model ?? this.getModel?.(opts?.role) ?? this.model`（`getModel` 升级为可接收 `role`）。
   - `temperature`：`opts?.temperature ?? this.temperature`。
   - 超时：`opts?.timeoutMs ?? this.timeoutMs`。
   - **不传 opts → 行为逐字不变**（零回归不变量）。
2. **统一 `LlmClient` 接口**：`{ complete(prompt, opts?), chat(messages, opts?) }`；发布角色 `llmClient` 字段类型放宽为该接口。
3. **role-bound thin wrapper（注入侧，不动角色内部）**：
   - `resolveRoleLlmConfig(roleId)` 读 `RoleConfigStore`（缺/空/无效回落全局/默认）。
   - 浏览侧（`role-dispatcher.ts:260`）：`commonOptions.llm = { complete: p => llm.complete(p, resolve('browse:'+roleName)) }`。
   - 发布侧（`server.ts:474`）：每个 `new XxxRole({ llmClient: wrap(llm, 'publish:'+name) })`。
4. **`RoleConfigStore`**：`init()` 载内存镜像；`getForRole(roleId)` 同步返回生效 `{ model, temperature }`（缺/空/无效回落）；`set(roleId, patch, by)` **先写库成功、再刷镜像**（复刻 `model-config-store.ts:101` 时序）；解析器**永不抛**（任一字段坏 → 回落）。

## 无效模型名诚实处理（自由输入 + 保存前探活）

- 模型名由运营**自由输入**（不维护白名单下拉，避免新增模型还要改清单）。
- `PUT /api/roles/:id/config` 对非空 `model` 做**保存前探活**：用该模型发一次极小的轻量请求（如最短 prompt + 极小 max tokens），成功才落库；探活失败 → **400 + 诚实原因（`model_invalid`），绝不落库**。空 `model` 视作「保持回落」，不探活、不报错。
- 探活复用现有文本客户端的 per-call `opts.model + opts.timeoutMs`（短超时），不新建调用通道。
- 理由：现状回退只认空值（`model-config-store.ts:73`），无效名会原样进缓存、运行期才 4xx；浏览侧 throw 被吞成保守降级（安全但功能哑火），**发布侧无兜底角色（如 ContentCreator）会整条流水线卡死**。这是「绝不静默假成功」红线在配置面的体现。

## 面板接口（JWT 守护，非乐观）

- `GET /api/roles` → `{ roles: RoleCatalogItem[] }`（含 `currentModel` 生效值、`currentTemperature`、`tunable`）。
- `GET /api/roles/:roleId/config` → 该角色生效配置 + 是否为覆盖值。
- `PUT /api/roles/:roleId/config` `{ model?, temperature? }` → 校验（角色在 catalog 白名单内 / 非空模型经保存前探活通过 / 温度仅 tunable 角色可改且在 [0,1] 区间）→ `set` → **回显写后真态 + `updated_by` + `updated_at`**（使并发 last-write-wins 可见）。
- 复用 `panel-server.ts` 现有 JWT 前置校验（operator = `verified.payload.sub`）。

## 红线与不变量

- **per-call opts 不传即不变**：现有所有 `complete/chat` 调用零回归（护栏测试）。
- **绝不 brick**：角色配置任一字段缺/空/无效一律回落全局/代码默认；解析器永不抛。
- **绝不静默假成功**：无效模型名写入被拒报因，不落库。
- **写库成功才刷内存镜像**：复刻现有时序，避免缓存与库不一致。
- **协议无关**：不碰边-云协议 v2；面板新路由全程 JWT、写非乐观。
- **不触发布安全闸**：人审硬闸在代码层、与配置无关。
- **温度仅生成/改写类**：判定类无温度字段（少一个能改坏结构化解析的口子）。

## 并发与可观测

- 多运营并发 PUT 同角色 = last-write-wins（单行 upsert）；MVP 接受，但 **PUT 必回显真态 + updated_by/at** 让覆盖可见（无乐观锁）。
- 热加载与进行中会话：下次 `getForRole` 即生效，可能「同会话中途换模型」——模型名无害；温度仅生成类开，规避「会话中途解析变脆」。
- LLM 出口记 `role + 生效 model + 耗时` 结构化日志（防黑盒），**不建 dashboard**。
