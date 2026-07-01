## 1. aidcp-cloud — 单次模型调用天花板 + env 旋钮

- [x] 1.1 `src/llm/qwen.ts`：构造默认超时 `60_000` → `180_000`，更新旁注（原「60s 因非 thinking 峰值 25-30s」→「180s 容纳 thinking 模型 60-150s+」）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 1.2 `src/server.ts` QwenClient 构造处：读 `AIDCP_LLM_TIMEOUT_MS` 注入 `timeoutMs`，非法/缺省回落 `180_000`（新增 `normalizeTimeoutMs` helper：非有限数 / <1s 视为非法回落，正数下限保护）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 1.3 回归：`role-llm-config` 向后兼容由既有全量套件覆盖（不传 opts 走构造默认；探活显式 `timeoutMs:8000` 路径不变）——全量 994 tests 绿 <!-- 既有覆盖 -->

## 2. aidcp-cloud — 发布角色执行超时对齐模型预算（角色闸 = 传进模型调用）

- [x] 2.1 `approval-gatekeeper.ts`：角色闸 `15000` → `GATE_TIMEOUT_MS`(env `AIDCP_PUBLISH_GATE_TIMEOUT_MS` 缺省 180000)，并把该值传进 `chat(..., { timeoutMs })` <!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 2.2 `quality-scorer.ts`：角色闸 `20000` → `QUALITY_TIMEOUT_MS`(env `AIDCP_PUBLISH_QUALITY_TIMEOUT_MS`)，传进 `chat()` <!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 2.3 `content-cleaner.ts`：角色闸 `20000` → 导出常量 `CLEAN_TIMEOUT_MS`(env `AIDCP_PUBLISH_CLEAN_TIMEOUT_MS`)；实际模型调用在 `server.ts` 注入的 `postProcessor.rewrite → complete()`，在该处传进同一 `CLEAN_TIMEOUT_MS`（经 roles/index 桶导出、两处共读防漂移）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 2.4 配图文本 LLM 角色（旧单一 ImagePlanner 已被 change publish-multi-image 拆成两个真实角色，本次覆盖两者）：`image-set-planner.ts` 角色闸 `30000` → `IMAGE_SET_PLAN_TIMEOUT_MS`(env `AIDCP_PUBLISH_IMGSETPLAN_TIMEOUT_MS`) + 传进 `chat()`；`image-prompt-composer.ts` 角色闸 `45000` → `IMAGE_PROMPT_TIMEOUT_MS`(env `AIDCP_PUBLISH_IMGPROMPT_TIMEOUT_MS`) + 传进每次 `chat()`（并行 `Promise.all`，墙钟=最慢单次）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 2.5 标杆角色随天花板抬到 180s（已是「角色闸=传模型」范式，仅调默认值）：`content-scout.ts`(90000→180000)、`content-creator.ts`(120000→180000)、`title-creator.ts`(120000→180000，与 publish-pipeline spec `timeoutMs≥180000` 一致)<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 2.6 回归守护：新增 `test/publish-agent/model-call-timeout-invariants.test.ts`——断言每个调用模型的发布角色角色闸 ≥ 单次天花板(180s)、`CLEAN_TIMEOUT_MS` ≥ 180s（拦住「角色闸短于模型预算」这类退化再次出现）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->

## 3. aidcp-cloud — 发布流水线总闸 ≥ 关键路径角色预算之和

- [x] 3.1 `server.ts`：`AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS` 缺省 `180_000` → `600_000`（经 `normalizeTimeoutMs`）；`publish-orchestrator.ts` 兜底默认 `120000` → `600_000` 同步 <!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 3.2 不变量守护：同一新增测试断言「总闸(默认) ≥ 每个模型角色闸」（容器不得小于内容物；生图 200s 角色闸 < 600s 总闸，诚实 skip 可达）<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 3.3 回归：由既有 `publish-orchestrator.test.ts` + 全量套件覆盖（总闸放大不改既有通过用例；不变量测试守住「总闸≥角色闸」）——全量 994 tests 绿 <!-- 既有覆盖 -->

## 4. aidcp-cloud — 看门狗轻推阈值联动抬高（守「轻推 > 单次天花板」不变量）

- [x] 4.1 `src/risk/resume-limits.ts` `DEFAULT_IDLE_NUDGE_MS` `130_000` → `240_000`（> 180s 天花板）；旁注更新为「须 > 单次模型天花板 与 详情页停留上限之更大者，抬天花板须同步抬本值」<!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 4.2 `IDLE_NUDGE_MIN_MS` `91_000` → `200_000`（配置下限 ≥ 模型天花板）；`resume-config-facade.ts` 的 `inRange` 校验用该下限（已核对，写入即拒 <200s）；`resume-config-store.ts` 读时钳制：DB 存旧值(如130s/91s)自动抬到默认（旁注已更新），无需手动改 DB 即守不变量 <!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->
- [x] 4.3 回归：更新 `resume-config-store.test.ts`(库值须 ≥200s 方原样取用) + `resume-config-facade.test.ts`(<200s 拒) 用例与命名；两文件 14 tests 绿、全量 994 绿 <!-- aidcp-cloud 704bbd2 (与 panel change 合并提交) -->

## 5. aidcp-edge — 边→云 选元素等待对齐（> 云端天花板）

- [x] 5.1 `src/client/cloud-selector.ts`：`request('select.request', ...)` 等待超时由默认 `15000` → 显式 `SELECT_TIMEOUT_MS=200000`（> 云端 180s 天花板）；`edge-client.ts` request 第三参 `timeoutMs` 确按传入值生效 <!-- aidcp-edge 082ad12 -->
- [x] 5.2 回归：edge 全量 397 tests 绿 + typecheck 绿（等待放宽不改既有用例）<!-- 既有覆盖 -->

## 6. 回归与类型（两仓，红线必过）

- [x] 6.1 cloud：`test:acceptance` 27 绿（AC-RISK/AC-PUB/AC-SEARCH 等）→ `npm test` 994 绿 → `typecheck` 绿 <!-- 全绿 -->
- [x] 6.2 edge：`test:acceptance` 11 绿（AC-PUB 等，AC-E2E gated 跳过）→ `npm test` 397 绿 → `typecheck` 绿 <!-- 全绿 -->

## 7. 部署与文档（含看门狗结束阈值生产值同步）

- [ ] 7.1 部署 cloud（§5 安全序列：备份 → rsync → restart → healthcheck）
- [ ] 7.2 **部署后必做**：经后台把生产账号 idle-end 阈值抬到 ≥480s（须显著 > 新轻推 240s）。注意：读时钳制下，若 DB idle-end ≤ 现轻推(240s) 会回落写死默认 1h（安全但回收变慢），故须显式设 ≥480s 恢复较快回收；此值走既有配置管线（属 change `restore-auto-resume-and-global-safety-config`），本 change 只核对不改管线
- [ ] 7.3 在部署文档 / `.env` 说明登记新增 env 旋钮：`AIDCP_LLM_TIMEOUT_MS`、`AIDCP_PUBLISH_{GATE,QUALITY,CLEAN,IMGSETPLAN,IMGPROMPT,SCOUT,CONTENT,TITLE}_TIMEOUT_MS`、`AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS`（缺省值与含义）
- [ ] 7.4 回写本 change tasks 的 commit-sha / 部署注记（`<!-- <repo> <sha> 备注 -->` + `<!-- <date> deployed -->`）

## 8. Backlog（非本次目标，仅登记）

- [ ] 8.1 （换更慢 thinking 生图模型时再做）万相生图轮询次数/间隔与生图角色闸等比放大
- [ ] 8.2 （健壮性）`src/publish-agent/wanxiang-client.ts` submit/poll 加单请求 AbortController（~15-30s）快速失败走 fallback:'skip'
