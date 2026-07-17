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

总览只读接口 `GET /api/dashboard/summary` SHALL 在响应中附带一个**服务端生成的数据新鲜度时间戳**（`asOf`，每次请求落地为该次查询的服务器当前时刻），并 SHALL 继续如实回报**在线边缘数**（`edgesOnline`，由活态在线边缘登记得出、死连接不计）。管理后台总览页 SHALL 用这两项把「系统当前没有新活动」与「界面冻结 / 看板坏了」**可视化区分**：

- SHALL 呈现「数据截至 `asOf` / 自动刷新中」一类的新鲜度标识，使运营一眼看出数据是按轮询实时拉取的（每轮刷新后 `asOf` 推进即证明界面在更新）；
- 当 `edgesOnline` 为 0 时 SHALL 呈现「系统当前未在浏览，故无新数据」一类的提示，把「没有新计数」如实归因为无边缘在浏览，而非伪造活跃感。

该呈现 MUST 诚实：MUST NOT 把「无新活动」粉饰为有数据流入，也 MUST NOT 在无边缘在线时显示虚构的进行中状态。本要求只触及**前端可读性与新鲜度暴露**：MUST NOT 改变互动计数的采集口径（不向互动 allow-list 增列 `view`），MUST NOT 在总览接口引入会阻塞事件循环的全表扫描或重聚合（沿用既有索引查询）。

#### Scenario: 总览响应带服务端新鲜度时间戳

- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 响应含一个服务端生成的 `asOf` 时间戳（该次查询的服务器当前时刻）与如实的 `edgesOnline`，且不执行阻塞事件循环的全表扫描

#### Scenario: 自动刷新时新鲜度标识推进，证明界面未冻结

- **WHEN** 后台总览页按轮询完成一次刷新且后端返回了更晚的 `asOf`
- **THEN** 页面上的「数据截至 …」标识推进到新的 `asOf`，运营据此判定界面在实时更新，即使各计数无变化

#### Scenario: 无边缘在线时如实提示无新数据来源

- **WHEN** 总览数据中 `edgesOnline` 为 0
- **THEN** 后台总览页显示「系统当前未在浏览，故无新数据」一类提示，把无新计数归因为无边缘在浏览，而非显示为界面故障或伪造活跃

#### Scenario: 诚实呈现，不粉饰无活动

- **WHEN** 当前无新互动产生（计数较上次无变化）
- **THEN** 后台如实呈现「数据已更新但无新活动」，MUST NOT 伪造活跃感，也 MUST NOT 改变互动计数采集口径（不把 `view` 加进互动 allow-list）

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

Cloud 的 `GET /api/content/queue` SHALL 在保留既有 `status`、`snapshot` 与 `runs` 字段的同时，返回面向管理后台的发布生命周期投影。该投影 SHALL 将每份稿件拆为触发与选题、正文生成、文本质检、视觉策划、出图复核、成稿封装、人工审批、平台下发八个阶段，并为每个阶段返回明确状态和可证实摘要。阶段状态 MUST 至少能区分未开始、进行中、重试中、等待人工、已完成、部分完成、失败与跳过。

生命周期投影 SHALL 组合当前 orchestrator runs、`publish_log` 持久化状态和 dispatcher 下发在途状态。管理后台 SHALL 优先使用该投影，将仍在生成、等待人工或正在下发的稿件展示在“活跃稿件”，将 published、submitted、failed、needs_review、draft、skipped 等终态展示在“最近结果”或发布历史；最近终态快照 MUST NOT 因存在 snapshot 而继续冒充活跃稿件。

该呈现 MUST 保持诚实：阶段完成 SHALL 由明确终点或持久化状态证明，不得因任意中间字段出现而声称整段完成；文本质检和视觉策划等真实并行分支 MAY 同时显示进行中；没有逐命令证据时不得臆造平台下发子步骤。原始 snapshot 字段 MUST 继续通过二级展开入口可见，供排障和未知未来字段检查。新字段 MUST 向后兼容，不得改变发布编排行为、审批授权或平台成功判定。

#### Scenario: 生成中的稿件显示八阶段投影

- **WHEN** 管理后台读取到一个 running orchestrator run，正文已经产出而文本质检与视觉策划尚未收敛
- **THEN** 活跃稿件 SHALL 显示该账号和稿件摘要，正文生成标记已完成，文本质检与视觉策划 MAY 同时标记进行中，其余阶段按依赖保持未开始

#### Scenario: 待审稿件明确等待人工

- **WHEN** `publish_log` 中一份稿件状态为 `pending_approval` 且其 record id 不在 dispatcher in-flight 集合
- **THEN** 该稿件 SHALL 位于活跃稿件，人工审批阶段标记等待人工，平台下发阶段标记未开始

#### Scenario: 已批准稿件显示平台下发中

- **WHEN** `publish_log` 中一份 `pending_approval` 稿件的 record id 位于 dispatcher in-flight 集合
- **THEN** 人工审批阶段 SHALL 标记已完成，平台下发阶段 SHALL 标记进行中，后台不得继续显示为单纯待审

#### Scenario: 下发失败离开活跃稿件

- **WHEN** 一份稿件的持久化状态从 `pending_approval` 变为 `failed`
- **THEN** 该稿件 MUST 从活跃稿件移入最近结果或发布历史，平台下发阶段标记失败，并明确不得声称已经发布

#### Scenario: 已提交但链接未确认显示部分完成

- **WHEN** 一份稿件的持久化状态为 `submitted` 且没有可验证的平台帖子链接
- **THEN** 平台下发阶段 SHALL 标记部分完成并显示“已提交，待链接确认”语义，不得标成失败或已发布

#### Scenario: 原始字段仍可展开排障

- **WHEN** 生命周期关联的生成 snapshot 中存在未被阶段摘要识别的顶层字段
- **THEN** 页面 SHALL 提供原始字段展开入口并显示该字段的序列化值，运营排障不需要翻服务器日志确认字段是否存在

#### Scenario: 空闲状态不伪造进度

- **WHEN** 生命周期投影没有 running、waiting_human 或 dispatching 稿件
- **THEN** 发布队列 SHALL 显示无活跃稿件，MUST NOT 因最近终态 snapshot 存在而渲染虚假的进行中阶段；最近终态 MAY 在独立的最近结果区域展示

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

