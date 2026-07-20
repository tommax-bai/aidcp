## 1. Cloud 环境生命周期与安装实例真源

- [x] 1.1 为环境注册表增加环境名、绑定观测和生命周期 additive 字段，并新增 installation observation 与单环境删除申请/回执表、索引和自愈建表测试。
- [x] 1.2 在 ClientUserStore 实现环境资产投影、账号环境摘要、删除申请、installation poll/claim/result 幂等状态机和软删除审计。
- [x] 1.3 增加真实 PostgreSQL/存储聚焦测试，覆盖唯一/冲突 installation、重复申请、claim 失配、回执丢失重试、AdsPower 失败与已删除终态。
<!-- aidcp-cloud d893245; post-rebase focused tests 116 passed, land full 2672 passed + 8 gated skips; live additive schema verified in task 5.4. -->

## 2. Cloud HTTP 与调度边界

- [x] 2.1 增加客户鉴权 HTTP maintenance poll/claim/result 端点，只返回当前 installation 的责任，并保持与 `/my-environments` 正常可运行范围分离。
- [x] 2.2 增加内部 Panel 环境资产列表和逐环境删除申请 API，扩展账号 DTO 的 active/deleting/online 环境摘要并统一生命周期过滤。
- [x] 2.3 把删除申请后的环境接入环境选择/调度 fail-closed 闸，视频号物理删除继续等待既有 offboard/hold 前置，不新增 WS 消息或 command mapping。
- [x] 2.4 补客户鉴权、Panel、调度与协议漂移测试，证明客户令牌不可读跨客户资产、202 不等于删除完成且协议 v2 无新增删除类型。
<!-- aidcp-cloud d893245; customer-auth/Panel/WS target guard passed; protocol v2 remains 91 message types and no deletion envelope was added. -->

## 3. Edge HTTP pull 与 AdsPower 回执

- [x] 3.1 增加持久化随机 installationId、环境维护轮询和本地删除结果 outbox；启动、会话维护与失败重试均复用有界客户鉴权 HTTP。
- [x] 3.2 实现 poll/claim 后停止目标 handle、按平台前置状态调用既有 `deleteProfile()`、持久化真实结果并以 Idempotency-Key 回写；Cloud 2xx 前不清 outbox。
- [x] 3.3 保持本地双确认删除与 AdsPower 写 allowlist，新增远程删除、installation 失配、环境运行中、already-missing、响应丢失和重启恢复测试。
- [x] 3.4 更新 Edge operation registry/结构测试，将环境维护归类为 `customer_auth_http`，并证明未增加 Cloud 主动 WS 删除 operation。
<!-- aidcp-edge 1198b26; post-rebase focused tests 11 passed, land acceptance 26 passed and full 1993/1993 passed; no installer built and no real AdsPower profile deleted. -->

## 4. Console 环境资产与账号反向可见性

- [x] 4.1 增加 `/environments` 路由、账号分组导航、环境资产类型/查询和按生命周期、平台、账号、分组、端用户筛选的环境页面。
- [x] 4.2 环境表展示分离的环境名与账号统一显示名、账号风控/档位/分组、归属、最近 Edge 观测和诚实删除状态，并支持已删除历史筛选。
- [x] 4.3 增加删除影响预览与完整 envKey 确认；提交后只显示删除申请已创建并轮询 Cloud 真态，失败保留真实原因。
- [x] 4.4 在账号页增加环境摘要列和按 accountId 深链；删除最后环境只显示无可执行环境，不改变风险/分组/运营状态。
- [x] 4.5 补路由、页面、筛选、确认、状态文案、账号摘要与旧 DTO 回落测试。
<!-- aidcp-console b66579d; post-rebase focused tests 20 passed, land full 220 passed + 1 skipped, typecheck and production build passed. -->

## 5. 验证、集成与 dev 发布

- [x] 5.1 运行 Cloud/Edge/Console 聚焦测试、适用 acceptance、全量测试、typecheck/build，并记录真实通过范围。
<!-- Cloud 2672 pass/8 gated skip; Edge acceptance 26 + full 1993 pass; Console 220 pass/1 skip; all typechecks passed and Console build produced assets with the existing large-chunk warning. -->
- [x] 5.2 运行 `openspec validate admin-environment-lifecycle-management --strict`，核对设计、delta specs、代码和无 WS 删除消息边界。
<!-- Strict validation passed on 2026-07-20; protocol acceptance stayed at v2/91 message types. -->
- [x] 5.3 各仓提交后 fetch/rebase 最新默认分支，复验并 fast-forward 推送 Edge/Cloud/Console/control 默认分支，绝不 force。
<!-- Fast-forward default-branch commits: aidcp-cloud d893245, aidcp-edge 1198b26, aidcp-console b66579d, control proposal 7f02994 plus this rollout record; no force push. -->
- [x] 5.4 按部署规范从干净默认分支部署 Cloud 与 Console 到 `dev`，验证服务、监听、健康、数据库 additive schema、Panel 环境 DTO 与静态页面；不构建 Edge 安装包。
<!-- dev 2026-07-20: backups cloud/console-20260720-160919.tgz; service active; 8787/8090/8091 listening; health/version 200; both new tables + 4 environment columns + 2 result contract columns present; Panel environments 200/32 rows and account summary present; console route/assets 200 with lifecycle copy; Feishu bot Dev.A; no Edge package built. -->
- [x] 5.5 记录非破坏性验证边界：自动测试不得删除真实 AdsPower profile，真实删除只在后续具备明确一次性测试环境和操作者授权时执行。
<!-- No live deletion request was created and no real AdsPower profile was deleted. Physical-delete acceptance remains explicitly gated on a disposable environment and operator authorization. -->
