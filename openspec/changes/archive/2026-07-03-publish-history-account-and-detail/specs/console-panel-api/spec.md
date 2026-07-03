## MODIFIED Requirements

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
