# Tasks: 保真参照洗稿角色链

## 1. OpenSpec

- [x] 1.1 新增 proposal/design/tasks 与 spec deltas，明确洗稿只做保真改写，不做解读二创/借题重写。 <!-- aidcp worktree faithful-reference-rewrite: proposal/design/tasks + curated-note-actions/curated-inspiration-corpus/publish-pipeline/role-llm-config deltas -->
- [x] 1.2 `openspec validate faithful-reference-rewrite --strict` 通过。 <!-- 2026-07-05 strict valid -->

## 2. aidcp-cloud

- [x] 2.1 扩展 `PipelineFields` 类型，增加 `referenceAnalysis`、`faithfulRewritePlan`、`faithfulDraft`。 <!-- aidcp-cloud 8d9536b + fidelityAuditReport -->
- [x] 2.2 新增 `ReferenceAnalyzerRole`、`FaithfulRewritePlannerRole`、`FaithfulDraftWriterRole`、`FidelityAuditorRole`。 <!-- aidcp-cloud 8d9536b src/publish-agent/roles/faithful-reference-rewrite.ts -->
- [x] 2.3 修改 `ContentScoutRole` / `ContentCreatorRole`：`referenceNote` 存在时不走常规选题/正文创作。 <!-- aidcp-cloud 8d9536b guard tests cover skip -->
- [x] 2.4 在 `server.ts` 注册四个新角色，确保 `FidelityAuditor` 通过后写 `createdContent` 并接入既有下游。 <!-- aidcp-cloud 8d9536b publish-orchestrator reference chain test covers downstream reuse -->
- [x] 2.5 `ROLE_CATALOG` 登记四个新角色，模型/温度可配置口径正确。 <!-- aidcp-cloud 8d9536b FaithfulDraftWriter tunableTemperature=true, others=false -->
- [x] 2.6 增加 prompt 构建函数与单测，覆盖参照保真、禁止新增事实、角色目录可配置、常规发布不受影响。 <!-- aidcp-cloud 8d9536b prompt/role-catalog/orchestrator tests -->

## 3. Validation

- [x] 3.1 运行 cloud 相关单测。 <!-- aidcp-cloud 8d9536b after rebase: npm run test:acceptance 44 pass; npx tsx --test "test/**/*.test.ts" 1330 pass -->
- [x] 3.2 运行 cloud typecheck。 <!-- aidcp-cloud 8d9536b npm run typecheck pass -->
- [x] 3.3 回看 console 角色配置页是否数据驱动无需改；若需要类型/文案镜像，再补 console 验证。 <!-- 管理后台角色页走 /api/roles + prompt preview provider；cloud 目录/预览测试已覆盖 -->
