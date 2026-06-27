## Why

后台「账号」列显示的是占位/运营字符串（实测单租户下就是 `default`），而不是登录账号的小红书真实昵称（如「工程师大白」）。坐实现状：

- `accounts` 主表（`../aidcp-cloud/src/account-store.ts`）只有 `account_id`(PK) / `label` / `platform` / `quota_level` / `status` / `machine_label` / `group_label`，**没有 nickname 列**；seed 行是 `('default','default')`，`label` 只是 `account_id` 的副本（ECS 实测全表仅 `default|default|xiaohongshu` 一行）。
- console 渲染 `r.label ?? r.accountId`（`../aidcp-console/src/components/AccountsTable.tsx:19`），多处账号面直接显示原始 `accountId`。
- `accountId` 现在来自**登录态读出的真实稳定 userid**（24 位 hex；`account-identity-from-login` 已落），`AIDCP_ACCOUNT_ID` 仅作可选覆盖——是稳定 ID、**不是平台昵称**。
- 协议里的 `author` / `authorId`（`note.detail` / `profile.detail`）描述的是**被浏览**对象，**不是当前登录的操作账号**。

结论：**当前登录账号自身的真实昵称在系统里任何地方都没有被采集**。要让后台显真名，必须新增「边缘采集登录账号自身昵称 → 上报 → 持久化 → 展示」这条链路。

> 本提案经一道多 agent 对抗评审（CLAUDE.md §3）打磨，相对初稿有重大纠偏（含一条红线 BLOCKER 修复），详见 design.md「Drift corrections」。

## What Changes

- **edge（采集，DOM-first + 诚实失败 + 红线：可证明属己）**：复用确立身份（握手 / 重确立身份）这一刻——边缘**本就**在 `readSelfIdentity` 里读账号信息——读取登录账号**自身**昵称。**关键修复**：必须**限定在自己头像所在的导航容器作用域内**读名字（与可靠读出自己 ID 同一作用域），**绝不**用现有那段无作用域全局查询（在推荐流页上会抓成被浏览作者的名字、配自己的 ID 存库 = 错配身份红线）。读不到 / 非自作用域 / override 与真实 id 不一致 → **省略昵称字段**，绝不伪造。
- **协议 v2（本 change 是协议唯一改动方）**：**不新增消息类型**——在**已有的握手消息 `HelloPayload`** 上加一个可选字段 `nickname?`（握手在身份可变的两个时刻自动重发）。消息计数**保持 56 不变**；不碰 `command-bridge`、不碰 `onMessage` 白名单。
- **cloud（持久化 + 消费 + 暴露）**：`accounts` 表新增可空列 `nickname`——**本仓无迁移执行器**，靠 store `init()` 的**幂等自愈 DDL**（`CREATE TABLE` 加列 + 追加 `ALTER TABLE … ADD COLUMN IF NOT EXISTS`，照 model-config 0018 先例；迁移号 **0021** 仅文档伴随）。握手处理里**按已认证连接账号、不阻塞握手、ON CONFLICT 自愈 upsert、非空才写**地持久化；`PanelAccount` 暴露 `nickname`。
- **console（展示）**：建一个纯诚实回落 helper `accountDisplayName(nickname, label, accountId) => nickname || label || accountId`，账号名各面统一走它。MVP：账号表 + 总表（客户端 join，不动 GROUP-BY）+ 发布历史（云端 label 折叠）+ 发布筛选 + 通知联系人选择器；人设页与监控/配额/用量等次要面 DEFER。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `accounts-master-data`: 新增一条要求「账号的平台真实昵称由边缘**诚实且可证明属己地**采集、随握手带回、持久化到账号行、并经面板 API + console 展示（读不到不伪造、绝不错配他人昵称）」。

## Impact

- **协议（本中控仓 + 两 sub-repo）**：
  - `../aidcp-edge/src/comm/protocol.ts` 与 `../aidcp-cloud/src/comm/protocol.ts`：`HelloPayload` 加可选 `nickname?: string`（两份**逐字一致**含注释）。**无新 MessageType 成员** → `Record<MessageType,true>` 穷举不变、计数不变。
  - `../aidcp-cloud/src/comm/command-bridge.ts`：**无改动**（hello 是握手、非动作 verb→message 映射）。
  - `docs/protocol.md`（本仓）：§3 hello payload 加 `nickname` 字段说明；**头部计数保持 56**（无新消息类型，`AC-PROTO-02` 无需改）。
- **edge（aidcp-edge）**：`src/cdp/self-identity.ts`（自作用域昵称读）；`src/client/edge-client.ts`（透传 + `setNickname` setter）；`src/main.ts`（握手 + 重确立身份按诚实闸传入）。
- **cloud（aidcp-cloud）**：`src/account-store.ts`（CREATE 加列 + 幂等 ALTER + `setNickname` 单写）；`src/comm/handler.ts`（onHello 非阻塞持久化，按 session.accountId）；`src/panel/panel-store.ts`（`PanelAccount.nickname` + 发布历史 accountLabel 折叠）+ `src/panel/types.ts`（镜像）；`migrations/0021_account_nickname.sql`（文档伴随）。
- **console（aidcp-console）**：`src/types/api.ts`（`PanelAccount.nickname`）；新增 `accountDisplayName` helper；`AccountsTable.tsx` / `AccountTotalsTable.tsx`（客户端 join）/ 发布筛选 / 通知联系人选择器走回落链。
- **红线 / 保留**：诚实失败（读不到不写、不伪造）；**可证明属己**（不把被浏览作者昵称误报/错存）；单写、不阻塞握手；不动 `account_id` 作为 PK 与已 keyed 子表；不引入 cloud→edge 新命令（不碰 onMessage 白名单）。
- **并发**：cloud 有并发 WIP（publish-multi-image 等）——只暂存本 change 自己的文件；迁移号落地前再核 0021 仍空；部署用干净 origin/master + 内容级 dry-run，绝不碰 isales。
