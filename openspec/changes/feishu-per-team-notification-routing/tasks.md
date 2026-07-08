<!-- 进度按 sub-repo 分节回写本仓；代码改动落 aidcp-cloud / aidcp-console。标 [x] 时附 <!-- <repo> <sha> 备注 -->，部署后追加 <!-- <date> deployed -->。 -->

## 1. aidcp-cloud — 存储与解析基座

- [ ] 1.1 新建 `src/cache/group-route-store.ts` + 表 `group_route(group_label TEXT PRIMARY KEY, chat_id TEXT NOT NULL, updated_by TEXT, updated_at TIMESTAMPTZ DEFAULT now())`；`init()` 内 `CREATE TABLE IF NOT EXISTS` 自建，单写者 upsert / 清除 / 读回为真（照 `account-store.ts:269-303` 模板），加 `getRoute(groupLabel)` 与 `listRoutes()` 读。
- [ ] 1.2 把 `group-route-store` 接入 `src/server.ts` 启动 init 链（仿 `notification-contact-store` 装配：`init()` 失败退化 + 准确日志、不拖垮启动）；配套迁移文档编号（沿用现有编号序，仅文档不建执行器）。
- [ ] 1.3 `src/account-store.ts` 新增 `getGroupLabel(accountId): Promise<string | null>` 纯读（异步直读 PG，读失败按 null / 无路由处理、不上抛）。
- [ ] 1.4 `src/feishu/chat-target.ts` 新增 `resolveChatIdForAccount(accountId?, deps)`：`getGroupLabel` → `group_route` 精确相等查 → 命中返回；否则调**不动的** `resolveDefaultChatId`。每层读各自 try/catch、失败向下穿透、**绝不抛出**；有非空 `group_label` 却落默认时打 config-gap 日志。`resolveDefaultChatId` 保持不变。

## 2. aidcp-cloud — 自主推送改路由

- [ ] 2.1 `notifyComments`（`src/server.ts` ~1738）换用 `resolveChatIdForAccount(ctx.accountId)`（最高价值、先改这一个，回归先绿）。
- [ ] 2.2 其余自主推送发送点换新解析器：评论审批卡(~1607)、persona-setup 告警(~1624)、排期发帖/评论/群评回执(~2153/2180/2222)、参照创作结果(~2681)。
- [ ] 2.3 `src/comm/captcha-coordinator.ts`（~208）的 `resolveChatId` 注入改为账号级（accountId 可选、undefined 落默认）。
- [ ] 2.4 无 accountId 的 config-error 告警(`server.ts` ~1639)明确落默认群、不建 scope；`src/comm/handler.ts:558` 边缘发起审批由 `session.edgeId` 推 accountId，推不出 `resolveChatIdForAccount(undefined)` 落默认。

## 3. aidcp-cloud — 命令回执 / 审批走源群

- [ ] 3.1 `runComment`（`src/feishu/commands.ts:270`）接 `context.chatId` 并把 `sourceChatId` 像 `runPublish` 一样穿到执行层，令 `/comment` 结果卡回源群；确认发布结果卡同样回源群。
- [ ] 3.2 保持 `resolveApprovalCardTarget`（`src/publish-agent/roles/publish-executor.ts:372`）`manualApprovalChatId → 默认群`、**不插账号层**（审批属命令 / 源群语义）；`ws-receiver.ts:239` 回源群已成立，加断言防回归。

## 4. aidcp-cloud — 入站作用域安全闸

- [ ] 4.1 引入**管理群**独立显式配置（面板 / 独立标志，**不复用** `is_default`）；`CommandRouter` / 执行层据来源群判定是否管理群。
- [ ] 4.2 账号影响类命令（`/publish` `/comment` `/pause` `/resume` 及对指定账号的 `/status`）从外部 / 非管理群下达时诚实拒（回执说明本群无权），MUST NOT 执行。
- [ ] 4.3 修 `/bind`（`runBind` `commands.ts:393`）：不再授予全局默认 / 管理语义（改独立配置或挪 panel-only）；补最小鉴权，杜绝自助提权。
- [ ] 4.4 显式 accountId 的 `/status|/pause|/resume` 与单账号 / 空昵称短路（`requireCommandAccount` `server.ts:1184`、`server.ts:987/1192`）接来源群并过同一作用域判定（`CommandActions` 接口随之带来源群），非管理群一律诚实拒；入站 / 出站复用同一 resolve、绝不集合并集。

## 5. aidcp-cloud — 面板路由

- [ ] 5.1 `src/cache/bot-chat-store.ts` 加 `listActive()` 只读（列机器人活跃所在群，无 DDL）。
- [ ] 5.2 `src/panel/panel-server.ts` + `src/panel/types.ts`：新增 `GET/PUT /api/notification/routes`（写者注入 `PanelDeps`，仿 `notificationContact`；未注入 → 503；body 类型守卫；读回为真）+ `GET /api/bot-chats`（复用已注入 `botChatStore`）。绑定目标为 opaque `chat_id`（TEXT 非枚举），不新增 cloud→console 枚举。

## 6. aidcp-console — 配置界面

- [ ] 6.1 新增 `group_label→chat` 映射表页 / 区块：目标下拉数据来自 `GET /api/bot-chats`（+ 自由文本兜底），读写走 `/api/notification/routes`；无新枚举、目标为 opaque `chat_id`（防白屏漂移）。

## 7. 测试（克制：只覆盖关键红线行为，别每子任务各塞一个）

- [ ] 7.1 `resolveChatIdForAccount` 单测：已绑定→团队群；未绑定 / 空表→默认群（与 `resolveDefaultChatId` 逐字一致）；**任一层读抛异常→仍返默认群、不外抛**（异常路径不静默作废）；非空 `group_label` 未命中→落默认 + config-gap 日志。
- [ ] 7.2 `group-route-store` 单测：`init()` 幂等自建；upsert / 清除 / 读回为真；缺表回落安全。
- [ ] 7.3 入站作用域单测：外部 / 非管理群账号命令被诚实拒；显式 accountId 路径不绕过作用域；`/bind` 不提权。
- [ ] 7.4 面板路由单测：未注入依赖 → 503；PUT 读回；`GET /api/bot-chats` 列群。
- [ ] 7.5 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck` 全绿（含 `AC-PROTO-*` 不漂移、`AC-PUB-*` 未授权不发、`AC-RISK-*` 不自残）。console `npm run build && npm run typecheck`。

## 8. 文档与运营 runbook

- [ ] 8.1 写运营 runbook（本仓 `docs/` 或 change 内）：如何开对外共享认证 + 逐客户建外部群 / 拉客户成员（对方确认、须在应用可用范围）/ 加机器人 / 指定自然人群主 / 面板绑定 `group_label`。
- [ ] 8.2 落地前核对外部群 API 支持清单：`im/v1/messages`（text + interactive card）+ reactions 均在支持列表；机器人不能当群主、外部成员只拿 open_id 的影响记入文档。
- [ ] 8.3 真机验收项登记到 `docs/real-machine-acceptance-backlog.md`（桩验不了的：真外部群收发、错映射防线、外部群命令拒绝、认证前置）。

## 9. 部署与验收

- [ ] 9.1 dev 部署（默认 target，走 CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync 排除 `.env`/`node_modules`/`.git` → restart → healthcheck）；干净 worktree / `git archive HEAD` 快照打包，绝不从脏工作区上线；**绝不碰同机 isales**。
- [ ] 9.2 部署后冒烟：空表下投递行为与改动前一致（零回归）；绑一个 `group_label→群` 后该账号自主推送落对群、命令结果卡仍回源群；config-gap 日志按预期出现。
