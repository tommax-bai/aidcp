# llm-token-usage-stats Specification

## Purpose
TBD - created by archiving change llm-token-usage-stats. Update Purpose after archive.
## Requirements
### Requirement: 文本 LLM token 用量在出口处诚实捕获

系统 SHALL 在云端唯一文本 LLM 出口（`QwenClient.chat()`）处，把 DashScope 兼容模式响应体里的 `usage`（prompt / completion / total tokens）如实捕获，并连同**生效模型名**、**角色标识**、**账号标识**、**成功与否**交给记账。

- **token 与 `ok` 解耦（红线）**：token 量 SHALL 取自响应体 `usage`，**MUST NOT 因调用被判失败（`ok=false`）而清零真实已计费 token**。当响应体已带 `usage` 但后续因缺 content 等判失败时，系统 SHALL 记下真实 token 且把该次计为「失败调用」（不计入成功数）。仅当响应体确实没有 `usage`（HTTP 错 / 网络错 / 未解析）时 SHALL 记 0。
- **不伪造**：缺字段 SHALL 以 0 充数（`prompt/completion/total` 各自 `?? 0`），MUST NOT 由 `prompt+completion` 反推 `total`、MUST NOT 由 `total` 反拆 `prompt/completion`。
- **角色 / 账号缺省为保留值**：无角色 tag 的调用 SHALL 记 `role='untagged'`；无账号的调用 SHALL 记 `account='default'`。两者为**保留诚实标签**，MUST NOT 静默丢弃该次用量。
- **零回归**：新增的可选字段（响应体 `usage?`、调用选项 `accountId?`、回报 token 字段）MUST NOT 改变任何既有调用方在不传新选项时的行为。

#### Scenario: 成功调用如实记录 token

- **WHEN** 一次 `chat()` 成功返回且响应体带 `usage`
- **THEN** 系统按 `usage` 记下 prompt / completion / total token，模型为按角色解析后的生效模型名，该次计入 `calls` 与 `ok_calls`

#### Scenario: 已计费但判失败不清零（红线）

- **WHEN** DashScope 已返回 `usage`（prompt token 已计费）但因 content 缺失等被判失败
- **THEN** 系统 SHALL 记下响应体里的真实 token，`calls` +1 而 `ok_calls` 不增；MUST NOT 把该次 token 记为 0

#### Scenario: 真没拿到 usage 才记 0

- **WHEN** 调用因 HTTP 非 2xx / 网络错 / 响应未解析而失败、响应体无 `usage`
- **THEN** 系统记该次 token 为 0、`ok_calls` 不增，MUST NOT 伪造任何 token 值

#### Scenario: 探活调用如实可区分

- **WHEN** 保存模型配置前触发一次活性 ping 调用
- **THEN** 该次以 `role='system:model_probe'` 如实记录（真实 token、可被筛选区分），MUST NOT 静默丢弃、MUST NOT 混入 `untagged`

### Requirement: 记账绝不阻塞、抛进或拖垮 LLM 调用路径

系统记 token 用量 MUST NOT 阻塞、延迟、抛异常进入、或以反压拖垮 LLM 调用路径。

- LLM 出口钩子 SHALL 只做纯内存累加且被 try/catch 包住；记账的任何慢 / 失败 / 同步异常 MUST NOT 传播回 LLM 调用方，MUST NOT 顶替 LLM 调用的原返回或原错误。
- 持久化 SHALL 走**定时 flush**（与每次调用解耦），用与热路径隔离的专用连接池；进程退出前 SHALL 再 flush 一次。
- flush 失败 SHALL 丢弃当窗增量并计数（warn-once），**MUST NOT 重试累加**（加法 upsert 非幂等，重试会二次累加造假）。
- 记账存储就绪（建表 + 起定时器）SHALL 早于开始接受 LLM 调用 / 探活，避免首批真实用量落空。

#### Scenario: PG 写慢 / 失败不影响 LLM 调用

- **WHEN** 记账的 PG 写变慢或失败
- **THEN** 当次及后续 LLM 调用照常返回（不阻塞、不抛错、不崩进程）；失败的 flush 被计数告警，对应增量被丢弃而非二次累加

#### Scenario: 进程退出前 flush

- **WHEN** 云端进程正常退出
- **THEN** 系统在退出前把内存累计增量 flush 一次，尽量不丢已统计窗口

### Requirement: token 用量按 10 分钟桶 × 四维预聚合落库

系统 SHALL 把 token 用量按 `(10 分钟桶起点, 账号, 角色, 模型)` 预聚合到一张表，主键即该四维组合。

- `bucket_start` SHALL = 调用时刻 floor 到 10 分钟 UTC 边界（`floor(epochMs/600000)*600000`），写入以 `to_timestamp($1::bigint/1000.0)` 绑定为 `timestamptz`。
- 表 SHALL 以 `PRIMARY KEY (bucket_start, account_id, role, model)`（真唯一约束）支撑 `ON CONFLICT` 累加；计数列（prompt/completion/total tokens、calls、ok_calls）SHALL 为 `BIGINT NOT NULL DEFAULT 0`。
- 写入 SHALL 走 `INSERT ... ON CONFLICT (...) DO UPDATE SET 列 = 表.列 + EXCLUDED.列` 累加（含 calls、ok_calls）。
- 迁移号 SHALL 为 `0013`（与已锁定的 0012 及更早号不冲突），表 DDL SHALL 幂等（`CREATE TABLE IF NOT EXISTS`）并与 store 内嵌 DDL 同源。

#### Scenario: 同桶同维度多次调用累加为一行

- **WHEN** 10 分钟内对同一 `(账号, 角色, 模型)` 发生多次 LLM 调用
- **THEN** 它们累加进同一行（token 与 calls 相加），而非多行

#### Scenario: 缺唯一约束即拒绝（约束正确性）

- **WHEN** 表创建
- **THEN** 四维组合 SHALL 是 PRIMARY KEY/UNIQUE 约束，使 `ON CONFLICT (bucket_start,account_id,role,model)` 在第二次进同桶时正确累加而非运行期报错

### Requirement: 面板暴露 token 用量只读查询（JWT 闸、单端点返表与曲线）

面板 API SHALL 提供一个 JWT 鉴权的只读端点 `GET /api/llm-usage`，一次返回表格行与 10 分钟曲线桶。

- 查询 SHALL 支持 `from` / `to`（epoch ms）及可选 `accountId` / `role` / `model` 过滤。
- 返回 `rows` SHALL 按 `(北京日期, 账号, 角色, 模型)` 聚合（北京日期 = `(bucket_start AT TIME ZONE 'Asia/Shanghai')::date`）；`buckets` SHALL 按 10 分钟桶聚合（`bucketMs` 为 UTC epoch ms），二者受同一筛选约束。
- 系统 SHALL 设服务端默认窗（缺省 `to=now`、`from=now-24h`）与硬上限（`to-from` 超 31 天则 clamp 并回报），防全表扫。
- 表缺失（迁移未应用）SHALL 回落空结果（`rows:[]`,`buckets:[]`），MUST NOT 500。
- 该端点 SHALL 沿用面板既有 JWT 鉴权，MUST NOT 另开免鉴权入口。

#### Scenario: 取某时间窗的表与曲线

- **WHEN** 已鉴权请求 `GET /api/llm-usage?from=..&to=..`
- **THEN** 返回该窗内按四维聚合的 `rows` 与按 10 分钟聚合的 `buckets`，token 量为 BIGINT 求和后按数值返回

#### Scenario: 缺省窗与超限 clamp

- **WHEN** 请求不带 `from/to`，或区间超过 31 天
- **THEN** 缺省回落近 24 小时；超限区间被 clamp 到上限并在响应里回报，绝不全表扫

#### Scenario: 未带 JWT 被拒

- **WHEN** 未带有效 JWT 请求 `GET /api/llm-usage`
- **THEN** 返回 401，MUST NOT 返回任何用量数据

#### Scenario: 表未建时回落空

- **WHEN** 迁移 0013 尚未应用
- **THEN** 端点返回空 `rows`/`buckets`（非错误）

### Requirement: console 提供 token 用量表格 + 10 分钟曲线页

管理后台 SHALL 新增「用量」页（路由 `/usage`），展示 token 消耗的四维表格与每 10 分钟曲线。

- 表格 SHALL 含列：日期、账号、角色、模型、输入 token、输出 token、**总 token（醒目主列）**、调用次数；空区间 SHALL 显式空态提示（非空白）。
- 曲线 SHALL 为单条总量线（每 10 分钟一点），受页面筛选器（账号 / 角色 / 模型）约束，时间轴 SHALL 显式按 `Asia/Shanghai` 渲染（不依赖浏览器本地时区）。
- 页面 SHALL 提供日期范围选择与账号/角色/模型筛选。
- 角色列 SHALL 把原始内部 tag（如 `browse:content_evaluator` / `publish:TitleCreator` / `system:model_probe` / `untagged`）映射为人类可读中文标签展示（PG 仍存原 tag 做稳定键）；未知 tag SHALL 回落去前缀的可读形，MUST NOT 直露内部 tag 串。
- 账号维度今天为单值 `default`：console SHALL 显式标注其为单租户（如「默认账号（单租户）」+ 提示「多账号上线后按真实账号拆分」），MUST NOT 让运营误判统计损坏。

#### Scenario: 查看用量表与曲线

- **WHEN** 运营打开 `/usage`
- **THEN** 默认展示近 24 小时的总量曲线（每 10 分钟）与按四维聚合的表格，总 token 列醒目

#### Scenario: 角色显示中文标签

- **WHEN** 表格渲染某行角色为 `browse:content_evaluator`
- **THEN** 显示「内容评估」式中文标签，而非原始 `browse:content_evaluator` 串

#### Scenario: 筛选驱动曲线

- **WHEN** 运营在筛选器选定某角色
- **THEN** 曲线变为该角色的总量线，表格相应收窄

#### Scenario: 空区间显式空态

- **WHEN** 所选区间无任何用量
- **THEN** 表格与图各显示「暂无数据」，而非空白或报错

