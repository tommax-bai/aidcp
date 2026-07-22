## 1. Cloud 自动资格

- [x] 1.1 实现共享的 AI 自动回复内容资格判定，并修正 `forceHumanTags` 为实际标签交集语义。
- [x] 1.2 接入回复生成/预览：允许安全风格润色和有文档依据的普通问答直接 queued，所有 fallback、未知和实质风险继续降级人工。
- [x] 1.3 接入发送编排的固定配置版本复核，保留运行控制、身份能力、冷却、RiskController、限速、CAS、幂等和核验门禁。
- [x] 1.4 调整 reviewer 提示词，使低风险内容明确给出自动发送建议而不替代 Cloud 确定性决策。

<!-- Implemented in aidcp-cloud commit 3820eef: shared reply-auto-send gate, workflow admission, dispatch recheck, prompt and forceHumanTags semantics. -->

## 2. Console 规则配置

- [x] 2.1 把规则发送方式改为“人工审核 / 自动回复”互斥选择，取消 AI 润色对 `allowAutoSend=false` 的隐式覆盖。
- [x] 2.2 更新规则列表、渠道说明和发布摘要，明确自动回复通过安全检查后直接发送且仍受上层和 Cloud 门禁约束。

<!-- Implemented in aidcp-console commit 8ae55aa. -->

## 3. 测试与契约

- [x] 3.1 增加 Cloud 测试，覆盖安全 AI 自动入队、知识回答、模型/候选失败、实质风险、强制标签和派发复核。
- [x] 3.2 更新 Console 组件测试，覆盖 AI 开关与发送方式互不覆盖、保存 payload、列表和摘要文案。
- [x] 3.3 更新视频号互动契约说明，记录 AI 自动回复资格和两阶段 fail-closed 边界。

## 4. 验证与交付

- [x] 4.1 运行 Cloud 聚焦测试、全量测试和 typecheck；运行 Console 聚焦测试、全量测试和 build。
- [x] 4.2 运行 `openspec validate wechat-ai-polish-auto-send --strict`，记录实现仓库、commit、验证与偏差。
- [x] 4.3 快进集成并推送 control/main、Cloud/master、Console/master，按 Cloud 先、Console 后部署 dev。
- [x] 4.4 验证 dev 文件哈希、服务/监听/健康、PostgreSQL、Feishu、日志和 isales 不受影响，并确认无真实回复任务或发送尝试新增。

<!-- Validation 2026-07-22: Cloud focused interaction suite 53 passed, acceptance 68 passed, full suite exited 0, and typecheck passed. Console focused suite 51 passed, full suite 254 passed/1 skipped across 37 files with two workers, and production build passed. The first parallel full run was discarded after host resource contention caused Vitest worker and 5-second test timeouts; serial bounded-worker reruns were green. -->
<!-- OpenSpec strict validation passed. Implementation commits before integration: aidcp-cloud 3820eef and aidcp-console 8ae55aa. No DTO, schema, database, Edge, WS v2, or package dependency change. -->
<!-- Delivery 2026-07-22: fast-forward integrated and pushed aidcp-cloud master 3820eef, aidcp-console master 8ae55aa, and control main f010d80, then deployed dev in Cloud-before-Console order from clean default checkouts. Rollback backups: cloud.bak.20260722-200811.tar.gz, cloud.env.20260722-200811.bak, console.bak.20260722-200811.tar.gz. Local/remote hashes matched for reply-auto-send.ts, reply-workflow.ts, send-orchestrator.ts, and console index.html. aidcp-cloud.service active with NRestarts=0; 5432/8088/8090/8091/8787 listened; panel/client/public health returned ok; PostgreSQL SELECT 1 passed; Feishu bot was Dev.A and WSClient reached onReady; error-priority journal was empty; isales api/engine/scheduler/worker remained active. Reply jobs/send attempts/contact comment attempts remained 4/0/64, so validation created no real platform reply or send attempt. The hidden account allowlist retained by this delivery was removed by follow-up section 5. -->

## 5. 删除隐藏账号白名单

- [x] 5.1 从 Cloud 生成准入和派发复核中删除隐藏账号 allowlist 及其降级路径。
- [x] 5.2 增加 Cloud 测试，证明公开配置与硬门禁通过时不需要任何隐藏账号白名单，并更新 OpenSpec 契约。
- [x] 5.3 运行 Cloud 聚焦测试、全量测试、typecheck 与 OpenSpec strict validation，提交、推送并部署 dev。
- [x] 5.4 核验 dev 文件哈希、服务/监听/健康、PostgreSQL、Feishu、日志与 isales；不主动开启 runtime controls 或触发真实发送。

<!-- Follow-up validation 2026-07-22: Cloud send-orchestrator focused 15/15, focused interaction 58/58, acceptance 68/68, full suite 2880 passed/8 skipped/0 failed, and typecheck passed. OpenSpec strict validation passed. Cloud implementation commit after rebase/integration: 64e2bb6. -->
<!-- Follow-up delivery 2026-07-22: pushed Cloud master 64e2bb6 and Control main ef9cefc, then deployed Cloud-only to dev from the clean canonical checkout. Backup stamp 20260722-205237 created cloud.bak and cloud.env artifacts. The stale hidden allowlist line was removed from dev .env after backup; local/remote send-orchestrator hash matched a62f8fda. aidcp-cloud.service was active with NRestarts=0; 5432/8088/8090/8091/8787 listened; PostgreSQL SELECT 1 passed; Feishu bot was Dev.A and WSClient reached onReady; the error-priority journal had no entries; isales api/engine/scheduler/worker remained active. Reply jobs/send attempts for the target account were 4/0, and runtime controls remained writePaused=true, commentsReplyEnabled=false, dmSendTextEnabled=false, so deployment neither enabled nor triggered a real reply. -->
