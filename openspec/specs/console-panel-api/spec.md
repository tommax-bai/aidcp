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

#### Scenario: 未携带有效 token 被拒
- **WHEN** 一个 `/api/*`（非登录）请求未带或带了过期 JWT
- **THEN** 面板层返回 401，不执行任何读或写

#### Scenario: 登录签发短 TTL token
- **WHEN** 凭 `.env` 内置用户的正确凭据请求 `POST /api/auth/login`
- **THEN** 面板层返回一个短 TTL 签名 JWT，后续 `/api/*` 凭它通过校验

### Requirement: 只读聚合接口非阻塞、组合现有存储与活态

面板只读接口 SHALL 组合已持久化存储（风控状态 / 计数器 / 发布记录 / 概念）与进程内活态（在线边缘登记、在途发布槽）产出视图，且 MUST 只用已有索引的点查/范围查询、MUST NOT 跑会阻塞事件循环的全表扫描或重聚合（避免给 `8787` 边缘命令下发加延迟）。MVP 接口至少含：`GET /api/version`、`GET /api/dashboard/summary`、`GET /api/accounts`、`GET /api/accounts/:id`、`GET /api/content/queue`、`GET /api/content/published`、`GET /api/analytics/like-rate`。

已发布历史接口 `GET /api/content/published` SHALL 在每条记录中返回 `accountId`、`content`（已发布正文全文）、`postUrl`（详情页链接，可空），以及既有 `id`/`title`/`status`/`platformPostId`/`publishedAt`；账号展示名 SHALL 取 `accounts.nickname ?? accounts.label ?? account_id`。该接口 SHALL 接受可选 `?accountId` 过滤，命中时凭 `publish_log.account_id` 既有索引做范围/点查、MUST NOT 退化为全表扫描。

#### Scenario: 总览汇总走索引查询
- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 面板层用计数器的窗口查询 + 在线边缘数 + 风控状态点查组合返回，不执行阻塞事件循环的全表扫描

#### Scenario: 归因待补时不冒充按账号数字
- **WHEN** `accountId` 归因尚未在事件上流通，而 `GET /api/dashboard/summary` 被请求
- **THEN** 按账号切片被标记为「全部账号 / 归因待补」，绝不显示为按行的按账号数字

#### Scenario: 已发布历史带账号、正文与详情链接
- **WHEN** 请求 `GET /api/content/published`
- **THEN** 每条记录含 `accountId`（及可解析的账号展示名）、`content` 全文、可空的 `postUrl`，以及既有字段；`postUrl` 缺失时为 null 而非伪造链接

#### Scenario: 按账号过滤已发布历史
- **WHEN** 请求 `GET /api/content/published?accountId=A`
- **THEN** 仅返回 `account_id = 'A'` 的已发布记录，查询走 `publish_log.account_id` 索引、不全表扫描

### Requirement: 面板 WebSocket 为纯只读事件扇出，与边-云 ws 物理隔离

面板层 SHALL 提供一个面板 WebSocket，订阅进程内事件总线，过滤为面板相关事件、归一化为统一帧（`docs/product-dashboard.md §2.3`），以**单一全局流 + 客户端过滤**推送给浏览器。它 MUST 是纯只读扇出：MUST NOT 与 edge 直接通信、MUST NOT 触碰 `ws-server.ts` 或边缘 socket，与边-云 `:8787` 物理隔离、逻辑复用事件流。面板 WS 连接 SHALL 经 JWT 鉴权（query 或首帧）。

#### Scenario: 实时日志流来自事件总线扇出
- **WHEN** 浏览器连上面板 WebSocket 并通过 JWT 鉴权
- **THEN** 它收到由事件总线过滤、归一化后的单一全局事件流，期间面板层从不向 edge 发送任何消息

#### Scenario: 面板 WS 不触碰边缘通道
- **WHEN** 面板 WebSocket 有活跃浏览器订阅
- **THEN** 边-云 `:8787` ws 与边缘 socket 不被面板层读写，两者物理隔离

### Requirement: enum 漂移哨兵——`/api/version` 暴露 live 枚举值

`GET /api/version` SHALL 返回面板 API 契约版本**与** live 枚举值（风控状态 / 档位 / 告警分级），作为前端 `aidcp-console` 的漂移哨兵。这些枚举值 MUST 与 `risk-control §7`、`product-exception §1` 同一套，使三处（cloud 实现 / console 镜像 / 文档）不漂移。

#### Scenario: 版本接口回传 live 枚举
- **WHEN** 请求 `GET /api/version`
- **THEN** 响应含面板契约版本与 live 的风控状态/档位/告警分级枚举值，供 console 端断言其镜像副本

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

