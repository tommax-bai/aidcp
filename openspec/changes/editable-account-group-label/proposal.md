## Why

管理后台账号列表的「分组」列一直显示破折号「—」：`accounts` 主表建表时预留了 `group_label` 列、面板 API 只读暴露、前端也渲染了这一列，但**全链路没有任何写入路径**（`ensureAccount` / `setPaused` / `setNickname` 都不碰它），也没有任何编辑入口，所以该列恒为 NULL、对运营毫无价值。运营需要一个直接、低成本的方式给账号打分组标签（按矩阵 / 项目 / 团队归堆），把这个占位列接通成可用功能。

## What Changes

- **账号存储新增一等「写分组」单写方法**：在拥有 `accounts` 表写的进程内对象上加 `setGroupLabel(accountId, label)`，与既有写昵称同构——按 `account_id` upsert、拒退役保留账号 `default`、空字符串归 NULL（即清空分组）、写后可回读真态。
- **面板 API 新增分组写路由**：受既有 JWT 保护的写接口（`PUT /api/accounts/:id/group-label`，body `{ groupLabel }`），经上面的单写方法落库并**返回写后回读的真态**，绝不面板层 raw UPDATE、绝不乐观假成功、拒绝与成功可区分。
- **前端「分组」列改为点击即编辑单元格**：点单元格 → 就地变自由文本输入框 → 回车 / 失焦保存（复用通知联系人页已有的「点击编辑」单元格模式）；非乐观、成功后刷新账号列表、诚实文案。只读账号表（仪表盘页）不传保存回调 → 保持纯文本、不受影响。
- **范围裁剪（YAGNI）**：本次只做自由文本 MVP；**不做**下拉选已有分组 + 新建、**不做**按分组筛选 / 批量操作、**不做**分组维度的配额 / 风控。权限沿用现状（单角色 JWT，任何登录运营可改），不引入新权限体系。

## Capabilities

### New Capabilities
<!-- 无新增能力：账号属性写入天然属于既有「后台写操作」能力域。 -->

### Modified Capabilities
- `console-write-operations`: 新增一条 Requirement——账号分组标签（`group_label`）编辑经账号存储的一等单写方法完成，面板层绝不 raw UPDATE、绝不乐观假成功、写后回读真态、拒绝（退役账号）与成功可区分；空输入归 NULL（清空）。这与该 spec 既有「写只经拥有者对象、诚实非乐观」的核心不变量同构。

## Impact

- **aidcp-cloud**：`src/account-store.ts`（`AccountStore` 接口 + `PgAccountStore` 加 `setGroupLabel`，schema 无需改——列已存在）；`src/panel/panel-server.ts`（新路由）+ `src/panel/types.ts`（`PanelServerDeps` 加账号属性写入依赖）；`src/server.ts` / `src/panel/index.ts`（注入 dep 指到账号存储）。测试：account-store 单写 + panel-server 路由。
- **aidcp-console**：`src/components/AccountsTable.tsx`（「分组」列改可编辑 + 新增可选保存回调 prop）；`src/pages/AccountsPage.tsx`（`useMutation` 打新接口、非乐观、`invalidate ['accounts']`、诚实 toast）；`src/pages/DashboardPage.tsx` 只读表不传回调（保持现状）；必要时复用 `styles/app.css` 的 `.editable-cell` 样式。
- **不触及**：风控最终状态单写路径、边-云 WebSocket 协议、边缘端、发布链、`accounts-master-data` 现有列定义（`group_label` 列已存在，加写者不与之矛盾）。
