# Tasks

## 1. aidcp-cloud — 统一账号级群解析入口

- [x] 1.1 在 `src/server.ts` 的 `accountDisplayName` 附近新增 `resolveAccountChatId(accountId?: string): Promise<string>`，内聚注入 `accountStore` / `groupRouteStore` / `botChatStore` / `fallbackChatId: process.env.FEISHU_CHAT_ID` / `logger: console`，内部直调既有 `resolveChatIdForAccount`（`src/feishu/chat-target.ts` **一行不改**）。 <!-- aidcp-cloud 9498092 -->
- [x] 1.2 把现有唯一账号路由调用点（通知巡视 `notifyComments`）切到该 helper，消除两套注入写法并存。 <!-- aidcp-cloud 9498092 -->

## 2. aidcp-cloud — 6 处账号业务结果卡切到账号路由

> 每处只替换目标群解析，卡片内容 / 层级 / 错误处理不动；解析失败仍回落默认群、绝不静默丢卡。

- [x] 2.1 排期评论 / 排期联系评论**免审通知卡**（`autoApproveNotify`）改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 -->
- [x] 2.2 评论**终态结果卡**（`postResultCard`，含自动排期与人工 `/comment`）改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 人工 /comment 终态卡也随之落团队群（design 决策一）；命令受理回执与人审卡仍在管理群 -->
- [x] 2.3 **排期发帖结果卡**（`triggerPost`）改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 -->
- [x] 2.4 **排期评论触发回执**（`triggerComment` 的 `sendReceiptCard`）改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 -->
- [x] 2.5 **排期联系评论触发回执**（`triggerContactComment` 的 `sendReceiptCard`）改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 -->
- [x] 2.6 **参照创作结果卡**改用 `resolveAccountChatId`。 <!-- aidcp-cloud 9498092 -->
- [x] 2.7 确认审批卡（评论人审 / 发布审批）与运维告警（离线 / CDP 不健康 / 熔断 / 验证码 / 握手 config-error）**未被改动**，仍走默认群解析；`comm/handler.ts` 与 `publish-executor.ts` 的内联默认群链保持原样。 <!-- aidcp-cloud 9498092 改后 server.ts 仅余 5 处 resolveDefaultChatId：面板默认群标注 / 验证码协调器 / 发布下发运维告警 / 评论人审卡 / 握手 config-error —— 全部为审批或运维类 -->

## 3. aidcp-cloud — 测试

- [x] 3.1 单测：账号绑定团队时，排期发帖结果卡 / 评论终态结果卡的投递目标为团队群（非默认群）。 <!-- aidcp-cloud 9498092 偏离：6 处出口均在 startServer 巨函数闭包内，桩测无法在不起服务的前提下抵达；解析层已有覆盖（已绑定→团队群）。投递层改由 ECS 真库实证（见下）+ 真机 backlog 簇 63 -->
- [x] 3.2 单测：账号未绑定团队（或路由存储 undefined）时，同样两类卡仍投递到默认群、绝不丢。 <!-- aidcp-cloud 9498092 新增两例：groupRouteStore 未注入 → 落默认群且仍留 config-gap 线索；accountStore 未注入 → 落默认群、绝不抛入投递闭包 -->
- [x] 3.3 单测：审批卡与运维告警的目标**不受** `group_route` 映射影响（守住不外流边界）。 <!-- aidcp-cloud 9498092 以结构性方式守：这些出口调用的 resolveDefaultChatId 在类型上不接受 accountId / 不注入 groupRouteStore，无法被路由表影响 -->
- [x] 3.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。 <!-- aidcp-cloud 9498092 acceptance 50/50、全量 1921/1921、typecheck 干净 -->

## 4. 集成与部署

- [x] 4.1 合回 `aidcp-cloud` master（rebase，非 ff 一律 rebase 重来）。 <!-- aidcp-cloud 9498092 scripts/land-change ff 推送，709c894..9498092 -->
- [x] 4.2 部署 dev（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）。 <!-- 2026-07-14 deployed 部署前探 ECS：其 server.ts md5 == 709c894，无并发漂移；canonical 工作区有未跟踪残渣文件 `1`，按 §6 改用 `git archive HEAD` 干净快照 rsync（备份 cloud.bak.20260714-115358.tar.gz + .env.bak.20260714） -->
- [x] 4.3 部署后 healthcheck：服务 active、8787 监听、飞书长连接已建立、PG `select 1`。 <!-- 2026-07-14 deployed active + 8787 LISTEN + GroupRouteStore/AccountStore 已就绪 + 飞书长连接已建立（WSClient onReady） -->
- [x] 4.4 **部署后在 ECS 上用真实 dev 库跑解析实证**（超出原计划、加做）。 <!-- 2026-07-14 deployed 部署好的代码直连真库：默认群=oc_144e761f…（AI运营）；工程师大白 / Tmax（tom）→ oc_1c268549…（Tom.A）；小猫（YY）→ oc_f5c3f6fc…；阿柚（ninghao，其路由即默认群）→ 默认群。解析层坐实，投递层留真机 -->

## 5. 真机验收（登记 backlog，不在本 change 内闭环）

- [x] 5.1 dev 真机：触发一次「工程师大白」（`group_label=tom`）的排期发帖 / 排期评论，确认结果卡落「Tom.A」群而非「AI运营」群。 <!-- 已登记 docs/real-machine-acceptance-backlog.md 簇 63.1 / 63.2 -->
- [x] 5.2 dev 真机：确认审批卡与验证码 / 离线告警仍落「AI运营」群。 <!-- 已登记 簇 63.4 -->
- [x] 5.3 未在 `group_route` 绑定的账号，其业务结果卡仍落默认群且日志有 config-gap（若其 `group_label` 非空）。 <!-- 已登记 簇 63.5；另补登 63.3（人工 /comment 终态卡行为变更）与 63.6（机器人在团队群的发言权限） -->
