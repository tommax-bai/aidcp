# console-panel-api Specification

## Purpose
TBD - created by archiving change aidcp-console-panel-mvp. Update Purpose after archive.
## Requirements
### Requirement: 面板 API 层进程内挂载、独立端口、无 Web 框架、启动自检

云端进程 SHALL 在现有 `http.Server`（为边-云 ws 升级而建）之上挂载一个进程内面板 API 层（`src/panel/`），用一个极小路由暴露管理后台所需的 HTTP 接口，**MUST NOT** 引入 Web 框架依赖。面板层 SHALL 绑定独立的、由环境变量驱动的端口 `AIDCP_PANEL_PORT`（默认占位 `8090`，最终值由 ECS live 盘点确定）。启动时 SHALL 跑一个自检：记录解析出的端口，并 MUST 拒绝绑定 `8787`（边-云 ws）/ `5432`（PostgreSQL）/ `8788`（调试桩）/ 已知 isales 端口。面板层 SHALL 由注入构造，复用 `main()` 已接好的单例（风控注册表 / 发布记录存储 / 概念存储 / 飞书绑定存储 / 事件总线 / 边-云服务 / 账号存储），MUST NOT 触碰两份 `protocol.ts` 或 `command-bridge`。

#### Scenario: 独立端口挂载、不碰协议
- **WHEN** 云端进程启动且 `AIDCP_PANEL_PORT` 已配置且空闲
- **THEN** 面板 API 层在该端口监听，复用现有 `http.Server`，边-云 `:8787` 与协议映射不受任何改动

#### Scenario: 自检拒绝绑定保留端口
- **WHEN** `AIDCP_PANEL_PORT` 被配置为 `8787` / `5432` / `8788` / 已知 isales 端口
- **THEN** 启动自检拒绝绑定该端口并记录明确错误，不与现役服务抢端口

### Requirement: 面板 listen 失败非致命，绝不崩塌关键闭环

面板层 `listen()` SHALL 包裹在错误捕获中：当端口占用（`EADDRINUSE`）或任何面板初始化错误发生时，系统 MUST 记录明显日志并**继续运行** `8787` 边缘浏览闭环与飞书核心长连接，MUST NOT 让 `main()` 崩溃。面板不可用 MUST 表现为「后台用不了」，绝不连累边缘闭环或飞书。

#### Scenario: 端口占用不连累边缘闭环
- **WHEN** 面板 `listen()` 因端口被占用而失败
- **THEN** 进程记录面板启动失败日志，但 `8787` 边缘闭环与飞书长连接照常运行，进程不退出

### Requirement: JWT 鉴权守护所有面板接口

面板层 SHALL 用 JWT 守护所有 `/api/*` 接口（登录端点除外）。`POST /api/auth/login` SHALL 对 `.env` 内置用户列表校验并签发短 TTL 签名 JWT，密钥 MUST 来自 `.env`、MUST NOT 硬编码或写入仓库。除登录外的每个 `/api/*` 请求 MUST 经校验中间件，token 缺失或过期 SHALL 返回 401。

JWT payload MUST 含唯一标识 `jti`，使已签出令牌**可被服务端撤销**：面板层 SHALL 维护一个撤销黑名单（内存 + 可选 PG 持久化跨重启），`verifyJwt` MUST 拒绝黑名单中的 `jti`；黑名单条目 SHALL 按令牌 `exp` 自然过期后清理（表恒小）。面板层 SHALL 暴露 `POST /api/auth/refresh`（持未过期令牌者换发一枚新令牌，滑动续签，使活跃用户不因定长 TTL 被踢）与 `POST /api/auth/logout`（拉黑当前 `jti`，使退出登录对服务端可见）。滑动续签使 TTL 可保持短以缩短泄露窗口而不牺牲活跃体验。

#### Scenario: 未携带有效 token 被拒
- **WHEN** 一个 `/api/*`（非登录）请求未带或带了过期 JWT
- **THEN** 面板层返回 401，不执行任何读或写

#### Scenario: 登录签发短 TTL token
- **WHEN** 凭 `.env` 内置用户的正确凭据请求 `POST /api/auth/login`
- **THEN** 面板层返回一个短 TTL 签名 JWT（payload 含 `jti`），后续 `/api/*` 凭它通过校验

#### Scenario: 活跃用户滑动续签不被踢
- **WHEN** 持有未过期令牌者请求 `POST /api/auth/refresh`
- **THEN** 面板层换发一枚 `exp` 推进的新令牌，旧令牌可继续用至其自然过期，活跃使用不被定长 TTL 中断

#### Scenario: 登出令牌被撤销、不可再用
- **WHEN** 已登录者请求 `POST /api/auth/logout`（或管理侧撤销某 `jti`）
- **THEN** 该 `jti` 进入黑名单，其后携该令牌的任何 `/api/*` 请求返回 401，即使令牌尚未到 `exp`

### Requirement: 只读聚合接口非阻塞、组合现有存储与活态

面板只读接口 SHALL 组合已持久化存储（风控状态 / 计数器 / 发布记录 / 概念）与进程内活态（在线边缘登记、在途发布槽）产出视图，且 MUST 只用已有索引的点查/范围查询、MUST NOT 跑会阻塞事件循环的全表扫描或重聚合（避免给 `8787` 边缘命令下发加延迟）。MVP 接口至少含：`GET /api/version`、`GET /api/dashboard/summary`、`GET /api/accounts`、`GET /api/accounts/:id`、`GET /api/content/queue`、`GET /api/content/published`、`GET /api/analytics/like-rate`。

面板层「全局 / 纯时间窗」读查询（今日各动作聚合、全局互动流、时间窗用量）MUST 有可服务其访问路径的索引：`risk_counters`、`interaction_feed`（及按窗口查询的 `llm_token_usage`）SHALL 各具一个 `occurred_at` 打头（或单列）索引，使这些不带账号前缀的查询走索引而非退化为顺序全表扫描（账号打头的既有复合索引服务不了纯时间窗查询）。索引 MUST 在启动自建（`CREATE INDEX IF NOT EXISTS`）与 migration 文件两处同步声明。

面板读命中的追加型表 MUST 有已接线的数据保留清理，防止无限增长使扫描成本随运行时长单调恶化：`risk_counters` SHALL 保留不少于风控回读窗（≥7d）、`interaction_feed` 与 `llm_token_usage` SHALL 各挂一个已调度的周期清理（后者接线其既有 `purgeOlderThan`）。清理 DELETE MUST 走 `occurred_at` 索引、MUST NOT 全表扫描。

已发布历史接口 `GET /api/content/published` SHALL 在每条记录中返回 `accountId`、`content`（已发布正文全文）、`postUrl`（详情页链接，可空），以及既有 `id`/`title`/`status`/`platformPostId`/`publishedAt`；账号展示名 SHALL 取 `accounts.nickname ?? accounts.label ?? account_id`。该接口 SHALL 接受可选 `?accountId` 过滤，命中时凭 `publish_log.account_id` 既有索引做范围/点查、MUST NOT 退化为全表扫描。

#### Scenario: 总览汇总走索引查询
- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 面板层用计数器的窗口查询 + 在线边缘数 + 风控状态点查组合返回，不执行阻塞事件循环的全表扫描

#### Scenario: 全局时间窗查询走 occurred_at 索引
- **WHEN** 面板层执行今日各动作聚合 / 全局互动流 / 时间窗用量这类不带账号前缀的查询
- **THEN** 查询走 `occurred_at` 打头索引，查询计划不含对 `risk_counters` / `interaction_feed` / `llm_token_usage` 的顺序全表扫描

#### Scenario: 追加型表有已接线的保留清理
- **WHEN** 面板读命中的追加型表随运行时长积累历史行
- **THEN** 周期清理任务按各表保留窗删除超窗行（走 `occurred_at` 索引），风控回读窗内数据不受影响，扫描成本不随时长单调恶化

#### Scenario: 按账号过滤已发布历史
- **WHEN** 请求 `GET /api/content/published?accountId=A`
- **THEN** 仅返回 `account_id = 'A'` 的已发布记录，查询走 `publish_log.account_id` 索引、不全表扫描

### Requirement: 面板 WebSocket 为纯只读事件扇出，与边-云 ws 物理隔离

面板层 SHALL 提供一个面板 WebSocket，订阅进程内事件总线，过滤为面板相关事件、归一化为统一帧（`docs/product-dashboard.md §2.3`），以**单一全局流 + 客户端过滤**推送给浏览器。它 MUST 是纯只读扇出：MUST NOT 与 edge 直接通信、MUST NOT 触碰 `ws-server.ts` 或边缘 socket，与边-云 `:8787` 物理隔离、逻辑复用事件流。

面板 WS 连接 SHALL 经 JWT 鉴权，token MUST 经**首帧**传递、MUST NOT 经连接 URL 的 query 传递（query 会随 URL 落进 Nginx 访问日志、明文泄露有效凭证）。连接建立后面板层 SHALL 在 token `exp` 时主动 `close`（关闭码使前端可辨识为鉴权失效），使 TTL 对实时流同样生效、过期令牌不再享有「连接期法外之地」。

面板 WS 广播 MUST 有背压保护，因面板层与浏览编排同进程、慢客户端的无界发送缓冲会 OOM 连累整个云端：广播前 MUST 对每客户端检查发送缓冲堆积（`bufferedAmount`），超阈值 SHALL 跳过该帧（只读监控流丢帧优于 OOM）、持续超阈值 SHALL 断开该慢客户端；单帧序列化载荷超大小上限 SHALL 截断为带标记的摘要帧；无活跃面板订阅时 MUST 跳过序列化（不在编排热路径白耗 CPU）。

#### Scenario: 实时日志流来自事件总线扇出
- **WHEN** 浏览器连上面板 WebSocket 并通过首帧 JWT 鉴权
- **THEN** 它收到由事件总线过滤、归一化后的单一全局事件流，期间面板层从不向 edge 发送任何消息

#### Scenario: token 不经 URL query 传递
- **WHEN** 浏览器发起面板 WS 连接
- **THEN** token 经首帧传递、不出现在连接 URL 中，故不会落入 Nginx 访问日志

#### Scenario: 慢客户端触发背压、不拖垮进程
- **WHEN** 某浏览器客户端消费变慢、发送缓冲 `bufferedAmount` 持续超阈值
- **THEN** 面板层对其跳帧、持续超阈值则断开该客户端，其它客户端与浏览编排进程不受影响，进程内存不被无界缓冲堆垮

#### Scenario: 连接期到期主动断开
- **WHEN** 一条已鉴权的面板 WS 连接的 token 到达 `exp`
- **THEN** 面板层主动关闭该连接（前端可辨识为鉴权失效），过期令牌不再继续收流

### Requirement: enum 漂移哨兵——`/api/version` 暴露 live 枚举值

`GET /api/version` SHALL 返回面板 API 契约版本**与** live 枚举值及关键 DTO 字段集合的结构指纹，作为前端 `aidcp-console` 的漂移哨兵。这些枚举值 MUST 与云端实现同一套 live 真值。

指纹暴露的枚举集合 SHALL 至少包含两类：

1. **风控 / 告警 / 厂商类**：风控状态 / 档位 / 告警分级 / **风控动作全集** / **图片生成厂商**。
2. **面板角色 / 模型配置类**：**模型类型 `llmKind`（含 `vision` 视觉角色）/ 生效模型来源 `effectiveSource` / 人设来源 `personaSource` / 思考模式 `thinkingMode`**。此类枚举被 console 直接用作 `{text,color}` 徽标映射的键，其漂移会令未同步的 console 出现「键缺失」——故 MUST 纳入哨兵。

云端侧这些枚举 MUST 有一份权威 runtime 全集（`as const` 数组）并以 type-level 断言强制其与对应类型全集严格一致（漏 / 多成员均编译失败，对齐 `PANEL_ACCOUNT_FIELDS` / protocol.ts 穷举范式），`/api/version` 从该权威全集导出、而非硬编码副本。

console 端的漂移哨兵测试 MUST 对 `/api/version` 暴露的 live 真值断言，MUST NOT 以「写死的本地副本对副本」方式恒绿——后者无法检出漂移（甚至会在有人修正镜像时反而失败）。会扩张的枚举（风控动作全集、图片厂商、模型 `llmKind` / `effectiveSource` 等）漂移 MUST 由该哨兵检出。

> 注：哨兵是**探测**手段（能连 live 云端时检出漂移），非崩溃防线。console 渲染侧对未知枚举值 MUST 独立容错回落（不 throw、不整页 white-screen），使离线 / 云端领先场景下未知值降级为可见的中性标签而非崩溃——两者互补。

#### Scenario: 版本接口回传 live 枚举与结构指纹
- **WHEN** 请求 `GET /api/version`
- **THEN** 响应含面板契约版本、live 的风控状态 / 档位 / 告警分级 / 风控动作全集 / 图片厂商枚举值，以及面板角色 / 模型配置枚举（`llmKind` / `effectiveSource` / `personaSource` / `thinkingMode`）与关键 DTO 字段集合指纹，供 console 端断言其镜像副本

#### Scenario: 哨兵对 live 真值断言、检出动作集漂移
- **WHEN** 云端风控动作集合从 6 扩到 7（新增评论赞），而 console 镜像未同步
- **THEN** console 漂移哨兵测试对 `/api/version` live 真值比对失败（红），而非因「副本对副本」恒绿而漏检

#### Scenario: 哨兵检出模型配置枚举漂移
- **WHEN** 云端角色目录新增一个 `llmKind:'vision'` / `effectiveSource:'vision'` 的角色（配置枚举全集扩张），而 console 镜像未同步
- **THEN** `/api/version` 的 `enums.llmKind` / `enums.effectiveSource` live 全集含 `vision`，console 漂移哨兵测试比对其镜像副本失败（红），在部署前暴露漂移；即便漏检，console 渲染侧亦以中性标签容错、不整页崩溃

### Requirement: 看板按账号活动暴露配额用量与上限

`GET /api/dashboard/summary` 的按账号今日切片（`totalsByAccount`）SHALL 对每个账号附上当前 **day 窗口生效配额上限**（每动作，取自该账号 `RiskController.effectiveQuotas()` 的现读值，随风控态 / 档位变化）与**每动作是否已在任一滑动窗饱和**的标记，使管理后台能就地把「用了多少 / 上限多少」呈现、到顶标红。

该组合 MUST 为**只读**：MUST NOT 经 `RiskController` 写、MUST NOT 触发任何风控状态迁移，且沿用面板「只用点查 / 内存态、不跑阻塞全表扫描」红线。缺 controller / 缺账号态时 MUST 诚实回落（不编造上限），归因待补的全局切片语义不变。此「配额用量」呈现 MUST 与风控状态徽标在语义上区分——它是**我方节流用量**，不是平台威胁态。

#### Scenario: 按账号今日活动带当前生效上限

- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 每个账号的今日各动作计数旁附当前 day 窗口生效上限（如 `restricted` 账号的互动上限如实为 0、`warned` 账号为缩放值）

#### Scenario: 已饱和动作被标记供前端标红

- **WHEN** 某账号某动作已撞到当日或突发窗上限
- **THEN** 该动作在响应中带「已饱和」标记，管理后台据此把该格标红

#### Scenario: 用量组合只读、不写风控态

- **WHEN** 面板层为总览接口计算按账号用量 / 上限
- **THEN** 该计算不触发任何风控状态写 / 迁移（`applySignal` / `setQuotaLevel` 不被调用），风控终态单写不变量不受影响

### Requirement: 账号接口暴露人设绑定状态

`GET /api/accounts`（及 `GET /api/accounts/:id`）SHALL 在账号视图中暴露**人设绑定状态**（如 `personaBound` / `needsPersonaSetup`），供后台账号列表标示「需设置人设」并跳转人设页。该字段 SHALL 沿用面板既有 JWT 鉴权，MUST NOT 另开免鉴权入口。该字段在 cloud 面板类型与 console 端类型为**手工镜像**，两处 MUST 同步以防漂移。

#### Scenario: 账号列表标示需设置人设
- **WHEN** 一个已登记但未绑人设的账号，经鉴权请求 `GET /api/accounts`
- **THEN** 响应中该账号带「未绑人设 / 需设置」状态，后台据此标示并提供跳转人设页的入口

#### Scenario: 状态字段受同一 JWT 守护
- **WHEN** 未携带有效 JWT 请求 `GET /api/accounts`
- **THEN** 返回 401，不泄露任何账号或其人设绑定状态

### Requirement: 看板事件扇出跨每连接私有通道聚合

当编排改为「每连接一条私有事件通道」后，实时看板的事件扇出 SHALL **跨所有连接的私有通道聚合**，对外仍呈现为**单一全局只读流**（与既有面板 WS 契约一致），MUST NOT 因通道私有化而漏掉某连接的事件或重复推送。该聚合仍是纯只读扇出，MUST NOT 触碰边缘 socket、MUST 沿用面板 WS 的 JWT 鉴权。

#### Scenario: 多连接事件汇入单一看板流
- **WHEN** 多个 edge 连接各自在自己的私有通道上产生面板相关事件
- **THEN** 看板聚合这些通道、对浏览器仍输出一条单一全局流，各连接事件不漏不重

#### Scenario: 私有化不破坏单连接看板
- **WHEN** 全机只有一个 edge 连接
- **THEN** 看板流内容与「单一全局总线」时代等价，无可见差异

### Requirement: 待审草稿编辑端点（JWT 守护、依赖缺失非致命、拒因映射 HTTP）

面板层 SHALL 暴露 `PUT /api/publish/:recordId/draft` 用于就地编辑待审正文草稿的标题 / 正文 / 可见范围 / 话题。该端点 MUST 落在既有 JWT 鉴权闸之下（以 JWT 主体作编辑者审计），MUST 在其依赖的草稿写对象缺失时返回 503（非致命、绝不崩塌关键闭环），MUST 对请求体做类型校验，并 MUST 把拥有者对象返回的可区分拒因映射为可区分 HTTP 语义（`not_found` → 404；`version_conflict` / `already_decided` / `not_pending` → 409；`invalid_title` / 非法字段 → 400；缺可见范围 → 422；成功 → 200 携写回后的 `recordId` / `contentVersion` / 标题 / 正文 / 元数据）。该端点 MUST NOT 发裸 SQL，一切写经拥有者对象。

#### Scenario: 编辑成功回写真态
- **WHEN** 已鉴权运营 PUT 合法的标题 / 正文 / 可见范围 / 话题到一条待审草稿
- **THEN** 端点经拥有者对象单写、返回 200 及写回后的 `contentVersion` 与字段真态

#### Scenario: 依赖缺失非致命
- **WHEN** 草稿写对象未注入
- **THEN** 端点返回 503 而非崩塌，其余面板接口与关键闭环不受影响

#### Scenario: 拒因映射可区分 HTTP
- **WHEN** 编辑因版本冲突 / 授权在途 / 非待审 / 非法标题 / 缺可见范围被拒
- **THEN** 端点分别返回 409 / 409 / 409 / 400 / 422，前端据码回不同文案，绝不混淆

### Requirement: 已发布投影增量带出内容版本号

只读聚合接口 `GET /api/content/published` SHALL 在既有投影上**增量**带出 `content_version`，供前端渲染草稿生命周期标签并快照「人所见的版本」以随授权携带。该扩展 MUST 为加性——MUST NOT fork 抽屉或另起端点、MUST NOT 改动既有字段语义，与已归档的发布历史 item 形状协调。

#### Scenario: 投影含版本号
- **WHEN** 控制台拉取已发布 / 待审历史
- **THEN** 每条 item 额外带 `content_version`，其余既有字段语义不变

#### Scenario: 加性不 fork
- **WHEN** 本能力扩展投影
- **THEN** 复用同一端点与 item 形状（仅新增字段），不新建并行端点、不 fork 只读抽屉

### Requirement: 总览接口暴露数据新鲜度，后台据此区分「无新活动」与「界面冻结」

总览只读接口 `GET /api/dashboard/summary` SHALL 在响应中附带一个**服务端生成的数据新鲜度时间戳**
（`asOf`，每次请求落地为该次查询的服务器当前时刻），并 SHALL 继续如实回报在线边缘事实：
Edge presence 镜像 fresh 时返回 `edgesOnline` 数值以及 `edgePresenceState=fresh`、owner
`edgePresenceAsOf`；镜像 uninitialized/stale/invalid 时返回 `edgesOnline=null` 与可区分的
`edgePresenceState=unknown|stale|invalid`，MUST NOT 把最后好值或空集合冒充当前在线数。
管理后台总览页 SHALL 用响应时刻与 presence 数据时刻把「系统当前没有新活动」「presence 暂不可用」
与「界面冻结 / 看板坏了」可视化区分：

- SHALL 呈现「数据截至 `asOf` / 自动刷新中」一类的新鲜度标识，使运营一眼看出页面轮询仍在更新；
- 只有 `edgePresenceState=fresh` 且 `edgesOnline=0` 时 SHALL 呈现「系统当前未在浏览」；
- presence unknown/stale/invalid 时 SHALL 呈现「在线状态暂不可用」及其数据时刻，
  MUST NOT 归因为零个 Edge 或虚构正在浏览。

该呈现 MUST 诚实：MUST NOT 把「无新活动」粉饰为有数据流入，也 MUST NOT 在无可靠 presence
证据时显示虚构的在线/离线结论。本要求只触及前端可读性与新鲜度暴露：MUST NOT 改变互动计数的
采集口径，MUST NOT 在总览接口引入会阻塞事件循环的全表扫描或重聚合。

#### Scenario: 总览响应带服务端新鲜度时间戳

- **WHEN** 请求 `GET /api/dashboard/summary` 且 Edge presence mirror fresh
- **THEN** 响应含本次请求 `asOf`、owner `edgePresenceAsOf`、`edgePresenceState=fresh` 与如实的 `edgesOnline`
- **AND** 不执行阻塞事件循环的全表扫描

#### Scenario: 自动刷新时新鲜度标识推进，证明界面未冻结

- **WHEN** 后台总览页按轮询完成一次刷新且后端返回了更晚的响应 `asOf`
- **THEN** 页面上的「数据截至 …」标识推进到新的响应时刻
- **AND** Edge presence 数据时刻独立呈现，MUST NOT 用响应时刻伪造 source freshness

#### Scenario: 无边缘在线时如实提示无新数据来源

- **WHEN** `edgePresenceState=fresh` 且 `edgesOnline=0`
- **THEN** 后台总览页显示「系统当前未在浏览，故无新数据」一类提示
- **AND** 把无新计数归因为 owner 已确认的零在线，而非界面故障

#### Scenario: Edge presence 暂不可用

- **WHEN** `edgePresenceState` 为 unknown、stale 或 invalid
- **THEN** 后台显示「在线状态暂不可用」并保留 owner 数据时刻
- **AND** MUST NOT 显示零个在线 Edge、无边缘在浏览或其它肯定离线结论

#### Scenario: 诚实呈现，不粉饰无活动

- **WHEN** 当前无新互动产生且计数较上次无变化
- **THEN** 后台如实呈现「数据已更新但无新活动」，MUST NOT 伪造活跃感
- **AND** MUST NOT 改变互动计数采集口径或把 `view` 加进互动 allow-list

### Requirement: 面板写端点校验目标存在性与输入格式，绝不静默假成功

面板写端点 MUST 校验其操作目标的存在性与外部输入的格式，杜绝「对不存在目标返回假成功」与「不可信输入直达副作用」（承本项目「MUST NOT 静默假成功」红线于面板写路径）。

账号相关写端点（暂停 / 恢复 / 设风控状态 / 设配额）MUST 在写库前校验账号存在，不存在 SHALL 返回 404 `account_not_found`、MUST NOT 经底层 `INSERT ... ON CONFLICT` 凭空造出幽灵账号行并返回成功。

发布审批端点接收的 `requestId` MUST 经格式白名单校验（仅允许受控字符集，如 `publish-<数字>` 或 `[A-Za-z0-9_-]+`）后方可参与审批信号文件的落盘路径拼接，MUST NOT 把含 `../` 等路径穿越片段的输入原样拼入文件路径；非法格式 SHALL 返回 400、不触发任何文件写。

#### Scenario: 对不存在账号的写返回 404 而非假成功
- **WHEN** 以一个不存在的账号 ID 请求暂停 / 恢复 / 设风控状态 / 设配额
- **THEN** 端点返回 404 `account_not_found`、不写库、不制造幽灵账号或幽灵风控状态行

#### Scenario: 审批 requestId 路径穿越被拒
- **WHEN** 审批请求的 `requestId` 含 `../` 或白名单外字符
- **THEN** 端点返回 400、不进行任何审批信号文件写，落盘路径不逃出预期目录

### Requirement: 管理后台读查询诚实呈现错误，不把失败伪装成加载或空数据

管理后台（console）的数据读查询失败时 MUST 向运营诚实呈现「加载失败」并提供重试入口，MUST NOT 把请求失败呈现为「仍在加载」（永久骨架屏）、「暂无数据」（误导空态）或回落到内置默认值冒充真实配置——这些等同于 UI 层的静默假成功，与后端「MUST NOT 静默假成功」红线同源。

读查询失败呈现 SHALL 由统一的读查询门组件收口（三态：加载中 / 失败可重试 / 成功）。写操作失败 MUST 呈现服务端返回的可区分原因（保留 `body.reason` 并映射为可读中文），MUST NOT 直接把英文机器错误码上屏。

#### Scenario: 读失败呈现错误与重试、不永久骨架屏
- **WHEN** 某页面的读查询请求失败
- **THEN** 页面呈现「加载失败」与重试入口，而非无限骨架屏、误导性「暂无数据」或伪造的默认配置

#### Scenario: 写失败呈现可读中文原因
- **WHEN** 某写操作因可区分原因（如掩码格式错 / 字段非法 / 版本冲突）失败
- **THEN** 界面呈现映射后的中文原因，而非 `bad_request` 一类英文机器码

### Requirement: 面板 DTO 单一来源，跨仓镜像由逐字 diff 测试守护

面板 API 的数据结构 SHALL 有单一权威来源（cloud `src/panel/`），并导出一份可供 console 侧断言的契约指纹（枚举值集合 + 关键 DTO 字段集合）。console 侧的手抄镜像（受跨仓边界所限不可消除）MUST 由对拍测试守护：把镜像与 cloud 导出的契约指纹逐一比对，任一漂移 SHALL 使测试失败。此机制对齐边云 `protocol.ts`「两份逐字一致 + typecheck 穷举 + 验收断言」范式，替代当前「仅 4 组枚举、且本地副本对副本恒绿」的失效防线。

#### Scenario: 镜像漂移被 diff 测试检出
- **WHEN** cloud 面板 DTO 新增 / 改名一个字段或枚举值，而 console 镜像未同步
- **THEN** console 的契约指纹对拍测试失败（红），漂移在 CI 暴露而非静默丢数据 / 显示旧值

#### Scenario: DTO 单源不引入跨仓构建依赖
- **WHEN** 面板 DTO 收敛到单一来源
- **THEN** 该来源为零运行时依赖的纯类型 + 可序列化契约清单，不在两仓间引入破坏各自独立 CI/部署的构建期依赖

### Requirement: 节奏兜底配置只读端点

面板 API SHALL 暴露只读端点 `GET /api/pacing`，返回每类操作（`action` / `scroll` / `card_gap` / `detail_dwell`）的兜底 floor 配置目录：每项含**生效值**（`minMs` / `maxMs`，已含读出口夹逼护栏）、`overridden`（库内是否有该 op 行，用于区分「运营已覆盖」与「系统默认」）以及审计字段（`updatedAt` / `updatedBy`）。当 pacing 配置依赖未注入（进程未装配该能力）时该端点 SHALL 返回 `503 pacing_unavailable`，MUST NOT 崩溃或返回半初始化数据。该端点 MUST 只读，MUST NOT 触发任何写库或状态迁移。

#### Scenario: 返回生效值与覆盖标记

- **WHEN** console 请求 `GET /api/pacing`，且 `action` 已被运营覆盖、`scroll` 未覆盖
- **THEN** 返回目录中 `action` 项 `overridden=true` 带审计字段、`scroll` 项 `overridden=false` 取系统默认值

#### Scenario: 依赖未注入返回 503

- **WHEN** 云端进程未装配 pacing 配置能力，收到 `GET /api/pacing`
- **THEN** 返回 `503 pacing_unavailable`，不崩溃

#### Scenario: 只读不改状态

- **WHEN** 反复请求 `GET /api/pacing`
- **THEN** 不产生任何写库副作用、不触发风控或配置状态迁移

### Requirement: 已发布投影展示参照洗稿来稿件

只读接口 `GET /api/content/published` SHALL 在既有发布记录投影上加性返回 `sourceReference` 字段。该字段在参照洗稿记录上为触发时来稿快照，在普通发布记录上为 `null`。接口 MUST 复用既有端点、既有账号过滤和既有排序，MUST NOT 为展示来源而 join 当前 `curated_content` 或退化为全表扫描。

管理后台「内容」tab SHALL 在发布内容列表或标题副信息中标识参照洗稿来源，并允许运营点击查看来稿件详情。发布详情浮层中 SHALL 提供同一入口。来稿件详情 SHALL 展示来源标题、正文、作者、话题、sourceId、快照时间与来源链接；来源链接缺失时 SHALL 诚实显示「无链接」或禁用按钮，MUST NOT 渲染死链。

#### Scenario: 参照洗稿行展示可点击来源

- **WHEN** `GET /api/content/published` 返回某行 `sourceReference != null`
- **THEN** 内容 tab 在该发布记录上展示「洗稿来源」入口，点击后打开来稿件详情，而非只打开发布稿详情

#### Scenario: 普通发布不展示来源入口

- **WHEN** 某发布记录 `sourceReference == null`
- **THEN** 内容 tab 不展示洗稿来源入口，也不暗示该记录由来稿触发

#### Scenario: 来稿件详情使用快照且链接诚实

- **WHEN** 运营打开参照洗稿记录的来稿件详情
- **THEN** 页面展示 `sourceReference` 快照中的标题、正文、作者、话题、sourceId 和快照时间；若 `sourceUrl` 存在则新标签打开，若为空则显示无链接且不渲染死链

#### Scenario: 账号过滤保持索引友好

- **WHEN** 请求 `GET /api/content/published?accountId=A`
- **THEN** 接口仍按 `publish_log.account_id` 过滤并返回该账号记录及其 `sourceReference`，MUST NOT 为来源展示跨账号读取当前精选池

### Requirement: 内容面板展示参照配图使用审计

`GET /api/content/published` SHALL 在发布记录投影中加性返回参考图使用审计字段。该字段在新参照洗稿记录上反映生成候审段落库的参考图使用状态，在普通发布或历史无审计记录上为 `null`。管理后台内容详情 SHALL 在参照洗稿记录的配图区域展示该审计：当状态为 `unsupported` 时，必须明确提示当前图片厂商未实际使用参考图、配图是按文本重新生成；当状态为 `used` 时，显示参考图已被图片模型使用；当状态为 `unavailable` 或 `skipped` 时，显示对应降级原因。前端 MUST NOT 因请求中带过参考图就宣称图片模型已使用参考图。

#### Scenario: unsupported 状态在内容详情可见
- **WHEN** 内容接口返回某参照洗稿记录 `imageReferenceAudit.status='unsupported'`
- **THEN** 内容详情在配图说明附近展示“当前图片厂商不支持参考图，已按文本重新生成”一类文案，并显示参考图数量

#### Scenario: used 状态在内容详情可见
- **WHEN** 内容接口返回 `imageReferenceAudit.status='used'`
- **THEN** 内容详情展示参考图已实际用于生成，并显示参考图数量

#### Scenario: 历史无字段不编造状态
- **WHEN** 内容接口返回 `imageReferenceAudit=null`
- **THEN** 内容详情不展示“已使用参考图”，也不把历史记录误标为 unsupported

### Requirement: 发布生成队列多 run 观测，形状向后兼容

发布生成队列接口 SHALL 暴露并行生成的多 run 视图（每轮账号 / 类型 / 参照稿标识 / 启动时刻 / 阶段快照），且 MUST 保留旧的单快照字段以向后兼容：旧字段按显式聚合规则取值（最新启动的 running 轮；无 running 则最近一次终态，失败态不被并行 running 永久遮蔽）。console 侧类型与渲染 SHALL 与 cloud 同批对齐（枚举 / 形状漂移曾致整页白屏），对空 runs 与未知字段 MUST 优雅回落。

#### Scenario: 多轮并发时队列页逐轮可见
- **WHEN** 同账号两轮洗稿并行生成中，运营打开 console 内容页
- **THEN** 发布队列卡按轮列出两条管线各自的账号、参照稿与阶段进度

#### Scenario: 旧形状消费者不白屏
- **WHEN** console 版本尚未升级、仍按旧单快照字段渲染
- **THEN** 旧字段按聚合规则持续有值，页面正常渲染不白屏、不冻结

### Requirement: 已发布投影支持服务端状态与账号过滤

已发布投影列表接口 SHALL 支持按状态（如 `pending_approval`）与账号的服务端过滤参数——多候选草稿场景下待审集合 MUST 完整可见，MUST NOT 依赖「全局最近 N 条再客户端过滤」的窗口（老待审草稿会被新发布记录挤出视野，导致「挑选」入口面残缺）。

#### Scenario: 待审列表完整不受窗口挤出
- **WHEN** 某账号有多份待审草稿、且全局最近发布记录数已超过默认窗口
- **THEN** 按状态过滤请求返回该账号全部待审草稿，运营可逐条查看、编辑、批准或驳回

### Requirement: 发布队列快照按阶段摘要呈现并保留原始明细

Cloud 的 `GET /api/content/queue` SHALL 在保留既有 `status`、`snapshot` 与 `runs` 字段的同时，
返回面向管理后台的发布生命周期投影。该投影 SHALL 将每份稿件拆为触发与选题、正文生成、文本质检、
视觉策划、出图复核、成稿封装、人工审批、平台下发八个阶段，并为每个阶段返回明确状态和可证实摘要。
阶段状态 MUST 至少能区分未开始、进行中、重试中、等待人工、已完成、部分完成、失败、跳过与
`evidence_unavailable`。

生命周期投影 SHALL 组合当前 orchestrator runs、`publish_log` 持久化状态、API-owned durable approval
dispatch projection 和 automation dispatcher in-flight 镜像，并返回 `inFlightEvidence.state/asOf`。
durable dispatch projection 已证明状态时 SHALL 以其为准；只有缺少 durable 证明且
`inFlightEvidence.state=fresh` 时，才可用 record id 是否在集合中补足等待人工/正在下发分类。
in-flight evidence unknown/stale/invalid 时，受影响稿件的下发阶段 SHALL 标记
`evidence_unavailable`，MUST NOT 由空集合推断“未下发”或“等待人工”。

管理后台 SHALL 优先使用该投影，将有可靠证据的生成中、等待人工或正在下发稿件展示在“活跃稿件”，
将 published、submitted、failed、needs_review、draft、skipped 等终态展示在“最近结果”或发布历史；
最近终态快照 MUST NOT 因存在 snapshot 而继续冒充活跃稿件。

该呈现 MUST 保持诚实：阶段完成 SHALL 由明确终点或持久化状态证明，不得因任意中间字段出现而声称
整段完成；文本质检和视觉策划等真实并行分支 MAY 同时显示进行中；没有逐命令证据时不得臆造平台下发
子步骤。原始 snapshot 字段 MUST 继续通过二级展开入口可见，供排障和未知未来字段检查。新字段
MUST 向后兼容，不得改变发布编排行为、审批授权或平台成功判定。

#### Scenario: 生成中的稿件显示八阶段投影

- **WHEN** 管理后台读取到一个 running orchestrator run，正文已经产出而文本质检与视觉策划尚未收敛
- **THEN** 活跃稿件 SHALL 显示该账号和稿件摘要，正文生成标记已完成
- **AND** 文本质检与视觉策划 MAY 同时标记进行中，其余阶段按依赖保持未开始

#### Scenario: 待审稿件明确等待人工

- **WHEN** `publish_log` 为 `pending_approval`，durable projection 未证明已开始下发，
  且 fresh in-flight 集合明确不含该 record id
- **THEN** 该稿件 SHALL 位于活跃稿件，人工审批阶段标记等待人工，平台下发阶段标记未开始

#### Scenario: 已批准稿件显示平台下发中

- **WHEN** durable dispatch projection 证明 dispatching，或 fresh in-flight 集合明确包含该 record id
- **THEN** 人工审批阶段 SHALL 标记已完成，平台下发阶段 SHALL 标记进行中
- **AND** 后台不得继续显示为单纯待审

#### Scenario: in-flight 证据不可用

- **WHEN** 稿件缺少 durable dispatch 证明且 `inFlightEvidence.state` 为 unknown、stale 或 invalid
- **THEN** 平台下发阶段 SHALL 标记 `evidence_unavailable` 并显示“下发状态暂不可用”
- **AND** MUST NOT 因本地集合为空将其标为等待人工、未下发或正在下发

#### Scenario: 下发失败离开活跃稿件

- **WHEN** 一份稿件的持久化状态从 `pending_approval` 变为 `failed`
- **THEN** 该稿件 MUST 从活跃稿件移入最近结果或发布历史
- **AND** 平台下发阶段标记失败并明确不得声称已经发布

#### Scenario: 已提交但链接未确认显示部分完成

- **WHEN** 一份稿件的持久化状态为 `submitted` 且没有可验证的平台帖子链接
- **THEN** 平台下发阶段 SHALL 标记部分完成并显示“已提交，待链接确认”
- **AND** 不得标成失败或已发布

#### Scenario: 原始字段仍可展开排障

- **WHEN** 生命周期关联的生成 snapshot 中存在未被阶段摘要识别的顶层字段
- **THEN** 页面 SHALL 提供原始字段展开入口并显示该字段的序列化值
- **AND** 运营排障不需要翻服务器日志确认字段是否存在

#### Scenario: 空闲状态不伪造进度

- **WHEN** lifecycle 没有可靠 running、waiting_human 或 dispatching 稿件
- **THEN** 发布队列 SHALL 显示无可确认的活跃稿件
- **AND** MUST NOT 因最近终态 snapshot 或 unavailable in-flight evidence 渲染虚假进行中阶段

### Requirement: Facebook groups API accepts metadata filters and metadata-bearing imports
The panel API SHALL extend Facebook group management endpoints additively. `GET /api/facebook/groups` SHALL accept optional `region`, `park`, and `direction` query parameters. `POST /api/facebook/groups/import` SHALL accept `items[]` entries containing `url` plus optional `name`, `region`, `park`, and `direction`. Existing URL-only `text` and `urls` import payloads SHALL remain accepted.

#### Scenario: Metadata import item is accepted
- **WHEN** the console posts an import item with `url`, `region`, `park`, and `direction`
- **THEN** the panel API validates the fields and passes the metadata to the Facebook group target store

#### Scenario: Existing text import still works
- **WHEN** an API caller posts `text` containing one or more Facebook group URLs
- **THEN** the panel API still imports those URLs without requiring metadata

#### Scenario: Bad metadata type is rejected
- **WHEN** an import item has a non-string `region`, `park`, or `direction`
- **THEN** the panel API returns a bad request and does not import the malformed item

### Requirement: Console supports wide spreadsheet paste import for Facebook groups
The console SHALL parse pasted Facebook group data from both URL-only text and wide spreadsheet-like tabular text. For wide tables, it SHALL associate URLs under repeated `序号 + 园区名` column pairs with the active region header above them, and SHALL associate trailing non-park URL columns with their direction header. Missing region, park, or direction metadata SHALL be allowed.

#### Scenario: Repeated park columns import with region and park
- **WHEN** an operator pastes rows whose region header is `河南区域` and whose URL column belongs to `序号 + 同文1工业区`
- **THEN** the console sends import items for those URLs with `region=河南区域` and `park=同文1工业区`

#### Scenario: Direction columns import with direction
- **WHEN** an operator pastes rows whose URL column belongs to a header such as `机械和电气`
- **THEN** the console sends import items for those URLs with `direction=机械和电气`

#### Scenario: URL-only text import remains supported
- **WHEN** an operator pastes plain URL-only lines
- **THEN** the console sends URL-only import items and no metadata is required

### Requirement: Console exposes optional cascading metadata filters
The console Facebook groups page SHALL expose optional filters for region, park, and direction. The park selector SHALL be presented as a child of the selected region: changing or clearing region MUST clear the selected park, and only parks known under the selected region are selectable. None of the three filters SHALL be mandatory.

#### Scenario: Region controls park options
- **WHEN** an operator selects region `北宁区域`
- **THEN** the park selector only offers parks stored under `北宁区域`

#### Scenario: Clearing region clears park
- **WHEN** an operator clears the selected region
- **THEN** the selected park is cleared and the group list no longer applies a park filter

#### Scenario: All metadata filters are optional
- **WHEN** an operator leaves region, park, and direction unset
- **THEN** the group list still loads using the existing status/enabled filters

### Requirement: 安装包清单由所在机器现扫得出，绝不写死在源码里

The panel API SHALL expose the edge desktop installer list by scanning the downloads directory **on the host it runs on**, and the console SHALL render the download menu from that response. The installer version and filenames MUST NOT be hardcoded in console source.

A hardcoded version describes deployment state ("which binary is sitting in *this* host's directory"), which differs per host. Baking it into source guarantees it is a lie on every host but one: trunk pointing at the `ol` artifact yields dead links on `dev`, and trunk pointing at the `dev` artifact silently downgrades the `ol` download page.

The scan SHALL ignore non-release files (backups such as `*.bak-*`, partial downloads). When several versions of the same platform's installer are present, the highest semantic version SHALL be offered. The directory location SHALL be configurable, defaulting to the deployed convention.

#### Scenario: 页面只提供确实存在的包

- **WHEN** the console renders the installer download menu
- **THEN** every offered entry corresponds to a file that exists in that host's downloads directory at request time
- **AND** the displayed version is derived from those files, not from console source

#### Scenario: 两台机器各说各的真话

- **WHEN** the same console build is deployed to a host holding `0.3.18` and to a host holding `0.3.20`
- **THEN** each one offers the installer it actually has, with no source change and no rebuild between them

#### Scenario: 没有可用安装包时诚实说没有

- **WHEN** the downloads directory is empty, unreadable, or contains no recognizable installer, or the API call fails
- **THEN** the console shows that no installer is currently available
- **AND** it MUST NOT fall back to a hardcoded version or emit a link to a file it has not confirmed exists

#### Scenario: 备份与残留文件不被当成发布包

- **WHEN** the downloads directory also contains backup or partial files alongside real installers
- **THEN** those files are excluded from the manifest

#### Scenario: 同平台多版本取最高版本

- **WHEN** several versions of the same platform's installer are present in the directory
- **THEN** the manifest offers the highest semantic version for that platform

### Requirement: 回复配置缺失必须由显式安全初始化恢复

internal panel API SHALL 提供 permission-gated `POST /api/accounts/:accountId/reply-config/initialize`。请求 MUST 要求 `interaction.config.edit`、`expectedVersion=0` 并验证账号 platform=`wechat_channels`；成功只创建使用默认关闭发送/自动化 policy、两渠道默认 profile 的 draft v1，不创建启用模板/规则、不发布、不修改 runtime controls。重复或并发初始化 MUST 以当前版本冲突返回，MUST NOT 覆盖既有配置。

#### Scenario: 新视频号账号初始化安全草稿
- **WHEN** 有 config.edit 权限的管理员对无 config head 的视频号账号执行初始化
- **THEN** Cloud 原子创建 draft v1、publishedVersion 仍为空、发送与自动化保持关闭，并记录无正文审计

#### Scenario: 初始化不能覆盖已有草稿或发布版本
- **WHEN** 账号已经有任意 config head 后再次调用初始化
- **THEN** Cloud 返回版本冲突与当前版本，既有模板、规则、profile 和 publishedVersion 不变化

#### Scenario: 非视频号账号不能初始化互动回复配置
- **WHEN** 管理员对 XHS 或 Facebook 账号调用初始化
- **THEN** API 返回不可用/不存在且不创建 interaction config 行

### Requirement: Console 必须把缺少配置呈现为可初始化状态

Console 回复设置抽屉 SHALL 区分 permission denied、配置缺失和普通加载失败。配置缺失时 SHALL 显示初始化说明与显式按钮；初始化成功后重新读取服务端真态并进入 draft 编辑页，MUST NOT 在按钮点击前本地伪造默认快照或显示已发布。

#### Scenario: 新账号打开回复设置
- **WHEN** 聚合配置读取返回 INTERACTION_CONFIG_MISSING
- **THEN** 页面显示“尚未初始化回复配置”和“初始化安全草稿”，而不是通用加载失败

#### Scenario: 初始化成功后仍提示未发布
- **WHEN** 初始化 API 成功并重新读取 draft v1
- **THEN** 页面显示 draft v1、published 未发布，并要求创建模板/规则和显式发布

### Requirement: 内容投影与待审详情增量呈现平台原生定时信息

`GET /api/content/published` SHALL 在既有 item 上增量返回 `platform`、`publishMode`、`publishTime`、`scheduledAt` 与 `scheduledPlatformId`，历史行缺值时 null-safe。控制台待审详情 SHALL 在标题、正文、话题/其它稿件字段之后、批准动作之前提供“立即发布 / 定时发布”选择；选择定时时显示北京时间输入与 1 小时至 14 天约束。内部定时 id 只可作诊断文本，MUST NOT 渲染为公开链接。

#### Scenario: 待审详情编辑定时时间
- **WHEN** 小红书待审 item 的 `publishMode='scheduled'`
- **THEN** 控制台回显目标北京时间，时间或模式变化计入未保存改动并随 `modify_candidate` 提交

#### Scenario: 定时排队状态诚实展示
- **WHEN** item 状态为 `scheduled` 且尚无 `postUrl`
- **THEN** 控制台显示“定时发布，待公开确认”及目标时间，不显示“已发布”或可点击的伪链接

### Requirement: 发布队列展示尚未开跑的发布委托

管理后台独立发布队列页 SHALL 在活跃稿件区域之外提供“排队任务”只读区域。该区域 MUST 展示发布动作族中状态为 `queued`、`planning` 或 `deferred` 的任务，并至少包含账号、动作、状态和任务标识；来源标题有证据时 SHALL 展示。`awaiting_confirmation`、`waiting_approval`、`executing` 与终态任务 MUST NOT 混入该区域。页面 MUST NOT 把列表顺序描述为精确队列名次。内容页 SHALL 不再重复渲染该队列区域。

`GET /api/delegated-tasks` SHALL 加性支持按动作族和一个或多个状态过滤，并在服务端过滤后应用 limit，确保仍在排队的任务不会被较新的无关终态记录挤出结果窗口。不带新过滤参数的既有请求 SHALL 保持兼容。

#### Scenario: 排队发布任务显示在独立区域

- **WHEN** 一个发布类委托处于 `queued` 且尚未产生 orchestrator run
- **THEN** 独立发布队列页在“排队任务”区域显示其账号、发布动作、排队状态和任务短标识，活跃稿件区不伪造生成阶段

#### Scenario: 暂缓任务与来源标题诚实可见

- **WHEN** 一个发布类委托处于 `deferred` 且 `sourceConstraints.title` 为非空标题
- **THEN** 排队任务区域显示“暂缓”状态与该来源标题，不把它描述为执行中或已发布

#### Scenario: 已进入生命周期的任务不重复

- **WHEN** 发布类委托进入 `executing` 或 `waiting_approval`
- **THEN** 该委托不再出现在排队任务区域，并由既有发布生命周期投影承担生成中或等待审批的展示

#### Scenario: 服务端过滤先于窗口限制

- **WHEN** 请求按 `actionFamily=publish` 和排队状态过滤，且较新的无关终态任务数量超过 limit
- **THEN** 服务端先筛选匹配任务再应用 limit，仍在排队的发布任务不会被无关记录挤出

#### Scenario: 排队任务查询失败不遮蔽活跃稿件

- **WHEN** 排队任务请求失败而发布生命周期请求成功
- **THEN** 排队任务区域明确显示加载失败，活跃稿件、阶段和最近结果仍可查看

### Requirement: 视频号账号限速必须以预设优先并保留高级真值

Console SHALL 默认以“保守 / 标准 / 自定义”表达视频号账号限速。保守与标准预设 MUST 确定性映射完整 rateLimits；历史值只有逐位匹配预设时才能显示为该预设，否则 SHALL 显示自定义。六个原始字段 SHALL 收进可展开的高级设置并始终展示服务端真值；打开页面、识别预设或切换到自定义 MUST NOT 自动保存或扩大权限。

#### Scenario: 新安全草稿显示保守预设
- **WHEN** Cloud 返回新初始化 policy 的保守限速值
- **THEN** Console 选择“保守”并显示摘要
- **AND** 详细数字默认收折但可展开查看

#### Scenario: 历史零值不被静默改写
- **WHEN** Cloud 返回不匹配任何预设的历史 rateLimits
- **THEN** Console 显示“自定义”及真实数字
- **AND** 未经管理员主动选择预设并保存时不发送修改请求

### Requirement: 限速预设不得模糊系统硬门禁和平台事实

Console SHALL 将限速预设描述为 Cloud 本地回复节流，MUST NOT 声称其为视频号官方安全额度。选择预设 MUST NOT 修改 runtime controls、published version、平台 capability、RiskController 风险状态或熔断状态；保存仍只更新 policy draft，发布仍遵循既有原子边界。

#### Scenario: 选择标准预设只修改草稿限速
- **WHEN** 管理员选择标准预设并保存
- **THEN** 请求只携带现有 policy DTO 中更新后的 rateLimits
- **AND** 即时运行开关、平台能力和已发布版本保持不变

### Requirement: 面板把搜索展示为账号风险动作

Cloud `/api/version` 的风险动作全集、配额 API、`GET /api/dashboard/summary` 的全局/按账号今日活动、day 上限与饱和标记 SHALL 包含 `search`。Console SHALL 同步镜像 search 枚举、标签与排序，在配额页和今日账号活动中显示“搜索”，并继续对未知动作做中性回落；漂移哨兵 SHALL 以 live Cloud 枚举检出 Cloud/Console 不一致。

#### Scenario: 今日活动显示搜索用量与上限

- **WHEN** 某账号今日已真实执行 2 次搜索且生效 day 上限为 10
- **THEN** 总览按账号活动显示 search 用量 2、上限 10，并按真实窗口状态显示是否饱和

#### Scenario: 搜索枚举漂移被哨兵检出

- **WHEN** Cloud `/api/version` 已包含 search，而 Console 镜像缺失
- **THEN** 枚举漂移测试失败，阻止把不完整看板当作兼容成功

### Requirement: 单场搜索预算使用行为术语

Console 配额页中同时包含浏览/搜索与互动动作的会话预算分组 SHALL 命名为“单场行为预算”，MUST NOT 继续把其中的搜索误称为“互动”。该文案调整不改变 `budget.searches` 的数值、扣减时机或服务端契约。

#### Scenario: 配额页准确描述搜索预算

- **WHEN** 运营打开配额页查看包含搜索的单场预算
- **THEN** 页面显示“单场行为预算”，搜索仍作为独立一项展示

### Requirement: 内容排期目录返回规范化平台与权威自动化动作投影

Cloud `GET /api/content-schedule` SHALL 为每个账号目录行增量返回规范化 `platform` 与服务端权威 `availableActions`。每个可用动作描述 MUST 至少包含稳定动作 id、该平台允许的非关闭模式和服务端日上限；该投影 MUST 来自有真实消费者的平台注册声明，而不是复用仅供指标显示的 `group_join` capability，也不得由 Console 维护第二份平台动作矩阵。旧平台别名 SHALL 按既有规范化规则归一；未知平台 MUST NOT 被伪装成任一已知平台的可配置动作。

#### Scenario: 小红书目录行返回规范化动作能力
- **WHEN** 目录包含平台原始值为 `xhs` 的账号
- **THEN** 返回行的 `platform` 为 `xiaohongshu`，且 `availableActions` 精确描述当前小红书排期支持的动作、模式与上限

#### Scenario: 视频号无内容自动化动作
- **WHEN** 目录包含当前只支持互动收件箱工作流的视频号账号
- **THEN** 返回规范化平台 `wechat_channels` 和空 `availableActions`，不得因通用内容排期字段存在而声称可自动发帖或评论

#### Scenario: Facebook 发帖模式诚实受限
- **WHEN** 目录包含 Facebook 账号且当前 Facebook 自动发帖只支持待审模式
- **THEN** 其发帖动作只声明 `review`，不得把运行时会跳过的 `auto_approve` 投影为可配置模式

### Requirement: Facebook 群组面板 API 暴露账号分组范围读模型

Facebook 群组列表 SHALL 为每个目标返回完整 `accountScopeMode` 和 `accountGroupLabels`，接受可选显式范围模式或精确账号分组过滤；facets 或等价只读端点 SHALL 返回当前 Facebook 账号实际使用的可选分组、全局目标计数及受限空范围目标计数。导入和批量范围 API SHALL 接受 `global` 或 `restricted + accountGroupLabels`，并让“未提供范围”“显式全局”“显式受限空集合”的语义可区分。`global` 与非空标签、非法目标或非法 Facebook 分组标签 MUST 使整个请求拒绝；成功写入 SHALL 返回数据库回读真态。既有 URL-only、元数据导入和 labels-only 旧请求继续有效，labels-only 按 restricted 解释。

#### Scenario: 列表区分全局和未设置范围
- **WHEN** 目录同时含 global 目标、restricted 多标签目标和 restricted 空范围目标
- **THEN** API 为每行返回可区分的范围模式和标签，并返回对应 facets 计数

#### Scenario: 批量全局写返回真态
- **WHEN** Console 把一批现有目标范围替换为 global
- **THEN** API 整块校验并写入后返回每个目标 `accountScopeMode=global` 且标签为空的数据库真态

#### Scenario: 旧 labels-only 写保持兼容
- **WHEN** 旧客户端只提交 `accountGroupLabels=["华东组"]`
- **THEN** API 按 `restricted` 范围处理，不把该请求解释为 global

### Requirement: 账号自动化目录聚合 Facebook 加群配置和 scheduled 最近结果

`GET /api/content-schedule` SHALL 在 `platform-aware-account-automation` 的服务端权威投影中，为 Facebook 增加 `join_group` 可用动作并返回每账号自动加群开关、配置日上限、有效日上限、动作时段/来源、是否已分组/映射候选摘要，以及最新 scheduled 审计结果。非 Facebook 行 MUST NOT 获得该动作；无配置或无审计 SHALL 返回 fail-closed 默认和 null 结果，不得伪造。

#### Scenario: Facebook 行显示可配置加群动作
- **WHEN** 内容排期目录包含 Facebook 账号
- **THEN** 其 `availableActions` 含 `join_group`，动作投影携带真实配置、有效额度、范围可用性和最近 scheduled 结果

#### Scenario: 小红书行不出现加群
- **WHEN** 目录包含小红书账号
- **THEN** 其 `availableActions` 不含 `join_group`，也不返回伪造的加群配置

### Requirement: 内部 Panel 提供环境资产投影与账号环境摘要

内部 Panel API SHALL 提供受内部 JWT 保护的环境资产列表，聚合环境生命周期、环境名来源、挂载账号统一显示名、账号风控/档位、分组、端用户归属、installation 观测与删除请求；客户令牌 MUST NOT 访问该跨客户投影。账号列表 SHALL additive 返回有效/删除中/在线环境计数，且所有账号环境摘要与环境列表使用同一生命周期过滤规则。

#### Scenario: 内部管理员读取环境资产
- **WHEN** 持内部 Panel JWT 请求环境列表
- **THEN** 返回环境与账号/风险/分组/归属/生命周期投影，并不暴露密钥、凭据、代理密码或客户 key/hash

#### Scenario: 客户令牌无法读取跨客户环境资产
- **WHEN** 持客户令牌请求内部环境资产端点
- **THEN** 请求被拒且不返回任何跨客户挂载或归属信息

#### Scenario: 账号摘要与环境生命周期一致
- **WHEN** 某账号有一个 active、一个 deleting 和一个 deleted 环境
- **THEN** 账号摘要返回 activeCount=1、deletingCount=1，deleted 环境不计入当前数量

### Requirement: 内部删除 API 只创建异步期望状态

内部 Panel SHALL 提供逐环境删除申请 API，要求完整 envKey 确认并支持幂等请求。成功响应 MUST 返回写后生命周期与 requestId，状态为请求已创建/已存在；该 API MUST NOT 直接声称 AdsPower 已删除。重复未终态请求 MUST 返回同一 active request，已删除环境 MUST 返回同一终态而非重建任务。

#### Scenario: 创建删除申请返回 202 真态
- **WHEN** 管理员对 active 环境提交匹配 envKey 的确认和新的幂等键
- **THEN** Cloud 原子创建删除申请、冻结调度并以 202 返回 `waiting_edge` 及 requestId，不返回“已删除”

#### Scenario: 重复提交不产生多条删除责任
- **WHEN** 同一环境已有未终态删除申请且管理员重试请求
- **THEN** API 返回现有 requestId/状态，不产生第二个 active 删除申请或第二次 AdsPower 执行责任

### Requirement: 排队任务必须解释有证据的暂缓原因

管理后台内容页显示 `deferred` 发布任务时，除状态与下一次检查时刻外，SHALL 根据 Cloud 已返回的稳定 `currentStep` 展示可读等待原因。页面 MUST NOT 把重试轮询时刻描述为届时一定开始；未知步骤码 MUST NOT 被猜测成具体原因。

#### Scenario: 同源 ownership 占用可见

- **WHEN** 一条发布任务为 `deferred` 且 `currentStep=waiting_ownership`
- **THEN** 排队卡 SHALL 说明正在等待同一参照稿任务释放
- **AND** SHALL 把 `nextEligibleAt` 描述为预计再次检查时刻，而非承诺起跑时刻

#### Scenario: 生成槽位暂满可见

- **WHEN** 一条发布任务为 `deferred` 且 `currentStep=waiting_safe_slot`
- **THEN** 排队卡 SHALL 说明生成槽位暂满、任务仍在排队

#### Scenario: 未知步骤不猜测

- **WHEN** 一条暂缓任务带有 Console 不认识的 `currentStep`
- **THEN** 页面 SHALL 保留“暂缓”状态与时间事实
- **AND** MUST NOT 补写未经 Cloud 证实的原因

### Requirement: Panel 账号 DTO 暴露统一显示名和来源

Panel 账号 API SHALL 为每个账号返回 Cloud 统一解析器产生的 `displayName` 与 `displayNameSource`，同时保留 `accountId`、平台昵称、运营标签和运营别名的原始字段供诊断。内部环境注册表 API SHALL 为已绑定环境返回同一解析结果产生的 `account.displayName`。Console 所有账号名展示、只持有 `accountId` 的 join，以及“环境归属”中按 `envKey` 关联到绑定账号的昵称展示 SHALL 使用服务端 `displayName`，MUST NOT 在页面或共享前端工具中重写别名优先级。没有绑定账号投影的环境 MAY 回落到环境系统名、既有环境备注和稳定 `envKey`，但 MUST NOT 把该回落用于账号身份或归属判断。

#### Scenario: 管理后台展示客户端人工别名
- **WHEN** 账号在 Cloud 已有运营别名
- **THEN** 账号列表、人设、内容、用量、联系方式及其它账号选择或展示位置均显示该别名并保留同一 `displayNameSource`，环境归属也显示同一别名

#### Scenario: 环境归属按稳定环境键关联显示名
- **WHEN** 已分配 scope 行只含 `envKey`，且全局环境注册表中该 `envKey` 已绑定带统一 `displayName` 的账号
- **THEN** Console 在环境归属的已分配与待分配位置都展示该 `displayName`，保存和归属判断仍使用原 `envKey`

#### Scenario: 未挂载环境回落环境自身名称
- **WHEN** 环境没有绑定账号投影或在滚动发布窗口暂未收到账号显示字段
- **THEN** Console 回落展示环境系统名、既有环境备注或稳定 `envKey`，且不在前端推断账号别名来源

#### Scenario: 人工别名清除后后台回落
- **WHEN** 运营别名被清空且平台昵称存在
- **THEN** 下一次 Panel 读取返回平台昵称和来源 `platform_nickname`，Console 不保留旧人工名

#### Scenario: 旧服务端兼容边界
- **WHEN** Console 在发布切换窗口收到尚无 `displayName` 的旧账号 DTO
- **THEN** 前端只做兼容性账号 ID 回落并明确不可判断来源，MUST NOT 重新复制完整昵称优先级

### Requirement: Runtime-control updates drive account-scoped Edge delivery
After a successful CAS update of `interaction_runtime_controls`, the internal API SHALL make the committed account/version available to the account's negotiated online Edge through `interaction.runtime.controls`. The database commit and audit record SHALL remain authoritative; delivery count or socket enqueue MUST NOT be reported as Edge application success.

#### Scenario: CAS update reaches one online Edge
- **WHEN** an authorized operator updates runtime controls with the current expected version and exactly one negotiated Edge is online for the account
- **THEN** Cloud commits and audits version `N+1`, pushes a scope-matching `interaction.runtime.controls` payload to that Edge, and returns the committed controls without claiming Edge application

#### Scenario: Edge is offline during update
- **WHEN** the runtime-control CAS succeeds while no negotiated Edge is online
- **THEN** Cloud keeps the committed version, records delivery as deferred/zero, and includes the latest fail-closed snapshot in the next negotiated welcome

### Requirement: Downlinked write controls are effective safety projections
The write booleans delivered to Edge SHALL be false unless the account channel control is enabled, `write_paused=false`, the Cloud global interaction write gate is enabled, offboarding is not pending, and the snapshot scope is valid. Read booleans SHALL also fail closed on provider errors or scope mismatch.

#### Scenario: Account enables replies while global writes remain disabled
- **WHEN** `comments_reply_enabled=true` for an account but the Cloud global write gate is false
- **THEN** the Edge snapshot reports comment reply disabled while preserving the stored account setting for administration

#### Scenario: Runtime-control lookup fails during hello
- **WHEN** Cloud cannot load the account runtime-control row while building welcome
- **THEN** welcome either carries an explicit all-false scope-matching snapshot or omits negotiation so Edge keeps every interaction capability false

### Requirement: Console 客户环境平台候选必须包含视频号并容忍未来值

Console 的客户环境注册与归属界面 SHALL 把 `wechat_channels` 作为受支持平台候选并显示中文“视频号”，同时继续支持 `xiaohongshu` 与 `facebook`。环境 registry DTO MUST 保持可接收未知字符串；未知未来平台值 MUST 显示原始值并保持可读取，MUST NOT 使页面白屏、擅自回落成其他平台或阻止既有归属加载。

#### Scenario: 管理员手动登记视频号环境
- **WHEN** 管理员在客户环境归属页手动登记环境并选择“视频号”
- **THEN** Console 提交稳定 wire 值 `wechat_channels`，保存回读后仍显示“视频号”

#### Scenario: Cloud 返回未来平台值
- **WHEN** 环境注册表返回当前 Console 尚未认识的平台字符串
- **THEN** Console 以中性样式显示原始值并保持页面可用，MUST NOT 把它标成视频号、小红书或 Facebook

### Requirement: Console 回复配置审计必须消费完整分页台账

Console SHALL 消费既有 `GET /api/accounts/:accountId/reply-config/audit` 的 opaque `nextCursor`，允许运营按需追加后续页，并明确显示加载中、可继续、已到底、权限拒绝和后续页失败状态。cursor MUST 只作为 opaque 字符串 URL 编码后回传，MUST NOT 由 Console 解析、改写或伪造；后续页失败 MUST 保留已经成功加载的记录并提供重试。

#### Scenario: 审计首屏还有后续页
- **WHEN** 首屏返回非空 `nextCursor` 且运营点击加载更多
- **THEN** Console 携该 cursor 请求同一账号的下一页，按服务端顺序追加事件，并以稳定 eventId 去重

#### Scenario: 审计已经加载到底
- **WHEN** 最近一次成功回包返回 `nextCursor=null`
- **THEN** Console 显示台账已全部加载且不再提供继续请求入口，MUST NOT 把首屏条数冒充总量统计

#### Scenario: 后续页加载失败
- **WHEN** 已展示首屏后追加请求返回错误
- **THEN** Console 保留已展示事件，明确提示后续审计加载失败并允许重试，MUST NOT 清空台账或显示已到底

### Requirement: Console 审计分页必须保持账号隔离和开放枚举回落

Console SHALL 将每次审计首屏与追加请求绑定当前 `accountId`。切换账号、关闭抽屉、重新加载或写后刷新时 MUST 中止旧的追加请求；旧账号或已中止回包 MUST NOT 追加到当前台账。Audit action/entity wire 值 MUST 按开放字符串处理：已知值可显示中文，未知值 MUST 显示原值，MUST NOT 空白、猜测含义或使页面崩溃。

#### Scenario: 加载更多期间切换账号
- **WHEN** 账号 A 的审计追加请求尚未完成时运营切换到账号 B
- **THEN** A 请求被中止或其回包被丢弃，B 的台账只包含 B 的事件与 cursor

#### Scenario: Cloud 先增加审计动作枚举
- **WHEN** Cloud 返回当前 Console 未认识的 audit action 或 entity type
- **THEN** Console 显示该原始 wire 值与事件其他事实，页面和后续分页保持可用

### Requirement: 管理后台必须只读展示视频号互动权限与有效授权用户

internal panel API SHALL 在有效 panel JWT 之后提供固定六项视频号互动权限的只读概览。每项 MUST 包含稳定 permission key、中文名称、中文说明和当前有效授权用户名；有效授权用户名 MUST 同时存在于后台登录用户与该 permission 的 grants 中。响应 MUST NOT 包含密码、JWT、环境变量原文或已经失效的 actor。Console 设置页 SHALL 展示该概览并明确标记只读，MUST NOT 提供权限新增、删除或编辑动作。

#### Scenario: 设置页展示六项权限与授权用户
- **WHEN** 已认证后台用户打开设置页
- **THEN** Console 展示 `interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full` 与 `interaction.audit.view` 的名称和说明
- **AND** 每项展示当前有效授权用户名或明确的空状态

#### Scenario: 失效 actor 与凭据不泄漏
- **WHEN** grants 配置包含一个不在后台登录用户清单中的 actor
- **THEN** 权限概览不返回该 actor
- **AND** 响应不包含任何后台密码、JWT 或环境变量原文

#### Scenario: 权限概览只读
- **WHEN** 后台用户查看视频号权限设置
- **THEN** 页面不显示新增、删除、保存或编辑权限的控件
- **AND** Cloud 不为该能力提供权限变更写端点

#### Scenario: 权限概览故障不遮蔽其他设置
- **WHEN** 权限概览接口不可用或返回错误
- **THEN** Console 在权限卡片内诚实显示失败和重试入口
- **AND** 已加载的模型与凭据设置仍可查看和使用

### Requirement: 视频号回复设置必须以单一处理方式表达管理员意图

管理后台 SHALL 把 `mode`、`generateDrafts` 与 `sendReplies` 表达为一个账号级“回复处理方式”，只提供“不自动处理，仅收取互动”“只生成回复草稿”“人工审核后发送”“低风险模板自动发送”四种互斥选择。Console MUST 将选择确定性映射到冻结 DTO，MUST NOT 让普通管理员保存互相矛盾的自由组合；Cloud API schema 与硬门禁保持不变。

#### Scenario: 四种处理方式写入规范组合
- **WHEN** 管理员依次选择四种处理方式并保存策略草稿
- **THEN** Console 分别写入 `draft_only/false/false`、`draft_only/true/false`、`review_before_send/true/true`、`auto_safe/true/true` 的 `mode/generateDrafts/sendReplies` 组合

#### Scenario: 历史非规范组合按不扩权规则加载
- **WHEN** Cloud 返回生成关闭、发送关闭或仅草稿但发送开启等历史非规范组合
- **THEN** Console SHALL 显示不扩大当前写权限的处理方式，且未获管理员主动选择更高方式时保存 MUST NOT 把 false 权限静默改为 true

### Requirement: 渠道和规则配置必须只表达参与范围或进一步收紧

评论与私信的 `enabled` SHALL 呈现为“处理该渠道的互动”，并明确它不等于停止收取。渠道自动发送范围 MUST 仅在账号处理方式为低风险自动发送时展示。规则级 `allowAutoSend` SHALL 以“必须人工审核”的收紧语义呈现；启用 AI 润色的规则 MUST 强制人工审核，MUST NOT 向管理员暗示 AI 润色结果可以自动发送。

#### Scenario: 非自动模式不重复询问渠道自动发送
- **WHEN** 账号处理方式为不自动处理、只生成草稿或人工审核后发送
- **THEN** 评论和私信区域不展示“允许低风险自动发送”选择，渠道参与开关仍可独立配置

#### Scenario: 规则人工审核语义不提升权限
- **WHEN** 管理员勾选“此规则必须人工审核”或为规则启用 AI 润色
- **THEN** Console 写入 `allowAutoSend=false`；取消人工审核只恢复继承上层自动化上限，最终自动发送仍受渠道范围与全部 Cloud 硬门禁约束

### Requirement: 版本化策略、即时运行控制与系统硬门禁必须清晰分区

管理后台 SHALL 把需要保存并发布的回复策略、保存后立即生效的 runtime controls、不可关闭的 Cloud 硬门禁分成可辨识区域。账号写总闸、评论回复与私信文本发送 MUST 保留为即时刹车；Cloud RiskController、身份、capability、幂等和待核验门禁 MUST 保持只读且不可由普通管理员关闭。策略保存与原子发布边界 MUST 保留。

#### Scenario: 即时停写不伪装成策略模式
- **WHEN** 管理员关闭账号写总闸或某渠道即时写开关
- **THEN** Console 明确显示这是立即生效的运行控制，读取、草稿和已发布策略保持原语义，真实发送仍被 Cloud 拒绝

#### Scenario: 发布摘要只展示有效用户意图
- **WHEN** 管理员准备发布回复配置
- **THEN** 发布确认 SHALL 展示单一回复处理方式、渠道参与/自动范围和当前即时写状态，MUST NOT 再要求分别理解 `mode` 与“允许发送”重复开关

### Requirement: 模拟预览拒绝必须说明链路未运行

无副作用预览 SHALL 与真实发送设置分离。缺少 `interaction.config.preview` 时，Console MUST 明确说明 Cloud 预览链路未运行；私信预览缺少权限时 MUST 同时说明还需要 `interaction.dm.view_full`。权限拒绝 MUST NOT 被呈现为风险评审结果或发送硬门禁结果。

#### Scenario: 评论预览权限不足
- **WHEN** 评论预览返回 `INTERACTION_PERMISSION_DENIED`
- **THEN** Console 显示当前后台账号缺少模拟预览权限且本次预览未运行，不展示伪造的规则、模板或风险结果

#### Scenario: 私信预览需要额外原文权限
- **WHEN** 私信预览返回 `INTERACTION_PERMISSION_DENIED`
- **THEN** Console 显示私信预览同时需要 `interaction.config.preview` 与 `interaction.dm.view_full`，且本次预览未运行

### Requirement: 配置镜像健康按消费服务分域并暴露 delivery 新鲜度

`GET /api/config-mirrors` SHALL 分别返回 api 本地 health 与 automation health 投影，每段带
`sourceService`、source `asOf` 和 `deliveryState=fresh|stale|unknown|invalid`。automation health
delivery 不 fresh 时，整段 entries MUST 视为 unavailable；响应 MUST NOT 沿用旧 entry 的 `fresh`
值拼成全局健康结论。管理后台 SHALL 分域展示，不合并成单个“全部正常”状态。

#### Scenario: 两个消费服务状态不同

- **WHEN** api 本地 mirror fresh，而 automation 某 gate mirror stale
- **THEN** API 与管理后台分别显示两个 source service 的状态
- **AND** MUST NOT 聚合为全局 fresh

#### Scenario: automation health delivery 陈旧

- **WHEN** automation health snapshot 的 deliveryState 为 stale
- **THEN** API 将 automation 段标为 unavailable 并保留 source/delivery 时刻
- **AND** 管理后台 MUST NOT 展示旧 entries 为当前 fresh

### Requirement: Internal API 必须按账号管理 runtime controls 与版本化回复配置

internal panel API SHALL 提供 `interaction-runtime-controls`、`interaction-reply-policy`、`reply-templates`、`reply-rules`、`reply-profile`、`reply-preview`、`reply-config/publish` 与 `reply-config/audit` 冻结路径。所有路径 MUST 校验 account 存在且 `accounts.platform='wechat_channels'`；MUST 使用共享 internal schema 与统一 envelope，MUST NOT 复用 Facebook 专用表或让客户 JWT 访问。

#### Scenario: 非视频号账号不可写视频号配置
- **WHEN** 管理员对 XHS/Facebook account 调用 reply config 写端点
- **THEN** API 返回稳定 validation/platform mismatch，MUST NOT 创建配置行

#### Scenario: 客户 token 不能进入 internal config API
- **WHEN** 持 customer-auth token 请求任一 `/api/accounts/:accountId/reply-*` 端点
- **THEN** 内部 JWT 校验失败并返回 401，不读写配置

### Requirement: 配置权限必须区分查看编辑发布预览与敏感内容

internal API SHALL 使用显式 permission：`interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full`、`interaction.audit.view`。缺 permission MUST fail closed；普通排障/配置列表 MUST 不因 config view 权限获得 DM 原文。

#### Scenario: 编辑者不能越权发布
- **WHEN** actor 有 config.edit 但无 config.publish
- **THEN** 可保存 draft，publish 返回 403 且 published 指针不变

#### Scenario: 无 DM full permission 只见脱敏内容
- **WHEN** actor 有 audit/view 但无 `interaction.dm.view_full`
- **THEN** DM 正文被脱敏或省略，MUST NOT 通过错误、preview 或 audit details 泄漏

### Requirement: Draft 写与 publish 必须非乐观且原子

配置写 SHALL 携 aggregate `expectedVersion`；服务端验证成功并落库后才回显写后真态。version conflict 返回 409/currentVersion；schema、变量、规则冲突或硬门禁错误整块拒绝，MUST NOT 部分落库或前端假保存。publish SHALL 生成 immutable version 和 append-only audit。

#### Scenario: 规则冲突整块拒绝
- **WHEN** draft 请求同时包含合法 profile 和同优先级冲突规则
- **THEN** 整次写/发布返回 validation issues，MUST NOT 只保存 profile 或产生 published version

#### Scenario: 写成功回显服务端真态
- **WHEN** 合法 draft CAS 写入成功
- **THEN** 响应 data 含新 currentVersion/updatedAt/updatedBy，Console 以回显刷新而非本地假设

### Requirement: Preview 与 audit 必须无发送副作用并保护正文

preview SHALL 只运行规则、template、可选 AI 与 risk 链并返回 would-action，MUST NOT 创建真实 job/attempt 或发 WS。audit SHALL 记录 actor、版本、实体 ID、状态/diff 摘要；普通日志/audit MUST NOT 保存完整 DM、Cookie 或第三方原始响应。

#### Scenario: Preview 不触发 Edge
- **WHEN** 管理员预览一条模拟私信
- **THEN** Cloud 不向任何 Edge 发 interaction.reply.send，数据库无真实 inbound message/job/attempt

#### Scenario: Audit 可追溯但不含私信正文
- **WHEN** 管理员发布配置或查看预览审计
- **THEN** 可读 actor/version/rule/template/result tags，普通 audit 中没有模拟/真实私信全文

### Requirement: 限频四类安全配置的面板读回值必须来自权威服务

面板对安全限额、操作兜底 floor、单场会话上限与自动续场护栏这四类配置的读取 SHALL 透传权威服务（这四项归属自动化服务）的同一次求值结果。客户业务 API MUST NOT 为这四张表维护本地副本并用它回答面板读请求，MUST NOT 由异步复制的投影充当这四项的当前真值。

回包 SHALL 携带**数据时刻**（该值在权威侧被求出的时刻），与响应时刻分开表达。权威侧不可达时 MUST 以具名不可用态诚实回落，MUST NOT 展示上次已知值而不标注、MUST NOT 展示代码写死默认冒充当前生效值。

理由与慢启动投影必须与实际 clamp 同源同格一致：展示值与生效值一旦分两处求值，就一定会出现「后台显示的数字」与「闸实际按的数字」不一致，而这类不一致在界面上完全看不出来。

#### Scenario: 面板数字与生效数字逐格相等
- **WHEN** 运营在面板查看某档某动作的当前限额
- **THEN** 展示值与同一时刻自动化侧实际采用的值逐格相等，且回包标注该值的数据时刻

#### Scenario: 权威不可达时诚实不可用
- **WHEN** 自动化服务不可达，面板请求这四类配置
- **THEN** 接口返回具名不可用态，MUST NOT 返回上次已知值而不标注，MUST NOT 返回代码写死默认冒充当前生效值

#### Scenario: 内容排期目录不自行合成全局活跃掩码
- **WHEN** 面板请求内容排期目录，其中某账号未设活跃时段覆盖、需回落全局掩码
- **THEN** 该全局掩码取自权威侧的生效值，MUST NOT 由客户业务 API 侧的本地副本自行合成

### Requirement: 内部 Panel 环境管理不提供删除写面

内部 Panel SHALL 保留环境资产与历史 lifecycle 的读取能力，但 MUST NOT 注册或代理环境删除写端点，MUST NOT 调用 AdsPower，MUST NOT 创建删除申请或改变环境 lifecycle。对曾存在的 `POST /api/environments/:envKey/deletion` 的任何请求 SHALL 返回非成功结果且保持零删除副作用。

#### Scenario: 旧删除路径不再可用
- **WHEN** 内部管理员或旧 Console 请求 `POST /api/environments/:envKey/deletion`
- **THEN** 请求返回非成功结果，Cloud 不请求 AdsPower、不新增删除审计且不改变目标环境状态

#### Scenario: 环境资产读取保持可用
- **WHEN** 内部管理员读取环境列表、单环境影响信息或账号环境摘要
- **THEN** Panel 继续返回真实只读数据，包括已有历史 lifecycle，但不返回可执行删除动作

#### Scenario: 历史删除状态只读保留
- **WHEN** 数据库存在 deleting、delete_failed 或 deleted 历史行
- **THEN** Panel MAY 在只读查询中按真实状态展示，但 MUST NOT 自动重试、复活或推进这些行

### Requirement: Panel 平台凭据接口不提供 AdsPower API Key

`GET /api/config/model` SHALL 从平台凭据目录中省略 AdsPower API Key；`PUT /api/config/credential` 收到 `provider=adspower, field=api_key` SHALL 按未知或不允许的凭据拒绝，MUST NOT 新增、覆盖或读取 AdsPower 密文。其它已注册平台凭据行为保持不变。

#### Scenario: 设置读取不展示 AdsPower 凭据
- **WHEN** 管理员读取平台配置
- **THEN** 返回的凭据目录不包含 AdsPower API Key、掩码、来源或删除生效提示

#### Scenario: 旧客户端保存 AdsPower Key 被拒绝
- **WHEN** 旧 Console 向凭据端点提交 `provider=adspower, field=api_key`
- **THEN** Cloud 返回非成功结果且不写入或覆盖凭据数据

#### Scenario: 其它平台凭据不受影响
- **WHEN** 管理员读取或保存仍在允许列表中的模型或账单凭据
- **THEN** 其加密、掩码、来源与生效时机保持既有契约

### Requirement: Facebook 群组面板 API 管理区域通用评论模板

Panel API SHALL 提供区域通用评论模板目录读取及单区域完整模板集合替换写。读取 SHALL 返回区域、完整模板集合、更新时间和更新人；写入 SHALL 校验区域非空且当前存在于群目标目录、模板集合类型/数量/长度合法，并在数据库成功后返回回读真态。非法请求 MUST 整块拒绝，不得只保存部分模板。该接口 MUST 经由 automation 配置权威写入，不得在 API 组合根形成第二写者。

#### Scenario: 读取区域模板目录
- **WHEN** Console 打开 Facebook 群组配置
- **THEN** API 返回所有已配置区域的通用模板真态且不包含账号私有模板

#### Scenario: 替换一个区域的完整模板集合
- **WHEN** 运营为一个现有群区域提交两条合法模板
- **THEN** API 经权威写入并返回该区域恰好两条模板及数据库更新时间

#### Scenario: 非法模板写不产生部分成功
- **WHEN** 同一写请求中任一模板类型错误、超长或区域不存在
- **THEN** API 具名拒绝，原区域模板集合保持不变

### Requirement: 内部 Panel 提供环境慢启动配置投影与写接口

内部 Panel 环境资产响应 SHALL additive 返回直接来自 `client_environments.slow_start_since` 的环境慢启动配置，以及当前 Cloud 的全局停用真态。内部 Panel SHALL 在有效 Panel JWT 之后提供按 `envKey` 写入 `{ enabled: boolean }` 的慢启动接口；请求 MUST NOT 接受 `accountId`、起点时间、平台或其它选择器。

接口开启慢启动时 SHALL 仅在原值为 NULL 时写入服务器当前时刻所属上海自然日的 00:00，重复开启 MUST 保留原起点；关闭时 SHALL 清空环境起点。写入成功后 MUST 在回包前推进并刷新 `client_environment_slow_start` 镜像，使已缓存 RiskController 的下一次同步读可见新值。环境不存在、非 active 或非 Facebook 时 MUST 具名拒绝，MUST NOT 部分写入、重置起点或改变账号风控状态。

#### Scenario: 内部管理员首次开启环境慢启动

- **WHEN** 有效 Panel JWT 对 active Facebook 环境提交严格的 `{ "enabled": true }`
- **THEN** Cloud 写入上海当日 00:00 起点、刷新环境慢启动镜像并返回写后配置
- **AND** 未挂载账号不阻止该环境配置保存

#### Scenario: 重复开启保持原起点

- **WHEN** 已开启第 4 天的 Facebook 环境再次收到 `enabled=true`
- **THEN** 接口幂等返回开启状态，`slow_start_since` 保持原值，MUST NOT 重置为第 1 天

#### Scenario: 关闭环境慢启动

- **WHEN** 有效 Panel JWT 对已开启的 active Facebook 环境提交 `{ "enabled": false }`
- **THEN** Cloud 清空该环境的 `slow_start_since`、刷新镜像并返回关闭真态
- **AND** 账号风险状态、档位和旧账号慢启动列逐位不变

#### Scenario: 非法目标和非法请求 fail closed

- **WHEN** 环境不存在、生命周期非 active、平台不是 Facebook，或请求体包含非布尔值或额外选择器
- **THEN** 接口返回可区分的 4xx 拒绝且不修改任何环境慢启动字段

#### Scenario: 客户令牌无法调用内部写接口

- **WHEN** 持客户令牌请求内部 Panel 环境慢启动写接口
- **THEN** Panel JWT 校验拒绝请求，且不返回跨客户环境配置或写入结果

#### Scenario: 全局停用真态随资产投影返回

- **WHEN** `AIDCP_SLOW_START_DISABLED=true` 且一个环境的慢启动配置已开启
- **THEN** 资产响应同时返回该环境配置为开启与 `globallyDisabled=true`
- **AND** 接口 MUST NOT 把全局停用改写成环境配置关闭

