## Why

后台需要「按账号 / 角色 / 模型 / 日期」看 LLM token 消耗，并按每 10 分钟看曲线。坐实现状：

- 云端只有一个文本 LLM 出口 `QwenClient`（`../aidcp-cloud/src/llm/qwen.ts`）走 DashScope OpenAI 兼容 `/chat/completions`。兼容模式响应体**带 `usage`（prompt/completion/total tokens）**，但 `ChatCompletionResponse` 类型（`qwen.ts:76-79`）没声明 `usage`，解析时只取 `choices[0].message.content`（`qwen.ts:149`）——**真实 token 用量被静默丢弃，全系统任何地方都没记录**（全仓 grep 无 tokens 持久化）。
- 已有一个可观测钩子 `onCall`（`qwen.ts:73` 类型、`qwen.ts:157` 在 finally 触发）回报 `{role, model, ms, ok}`，接到 `server.ts:186` 的 `console.log`。**生效模型名**在 `qwen.ts:120` 已按角色解析好；**角色标识**在所有真实调用点都在（浏览 `browse:<role>` 经 `base-role.ts:82`、发布 `publish:<Name>` 经 `roleLlm` wrapper `server.ts:182`）。即「角色 + 模型 + 时刻」三维在出口处天然可得，唯独 token 量被丢、account 维度未接线。
- 账号维度：系统**现为单租户**——`RoleDispatcher.currentAccountId` 钉死 `'default'`（`role-dispatcher.ts:164`），LLM 调用点拿不到真实账号。多账号内核 `multi-account-node-support`（已 propose、未实装）落地后 `currentAccountId` 才按连接变真。
- 面板 API 层（`../aidcp-cloud/src/panel/`）是 JWT 闸的只读 BFF，`PgPanelStore` 直查 PG、缺表回落 `[]`；console（`../aidcp-console`，React+Vite+AntD+TanStack Query）已带 `echarts`/`echarts-for-react` 依赖但**从未使用**。

结论：只要在出口处**把已经丢掉的 `usage` 捡回来**、按四维落一张预聚合表、面板暴露只读查询、console 加一页表格 + 曲线即可。token 捕获完全在云端内部，**不碰协议、不碰 edge**。

## What Changes

- **cloud 捕获（`qwen.ts`）**：`ChatCompletionResponse` 补 `usage?`；解析后把 `usage` 存进一个 finally 可见的变量；`LlmCallOpts` 补 `accountId?`；`onCall` 回报扩到 `{accountId?, promptTokens, completionTokens, totalTokens}`。**红线**：token 量按响应体 `usage` 如实记，**与调用是否判失败解耦**——「拿到内容前抛错」的失败路径里 DashScope 已计费的 prompt token 仍要如实记（绝不因 `ok=false` 清零真实已计费 token）；真没拿到 `usage` 才记 0。
- **cloud 记账（新 `TokenUsageStore`）**：出口钩子只做**纯内存累加**（同步、被 try/catch 包住，绝不把记账的慢 / 失败 / 异常带进 LLM 调用路径）；**定时 flush** 到 PG 预聚合表。flush 失败 = 丢弃并计数，**不重试累加**（避免加法 upsert 二次累加）。专用小连接池，与热路径池隔离。
- **cloud 存储（迁移 0013）**：`llm_token_usage` 表，主键 `(bucket_start, account_id, role, model)`，列 prompt/completion/total tokens + calls + ok_calls（全 `BIGINT NOT NULL DEFAULT 0`）。`bucket_start` = 调用时刻 floor 到 10 分钟 UTC 边界，写入用 `to_timestamp($1::bigint/1000.0)` 绑定。写入走 `ON CONFLICT DO UPDATE SET col = 表.col + EXCLUDED.col` 累加。
- **cloud 面板 API**：一个 JWT 闸只读 `GET /api/llm-usage?from&to&accountId?&role?&model?`，一次返回 `{rows, buckets}`——`rows` 按「北京日期 / 账号 / 角色 / 模型」聚合（表格），`buckets` 按 10 分钟桶聚合（曲线）。服务端默认时间窗（曲线 24h）+ 硬上限（≤31 天）防全表扫。
- **console 展示（新 `/usage` 页）**：AntD 表格（四维 + 输入/输出/总 token + 调用次数，**总 token 为主**）+ echarts **单条总量曲线**（受账号/角色/模型筛选器约束）+ 日期 RangePicker。角色原始 tag（`browse:content_evaluator` 等）**在 console 映射成中文标签**（PG 仍存原 tag 做稳定键）。账号列今天只有 `default`，标注「单租户」。

**口径（用户已确认）**：只统计 token 数量（输入/输出/总），不算费用（¥）；曲线为单条总量线 + 筛选器；账号现在就做、向前兼容（今天单值 `default`，多账号内核落地后自动按真实账号拆分）。

## Capabilities

### New Capabilities
- `llm-token-usage-stats`: 文本 LLM token 用量的诚实捕获 → 10 分钟预聚合落库 → 面板只读查询 → console 表格 + 曲线展示（四维：日期/账号/角色/模型）。

### Modified Capabilities
<!-- 无（面板新增端点与 console 新页归入新 capability；不改既有 spec） -->

## Impact

- **cloud（aidcp-cloud）**：
  - `src/llm/qwen.ts`：`ChatCompletionResponse.usage?`、`LlmCallOpts.accountId?`、`onCall` 回报扩展、finally 捕获 usage。
  - `src/metrics/token-usage-store.ts`（新）：内存累加 + 定时 flush + 预聚合 upsert + 查询；专用池。
  - `migrations/0013_llm_token_usage.sql`（新）+ 表内嵌 DDL（与既有 store 同源、幂等）。
  - `src/server.ts`：构造 `TokenUsageStore`、`await init()`、把 `onCall` 钩子改成「保留 console.log + 受 try/catch 包的 `tokenUsage.add(info)`」；探活调用（`server.ts:744`）打 `role:'system:model_probe'` 标。**APPEND，不动 C 的 model-resolver 块。**
  - `src/panel/panel-server.ts` / `panel-store.ts` / `types.ts`：新增 `GET /api/llm-usage` 路由 + `PgPanelStore.llmUsage(...)` 查询 + DTO。**APPEND 既有块尾。**
- **console（aidcp-console）**：
  - `src/pages/TokenUsagePage.tsx`（新）、`src/App.tsx`（路由）、`src/pages/AppShell.tsx`（导航）、`src/api/queries.ts`（`useLlmUsage`，APPEND）、`src/types/api.ts`（DTO，APPEND）、角色→中文标签映射（`src/types/aidcp-enums.ts` APPEND 或新文件）、`package.json`（`dayjs` 提为直接依赖、首次用 echarts）。
- **不涉及**：edge、协议 v2（`protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / onMessage 白名单全部不碰）、风控状态单写、发布链。
- **并发协调（多流并行）**：迁移号 **0013**（B 占 0012，本流取下一个空号）；共享 chokepoint（`panel-store.ts` / `panel/types.ts` / `server.ts` / console `types/api.ts` / `queries.ts`）**只 APPEND**，不重写他流块；`role-dispatcher.ts` **本流完全不碰**（账号穿线交给 `multi-account-node-support`，见 design D5）。
- **红线 / 保留**：诚实记账（已计费 token 不因失败清零、缺 usage 才记 0、`untagged`/`system:model_probe` 如实标不静默吞）；记账绝不阻塞 / 异常 / 拖垮 LLM 调用路径；不动既有 spec 与既有 keyed 子表。
