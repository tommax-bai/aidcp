## Context

`accounts` 主表建表时（change `aidcp-console-panel-mvp`）预留了 `group_label TEXT` 列（`aidcp-cloud/src/account-store.ts:38`），面板 API 在账号总览 join 里只读暴露为 `groupLabel`（`src/panel/panel-store.ts:170,184`），前端账号表也渲染了「分组」列（`aidcp-console/src/components/AccountsTable.tsx:44`，空值显示破折号）。但**全链路无任何写入路径**——`ensureAccount` / `setPaused` / `setNickname` 三个写入口都不碰 `group_label`，也没有面板写路由或前端编辑入口，故该列恒为 NULL。

约束来自既有 spec `console-write-operations` 的核心不变量：**后台所有写操作只经「已经拥有该写的进程内对象」，绝不 raw SQL UPDATE 绕过所有者，绝不乐观假成功，且返回写后真态、拒绝与成功可区分。** `accounts` 表行属性的拥有者是账号存储（`PgAccountStore`，已持有 `setPaused` / `setNickname` / `ensureAccount`）。

## Goals / Non-Goals

**Goals:**
- 让运营在管理后台账号列表里点击「分组」单元格、就地自由文本输入、回车 / 失焦保存、空输入清空分组。
- 写链路遵守 `console-write-operations` 不变量：经账号存储一等单写方法、写后回读真态、诚实非乐观、拒绝可区分。
- 把已存在但从未接线的 `group_label` 列接通成可用功能，最小侵入。

**Non-Goals:**
- 下拉选已有分组 + 新建（自由文本 MVP 先行）。
- 按分组筛选 / 排序 / 批量操作。
- 分组维度的配额 / 风控 / 调度语义。
- 新权限体系（沿用单角色 JWT，任何登录运营可改）。
- 触及风控最终状态单写、边-云协议、边缘端、发布链。

## Decisions

### 决策 1：写经账号存储一等方法 `setGroupLabel`，绝不面板层 raw UPDATE
在 `AccountStore` 接口与 `PgAccountStore` 上新增 `setGroupLabel(accountId, label: string | null)`，与 `setNickname` 同构。面板层只经注入的依赖闭包调用它，**不持有也不使用**对 `accounts` 表的 raw UPDATE 能力。
- **为何**：直接命中 `console-write-operations` 的核心不变量（写只经拥有者对象）。账号存储是 `accounts` 表的单一拥有者，把属性写收口在这里，与现有 `setPaused`/`setNickname` 一致。
- **备选**：面板层直接跑 `UPDATE accounts ...`——被 spec 明确禁止（raw UPDATE 绕过所有者），弃。

### 决策 2：UPDATE-only + `RETURNING`，不 upsert-seed；缺行 = 诚实 not-found
`setGroupLabel` 用 `UPDATE accounts SET group_label=$2 WHERE account_id=$1 RETURNING group_label`，返回回读的真值；无行返回则表示账号不存在，接口回 404 / `{error:'account_not_found'}`。
- **为何**：分组永远是从「已存在的账号行」上编辑，不存在握手竞态；UPDATE-only 天然满足「写后回真态」与「拒绝可区分」，且不会因误传 id 造出幽灵账号行。这一点与 `setNickname` 的「行不存在时连带 seed」不同——那是系统驱动、有握手竞态，这里是运营对既有行的属性编辑。
- **备选**：upsert-seed（照抄 setNickname）——会在传入不存在 id 时静默造行，与「拒绝可区分」相悖，弃。

### 决策 3：独立写路由 `PUT /api/accounts/:id/group-label`，不塞进 `/command`
新增 `PUT /api/accounts/:id/group-label`，body `{ groupLabel: string | null }`；经 `PanelServerDeps` 新增的账号属性写入依赖落库、返回写后真态。
- **为何**：`POST /api/accounts/:id/command` 语义是 durable 运营命令（pause/resume），复用共享 `CommandActions` 闭包；分组是纯属性编辑，语义不同、所有者不同（账号存储 vs 命令闭包），独立路由更清晰、PUT 语义贴合「设置某属性」。JWT 已覆盖全部非公开 `/api/*`，无需额外鉴权接线。
- **备选**：扩展 `/command` 加 `command:'set_group'`——混淆命令与属性两种语义、错挂到命令闭包所有者，弃。

### 决策 4：空 / 纯空白输入归 NULL（清空分组）
`setGroupLabel` 对入参 `trim`：trim 后为空即写 NULL；否则写 trim 后的值。路由层把 `groupLabel` 为 `''` / `null` / 缺省一律视作「清空」。
- **为何**：给运营一个直观的「清除分组」路径（清空输入即取消分组），且避免存入纯空白造成「看似有分组实为空白」的脏值。

### 决策 5：前端非乐观，复用既有「点击编辑」单元格模式
「分组」列渲染改为可点击编辑单元格，复用通知联系人页已有的 `.editable-cell`「点击编辑」交互（`aidcp-console/src/pages/NotificationContactsPage.tsx`）。保存回调由 `AccountsPage` 持有的 `useMutation`（打新接口）向下传给 `AccountsTable`；**非乐观**——round-trip 成功后 `invalidateQueries(['accounts'])` 拉真态、诚实 toast。`AccountsTable` 新增**可选** `onEditGroup` prop：不传则「分组」列退回纯文本（仪表盘只读表保持现状、不受影响）。
- **为何**：与后台既有交互一致、零新范式；可选 prop 保证只读视图零回归；非乐观贴合 `console-write-operations` 的「绝不乐观假成功」。

## Risks / Trade-offs

- **[自由文本 → 分组名不一致（大小写 / 错字把同一组拆成多组）]** → MVP 接受；后续可升级为下拉选已有分组 + 新建（聚合现有 `group_label` 去重当选项）。设计已按此预留干净扩展缝（写方法与接口形状不变，仅前端输入控件替换）。
- **[两名运营并发编辑同一账号分组]** → last-write-wins。`group_label` 是无复合状态的纯属性列（不同于风控状态的 mutation 队列需求），后写覆盖先写可接受，无 lost-update 正确性问题。
- **[误传不存在的 account_id]** → UPDATE-only + `RETURNING` 使其回 not-found、可区分，不造幽灵行。
- **[退役保留账号 `default`]** → `setGroupLabel` 显式拒绝 `RETIRED_ACCOUNT_ID`（与 `setPaused` 同款守卫），不写、不静默成功。
