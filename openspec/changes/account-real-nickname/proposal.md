## Why

后台「账号」列显示的不是小红书真实账号名称，而是运营字符串。坐实现状：

- `accounts` 主表（`../aidcp-cloud/src/account-store.ts`）只有 `account_id`(PK) / `label` / `platform` / `persona_ref` / `quota_level` / `status` / `machine_label` / `group_label`，**没有 nickname 列**；seed 行是 `('default','default')`，`label` 只是 `account_id` 的副本（ECS 实测全表仅 `default|default|xiaohongshu` 一行）。
- console 渲染 `r.label ?? r.accountId`（`../aidcp-console/src/components/AccountsTable.tsx:18`），总表直接显示原始 `accountId`（`../aidcp-console/src/components/AccountTotalsTable.tsx:12`）。
- `accountId` 来自边缘环境变量 `AIDCP_ACCOUNT_ID`，是**运营标识字符串，不是平台昵称**。
- 协议里的 `author` / `authorId` 字段描述的是**被浏览**的笔记/主页作者（`note.detail` / `profile.detail`），**不是当前登录的操作账号**。

结论：**当前登录账号自己的真实昵称在系统里任何地方都没有被采集**。要让后台显示真名，必须新增「边缘采集登录账号自身昵称 → 上报 → 持久化 → 展示」这条链路。

## What Changes

- **edge**：在已经身处自己主页 / 顶部账号区时（DOM-first），从页面读取**当前登录账号自身的昵称**，并通过一条**边缘 → 云端上报消息**回报。遵守项目「诚实硬失败」哲学：读不到就**什么都不报 / 报一个 `no_target` 式空信号**，**绝不派生 / 伪造昵称**。
- **协议 v2（本 change 是协议唯一改动方）**：新增一条**边缘 → 云端上报**消息类型 `account.identity`（携带 `accountId` + 真实 `nickname` + `extracted` 诚实标志）。优先选 edge→cloud 上报（不需要碰 `onMessage` 白名单），不引入 cloud→edge 新命令。四处同步见 design.md。
- **cloud**：`accounts` 表新增可空列 `nickname`（迁移 **0012**，additive、可空、不回填假值）；收到 `account.identity` 且 `extracted===true && nickname` 非空时 upsert 到该账号行；`PanelAccount` 暴露 `nickname`。
- **console**：`PanelAccount` 类型加 `nickname`；`AccountsTable` 与 `AccountTotalsTable` 的「账号」列改为 `nickname ?? label ?? accountId` 回落链。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `accounts-master-data`: 新增一条要求「账号的平台真实昵称由边缘诚实采集、持久化到账号行、并经面板 API + console 展示（读不到不伪造）」。

## Impact

- **协议（本中控仓 + 两 sub-repo，四处同步）**：
  - `../aidcp-edge/src/comm/protocol.ts` 与 `../aidcp-cloud/src/comm/protocol.ts`：新增 `MessageType` 成员 `account.identity` + `AccountIdentityPayload`（两份**逐字一致**，`Record<MessageType,true>` 穷举 + typecheck 保证不漂移）。
  - `../aidcp-cloud/src/comm/command-bridge.ts`：本消息为 edge→cloud 上报、**非动作下发**，无 verb→message 映射改动；仅在 design 清单中显式确认「无需新增映射」。
  - `docs/protocol.md`（本仓）：消息表新增 `account.identity` 行 + payload 定义；头部 v2 计数 56 → 57。
- **edge（aidcp-edge）**：在登录账号自身主页/账号区的浏览路径上新增一次昵称 DOM 抽取 + 上报（诚实失败、不伪造）。
- **cloud（aidcp-cloud）**：`src/account-store.ts`（迁移 0012：`ALTER TABLE accounts ADD COLUMN nickname TEXT` 可空 + upsert API）；`src/comm/`（消费 `account.identity`）；`src/panel/panel-store.ts`（`PanelAccount.nickname` + join/`toAccount` 映射）。
- **console（aidcp-console）**：`src/types/api.ts`（`PanelAccount.nickname`）；`src/components/AccountsTable.tsx` 与 `src/components/AccountTotalsTable.tsx`（账号列回落链）。
- **并发协调（5 流并行）**：本流（B）**独占协议四处**（其他流不得触碰 protocol.ts / command-bridge.ts / docs/protocol.md / edge-client.ts onMessage）；迁移号锁定 **0012**；共享 chokepoint 文件按 C→D→F→B 顺序**追加**（`panel-store.ts` / `panel/types.ts` / console `types/api.ts` / `queries.ts`），本流最后落。
- **红线 / 保留**：诚实失败（读不到昵称不写、不伪造）；不动 `account_id` 作为 PK 与已 keyed 子表；不引入 cloud→edge 新命令（不碰 onMessage 白名单）。
