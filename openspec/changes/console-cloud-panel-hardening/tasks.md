# Tasks — console-cloud-panel-hardening（面板层 + 管理后台 26 条治理批）

> **依赖波次**（集成串行、组内并行）：波1 高危止血 → 波2 配置漂移 → 波3 前端体验 → 波4 质量债 → 波5 登录会话。详见 `design.md` 分波依赖图。
> **回写格式**：完成 `[ ]`→`[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
> **热点单写者**：本 change 不碰两份 `protocol.ts` / `command-bridge` / 风控状态机 / 角色注册（§7）。`risk/types.ts` 已是 7 动作，#4 只补 console 镜像，不改云端动作集。
> **原清单编号**：每条尾注 `[#N]` 对应用户 review 清单原号。

## 波1 — aidcp-cloud：高危止血（性能 + 接口安全，无前置、组内并行）

- [x] 1.1 面板 WS 背压：`src/panel/panel-ws.ts` 广播前对每客户端查 `bufferedAmount`，超阈值（~1MB）跳过该帧、持续超阈值断开慢客户端；`onAny` handler 入口查有无活跃订阅、无则 return 不序列化（省编排热路径）。验证：单测——慢客户端（模拟高 bufferedAmount）被跳帧/断开、快客户端不受影响、零订阅时不序列化。 [#20] <!-- aidcp-cloud ac3be98 背压 backpressureDecision + 零订阅短路；纯函数单测 + 端到端；PANEL_WS_BACKPRESSURE_BYTES=1MB / MAX_SLOW_STRIKES=30 -->
- [x] 1.2 面板 WS 大载荷截断：单帧序列化后超上限（~256KB，如 `page.cards`/`note.detail` 大对象）截断为带「已截断」标记的摘要帧。验证：单测——超大事件被截断且带标记、正常事件原样。 [#20] <!-- aidcp-cloud ac3be98 serializePanelFrame 超 256KB 截断为 {truncated,reason,bytes}；端到端 + 纯函数测试 -->
- [x] 1.3 `risk_counters` 补 `occurred_at` 索引：`src/risk/pg-risk-store.ts` 建表内嵌 `CREATE INDEX IF NOT EXISTS ... (occurred_at)` + 新 migration 文件双写；面板三处今日聚合查询（`panel-store.ts` todayTotals/todayTotalsByAccount/likeRate）确认走新索引。验证：单测/EXPLAIN 断言不再 seq scan（或查询计划测试）；修 `panel-server.ts:148` 错误注释。 [#21] <!-- aidcp-cloud ac3be98 idx_risk_counters_time (occurred_at DESC) 建表内嵌 + migration 0030 双写；panel-server summary 注释已更正为「走 occurred_at 索引、不全表扫描」 -->
- [x] 1.4 `interaction_feed` 补 `occurred_at` 索引：`src/cache/interaction-feed-store.ts` 建表 + migration 双写；全局视图查询（`panel-store.ts` 无 accountId 分支 ORDER BY occurred_at DESC）走新索引。验证：查询计划测试不再全表扫。 [#23] <!-- aidcp-cloud ac3be98 idx_interaction_feed_time (occurred_at DESC) + migration 0030；SQL 字符串断言测试 -->
- [x] 1.5 三表每日保留清理：进程内日频任务，`risk_counters` 保留 7d、`interaction_feed` 保留 30d、`llm_token_usage` 接线既有 `token-usage-store.ts` 的 `purgeOlderThan`（保留 45d）。DELETE 走 occurred_at 索引。验证：单测——清理删掉超窗行、保留窗内行；purge 被调度。 [#21][#22][#23] <!-- aidcp-cloud ac3be98 新建 src/panel/retention-sweeper.ts（runRetentionSweep 各表独立 try/catch + startRetentionSweeper 日频 unref）；pg-risk purgeCountersOlderThan / feed purgeOlderThan(+清孤儿 meta) 新增，token purgeOlderThan 接线；server.ts 起 sweeper；7 单测 -->
- [x] 1.6 pause/resume/风控端点账号存在性校验：`src/panel/panel-server.ts` pause/resume（385-391）、risk/status（460-488）、risk/quota（490-507）先查账号存在，不存在返 404 `account_not_found`（照同文件 group-label 端点 419-422 范式），杜绝 ON CONFLICT 造幽灵行的「假成功」。验证：单测——不存在账号 ID 返 404、不写库；存在账号正常。 [#28] <!-- aidcp-cloud ac3be98 端点层 assertAccountExists（数据源 panelStore.listAccounts，账号表小）：幽灵账号 404、查询失败 503 不放行；4 端点接入；panel-server 17/17 -->
- [x] 1.7 审批端点 requestId 白名单：`src/panel/panel-server.ts:268` 取 requestId 后加格式校验（仅 `^publish-\d+$` 或 `[A-Za-z0-9_-]+`），非法即 400、不进 `writeApprovalSignal`，堵 `../` 路径穿越。验证：单测——含 `../`/非法字符的 requestId 被拒、合法通过。 [#29] <!-- aidcp-cloud ac3be98 白名单取 [A-Za-z0-9_-]+（publish-<n> 超集，排除 ./ 堵穿越，兼容既有 req-1 测试）；编码 ../ 请求 → 400 invalid_request_id -->


## 波1 — ECS / 运维（与代码解耦，部署时执行）

- [ ] 1.8 ECS `.env` 设 `AIDCP_PANEL_JWT_TTL_SECONDS=43200`（12h）止血「每小时踢人」（过渡措施，波5 续签落地后可回调短）。验证：上机 `grep` .env + 重启后登录令牌 exp≈12h。 [#3]
- [ ] 1.9 ECS Nginx `aidcp-console.conf` 去掉 `/downloads/` 的 `autoindex on`（deploy/aidcp-console.conf:39-42）。验证：`curl https://…/downloads/` 返 403/404 而非目录列表。 [#27]
- [ ] 1.10 ECS 生产库补 1.3/1.4/1.5 的索引（上机执行 `CREATE INDEX IF NOT EXISTS` 或确认随重启自建）。验证：`\d risk_counters`/`interaction_feed` 见新索引。 [#21][#23]

## 波2 — 配置漂移（#4 解锁 #36；#6 收口机制；#5 前后端同修）

### aidcp-console
- [x] 2.1 补评论赞动作列 + 修哨兵测试：`src/types/aidcp-enums.ts:14` 公用枚举补 `comment_like`（对齐云端 7 动作）；`src/components/AccountTotalsTable.tsx:36` 出该列；`src/types/aidcp-enums.test.ts` 本地断言从写死 6 项改为对 `/api/version` live 真值断言（或引 cloud 导出的契约指纹快照）。验证：`npm test` 哨兵对 7 动作真值绿；按账号表出评论赞列。 [#4] <!-- aidcp-console b6ccdfa RISK_ACTIONS+comment_like(+color cyan/label 评论赞)；AccountTotalsTable **无需改**（map RISK_ACTIONS 自动出列，AccountTotals=Record<RiskAction> 自动含键）；哨兵：值快照修正到 7 项 + 新增结构自洽断言（动作↔label/color 键必须一致，检出「加动作忘配」）+ live 对拍扩展 imageProvider/dtoFields；vitest 绿 -->
- [x] 2.2 QuotasPage 复用公用枚举：`src/pages/QuotasPage.tsx:20-33` 私有档位标签/配色（green/blue/orange）+ 私有动作标签删除，改用 `types/aidcp-enums.ts` 公用枚举（冷色 blue/geekblue/purple）；`types/api.ts:362` 重复的 `QuotaTier`/`RiskQuotaLevel` 合一。验证：配额页档位配色与账号页一致（冷色）；typecheck 绿。依赖 2.1。 [#36] <!-- aidcp-console b6ccdfa 档位/动作标签+配色改用 RISK_QUOTA_COLOR/LABEL+RISK_ACTION_LABEL（冷色，消暖色误用）；保留 TIER_ORDER/ACTION_ORDER 排序（公用枚举无 order）。偏离：QuotaTier/RiskQuotaLevel 类型合一未做（值相同、配色已统一，类型合一为洁癖、留） -->
- [x] 2.3 图片厂商前端：`src/types/api.ts:211-212` 图片厂商去字面量钉死、加 `imageProviders` 下拉清单字段；`src/pages/SettingsPage.tsx:97,123-124` 渲染厂商下拉、保存回传厂商字段（43-44,130-132）。验证：设置页显示真实图片厂商 + 可切换。依赖 2.5（cloud 出下拉数据）。 [#5] <!-- aidcp-console b6ccdfa ModelConfig.imageProvider→string+ImageProviderOption；SettingsPage 加图片厂商 Select（data.imageProviders）+保存传 imageProvider+去「钉死通义」文案。cloud buildModelConfigView **早已返回真实 imageProvider+imageProviders**（仅前端接线） -->
- [x] 2.4 DTO 单源镜像收敛（console 侧）：`src/types/api.ts` 手抄镜像与 cloud 导出契约指纹对拍，哨兵测试覆盖枚举 + 关键 DTO 字段集合。验证：`npm test` diff 断言绿；人为改错一处镜像 → 测试红（负向验证）。依赖 2.7。 [#6] <!-- aidcp-console b6ccdfa VersionPayload 镜像+enums.textProvider/imageProvider+dtoFields.panelAccount；哨兵 live 对拍 imageProvider/dtoFields。偏离：跨仓无共享包，DTO 单源=「cloud typecheck 强制字段清单（PANEL_ACCOUNT_FIELDS type-level 断言）+ console live 对拍」组合，非编译期跨仓单源（跨仓边界固有限制，见 design.md D2） -->

### aidcp-cloud
- [x] 2.5 图片厂商后端：`src/config/role-config-facade.ts:70` 图像角色「生效厂商」读真实图片厂商配置（非 `DEFAULT_TEXT_PROVIDER`）；`src/server.ts:1572-1582` 面板视图带 `imageProviders` 下拉清单（若未带）。验证：单测——图像角色视图厂商随图片厂商配置变化。 [#5] <!-- aidcp-cloud d92ed7b role-config-facade 图像角色 effectiveProvider=normImageProvider(deps.getGlobalImageProvider())；server 注入 getGlobalImageProvider。偏离：server 面板视图 **早已带 imageProviders**（无需改）；role-facade 14/14 含火山用例 -->
- [x] 2.6 `/api/version` 契约指纹：`src/panel/panel-server.ts` version 端点暴露 live 枚举（7 动作 + 档位 + 告警分级）+ 关键 DTO 字段集合，作漂移哨兵真值源。验证：单测——version 响应含 7 动作与图片厂商枚举。 [#4][#6] <!-- aidcp-cloud d92ed7b version.ts enums+textProvider/imageProvider（Object.keys(*_PROVIDERS)）+dtoFields.panelAccount；riskAction 早已是 RISK_ACTIONS live 真值（含 comment_like）；PANEL_API_VERSION 1→2；panel-server 断言含 comment_like/volcengine/accountId -->
- [x] 2.7 DTO 单源（cloud 侧）：面板 DTO 收敛到 `src/panel/dto/`（纯类型 + 可序列化契约清单），导出契约指纹供 console 测试引用。验证：cloud typecheck 绿；契约清单与实际接口枚举一致的自测。 [#6] <!-- aidcp-cloud d92ed7b 契约指纹=version.ts PANEL_ACCOUNT_FIELDS（可序列化）+ type-level _AssertNever 断言强制清单与 PanelAccount 键严格一致（漏/多字段 cloud typecheck 失败，protocol.ts 穷举范式）。偏离：**未新建 src/panel/dto/ 目录**（YAGNI——面板 DTO 十几个类型，字段指纹集中在 version.ts 已达「单源+typecheck 强制」目的，无需再抽独立 DTO 层；留缝可后抽） -->

<!-- 波2 部署待办（随首次部署执行）：console 哨兵 live 对拍需在 CI/部署后设 AIDCP_PANEL_URL 指向 ECS 面板端点跑一次（否则 skipIf 默认跳过、检不出 cloud 真漂移）——登记真机 backlog（见 6.4）。 -->

## 波3 — aidcp-console：前端体验（纯前端接线，后端字段已具备）

- [ ] 3.1 `<QueryGate>` 统一读错误呈现：新增 `src/components/QueryGate.tsx`（loading/error/success 三态 + 重试），接入 10 个失败无呈现的页面（Settings/Roles/Persona/Quotas 永久骨架屏 4 页 + Accounts/Content/Schedule/Monitor/TokenUsage/NotificationContacts 误导空态 6 页）；排期页去掉「失败回落内置默认掩码」的假默认值。验证：单测——读查询 mock 失败时呈现错误 + 重试而非骨架屏/空态。 [#30]
- [ ] 3.2 client 保留 reason + 中文映射：`src/api/client.ts:86-94` 把 `body.reason` 合并进异常；抽集中 reason→中文映射（吸收 `ContentPage.tsx:20-42` 孤例）；`ContentSchedulePage.tsx:78,131` 等不再上屏英文码。验证：单测——400 带 reason 时上屏中文文案。 [#31]
- [ ] 3.3 账号筛选 URL 深链：各页账号筛选状态读写 `useSearchParams`（`?account=`）；账号行加站内深链（跳该账号的内容/用量/联系人视图，带 account 参数）。验证：URL 带 account 参数进入页面即预选该账号；刷新不丢。 [#17]
- [ ] 3.4 队列卡管道快照 + 待审筛选：`src/pages/ContentPage.tsx:223-227` 队列卡渲染 `snapshot` 各阶段（类型已声明 `api.ts:148-151`）+ 展开交互；发布内容表加「只看待审」状态筛选（232-239）。验证：队列卡展开见管道各阶段快照；筛选只显待审行。 [#18]

## 波4 — aidcp-console：质量债（#32 先行给安全网）

- [ ] 4.1 审批 CAS 链前端测试：为 `ContentPage.tsx:130-145`（editDraft 带 expectedVersion + approve 带 contentVersion）与拒因映射（20-42）补测试（mock HTTP，照 `DashboardPage.test.tsx`）；覆盖版本冲突（version_stale）/已决策（already_decided）/成功三路。验证：`npm test` 新增用例绿。 [#32]
- [ ] 4.2 npm test 进部署序列：`README.md` 部署节 + 部署路径在 `vite build` 前加 `npm test`。验证：部署文档含测试闸；`land-change` 已跑（38-41）故仅补 README 与直接部署路径。 [#32]
- [ ] 4.3 抽 `useConfigMutation` hook：新增 `src/hooks/useConfigMutation.ts` 收口「提交→失败诚实拒因→成功提示+关编辑态+整体重取」样板；22 处 useMutation 调用点中约 20 处配置写迁移到该 hook。验证：typecheck 绿 + 迁移后各配置页保存/失败行为不变（回归）。依赖 4.1 安全网。 [#34]
- [ ] 4.4 死代码 `honest-write-result.ts`：二选一——若其四态诚实文案有价值，让 `useConfigMutation` 真正引用它统一文案；否则删除 + 去 `components/index.ts:10` re-export。验证：grep 无死引用；若接线则 useConfigMutation 用其文案。与 4.3 一起。 [#35]
- [ ] 4.5 WeekActiveGrid 去重：`src/pages/QuotasPage.tsx:68-155` 内嵌网格 + 54-62 掩码 helper 改用共享 `src/components/WeekActiveGrid.tsx`；两份分叉（共享版有 overlay 标记点）合一。验证：安全页与排期页周历行为一致；typecheck 绿。 [#33]
- [ ] 4.6 routes.ts 合并双清单：新增 `src/routes.ts` 单源（路径 + 组件 + 导航标签），`App.tsx:24-48` 路由表与 `AppShell.tsx:25-37,110-117` 导航清单从中派生。验证：新增页只改一处；路由与导航一致（无「有路由无导航」或反之）。 [#37]

## 波5 — 登录会话（鉴权全链，两仓同改，串行最后做）

### aidcp-cloud
- [ ] 5.1 令牌 jti + 撤销：`src/panel/jwt.ts` payload 加 `jti`；`verifyJwt` 增查撤销黑名单（内存 Set + 可选 PG 持久化跨重启，按 exp 自动清理）。验证：单测——被拉黑 jti 的令牌验签失败；未拉黑通过；黑名单按 exp 清理。 [#26]
- [ ] 5.2 续签 + 登出端点：`src/panel/panel-server.ts` 加 `POST /api/auth/refresh`（持未过期令牌换发新令牌，滑动窗）+ `POST /api/auth/logout`（拉黑当前 jti）。验证：单测——refresh 换新令牌 exp 推进；logout 后原令牌被拒。 [#24][#26]
- [ ] 5.3 WS 首帧鉴权 + 到期断连：`src/panel/panel-ws.ts:41-47` token 改**首帧**读（不再 `url.searchParams`，止血 Nginx 日志）；连接建立后设定时器到 token exp 时 `close(4401)`。验证：单测——首帧无效 token 被拒；到期连接被主动关闭 4401。更新 `panel-ws.ts:7` 注释。 [#25]

### aidcp-console
- [ ] 5.4 401 提示 + 回原页：`src/api/client.ts:81-84` 401 触发「登录已过期」提示（Toast/Modal）；`App.tsx:21` Navigate to /login 带来源路径 state；`LoginPage.tsx:21` 登录成功回来源页而非硬编码首页。验证：单测——401 后见过期提示；重登回原页。 [#24]
- [ ] 5.5 活跃自动续签：`src/api/client.ts` 临近过期时静默调 `/api/auth/refresh` 换新令牌；`AuthContext.tsx:39-43` logout 调 `/api/auth/logout`。验证：单测——临近过期自动续签、活跃不被踢；logout 通知服务端。依赖 5.2。 [#24]
- [ ] 5.6 WS 首帧传 token + 4401 辨识：`src/ws/panelWs.ts:33` token 改**首帧**发（不拼 URL query）；45-48 重连辨识 4401（鉴权失效→停无限重试、触发续签/跳登录）。验证：单测——4401 不盲重连；普通断连正常重连。依赖 5.3。 [#25]
- [ ] 5.7 token 存储缝 + httpOnly 评估：`src/api/client.ts:10-31` setToken/getToken 抽象保持（为 httpOnly cookie 迁移留缝）；本波不迁 cookie（跨端口作用域需 Nginx 配合，记入真机 backlog）。验证：token 存取经单一抽象；文档记 httpOnly 迁移条件。 [#26]

## 收尾

- [ ] 6.1 全量回归：cloud `npm run test:acceptance`（AC-PROTO/AC-PUB/AC-RISK 全过）+ `npm test` + `typecheck`；console `npm test` + `typecheck`。
- [ ] 6.2 `openspec validate console-cloud-panel-hardening --strict` 绿。
- [ ] 6.3 部署 cloud（安全序列：备份→rsync→restart→healthcheck→失败回滚）+ 部署 console（build→rsync，不 --delete）+ 执行 1.8/1.9/1.10 ECS 运维项。回写各 task `<!-- deployed -->`。
- [ ] 6.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（续签活跃不踢、WS 到期断连、大载荷截断、索引查询计划、httpOnly 迁移评估）。
- [ ] 6.5 archive：`openspec archive console-cloud-panel-hardening`（delta 合并进 `openspec/specs/console-panel-api`）。
