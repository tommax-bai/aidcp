## Why

结构化建草稿入口（后台面板 `/api/delegated-tasks/draft`、客户端 `/delegated-tasks/draft`）把客户端请求体原样铺进创建逻辑，**从不校验 `approvalMode`**；加上非飞书来源自动入队跳确认卡，一个带 `approvalMode:'auto_approve'` 的请求体就能让内容**两道审批闸全绕过**、直达平台——即使该账号设的是「必审」。免审本应只由账号级后台开关授予，不该是客户端可自选的字段。当前出货界面都硬编码 `review`／`draft_only` 没触发，但**服务端无条件信任**，是潜伏的信任缺口。

## What Changes

- 新增 `clampClientApprovalMode(mode)`：缺省→未定（交由 store 按动作取默认）；`draft_only`→`draft_only`（仅生成候选、不落平台）；其余（含 `auto_approve` 与任何未来新模式）→`review`。
- 在两处 HTTP 建草稿边界应用该收口（面板路由、客户端路由）。**服务端自建 intent**（后台洗稿 / 候选控制显式传 `review`、飞书 parser 硬编码 `review`）不经此路，零回归。

## Impact

- `aidcp-cloud`：`delegated-task/types.ts`（新 helper）、`panel/panel-server.ts`、`client-auth/client-auth-server.ts`（两边界收口）；单测 `delegated-task/types.test.ts`。
- `aidcp`：本 OpenSpec change 收紧 `user-delegated-tasks` 的结构化入口审批模式契约。
- 不涉及边云协议、风控写、热点单写文件。
- 真机验收：构造带 `auto_approve` 的结构化 draft 请求，断言不写审批信号、无免审直发 → 簇 86。
