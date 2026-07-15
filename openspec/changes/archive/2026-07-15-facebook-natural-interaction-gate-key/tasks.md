# Tasks — facebook-natural-interaction-gate-key

## 1. aidcp-cloud — 点赞资格闸去竞态

- [x] 1.1 `facebookNaturalInteractionEligibility` 不再硬闸 `facebookQualityPassedNoteIds` 集合；改闸 `content_selected`（能走到点赞判定＝curator 已放行）；「已放行」集合降级为观测。<!-- aidcp-cloud 56112be role-dispatcher.ts -->
- [x] 1.2 `facebookPostKey()` 归一 noteId 到规范帖数字 id（防形态漂移，防御性）+ 6 新单测。<!-- aidcp-cloud 354d6a6 -->
- [x] 1.3 `[fb-gate]` 诊断日志（eligibility / quality_passed add / content_selected add）。<!-- aidcp-cloud 354d6a6 + 56112be -->
- [x] 1.4 cloud acceptance 50 + typecheck 净。<!-- aidcp-cloud 56112be -->

## 2. 部署 + 真机验证

- [x] 2.1 部署 dev（cloud master）。<!-- 2026-07-15 deployed dev -->
- [x] 2.2 真机：修复后 like 命令真被下发（`interaction_appraiser` 出 LLM 判定 + `action=like`）；下游边缘两步提交问题另修 `facebook-feed-like-picker-commit-fix`。<!-- 2026-07-15 dev -->

## 3. 收尾

- [x] 3.1 `[fb-gate]` 诊断日志验证稳定后降噪——登记 backlog 簇 82（现留作观测）。<!-- → backlog 82 -->
- [x] 3.2 `openspec validate --strict` → archive。<!-- 2026-07-15 archived -->
