> **并发协调（5 流并行，本流 = B account-real-nickname）**
> - **协议红线独占**：本流是协议唯一改动方。**仅本流**可改 `../aidcp-edge/src/comm/protocol.ts`、`../aidcp-cloud/src/comm/protocol.ts`、`../aidcp-cloud/src/comm/command-bridge.ts`、本仓 `docs/protocol.md`（以及若改用 cloud→edge 命令时的 `../aidcp-edge/src/client/edge-client.ts` onMessage 白名单）。其他流（A/C/D/F）MUST NOT 触碰这些文件。
> - **迁移号锁定 0012**：本流用 accounts.nickname 迁移 = **0012**（C=0009 / D=0010 / F=0011 / B=0012）。勿占他流号。
> - **共享 chokepoint 文件按 C→D→F→B 顺序追加，本流最后落**：`../aidcp-cloud/src/panel/panel-store.ts`、`../aidcp-cloud/src/panel/types.ts`、`../aidcp-console/src/types/api.ts`、`../aidcp-console/src/api/queries.ts` 只 **APPEND**，不重写他流块；server.ts 的 model-resolver 块归 C，本流不碰。
> - **cloud src/server.ts**：本流如需 store-init 接线只在 C 之后 APPEND，绝不动 C 的 resolver 块。

## 1. aidcp-edge — 登录账号自身昵称采集 + 上报（DOM-first、诚实失败）

- [ ] 1.1 `src/comm/protocol.ts`：`MessageType` 加 `| 'account.identity'`（edge→cloud 上报）+ `AccountIdentityPayload`（`accountId` / `nickname` / `extracted`）+ `MessageMap` 条目；与 cloud 侧**逐字一致**
- [ ] 1.2 在登录账号自身主页/账号区的浏览路径上新增一次 DOM 抽取：读取**登录账号自身**昵称（与被浏览作者节点严格区分）
- [ ] 1.3 诚实失败：读到 → 上报 `{accountId, nickname, extracted:true}`；读不到 → 不发或发 `{nickname:'', extracted:false}`，**绝不**用 accountId/label/占位伪造
- [ ] 1.4 确认本消息是 edge→cloud 上报、不引入 cloud→edge 命令 → **不改** `src/client/edge-client.ts` onMessage 白名单

## 2. aidcp-cloud — 持久化（迁移 0012）+ 消费上报 + 面板暴露

- [ ] 2.1 `src/comm/protocol.ts`：同步加 `account.identity` + `AccountIdentityPayload` + `MessageMap`，**与 edge 逐字一致**（`Record<MessageType,true>` 穷举）
- [ ] 2.2 `src/comm/command-bridge.ts`：**确认无改动**——edge→cloud 上报非动作 verb→message 映射（在 tasks 显式记「无需新增映射」）
- [ ] 2.3 `src/account-store.ts`：迁移 **0012** `ALTER TABLE accounts ADD COLUMN nickname TEXT`（可空、无 DEFAULT、不回填）+ `setNickname(accountId, nickname)` upsert API
- [ ] 2.4 消费 `account.identity`：仅 `extracted===true && nickname` 非空时 `setNickname`；否则忽略保持现值
- [ ] 2.5 `src/panel/panel-store.ts`：`PanelAccount` 加 `nickname: string | null`，join/`toAccount` 映射该列（APPEND，不动他流块）

## 3. docs — 协议文档同步（四处同步第 4 处，本仓）

- [ ] 3.1 `docs/protocol.md`：§2「Edge 上报」分组新增 `account.identity` 行 + payload 定义
- [ ] 3.2 `docs/protocol.md`：头部 v2 消息计数 **56 → 57** 同步（以两份 protocol.ts `MessageType` 穷举为准）

## 4. aidcp-console — 账号列展示真名（回落链）

- [ ] 4.1 `src/types/api.ts`：`PanelAccount` 加 `nickname: string | null`（APPEND）
- [ ] 4.2 `src/components/AccountsTable.tsx`：账号列改 `r.nickname ?? r.label ?? r.accountId`
- [ ] 4.3 `src/components/AccountTotalsTable.tsx`：账号列由原始 `accountId` 改为真名优先回落链。注意 `AccountTotals` 类型当前只有 `{accountId, totals}`，**没有 label/nickname 字段**——必须先在 totals 数据源（cloud `panel/queries.ts` 总表查询 join `accounts.nickname`）+ `AccountTotals` 类型上带出 `nickname`，渲染才能 `r.nickname ?? r.accountId`（`label` 不在此行，故不进此处回落链）

## 5. 验证（协议红线 + 回归）

- [ ] 5.1 两仓 `npm run typecheck`（两份 protocol.ts 不漂移、`Record<MessageType,true>` 穷举通过）
- [ ] 5.2 两仓 `npm run test:acceptance`：`AC-PROTO-*`（两端 protocol.ts 一致、消息类型数对齐 57）必过
- [ ] 5.3 两仓 `npm test` 全量绿；新增/调整覆盖：诚实失败不写入、`extracted:false` 被忽略、回落链展示
- [ ] 5.4 真机 E2E（可 gated）：登录账号主页采到真名 → 上报 → PG `accounts.nickname` 落值 → console 显示真实昵称；读不到时不伪造

## 6. 收尾与归档

- [ ] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 6.2 `openspec validate account-real-nickname --strict` 通过
- [ ] 6.3 cloud 改动按 CLAUDE.md §5 安全序列部署 ECS（含 0012 迁移 healthcheck）
- [ ] 6.4 `/opsx:archive` 归档（delta 合并进 `openspec/specs/accounts-master-data`）
