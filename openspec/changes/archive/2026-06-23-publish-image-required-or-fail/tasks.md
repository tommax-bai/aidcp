# Tasks — publish-image-required-or-fail

回归铁律：发布链改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`；红线 `AC-PUB-*`/`AC-RISK-*`/`AC-PROTO-*` 全过。
提交纪律：并发会话同仓有 WIP；**精确 `git add` 仅本 change 文件、不 `-A`**；同机多会话部署错峰防竞态覆盖。
红线：MUST NOT 静默假成功（含不走必然失败的路径）；无图诚实 failed；边缘只忠实执行。

## 1. aidcp-cloud — 配图时长 env 化 + 调大

- [x] 1.1 `src/publish-agent/roles/image-generator.ts`：角色闸 `timeoutMs` env 化 `AIDCP_PUBLISH_IMAGE_TIMEOUT_MS`（默认调大 200000）；注释更新「须 > 万相轮询预算」。**验证**：`npm run typecheck`
<!-- cloud 534ee4a 2026-06-23 deployed。IMAGE_TIMEOUT_MS=env??200000；角色闸 timeoutMs=IMAGE_TIMEOUT_MS。 -->
- [x] 1.2 万相轮询默认调大：`src/server.ts` 处 `AIDCP_WANXIANG_MAX_POLL` 默认 18→34（≈170s<200s 角色闸）；保持 env 优先。**验证**：`npm run typecheck`；二者满足 角色闸 > 轮询×5s
<!-- cloud 534ee4a deployed。默认 34；ECS .env 设 AIDCP_WANXIANG_MAX_POLL=34（34×5=170s<200s 角色闸）。 -->

## 2. aidcp-cloud — 无图诚实失败（PublishExecutor）

- [x] 2.1 `src/publish-agent/roles/publish-executor.ts`：`handleAutoPublish` 起始判 `!assembled.imageUrl` → 落库 `status:'failed'` + `markImagesAttached(false)` + 返回 failed，**不进 sequencer、不发卡、不下发**。原因日志清晰（"无配图→图文帖无有效内容"）。**验证**：单测见 3.1
<!-- cloud 534ee4a deployed。检查在 handleAutoPublish 起始（lineage 后、insert 前），覆盖 sequencer + 旧整页两路径。 -->
- [x] 2.2 复核其他无图入口（旧 `handleManualReview`/旧整页路径）一致或注释说明仅生产 sequencer 路径需收口。**验证**：`npm run typecheck`
<!-- cloud 534ee4a 检查在 handleAutoPublish 顶部（sequencer 分支之前），故 auto_publish 全路径收口；manual_review 在 sequencer 注入下也走 handleAutoPublish（已覆盖）。 -->

## 3. aidcp-cloud — 测试

- [x] 3.1 `publish-executor.test.ts` 新增「无图（imageUrl=null）→ status=failed、未发卡、未下发、markImagesAttached(false)」用例。**验证**：`npm test`
<!-- cloud 534ee4a AC-IMG-REQUIRED 用例（seqCalls=0、sentCards=0、markImagesAttached(false)）。 -->
- [x] 3.2 更新断言"无图→draft/降级纯文字"的既有用例：`publish-orchestrator.test.ts`「配图失败降级…draft」改为「无图→failed」或改走 `enableImage:true` 有图 happy path；其余受影响用例同步。**验证**：`npm test`
<!-- cloud 534ee4a 「完整链路」改 enableImage:true 走 draft；「配图失败降级」改为「无图→诚实 failed、不下发」。 -->
- [x] 3.3 全量回归：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；红线不破。**验证**：三命令退出码 0
<!-- cloud 534ee4a test:acceptance 26/26、test 325/325、typecheck 0 err。 -->

## 4. 部署与验证

- [x] 4.1 cloud 部署（安全序列：私钥/子仓检查 → 备份 → dry-run surface scope → rsync **仅本 change 文件** → restart → healthcheck active+8787+飞书+PG+TitleCreator+isales 未触碰 → 失败回滚）；**与并发会话错峰**。**验证**：healthcheck 全过
<!-- cloud 534ee4a 2026-06-23 deployed。备份 .bak.20260623-163356。rsync 仅 3 源文件（避开并发 role-category test 文件）。healthcheck 全绿（active+8787+TitleCreator+MOCK触发+飞书+PG=1+isales 4 全 active）。错峰：15:34 后并发无重启。 -->
- [x] 4.2 mock 自驱验证（`AIDCP_MOCK_PUBLISH` + `touch /tmp/aidcp-mock-publish-trigger` + 信号文件审批）：配图成功 → 走到发布；配图失败 → **诚实 `failed`（清晰原因，非 `fill_field no_target`）**。**验证**：两条路径各观测一次（或日志确认）
<!-- 2026-06-23 部署后 mock 验证：publish-15 配图成功(30s)→ 发布成功(cmd-path published recordId=15、真帖上账号)、submit 诊断健康。无图诚实失败路径：配图给足时间后已少见、难按需复现 → 由单测 AC-IMG-REQUIRED 坐实（seqCalls=0/sentCards=0/markImagesAttached(false)）。两路径均已覆盖。 -->

## 5. 收尾（中控）

- [x] 5.1 各 task HTML 注释标 `[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。**验证**：本文件各 task 带注释
- [x] 5.2 三仓精确提交推送（本仓 `main`、cloud `master`，Co-Authored-By）。**验证**：干净、已 push
<!-- cloud 534ee4a / aidcp 本提交。精确 git add（未碰并发 role-category）。 -->
- [x] 5.3 `openspec validate publish-image-required-or-fail --strict` → `openspec archive`（delta 并入 `openspec/specs/publish-image-required/`）。**验证**：archive 后不再活跃
- [x] 5.4 收尾清理 mock 后门：`AIDCP_MOCK_PUBLISH` 移除 + 重启（错峰）。**验证**：重启后无「MOCK 触发已开启」日志。
<!-- 2026-06-23：ECS .env 移除 AIDCP_MOCK_PUBLISH + 重启清理（mock-trigger 代码仍在 master、env-guarded off；如需彻底移除代码另开小 change）。AIDCP_WANXIANG_MAX_POLL=34 保留（本 change 的配图时长改进）。 -->
