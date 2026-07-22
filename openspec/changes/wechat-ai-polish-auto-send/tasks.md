## 1. Cloud 自动资格

- [x] 1.1 实现共享的 AI 自动回复内容资格判定，并修正 `forceHumanTags` 为实际标签交集语义。
- [x] 1.2 接入回复生成/预览：允许安全风格润色和有文档依据的普通问答直接 queued，所有 fallback、未知和实质风险继续降级人工。
- [x] 1.3 接入发送编排的固定配置版本复核，保留账号 allowlist、运行控制、身份能力、冷却、RiskController、限速、CAS、幂等和核验门禁。
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
- [ ] 4.3 快进集成并推送 control/main、Cloud/master、Console/master，按 Cloud 先、Console 后部署 dev。
- [ ] 4.4 验证 dev 文件哈希、服务/监听/健康、PostgreSQL、Feishu、日志和 isales 不受影响，并确认无真实回复任务或发送尝试新增。

<!-- Validation 2026-07-22: Cloud focused interaction suite 53 passed, acceptance 68 passed, full suite exited 0, and typecheck passed. Console focused suite 51 passed, full suite 254 passed/1 skipped across 37 files with two workers, and production build passed. The first parallel full run was discarded after host resource contention caused Vitest worker and 5-second test timeouts; serial bounded-worker reruns were green. -->
<!-- OpenSpec strict validation passed. Implementation commits before integration: aidcp-cloud 3820eef and aidcp-console 8ae55aa. No DTO, schema, database, Edge, WS v2, or package dependency change. -->
