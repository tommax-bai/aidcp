> 本设计已过一轮多视角对抗评审（红线/热路径、数据模型/SQL/时区、账号归属/向前兼容、YAGNI/完整性）。下列决策含评审采纳项与被否项的理由。

## 上下文

云端唯一文本 LLM 出口 `QwenClient.chat()`（`../aidcp-cloud/src/llm/qwen.ts:115`）已在 `qwen.ts:120` 解析出**生效模型名**、在 `qwen.ts:157` 的 finally 触发 `onCall({role,model,ms,ok})`，但响应体里的 `usage`（DashScope 兼容模式带 prompt/completion/total tokens）在 `qwen.ts:145` 的类型转换中被丢弃。角色标识在所有真实调用点都在（`browse:<role>` / `publish:<Name>`）。account 现为单租户单值 `'default'`。所以本功能 = 在出口处捡回 `usage` + 落一张四维预聚合表 + 面板只读查询 + console 一页。

## D1：捕获点 = `onCall` 钩子，token 与 `ok` 解耦（红线）

- `ChatCompletionResponse` 补 `usage?: { prompt_tokens?: number; completion_tokens?: number; total_tokens?: number }`。在 `chat()` 里 `let usage` 声明于 `try` 之前，`const data = await res.json()` 后立即 `usage = data.usage`（**早于** `qwen.ts:149` 的「缺 content 抛错」），finally 才能在失败路径也看到它。
- `LlmCallOpts` 补 `accountId?`；`onCall` 回报扩为 `{role?, model, ms, ok, accountId?, promptTokens?, completionTokens?, totalTokens?}`。
- **红线（评审最高优先级修正）**：token 量按响应体如实记，**绝不因 `ok=false` 清零**。真实路径里「DashScope 返回了 usage、但 content 缺失导致判失败」会发生——那 prompt token **已经计费**，记 0 等于把真实成本「静默抹掉」，是 `MUST NOT 静默假成功` 在成本面的违背。所以：有 `usage` 就记真实值（`?? 0` 仅用于字段缺失），`ok` 单独进 `ok_calls` 计数；失败但已计费 = 真实 token + `ok_calls` 不增。只有「真没拿到 usage」（HTTP 错 / 网络错，`data` 未解析）才记 0。
- **零回归**：三个新字段都可选；不传 opts 的调用方行为逐字不变；`onCall` 实现方按结构子类型仍可赋值（参数对象多了可选字段不破坏既有实现）。

## D2：记账路径热隔离 = 内存累加 + 定时 flush（红线，对抗评审采纳）

`onCall` 在 LLM 调用的 finally 同步触发——若在这里做「每调用一次就 await 一次 PG 写」，慢/失败/异常的写会反压、堆积未决 promise、甚至（同步抛错或 `.catch` 未挂上）把异常带回 LLM 调用方、`finally` 抛错还会顶替原返回/原错误。故：

- **出口钩子只做纯内存累加**（同步 Map 更新），且整段被 `try { tokenUsage.add(info) } catch {}` 包住——记账绝不可能阻塞 / 抛进 / 拖垮 LLM 调用路径。保留原 `console.log`（独立守护，互不影响）。
- `TokenUsageStore` 内部按 `(bucket, account, role, model)` 键累加到内存 Map；**定时 flush**（默认 15s，可 env 调）把累计增量 upsert 到 PG，进程退出前再 flush 一次。
- **专用小连接池**（`max` 2~4），与热路径 / 边-云路径池物理隔离（构造支持 `options.pool ?? new Pool(...)`，本流注入专用池）。
- **flush 失败 = 丢弃并计数（warn-once）**，**不重试累加**：加法 upsert 非幂等，重试可能二次累加；宁可在 PG 故障窗口诚实丢一窗并计数，也不二次累加造假。内存 Map 的键被「当窗维度组合」天然有界（一个 flush 窗内 buckets×accounts×roles×models 只有个位数键），无无界堆积。
- **启动顺序**：`await tokenUsage.init()`（建表 + 起定时器）必须早于开始接边缘连接 / 早于任何探活，否则首批真实用量落空（诚实缺口）。本流把 init 接在既有 store-init 序列里。

## D3：存储 = 10 分钟预聚合 rollup（对抗评审定 schema 硬修正）

迁移 `0013_llm_token_usage.sql`（B 占 0012，本流取 0013）：

```sql
CREATE TABLE IF NOT EXISTS llm_token_usage (
  bucket_start      TIMESTAMPTZ NOT NULL,   -- 10 分钟 UTC 桶起点
  account_id        TEXT        NOT NULL,   -- 'default' 单租户；多账号上线后真实账号
  role              TEXT        NOT NULL,   -- 'browse:<role>' / 'publish:<Name>' / 'untagged' / 'system:model_probe'
  model             TEXT        NOT NULL,   -- 生效模型名（按角色解析后的实际值）
  prompt_tokens     BIGINT      NOT NULL DEFAULT 0,
  completion_tokens BIGINT      NOT NULL DEFAULT 0,
  total_tokens      BIGINT      NOT NULL DEFAULT 0,
  calls             BIGINT      NOT NULL DEFAULT 0,   -- 该桶该维度调用总次数（含失败）
  ok_calls          BIGINT      NOT NULL DEFAULT 0,   -- 其中成功次数（失败 = calls - ok_calls）
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (bucket_start, account_id, role, model)
);
CREATE INDEX IF NOT EXISTS idx_llm_token_usage_account_bucket
  ON llm_token_usage (account_id, bucket_start);
```

upsert（flush 时，每个内存键一行）：

```sql
INSERT INTO llm_token_usage
  (bucket_start, account_id, role, model, prompt_tokens, completion_tokens, total_tokens, calls, ok_calls)
VALUES (to_timestamp($1::bigint / 1000.0), $2, $3, $4, $5, $6, $7, $8, $9)
ON CONFLICT (bucket_start, account_id, role, model) DO UPDATE SET
  prompt_tokens     = llm_token_usage.prompt_tokens     + EXCLUDED.prompt_tokens,
  completion_tokens = llm_token_usage.completion_tokens + EXCLUDED.completion_tokens,
  total_tokens      = llm_token_usage.total_tokens      + EXCLUDED.total_tokens,
  calls             = llm_token_usage.calls             + EXCLUDED.calls,
  ok_calls          = llm_token_usage.ok_calls          + EXCLUDED.ok_calls,
  updated_at        = now();
```

评审硬修正全部采纳：
- **必须是 `PRIMARY KEY`（真唯一约束）不是普通索引**——否则 `ON CONFLICT (...)` 第二次进同一桶即运行期报错（无匹配唯一约束）。
- **绑定 `to_timestamp($1::bigint/1000.0)`**（Node 端 epoch ms → timestamptz），用真实表名 `llm_token_usage.col`（`table` 是保留字，不能用 `table.col`）。
- **计数列 `NOT NULL DEFAULT 0` + 捕获端 `?? 0`**——可空 + 加法 = `NULL+n=NULL` 静默清零累加器，双保险堵死。
- **`calls`/`ok_calls` 用 `BIGINT`**；查询 `SUM(...)::bigint`，DTO 读出按字符串感知解析（node-pg 把 bigint/numeric 当字符串返回，DTO `Number()` 解析，token 量在 2^53 内安全，文档标天花板）。
- `bucket_start` = `Math.floor(Date.now()/600000)*600000`：epoch ms 是单调 UTC，无 DST 不连续，floor 即对齐 10 分钟 UTC 桶；**在 Node 算桶规避 PG `date_bin`（14+）版本依赖**（ECS PG 版本未知）。
- **保留权衡（YAGNI）**：预聚合锁死 10 分钟粒度（用户就要 10 分钟），换来行数有界、查询简单、无 `date_bin`。代价是**永久失去逐调用下钻**（无 request id / 无逐调用 latency）——评审确认本需求不要，接受。
- **增长 / 留存**：单租户今天极小；多账号上线后上限 ≈ 144桶×账号×角色×模型/天。提供 `purgeOlderThan(days)` 方法 + 文档留存口径（如 180 天），本流不强接调度（YAGNI，单租户暂不需要），多账号上线时再接。

## D4：面板 API = 单端点返双形（YAGNI 评审采纳「合并两端点」）

`GET /api/llm-usage?from&to&accountId?&role?&model?`（JWT 闸，`PgPanelStore.llmUsage(...)`，缺表回落空）一次返回：

```jsonc
{
  "rows":    [{ "day":"2026-06-24", "accountId":"default", "role":"browse:content_evaluator",
                "model":"qwen-plus", "promptTokens":1234, "completionTokens":567,
                "totalTokens":1801, "calls":12, "okCalls":12 }],   // 表格：按北京日期/账号/角色/模型
  "buckets": [{ "bucketMs":1782290400000, "promptTokens":..., "completionTokens":...,
                "totalTokens":..., "calls":... }],                  // 曲线：按 10 分钟桶（受同一筛选约束）
  "window":  { "fromMs":..., "toMs":..., "clampedTo":31 }
}
```

- 表格日期列 = `(bucket_start AT TIME ZONE 'Asia/Shanghai')::date`。评审确认：中国 1991 起无 DST、全国单一 +08（10 分钟的整数倍偏移），**每个 UTC 10 分钟桶整落在同一北京日内**（北京零点 = 16:00 UTC 本身是 10 分钟边界），故「表格按北京日 SUM」与「曲线桶之和」**逐位一致、无午夜跨界**。（若将来服务非整点偏移时区如 +5:30 则此性质不再成立，文档标为约束。）
- 曲线 `bucketMs` 返回 epoch ms（UTC 瞬时）；**console 显式按 `Asia/Shanghai` 渲染**，不靠浏览器本地时区（防开发者异地 VPN 看到偏移曲线）。
- **服务端默认窗 + 硬上限**（评审「最可能的生产事故」）：缺 `from/to` 默认 `to=now, from=now-24h`（曲线 144 桶）；`to-from` 超 31 天则 clamp（`window.clampedTo`），绝不让 `from=0` 全表扫 + 巨量点打爆 PG/echarts。
- **合并两端点为一**（原设计两端点被 YAGNI 评审否）：表格与曲线同 WHERE、同 store、同筛选，仅 GROUP BY 粒度不同；一端点返 `{rows,buckets}` → 一次 fetch、一套 loading/empty、表与图天然一致。
- 索引：PK 前导列 `bucket_start` 已服务区间扫 + 按日/账号/角色/模型分组；删冗余的单列 `(bucket_start DESC)` 索引（PK 覆盖）；保留 `(account_id, bucket_start)` 服务账号锁定的曲线。

## D5：账号维度 = 只铺缝、不在本流穿线（账号评审采纳，反转初稿）

初稿想在 `RoleDispatcher` 包一层 llm wrapper 实时读 `this.currentAccountId` 盖到 `opts.accountId`。**对抗评审否决，本流改为只铺缝**：

- 今天 wrapper 只会盖 `'default'`（单租户），与「recorder 缺省即 `'default'`」**输出逐位相同 → 今天零收益**。
- 多账号上线后，`currentAccountId` 是**单个共享可变标量**，事件驱动模型下 `role.decide` 可能从 EventBus handler 异步触发、LLM 调用又是网络往返——wrapper 实时读这个共享字段会**跨账号竞态串号**（把 A 的 token 记到 B），是红线在归属面的违背。
- 发布侧 `roleLlm('publish:<Name>')` 由飞书手动 `/publish` 触发，**真实目标账号来自发布请求、不是 `currentAccountId`**；wrapper 在这里会「自信地盖一个真实但错误的账号」。
- `multi-account-node-support`（已 propose）**本就要改 `role-dispatcher.ts` 且拥有 `currentAccountId` 语义**——账号穿线应由它在「建立每连接上下文、拿到并发安全的真账号」处落，否则两流同改一文件 + 双盖 `opts.accountId` 顺序定真值 = 合并意外。
- **本流落地**：① `LlmCallOpts.accountId?` + `onCall.accountId?`（缝）；② recorder 缺省 `account → 'default'`、`role → 'untagged'`；③ **完全不碰 `role-dispatcher.ts`**；④ spec 显式写「账号归属现为 `default`-only，发布侧账号不取自 `currentAccountId`，待多账号流穿线」。account 维度在 schema/API/UI 全建好，只是今天单值——console 把 `default` 标注为「默认账号（单租户）」、附 tooltip「多账号上线后按真实账号拆分」，诚实不误导。

## D6：诚实标签 + 探活（红线小项）

- `role` 缺省 `'untagged'` 是保留值（三条 v1/工具路径无 tag：PostProcessor `server.ts:289`、v1 SimplePlanner、v1 selector；CLAUDE.md 禁改 v1 遗留路径，故它们如实落 `untagged`）。recorder 记到 `untagged` 时 **warn-once**，将来真角色丢 tag 的回归可见、不被吸收。
- 探活调用（`server.ts:744` 保存模型前的活性 ping）打 `role:'system:model_probe'` 标——真实但运营噪声的 token，**如实记、可区分、不静默丢**；console 默认不隐藏（隐藏=不诚实）、可被筛选器单列。
- `calls` 语义 = 每次 `chat()` 调用（`QwenClient` 内**无重试**，一次 fetch、finally 一次 `onCall`，故 calls = 逻辑 = 物理，无重试歧义）。

## D7：console（YAGNI 评审采纳：补可读性、砍多线）

- 新页 `/usage`，导航「用量」。日期 RangePicker（`dayjs` 提为直接依赖）+ 账号/角色/模型筛选器。
- AntD 表格：日期 / 账号 / 角色 / 模型 / 输入 token / 输出 token / **总 token（主，醒目）** / 调用次数。空区间显式「暂无数据」空态（非空白画布）。
- echarts **单条总量曲线**（首次用 echarts；受当前筛选器约束，选某角色即得该角色曲线）——评审砍掉 `by=` 多线 split 与多端点。
- **角色→中文标签映射**（评审唯一「必须补」的完整性项）：PG 存原始 tag 做稳定键，console 渲染映射成中文（`browse:content_evaluator`→「内容评估」、`publish:TitleCreator`→「标题创作」、`system:model_probe`→「模型探活」、`untagged`→「未标注/遗留」…）；未知 tag 回落「去前缀人性化」不露丑串。模型名直接显示（运营本就在模型配置页设的，认得）。

## D8：被否决的方案（留痕）

- **逐调用 raw insert + 查询期 GROUP BY**：写路径更简（无 upsert/无 Node 算桶），且支持任意粒度。**否**：行数随调用无界增长（浏览闭环每分钟多调用），本需求恰好只要 10 分钟粒度，预聚合换来行数有界 + 查询简单。允许实现者若更偏好可换 raw（但本流落预聚合）。
- **算费用（¥）**：用户确认只要 token 量；仓内无任何模型单价表，估费要新建价目表 + 按模型乘。**否（YAGNI）**，留干净扩展缝（将来加 `model→price` 表 + 派生列即可）。
- **纳入文生图（万相）调用**：图片生成无 token 概念。**否**，本表只记文本 LLM token；将来要图片只能另计「调用次数 / 张数」，不混入 token 表。
- **account-stamping wrapper（初稿 D5）**：见 D5，账号评审否决。
