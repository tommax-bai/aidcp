## Context

后台「账号」列要显示**小红书真实账号名称**，但坐实代码后发现：真实昵称今天**根本没被采集**。

- `accounts` 表（`../aidcp-cloud/src/account-store.ts:22-36`）无 nickname 列；seed `('default','default')`，`label` 是 `account_id` 副本。
- `accountId` 源自边缘 `AIDCP_ACCOUNT_ID`，运营字符串。
- 协议 `author`/`authorId`（`note.detail` / `profile.detail`，`protocol.ts:574-588`）描述的是**被浏览**对象，不是登录账号本身。

所以这是一条全新链路：**边缘采集登录账号自身昵称 → 上报 → 持久化 → 展示**，落点跨 edge / cloud / console 三仓 + 协议四处。

## Goals / Non-Goals

**Goals:**
- 边缘 DOM-first 读取**当前登录账号自身**昵称（不靠像素/截图），诚实失败（读不到不伪造）。
- 一条新 edge→cloud 上报消息把昵称带回云端。
- cloud 持久化到账号行（迁移 0012，可空、additive、不回填假值）。
- console 三处账号列展示真名（带回落链）。

**Non-Goals:**
- 不做主动「去采集昵称」的 cloud→edge 命令（YAGNI；趁边缘**本就**在自己主页/账号区时顺手采，避免新增 onMessage 白名单分支与多账号调度复杂度）。
- 不改 `account_id` 作为 PK，不动已 keyed 子表。
- 不做昵称历史版本表 / 改名审计（YAGNI；upsert 覆盖即可）。

## Decisions

### D1：采集时机与方式（edge，DOM-first + 诚实失败）

边缘在**已经身处自己主页 / 顶部账号区**的浏览路径上，顺手用 DOM 选择器读取**当前登录账号自身**的昵称文本（与「被浏览作者」严格区分：登录账号区域 ≠ 笔记/他人主页作者节点）。

- **读到** → 构造 `account.identity{ accountId, nickname, extracted: true }` 上报。
- **读不到 / 节点缺失** → **要么不发，要么发 `account.identity{ accountId, nickname: '', extracted: false }`**（`no_target` 式空信号），**绝不**用 `accountId` / `label` / 任意占位填充 nickname。
- **为何**：贯彻项目「边缘只原样执行、诚实硬失败、绝不静默假成功」的红线；昵称是展示字段，假值比缺失更糟（会让运营误以为采到真名）。

### D2：协议消息形状（edge → cloud 上报，非命令）

新增 `MessageType` 成员 `account.identity`（edge → cloud），payload：

```ts
export interface AccountIdentityPayload {
  /** 当前登录账号的运营标识（= AIDCP_ACCOUNT_ID，对齐 accounts.account_id） */
  accountId: string;
  /** 平台真实昵称；extracted=false 时为空串，云端忽略不写 */
  nickname: string;
  /** 是否成功从 DOM 抽到真实昵称；false=进了账号区但没抽到，诚实失败、绝不伪造 */
  extracted: boolean;
}
```

- 选 **edge→cloud 上报**而非 cloud→edge 命令：上报方向不经过 `edge-client.ts` 的 `onMessage` 控制命令白名单（第 4 处同步点是给 cloud→edge **主动控制命令**用的），因此**不引入** onMessage 改动，规避「漏白名单 → 静默丢弃 → 巡视挂死」的已知坑。
- 与既有上报对齐：`extracted` 标志沿用 `profile.detail.extracted`（`protocol.ts:587-588`）/ `note.detail` 同款「区分数据缺失 vs 真值」的口径。

### D3：cloud 持久化（迁移 0012，可空 additive）

- 迁移 **0012**：`ALTER TABLE accounts ADD COLUMN nickname TEXT`（**可空、无 DEFAULT、不回填**——缺失即 NULL，不造假名）。
- 消费 `account.identity`：仅当 `extracted === true && nickname.trim() !== ''` 时 `UPDATE accounts SET nickname = $1 WHERE account_id = $2`（upsert 覆盖最新真名）；否则**忽略**（保持现有 nickname，可能仍为 NULL）。
- `account-store.ts` 暴露 `setNickname(accountId, nickname)`；`PanelAccount`（`panel/panel-store.ts:28`）新增 `nickname: string | null`，join/`toAccount` 映射该列。

### D4：console 展示（回落链）

- `PanelAccount`（`../aidcp-console/src/types/api.ts:27`）新增 `nickname: string | null`。
- `AccountsTable.tsx:18` 账号列：`r.nickname ?? r.label ?? r.accountId`。
- `AccountTotalsTable.tsx:12` 账号列：由原始 `accountId` 改为真名优先回落。`AccountTotals`（`types/api.ts:55`）当前只有 `{accountId, totals}`，**无 label/nickname**——须先在 totals 查询（cloud `panel/queries.ts`）join `accounts.nickname` 并扩 `AccountTotals` 类型带出 `nickname`，渲染 `r.nickname ?? r.accountId`（此行无 `label`，不入回落链）。
- **为何回落链**：真名最优、其次运营 `label`、最后 `accountId` 兜底——保证无昵称账号仍可读，符合「不伪造」（NULL 时显示运营标识而非假名）。

## 协议四处同步清单（本 change 唯一协议改动方，逐项打勾后才算不漂移）

1. `../aidcp-edge/src/comm/protocol.ts`：加 `| 'account.identity'` 到 `MessageType` + `AccountIdentityPayload` 接口 + `MessageMap` 条目。
2. `../aidcp-cloud/src/comm/protocol.ts`：同上，**与 edge 逐字一致**（`Record<MessageType,true>` 穷举 + 两仓 `npm run typecheck` 暴露漂移）。
3. `../aidcp-cloud/src/comm/command-bridge.ts`：**无改动**——本消息是 edge→cloud 上报、不是动作 verb→message 下发映射；在 tasks 显式确认「无需新增映射」。
4. `docs/protocol.md`（本仓）：§2 消息表「Edge 上报」分组新增 `account.identity` 行 + payload 定义；同步头部 v2 计数 **56 → 57**。

附（仅当改为 cloud→edge 命令时才需，本 change 不触发）：`../aidcp-edge/src/client/edge-client.ts` `onMessage` 控制命令白名单——**本 change 选 edge→cloud 上报，故不涉及**。

## Risks / Trade-offs

- [采到「被浏览作者」而非登录账号自身] → D1 严格限定在登录账号区域选择器，与笔记/他人主页作者节点区分；抽错宁可 `extracted:false` 不写。
- [昵称含 emoji / 特殊字形入库异常] → 列为 `TEXT`，UTF-8 直存；展示层无字形约束（非发布标题，不涉及 `clampTitle` 字形安全）。
- [改名后旧名残留] → upsert 覆盖最新真名，单值即可（Non-Goal：不做历史版本）。
- [协议计数漂移] → 头部计数与 §2 表为人工维护，本 change 务必同步 56→57；以两份 protocol.ts 的 `MessageType` 穷举为准。

## Migration Plan

1. 协议：edge + cloud 两份 protocol.ts 同步加 `account.identity`（逐字一致）→ docs/protocol.md 同步 → 两仓 `npm run typecheck`（穷举不漂移）。
2. cloud：迁移 0012（加可空 nickname）→ 消费 `account.identity`（诚实写入）→ `PanelAccount.nickname` join。
3. edge：登录账号区昵称抽取 + 上报（诚实失败）。
4. console：类型 + 两表回落链。
5. 回归：两仓 `npm run test:acceptance`（含 `AC-PROTO-*` 两端一致）→ `npm test` → `npm run typecheck`。
6. 部署：cloud 按 §5 安全序列上 ECS（含 0012 迁移）；edge 本地运行。回滚：列可空、additive，回退代码即可，迁移列保留无害。

## Open Questions

- 登录账号自身昵称的具体 DOM 选择器（自己主页头部 vs 全局顶部账号区）——实装时按真机 DOM 定，落 `文件:行`。
- 是否需要一个最低重采频率（避免每次到主页都 upsert）——MVP 可每次覆盖（幂等、同值无害）；高频写入再加去抖。
- 多账号下 `accountId` 与登录态绑定的正确性（当前单 default 账号；item 9 的 nullable account_id seam 由 stream C 拥有，本 change 不动归因）。
