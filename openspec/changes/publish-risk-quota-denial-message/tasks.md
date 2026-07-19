## 1. 风控拒绝解释链

- [x] 1.1 扩展 `RiskController.explain()` 的配额拒绝结果，同一次判定返回窗口、已用量和生效上限；保持 `canDo()` 布尔语义不变
- [x] 1.2 governed 委托发帖使用 explain 结果，稳定携带风控状态、配额档位、原因、用量和上限；操作员 override 与人审语义不变
- [x] 1.3 更新 attempt reason 人话化：分别展示状态／档位中文含义与配额窗口，并兼容部署前旧 reason

## 2. 人工精选洗稿权限边界

- [x] 2.1 新增服务端可信 `operator_action` 来源，仅由 Panel 与 Client Auth 的精选 `create-post` 专用入口写入；通用建任务入口不可自报
- [x] 2.2 executor 仅对精确 slash 或形状完整的单篇人工精选洗稿透传 `operatorOverride=true`，其余自然语言／结构化／自动任务继续 governed
- [x] 2.3 验证人工洗稿只绕发布前闸且继续 `review`；平台确认发布后的既有 `RiskController.record('publish')` 事实计数链不被旁路

## 3. 测试与验证

- [x] 3.1 补齐 RiskController、PublishScheduler、reason humanizer、delegated executor、Panel 与 Client Auth 精选入口聚焦测试
- [x] 3.2 运行 Cloud `npm run test:acceptance`，重点保持 AC-RISK／AC-PUB 与未授权发布红线全绿
- [x] 3.3 运行 Cloud 全量测试与 `npm run typecheck`
- [x] 3.4 运行 `openspec validate publish-risk-quota-denial-message --strict`

## 4. 集成与 dev 验证

- [x] 4.1 提交并推送 `publish-risk-quota-denial-message` 分支，经 `scripts/land-change` 串行集成到 Cloud master
- [x] 4.2 从干净 Cloud master 按部署规范发布 dev，验证服务、监听、健康、PostgreSQL、飞书及目标提示；不修改 Tmax 配额、不触发真实平台发布
- [x] 4.3 回写 Cloud commit、测试、部署结果和诚实验证边界到本文件

<!-- Delivery (2026-07-19): Cloud was rebased onto current origin/master and fast-forward landed/pushed as master 732f53f73b3094adfb5c7af998f43369b4bc61c2. Validation after rebase: test:acceptance 59/59 passed; full suite 2546 passed with 8 gated skips and 0 failures; typecheck passed. `openspec validate publish-risk-quota-denial-message --strict` passed. `scripts/deploy-target dev --check` selected 121.89.85.150. Remote backups are `/opt/aidcp/backups/cloud.bak.20260719-172037.tar.gz` and `/opt/aidcp/backups/cloud.env.bak.20260719-172037`; `.env` remained byte-identical. A clean `git archive` snapshot was checksum-synced; the seven changed runtime files match the deployed copies. Only `aidcp-cloud.service` was restarted. It is active with NRestarts=0; ports 8787/8090/8091 listen; panel health is ok; PostgreSQL returned 1; Feishu bot identity is Dev.A and WSClient reached onReady; all four colocated isales services remained active. A deployed code-level probe rendered `风控状态：normal（正常）；配额档位：conservative（保守）；发布配额：分钟窗口 0/0，已达到上限`. No quota/risk state was changed, no delegated task was created, and no real platform publish was attempted; actual counter consumption remains verified by tests around the existing platform-confirmed record path. -->
