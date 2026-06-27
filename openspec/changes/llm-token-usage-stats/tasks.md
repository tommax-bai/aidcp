> **并发协调（多流并行，本流 = llm-token-usage-stats）**
> - **迁移号 0013**：B(account-real-nickname)=0012，本流取下一个空号 **0013**。勿占他号。
> - **共享 chokepoint 只 APPEND**：`../aidcp-cloud/src/panel/panel-store.ts`、`../aidcp-cloud/src/panel/types.ts`、`../aidcp-cloud/src/server.ts`、`../aidcp-console/src/types/api.ts`、`../aidcp-console/src/api/queries.ts`、`../aidcp-console/src/pages/AppShell.tsx`、`../aidcp-console/src/App.tsx` 只在既有块尾追加，不重写他流块；`server.ts` 的 model-resolver 块归 C，本流不碰，store-init 只 APPEND。
> - **本流完全不碰** `role-dispatcher.ts`（账号穿线交 `multi-account-node-support`，见 design D5）、协议四处（`protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / onMessage 白名单）、edge。
> - 同机多会话部署错峰（见 [[deploy-verify-content-after-rsync]]）。**实测确认**：实装期间 cloud 有并发会话 WIP（back-to-feed / role-dispatcher / prompt-viewer），均用精确 per-path staging 隔离，本流 commit 仅含自有文件。

## 1. aidcp-cloud — 出口捕获 token（红线：token 与 ok 解耦）

- [x] 1.1 `src/llm/qwen.ts`：`ChatCompletionResponse` 加 `usage?` <!-- aidcp-cloud c78b894 -->
- [x] 1.2 `src/llm/qwen.ts`：`LlmCallOpts` 加 `accountId?`；`onCall` 回报扩为 `{...accountId?, promptTokens?, completionTokens?, totalTokens?}` <!-- aidcp-cloud c78b894 -->
- [x] 1.3 `chat()`：`let usage` 声明于 try 前；`const data` 后立即 `usage = data.usage`（早于缺-content 抛错）；finally 带 accountId + 三 token 字段 <!-- aidcp-cloud c78b894 -->
- [x] 1.4 回归保证：不传新选项行为逐字不变（test/qwen-token-usage.test.ts「零回归」用例覆盖） <!-- aidcp-cloud c78b894 -->

## 2. aidcp-cloud — TokenUsageStore（内存累加 + 定时 flush + 预聚合 + 查询）

- [x] 2.1 `migrations/0013_llm_token_usage.sql`：PK 四维 + BIGINT NOT NULL DEFAULT 0 + `(account_id,bucket_start)` 索引，幂等 <!-- aidcp-cloud c78b894 -->
- [x] 2.2 `src/metrics/token-usage-store.ts`：`add(info)` 纯内存 Map 累加（account `?? 'default'`、role `?? 'untagged'`、token `?? 0`、ok 进 okCalls）；untagged warn-once <!-- aidcp-cloud c78b894 -->
- [x] 2.3 `init()` 建表 + 起定时 flush（`AIDCP_TOKEN_FLUSH_MS` 默认 15000）；专用池（小 max=4） <!-- aidcp-cloud c78b894 -->
- [x] 2.4 `flush()` 排空快照 → 逐键 upsert（`to_timestamp($1::bigint/1000.0)`，真实表名）；失败丢弃 + 计数 warn，绝不重试累加；`close()` 停定时器 + 末次 flush <!-- aidcp-cloud c78b894 -->
- [x] 2.5 `usage({fromMs,toMs,accountId?,role?,model?})` 返 `{rows,buckets,window}`（rows 按北京日四维、buckets 按 10 分钟桶；`SUM(...)::bigint` + 数值解析；默认窗 24h、超 31 天 clamp）；缺表回落空 <!-- aidcp-cloud c78b894 -->
- [x] 2.6 `purgeOlderThan(days)` 方法（留存口径，本流不接调度） <!-- aidcp-cloud c78b894 -->

## 3. aidcp-cloud — 接线（server.ts，APPEND）

- [x] 3.1 构造 `TokenUsageStore`、`await init()`（接在既有 store-init 之后、早于接边缘连接/探活） <!-- aidcp-cloud c78b894 -->
- [x] 3.2 `onCall` 钩子改为「保留 console.log(加 tokens) + `try { tokenUsage.add(info) } catch {}`」；不动 C 的 resolver 块 <!-- aidcp-cloud c78b894 -->
- [x] 3.3 探活调用传 `role: 'system:model_probe'` <!-- aidcp-cloud c78b894 -->
- [x] 3.4 退出前 flush：`SIGTERM/SIGINT` once 钩子调 `close()`（有界 3s 防挂住退出） <!-- aidcp-cloud c78b894 -->

## 4. aidcp-cloud — 面板 API（panel，APPEND）

- [x] 4.1 `src/panel/types.ts`：`PanelDeps.tokenUsage?`（结构类型，注入 TokenUsageStore；DTO 复用 store 导出的 `LlmUsageQuery`/`LlmUsagePayload`） <!-- aidcp-cloud c78b894 -->
- [x] 4.2 实现走 TokenUsageStore.usage（同一实例共享专用池），不另起 panel-store 查询 <!-- aidcp-cloud c78b894：design D4「委托 TokenUsageStore.usage」分支 -->
- [x] 4.3 `src/panel/panel-server.ts`：JWT 闸后加 `GET /api/llm-usage` 路由，解析 from/to/accountId/role/model → `deps.tokenUsage.usage(...)`；未注入 503 <!-- aidcp-cloud c78b894 -->
- [x] 4.4 server.ts panel deps 注入 `tokenUsage: tokenUsageStore`（与记账同一实例） <!-- aidcp-cloud c78b894 -->

## 5. aidcp-console — 用量页（表格 + 单线曲线）

- [x] 5.1 `package.json`：`dayjs` 提为直接依赖；echarts/echarts-for-react 首次用 <!-- aidcp-console 92a81bc -->
- [x] 5.2 `src/types/api.ts`：`LlmUsageRow`/`LlmUsageBucket`/`LlmUsagePayload`（与 cloud 逐字对齐，APPEND） <!-- aidcp-console 92a81bc -->
- [x] 5.3 `src/types/usageLabels.ts`（新）：角色 tag→中文标签映射 + 未知去前缀回落；`accountLabel`（default→「默认账号（单租户）」） <!-- aidcp-console 92a81bc -->
- [x] 5.4 `src/api/queries.ts`：`useLlmUsage({...})`（apiGet 带 query，APPEND） <!-- aidcp-console 92a81bc -->
- [x] 5.5 `src/pages/TokenUsagePage.tsx`（新）：RangePicker（默认近 24h）+ 账号/角色/模型筛选；echarts 单线总量曲线（x 轴显式 Asia/Shanghai 渲染）；AntD 表格（总 token 主，失败次数诚实显示）；空态；账号单租户标注 <!-- aidcp-console 92a81bc -->
- [x] 5.6 `src/App.tsx` 加 `/usage` 路由；`AppShell.tsx` BUSINESS 加「用量」入口（FundOutlined，APPEND） <!-- aidcp-console 92a81bc -->

## 6. 验证（红线 + 回归）

- [x] 6.1 cloud `npm run typecheck` 绿；console `npm run typecheck` + 生产 `npm run build` 绿（echarts 打包通过） <!-- c78b894 / 92a81bc -->
- [x] 6.2 cloud 新增覆盖：成功记真实 token、**已计费但失败不清零**、真缺 usage 记 0、untagged/probe 缺省、flush 失败不抛进调用路径不二次累加、同/异维度聚合（test/qwen-token-usage.test.ts + test/token-usage-store.test.ts，9 用例全绿）；全量 `npm test` **640/640**（连跑 3 次稳定） <!-- aidcp-cloud c78b894 -->
- [x] 6.3 cloud `npm run test:acceptance` **26/26**（AC-PROTO/PUB/RISK 不受影响——本流不碰协议/发布/风控） <!-- aidcp-cloud c78b894 -->
- [~] 6.4 console `/usage`：接线已验（ECS nginx 8088=200、新包 index-CxyWaiW9.js、`/api/llm-usage` 未带 JWT=401 证明路由+代理+JWT 闸+tokenUsage 注入全通）；登录后视觉目检 + 出数待真机浏览流量 <!-- 接线已验, 视觉/数据待 7.5 -->

## 7. 收尾与部署

- [x] 7.1 按 sub-repo 分节回写本 tasks.md 进度（cloud c78b894 / console 92a81bc） <!-- aidcp main 待提交 -->
- [x] 7.2 `openspec validate llm-token-usage-stats --strict` 通过（验证后提交本仓） <!-- aidcp main：2026-06-27 strict "Change is valid" -->
- [x] 7.3 cloud 按 §5 安全序列部署 ECS <!-- 2026-06-24 deployed。备份 cloud.bak.20260624-202639.tar.gz(572K,code) + .env.bak.20260624；dry-run surface scope=60 文件(c7abc67→7f59fbb 连带 safety-quota 0010+quota-config-store/risk* / return-to-feed back-to-feed/role-dispatcher / prompt-viewer persona / 本流 token-usage)；rsync(no --delete, exclude .env/node_modules/.git)；显式跑 0010+0013 迁移(status ok)；restart；healthcheck 全绿：active+8787 LISTENING+「token 用量记账已就绪（llm_token_usage）」+「安全限额存储已就绪」+面板8090+飞书长连接已建立；内容校验非仅信回执(grep server.ts tokenUsage=5/qwen usage capture=1/metrics dir 在 ECS)；psql \d llm_token_usage 确认 10 列+PK(bucket_start,account_id,role,model)+idx_account_bucket+全 BIGINT NOT NULL DEFAULT 0；PG select 1；quota_config 建表(空=回落默认)。isales :80=200 未碰。[[deploy-verify-content-after-rsync]] -->
- [x] 7.4 console dist 构建 + rsync → `/opt/aidcp/console` <!-- 2026-06-24 deployed。fresh build→index-CxyWaiW9.js；rsync --delete(删旧 index-m0WYD_WH.js)；nginx 8088=200 serve 新包；/api/llm-usage 未带 JWT=401 unauthorized 证明路由+代理+JWT闸+tokenUsage 注入全通(非 404/503)。console master 92a81bc(含并发会话 RolesPage 等连带) -->
- [ ] 7.5 真机验证：跑一段浏览闭环 → PG `llm_token_usage` 有真实行 → 登录 `/usage` 表格 + 曲线出数；探活记 `system:model_probe`（需边缘连上 + 浏览/调模型产生流量）
- [ ] 7.6 `/opsx:archive` 归档（待 7.5 真机出数后；delta 合并进新 capability `openspec/specs/llm-token-usage-stats`）
