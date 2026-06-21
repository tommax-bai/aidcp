## Why

上周归档的 `console-model-provider-config` 让运营能在后台改**全局**模型名（文本 Qwen / 图片万相，热加载）与密钥（加密落库）。但现状是**全系统所有角色共用同一个文本模型（`qwen-turbo`）、同一个温度（0）**：`server.ts` 只构造一个 `QwenClient`，浏览侧 ~11 个判定/生成角色经基类统一调用、发布侧 5 个角色直接持有同一客户端。

任务性质天然分层——**判定类**（该不该看 / 赞 / 关注 / 评论）要的是快和便宜，**生成类**（写帖子正文 / 写评论 / 配图文案）要的是强。当前无法给生成类单独升配模型，是一个现成的质量杠杆没用上。本 change 给后台补一个「角色配置列表页」，让运营**按角色**覆盖文本模型名与温度，复用 `console-model-provider-config` 已上线的存储/热加载范式。

设计与对抗评审基线（已收敛）：
- **只做按角色配「文本模型 + 温度」**；prompt 编辑/只读、图片模型 per-role、采样参数（maxTokens/超时）均明确**不在本期**。
- **温度只对生成/改写类角色开放**（判定类强依赖确定性结构化输出，温度高会让下游 JSON 解析变脆，温度旋钮在判定类 UI 上不存在）。
- **角色清单走白名单制**：只列「现役 + 真调大模型」的角色，纯规则角色与 v1 遗留角色**不出现在页面**。
- 一处关键安全纠正：发布审批门槛背后有**代码层人审硬闸**（`publish-executor` 下发前查批准信号），与模型/温度配置无关，本 change 不触碰发布安全闸。真正怕改坏的红线在浏览侧 prompt（本期不开放编辑，天然规避）。

## What Changes

- **cloud / 角色目录（新）**：新增 `src/config/role-catalog.ts`，把浏览侧 `RoleName` 与发布侧 `RoleConfig.name` 两套命名合并导出为统一形状 `{ roleId, displayName, group, llmKind, tunable }`，**统一加 `browse:` / `publish:` 前缀防撞键**。白名单制——只列现役且真调 LLM 的角色，标 `llmKind: 'text' | 'image' | 'none'` 与 `tunable.temperature`（仅生成/改写类为 true）。
- **cloud / 角色配置存储（新）**：新增 `src/config/role-config-store.ts` + `migrations/000N_role_config.sql`，新表 `role_config(role_id PK, model, temperature, updated_at, updated_by)`（**不复用 `model_config` 单行表**——它是 `id=1` 单行结构）。沿用 `ModelConfigStore` 范式：内存镜像 + 缺行/空/无效一律回落（模型回落全局 `textModel`、温度回落代码默认 0）+ 运行时热加载。**严格复刻「写库成功才刷新内存镜像」的时序**。
- **cloud / LLM 客户端 per-call 覆盖（核心改造，向后兼容）**：`QwenClient.chat()/complete()` 加可选 `opts?: { role?, model?, temperature?, timeoutMs? }`，请求体改为 opts 优先、再回落现有 `getModel()/this.temperature/this.timeoutMs`。**不传 opts 时行为完全不变**（作为不变量写进 spec，保证现有调用零回归）。把浏览侧弱接口 `{ complete }` 与发布侧具体 `QwenClient` 类型**统一到一个 `LlmClient` 接口**（含 `complete + chat + 可选 opts`），发布角色字段类型放宽为接口。
- **cloud / 按角色注入（不动角色内部代码）**：`RoleDispatcher` 与 publish 装配处，把传入的同一个 llm 换成「已绑定角色 id 的 thin wrapper」——`{ complete: p => llm.complete(p, resolve(roleId)) }`，`resolve(roleId)` 读 `RoleConfigStore`（缺则回落）。**两侧只换传入的 llm 对象，角色内部零改动。**
- **cloud / 无效模型名诚实处理（自由输入 + 保存前探活）**：模型名由运营**自由输入**（不维护白名单下拉）；`PUT` 时对非空模型名做一次**保存前探活**（发一次轻量请求验证模型真实可用）；**探活不过 MUST 被拒并报因，绝不静默落库**（避免无效名运行期才 4xx，发布侧无兜底角色会卡死）——遵守「绝不静默假成功」红线。空值视作「保持回落」。
- **cloud / 面板接口（JWT 守护，非乐观）**：`GET /api/roles`（返回 catalog）、`GET /api/roles/:roleId/config`、`PUT /api/roles/:roleId/config`（改模型/温度，校验后 round-trip 回真态 + `updated_by` + `updated_at`，使并发覆盖可见）。
- **cloud / 调用可观测（顺手，零成本）**：per-call opts 既带 `role`，在 LLM 出口记一行结构化日志（`role` + 生效 `model` + 耗时），让运营改完能验证是否真生效、是否真变贵——**只记日志，不建计费面板**。
- **console / 角色配置页（新）**：新增 `RolesPage`（AntD Table，每行一角色：显示名 / 组 / 模型类型 / 当前生效模型 / 温度；行内或抽屉编辑），复刻 `SettingsPage` 的非乐观写范式。纯规则/遗留角色不出现；判定类无温度字段。

## Capabilities

### New Capabilities
- `role-llm-config`: 管理后台按角色配置大模型——角色目录白名单暴露（区分模型类型、遗留/纯规则不列）、按角色覆盖文本模型名与温度（缺省回落全局/代码默认、运行时热加载、绝不 brick）、LLM 客户端 per-call 覆盖向后兼容、无效模型名诚实拒绝绝不假成功、面板接口 JWT 守护且写非乐观回真态、调用按角色可观测。

## Impact

- **cloud（aidcp-cloud）**：新 `src/config/role-catalog.ts`、`src/config/role-config-store.ts`、`migrations/000N_role_config.sql`；改 `src/llm/qwen.ts`（per-call opts + 统一 `LlmClient` 接口，保留默认与 `fetchImpl` 桩签名）、`src/orchestrator/role-dispatcher.ts`（注入 role-bound wrapper）、`src/server.ts`（装配 store、两侧 wrapper、面板 deps、LLM 出口日志）、`src/panel/panel-server.ts` + `src/panel/types.ts`（`/api/roles*` 路由）；publish 角色 `llmClient` 字段类型由具体 `QwenClient` 放宽为 `LlmClient` 接口。
- **console（aidcp-console）**：新 `src/pages/RolesPage.tsx`；改 `src/api/queries.ts`（`useRoleCatalog` / `useRoleConfig` + mutation）、`src/types/api.ts`（DTO，两端手动同步）、`src/App.tsx`（路由）、`src/pages/AppShell.tsx`（导航）。
- **协议无关**：本 change 是云端内部 LLM 注入改造，**不碰边-云 WebSocket 协议 v2**，无需 protocol.ts 三处同步那套。
- **回归红线**：per-call opts「不传即不变」必须有护栏测试；既有 `qwen` / 各角色调用与测试桩零破坏；面板新路由全程 JWT、写非乐观；无效模型名绝不静默落库（AC 级别）。
- **明确不做（YAGNI）**：图片模型 per-role 配置（已有全局 `model_config`，避免双写冲突）；maxTokens / HTTP 超时下放（两层超时易打架）；prompt 在线编辑/只读展示（后续独立 change，确有工单才启动）；用途分组抽象（真 LLM 角色 ≤ ~16 个，逐角色白名单即可）；RBAC / 多 provider / 灰度 A-B / 计费 dashboard。
