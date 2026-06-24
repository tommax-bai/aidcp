# Tasks — multi-account-node-support

> 进度按 sub-repo 分节回写本仓；代码改动落 edge / cloud / console。完成项用 HTML 注释标 `<!-- <repo> <sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。安全红线回归须全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`（见 §3、§5）。

## 0. 前置 / 迁移（必做，先于开闸）

- [ ] 0.1 盘点 ECS 现存真实账号，给每个**预种 `persona_config` 有效 soul 行**（否则上线诚实闸后它们突变「未绑定、拒启动」回归）；`default` 无需（豁免）
- [ ] 0.2 与并行 change 错峰协调：`safety-quota-config`（共改 `interaction-risk-gating`）、`account-real-nickname`（共改 `account-store.ts` / panel DTO）——确认对方落点、改动加性、不互相覆盖
- [ ] 0.3 核实改「每连接私有通道」后，后台看板扇出从「订阅一条总线」改为「聚合 N 条私有通道」的接法，且概念池 / SessionMonitor 等**不依赖单一全局总线做跨连接协调**（决策 1）
- [ ] 0.4 给现存默认账号的 edge 启动器**显式设 `AIDCP_ACCOUNT_ID=default`**（上线「拒绝缺 accountId 握手」后不显式声明会被拒，决策 4）

## 1. aidcp-cloud — 按连接多租户编排核心

- [ ] 1.1 `comm/handler.ts:282` 的 `edge.hello` 事件载荷加 `accountId`；`comm/event-bus/types.ts:126` 事件类型同步加字段
- [ ] 1.2 为每个 edge 连接建立一束**独立运行时**（**私有 `EventBus`** + `RoleDispatcher` + `SessionContext`(+SessionMonitor)），按 `sessionId/edgeId` 持有、握手创建断连拆除（`server.ts:525` 单实例化点改造）；入站消息只灌本连接私有通道、出站只发本 `edgeId`（决策 1）
- [ ] 1.3 `role-dispatcher.ts:157-164` 去掉 `currentAccountId='default'` 钉死，改为由连接运行时按真实 `accountId` 设入；`restartSession()`（`:418/478-503`）只重建**当前连接**会话，不动其它连接
- [ ] 1.4 `server.ts:568-572` `sendCommand` 闭包捕获本连接 `edgeId`，调 `pushToEdges(env, edgeId)` 定向下发（不再广播）；单连接行为保持等价（非 BREAKING）
- [ ] 1.5 连接生命周期：**同 `edgeId` 重连顶替**该账号下旧连接（同一节点回来，不与 CDP 重连机制冲突）；「同账号 + 不同 `edgeId` + 旧连接仍活」= **真并行第二节点**（交 §6 的 N:1 安全约束，**不再硬拒**，决策 2）
- [ ] 1.6 验证两连接（不同账号）决策上下文互不污染、互不重置；指令不串号（对照 `multi-tenant-orchestration` 各 Scenario）

## 2. aidcp-cloud — 诚实人设启动闸 + 新账号登记

- [ ] 2.1 在会话启动前加**独立绑定判据** `PersonaStore.getForAccount(accountId)!==null`（**不走会回落默认的解析器** `persona-store.ts:196`，解析器回落语义保持不动）
- [ ] 2.2 未绑（且非 `default`）→ 不 `startSession`、不 emit 巡刷信号、在角色重订阅/指令翻译重连**之前**短路（`role-dispatcher.ts:492-494` 之前）；置账号 `needs_persona_setup` 态 + 飞书告警
- [ ] 2.3 `default` 账号**硬豁免**：`if (accountId!=='default' && getForAccount===null) 拒绝`；握手**缺/空 `accountId` → 拒绝握手当配置错误**（无名连接无身份、无落点设人设），不建会话、不塞 `default`、不挂无名「需设置」（决策 4）
- [ ] 2.4 `account-store.ts` 加 `ensureAccount(accountId)` 幂等 upsert（显式状态、不覆盖已配置行、不默认 active），由 `handler.ts:278` 握手路径调用
- [ ] 2.5 账号「人设绑定状态」派生字段以 `persona_config` 行存在为准；`accounts.persona_ref`（`account-store.ts:25`）保留不用
- [ ] 2.6 验证：原有账号复用已绑人设直接启动、新账号未绑被诚实拒绝且出现在主表、`default` 永不被拒（对照 `persona-gated-session-start` 各 Scenario）

## 3. aidcp-cloud — 限频闸对齐 + 安全回归

- [ ] 3.1 限频闸由 `server.ts:375/530-538` 钉死 `getController('default')` 改为按连接真实账号 `riskRegistry.getController(accountId)`；闸与记账落同一真实账号、不分叉
- [ ] 3.2 安全红线回归：先 `npm run test:acceptance`（`AC-RISK-*` 绝不自残/被禁 record 返 false、`AC-PROTO-*` 两份 protocol 不漂移、`AC-PUB-*` 未授权不静默发布），再全量 `npm test`，再 `npm run typecheck`

## 4. aidcp-console — 人设绑定状态可见

- [ ] 4.1 cloud `panel-server.ts` 的 `GET /api/accounts`(+`/:id`) 暴露 `personaBound`/`needsPersonaSetup`（沿用既有 JWT，不另开免鉴权入口）；`panel/types.ts` 加字段
- [ ] 4.2 console `src/types/api.ts` 镜像该 DTO 字段（与 cloud `panel/types.ts` 两处手工同步，PR 自检防漂移）
- [ ] 4.3 console `src/pages/AccountsPage.tsx` 账号列表加「需设置人设 / 已绑人设」状态标 + 跳转 `PersonaPage` 链接（人设页 / 设置 API 复用 `account-persona-config`，不新建）
- [ ] 4.4 console `npm run typecheck` / build 通过；未带 JWT 请求 `GET /api/accounts` 返回 401（对照 `console-panel-api` Scenario）
- [ ] 4.5 cloud `panel-server.ts` 看板事件扇出改为**跨每连接私有通道聚合**，对外仍单一全局只读流、不漏不重，仍 JWT 守护、不碰边缘 socket（决策 1 连带，对照 `console-panel-api` 看板聚合 Scenario）

## 5. aidcp-edge — 每节点独立 Chrome

- [ ] 5.1 `cdp/chrome-launcher.ts:502-521` 探测到端口已有 Chrome 时**默认拒绝复用、诚实报错**；仅 `AIDCP_CDP_ALLOW_REUSE` 显式开启才复用
- [ ] 5.2 残留单例锁清理：仅在确认其指向进程已不存活时清，否则诚实失败，**绝不盲删**致并发损坏
- [ ] 5.3 新增 `scripts/` 启动器：按节点序号分配 `AIDCP_CDP_PORT=base+N` + `AIDCP_CHROME_PROFILE=~/.aidcp-chrome-profile-<accountId>-<节点号>` + 真实 `AIDCP_ACCOUNT_ID`/`AIDCP_EDGE_ID`，拉起 N 个进程（编排留 edge 外，保持边缘薄）
- [ ] 5.4 edge `npm run test:acceptance` / `npm test` / `npm run typecheck` 通过；不引入指纹浏览器

## 6. aidcp-cloud — 同账号并行（N:1）安全（决策 2）

- [ ] 6.1 确认同账号 N 连接经 per-account 控制器注册表**天然共用同一控制器** → 互动计数按账号合并、N 节点共用该账号每日额度（**不翻倍**）；加测试坐实（对照 `same-account-parallel-safety`）
- [ ] 6.2 **互动前按账号去重**：下发互动指令前查「该笔记 / 作者本账号是否已**在途或已完成**同类互动」，命中跳过；**in-flight 声明**（下发即占坑、回执 / 超时释放）；**关注 / 评论 / 评论赞（无 per-note 去重）尤须覆盖**
- [ ] 6.3 同账号控制器**记账串行化**（队列 / 锁），防并发竞争重复扣减 / 漏记
- [ ] 6.4 验证同账号两节点：共用一控制器、额度合并不翻倍、撞同一笔记 / 作者不双动、并发记账不竞争（对照 `same-account-parallel-safety` 各 Scenario）
- [ ] 6.5 **被拒 / 需配置呈现 = 飞书通知 + 后台状态**（决策 3）：未绑人设 / 缺账号身份被拒时发飞书通知 + 置后台状态；**不新增 cloud→edge 命令、不动边-云协议**；被拒节点接受空转、靠飞书把人叫去补人设

## 7. 验证 / 部署 / 归档

- [ ] 7.1 E2E 两场景：(a) **两不同账号**——两 Chrome PID / 两端口 / 两用户数据目录、指令不串、限频各按账号、未绑被诚实拒绝并在后台显示 `needs_persona_setup`、登录各自跨重启持久；(b) **同账号两节点**——共用一控制器额度合并不翻倍、撞同一笔记 / 作者不双动、同 `edgeId` 重连顶替不并列
- [ ] 7.2 `openspec validate multi-account-node-support --strict` 通过
- [ ] 7.3 ECS 部署（安全序列：备份 → `rsync --exclude .env/node_modules/.git` → `systemctl restart aidcp-cloud` → healthcheck active+8787+飞书+PG）；**注意 ECS 是 full-master 快照、本次会连带下游已累积 master**，dry-run 先盘点范围；部署后 grep 关键文件 + 看新启动日志确认新码生效，不只信 rsync 回执；同机 isales 不可碰
- [ ] 7.4 进度回写本仓（各 task 标 `[x]` + commit-sha），完成后 `/opsx:archive`
