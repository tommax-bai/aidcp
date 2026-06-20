## ADDED Requirements

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

#### Scenario: 总览汇总走索引查询
- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 面板层用计数器的窗口查询 + 在线边缘数 + 风控状态点查组合返回，不执行阻塞事件循环的全表扫描

#### Scenario: 归因待补时不冒充按账号数字
- **WHEN** `accountId` 归因尚未在事件上流通，而 `GET /api/dashboard/summary` 被请求
- **THEN** 按账号切片被标记为「全部账号 / 归因待补」，绝不显示为按行的按账号数字

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
