> **本 change = 协议唯一改动方**，但 add-to-hello 下协议改动极小（`HelloPayload` 加一个可选字段，**无新 MessageType**，计数不变 56）。仅本 change 可改两份 `protocol.ts` 的 `HelloPayload` + `docs/protocol.md`。
> **迁移号 0021**（`migrations/` 已有 0001-0011、0013-0019；**不用 0012**——低于当前最大号的空号会误导；**0020 已被并发 session-auto-resume 的 `0020_resume_config` 占用**，故取 0021）。本仓**无迁移执行器**，真正生效靠 `account-store init()` 的幂等 ALTER，`.sql` 仅文档伴随。
> **并发纪律**：cloud / 本仓有并发 WIP（publish-multi-image、session-auto-resume 等）。提交只暂存本 change 自己的文件（见 [[precise-git-add-concurrent-sessions]]）；实测已精确暂存、未裹挟他人 WIP。
>
> **进度（2026-06-27）**：代码全落 + 隔离验证全绿。edge `28ba097` / cloud `95f3db6` / console `b8484ce` / 本仓本 commit。剩真机探针(0.1) + 真机 E2E(5.4) + 部署(6.3) + 归档(6.4)，均 gated/显式动作。

## 0. 真机前置探针（决定 edge 采集形态）

- [ ] 0.1 跑只读探针 `../aidcp-edge/scripts/self-identity-probe.ts`（已登录工程师大白、独立 Chrome on 9222），确认：网页左栏/顶部账号区头像旁**是否暴露登录用户昵称文本**。命中 → 就地零跳转自作用域读；不命中 → 仅 navigate/重确立路径读，并在 5.4 验收标准诚实写明命中场景 <!-- GATED：需真机已登录账号 -->

## 1. aidcp-edge — 登录账号自身昵称采集（DOM-first、自作用域、诚实失败） <!-- edge 28ba097 -->

- [x] 1.1 `src/comm/protocol.ts`：`HelloPayload` 加 `nickname?: string` + 注释；与 cloud 逐字一致；**不**新增 MessageType <!-- edge 28ba097 -->
- [x] 1.2 `src/cdp/self-identity.ts`：昵称读改**自作用域**——`IN_PLACE_SCAN_JS` 在 `navScope` 内取 nickname/redId；in-place 返回用 `signals.nickname`，**不调**无作用域 `readDisplay`；navigate 路径在自己主页读保留作兜底 <!-- edge 28ba097 红线修复 -->
- [x] 1.3 `src/client/edge-client.ts`：`EdgeClientOptions` 加 `nickname?`；hello 携带；`setNickname()` setter <!-- edge 28ba097 -->
- [x] 1.4 `src/main.ts`：握手 + 重确立身份按诚实闸传入 nickname（`idRes.ok && displayName 非空 && decision.kind==='use' && !mismatch`） <!-- edge 28ba097 -->
- [x] 1.5 确认 edge→cloud 握手、不引入 cloud→edge 命令 → **未改** onMessage 白名单 <!-- edge 28ba097 确认无改 -->

## 2. aidcp-cloud — 持久化（自愈 DDL）+ 消费 + 面板暴露 <!-- cloud 95f3db6 -->

- [x] 2.1 `src/comm/protocol.ts`：`HelloPayload` 同步加 `nickname?`，与 edge 逐字一致；穷举不变 <!-- cloud 95f3db6 -->
- [x] 2.2 `src/comm/command-bridge.ts`：**确认无改动**（hello 是握手、非动作映射） <!-- cloud 95f3db6 未改、确认 -->
- [x] 2.3 `src/account-store.ts`：`CREATE TABLE` 加 `nickname TEXT` + 追加幂等 `ALTER … ADD COLUMN IF NOT EXISTS nickname TEXT`（init() 自愈） <!-- cloud 95f3db6 -->
- [x] 2.4 `src/account-store.ts`：`setNickname` 单写 `INSERT … ON CONFLICT DO UPDATE`，拒空白 + 防御性长度上限 <!-- cloud 95f3db6 -->
- [x] 2.5 `src/comm/handler.ts` onHello：按 `session.accountId` 持久化、仅非空写、**try/catch fire-and-forget 不阻塞握手**；`recordAccountNickname` 依赖经 server.ts 接线 <!-- cloud 95f3db6 -->
- [x] 2.6 `src/panel/panel-store.ts`：`PanelAccount`/`AccountJoinRow`/`toAccount` 加 `nickname`，`ACCOUNT_SELECT` 加 `a.nickname`（无新 join）；发布历史 accountLabel 折叠 `nickname ?? label ?? account_id`。（`panel/types.ts` 无 PanelAccount，API 直接返回 panel-store 类型，无需镜像） <!-- cloud 95f3db6 -->
- [x] 2.7 `migrations/0021_account_nickname.sql`：文档伴随（非执行） <!-- cloud 95f3db6 -->

## 3. docs — 协议文档同步（本仓） <!-- 本仓本 commit -->

- [x] 3.1 `docs/protocol.md`：§3 hello payload 加 `nickname` 字段说明 <!-- 本仓 -->
- [x] 3.2 `docs/protocol.md`：头部 v2 消息计数**保持 56 不变**（无新 MessageType）——已确认不改 <!-- 本仓 -->

## 4. aidcp-console — 账号名展示真名（统一回落 helper） <!-- console b8484ce -->

- [x] 4.1 `src/types/api.ts`：`PanelAccount` 加 `nickname: string | null` <!-- console b8484ce -->
- [x] 4.2 新增 `src/types/accountDisplay.ts`：`accountDisplayName(nickname,label,accountId) => nickname||label||accountId`（绝不造假） <!-- console b8484ce -->
- [x] 4.3 `src/components/AccountsTable.tsx`：账号列走 helper（覆盖 Dashboard + Accounts） <!-- console b8484ce -->
- [x] 4.4 `src/components/AccountTotalsTable.tsx`：**客户端 join**（`DashboardSummary.accounts` → 名）渲染 `nickname ?? accountId`，**未**加宽服务端 GROUP-BY；两处调用站点（Dashboard/Monitor）已传 accounts <!-- console b8484ce -->
- [x] 4.5 Tier2：发布筛选下拉、通知联系人页**账号选择器**走 helper（**未**碰联系人「昵称」列）；发布历史列/抽屉由 2.6 云端折叠覆盖、console 零改 <!-- console b8484ce -->
- [ ] 4.6 DEFER（记录、不做）：人设页 DTO 加宽 + 监控/Dashboard 告警与互动列 + 配额页 + 用量页（accountId-only DTO） <!-- DEFER (YAGNI) -->

## 5. 验证（红线 + 回归）

- [x] 5.1 typecheck：edge `npm run typecheck` 全绿；cloud 本 change 6 源文件 typecheck 干净（全项 typecheck 受并发 WIP publish-agent/role-dispatcher 污染、非本 change）；console `tsc --noEmit && vite build` 绿 <!-- 06-27 -->
- [x] 5.2 acceptance：edge 11/11；cloud 26/26（`AC-PROTO-*` 计数仍 56、两端一致 / `AC-RISK-*` / publish-approval / search 全过） <!-- 06-27 -->
- [x] 5.3 测试：edge `npm test` 365/365（含 3 新 self-identity 红线用例）；cloud 隔离跑本 change 相关 41+23 用例（account-store/handler/handler-attribution/panel-server/panel-store + 新增 setNickname/onHello 持久化/不阻塞握手）全绿。cloud 全量 `npm test` 受并发 WIP 阻塞（publish-agent/role-dispatcher 半成品），非本 change <!-- 06-27 隔离验证 -->
- [ ] 5.4 真机 E2E（gated）：登录账号自作用域采到真名 → 随 hello 上报 → PG `accounts.nickname` 落值 → console 显示真名；读不到不伪造、不错配。**归档以真机命中率为闸** <!-- GATED -->

## 6. 收尾与归档

- [x] 6.1 按 sub-repo 分节回写进度（本文件 + shas） <!-- 本仓 -->
- [x] 6.2 `openspec validate account-real-nickname --strict` 通过 <!-- 06-27 valid -->
- [ ] 6.3 cloud 按 CLAUDE.md §5 安全序列部署 ECS（干净 origin/master + 内容级 dry-run + 备份 + 重启 + healthcheck 确认 nickname 列已加 + default 行 NULL；绝不碰 isales） <!-- GATED：显式部署动作 -->
- [ ] 6.4 `/opsx:archive` 归档（delta 合并进 `openspec/specs/accounts-master-data`） <!-- 待 6.3 + 5.4 -->
