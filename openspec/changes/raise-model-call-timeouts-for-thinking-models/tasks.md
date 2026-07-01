## 1. aidcp-cloud — 单次模型调用天花板 + env 旋钮

- [ ] 1.1 `src/llm/qwen.ts`：构造默认超时 `60_000` → `180_000`，更新旁注（原「60s 因非 thinking 峰值 25-30s」→「180s 容纳 thinking 模型 60-150s+」）
- [ ] 1.2 `src/server.ts:274` QwenClient 构造处：读 `AIDCP_LLM_TIMEOUT_MS` 注入 `timeoutMs`，非法/缺省回落 `180_000`（`Number(process.env.AIDCP_LLM_TIMEOUT_MS ?? 180_000)` + 正数下限保护）
- [ ] 1.3 单测/回归：不传 opts 走新构造默认；per-call 传短超时（如探活 8s）仍覆盖、不受影响（守 `role-llm-config` 向后兼容不变量）

## 2. aidcp-cloud — 发布角色执行超时对齐模型预算（角色闸 = 传进模型调用）

- [ ] 2.1 `src/publish-agent/roles/approval-gatekeeper.ts`：角色闸 `15000` → `180000`，并把该值传进 `llmClient.chat(..., { timeoutMs })`；配 env `AIDCP_PUBLISH_GATE_TIMEOUT_MS`（缺省 180000）
- [ ] 2.2 `src/publish-agent/roles/quality-scorer.ts`：角色闸 `20000` → `180000`，把该值传进 `chat()`；env `AIDCP_PUBLISH_QUALITY_TIMEOUT_MS`
- [ ] 2.3 `src/publish-agent/roles/content-cleaner.ts`：角色闸 `20000` → `180000`；**实际模型调用在 `src/server.ts:469`（注入的 postProcessor.rewrite → `complete()`）**，在该处把同一超时传进 `complete(..., { timeoutMs })`；env `AIDCP_PUBLISH_CLEAN_TIMEOUT_MS`（角色文件与 server 注入处共读同一常量，防漂移）
- [ ] 2.4 `src/publish-agent/roles/image-planner.ts`：角色闸 `30000` → `180000`，把该值传进 `chat()`；env `AIDCP_PUBLISH_IMGPLAN_TIMEOUT_MS`
- [ ] 2.5 标杆角色随天花板抬到 180s（已是「角色闸=传模型」范式，仅调值）：`content-scout.ts`（`AIDCP_PUBLISH_SCOUT_TIMEOUT_MS` 90000→180000）、`content-creator.ts`（`AIDCP_PUBLISH_CONTENT_TIMEOUT_MS` 120000→180000）、`title-creator.ts`（`AIDCP_PUBLISH_TITLE_TIMEOUT_MS` 120000→180000，与 publish-pipeline spec 的 `timeoutMs≥180000` 一致）
- [ ] 2.6 回归：构造 4 角色的慢模型桩（返回耗时介于旧角色闸与 180s 之间），断言角色**不再提前降级**、拿到真实产出；断言超时后仍走诚实 fallback（守「MUST NOT 静默假成功」红线）

## 3. aidcp-cloud — 发布流水线总闸 ≥ 关键路径角色预算之和

- [ ] 3.1 `src/server.ts:487`：`AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS` 缺省 `180_000` → `600_000`（`publish-orchestrator.ts` 默认同步为一致的兜底值）
- [ ] 3.2 断言不变量「总闸 ≥ 关键路径模型角色预算之和」「任一角色闸 ≤ 总闸」：加一个数值断言测试（生图 200s 角色闸 < 600s 总闸，其诚实 skip 可达）
- [ ] 3.3 回归：模拟关键路径串行慢跑（scout+content 之和 > 旧 180s），断言总闸不再在正文未完时判 failed、不丢弃已产出

## 4. aidcp-cloud — 看门狗轻推阈值联动抬高（守「轻推 > 单次天花板」不变量）

- [ ] 4.1 `src/risk/resume-limits.ts:20` `DEFAULT_IDLE_NUDGE_MS` `130_000` → `240_000`（> 180s 天花板）；更新旁注为「须 > 单次模型调用天花板 与 详情页停留上限之更大者」
- [ ] 4.2 `src/risk/resume-limits.ts:26` `IDLE_NUDGE_MIN_MS` `91_000` → `200_000`（配置下限 ≥ 模型天花板，防后台把轻推配到低于一次合法调用）；核对 `resume-config-facade.ts` 的 `inRange` 校验用的是该下限
- [ ] 4.3 回归：断言「进行中 thinking 决策（耗时 ≤180s、其间无 edge 活动）不触发轻推 nudge」；断言后台把轻推配到 <200s 被拒/回落下限

## 5. aidcp-edge — 边→云 选元素等待对齐（> 云端天花板）

- [ ] 5.1 `src/client/cloud-selector.ts:36`：`request('select.request', ...)` 等待超时 `15000` → `200000`（> 云端 180s 天花板）；确认 `edge-client.ts` 的 request 超时确按传入值生效
- [ ] 5.2 回归：断言云端选元素慢响应（<200s）时边缘不提前放弃

## 6. 回归与类型（两仓，红线必过）

- [ ] 6.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck`；红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 全过
- [ ] 6.2 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck`

## 7. 部署与文档（含看门狗结束阈值生产值同步）

- [ ] 7.1 部署 cloud（§5 安全序列：备份 → rsync → restart → healthcheck）
- [ ] 7.2 **部署后必做**：经后台把生产账号 idle-end 阈值从 ~240s 抬到 ≥480s（须显著 > 新轻推 240s），并核对生效值（此值走既有配置管线，属 change `restore-auto-resume-and-global-safety-config` 范畴，本 change 只核对不改管线）
- [ ] 7.3 在部署文档 / `.env` 说明登记新增 env 旋钮：`AIDCP_LLM_TIMEOUT_MS`、`AIDCP_PUBLISH_{GATE,QUALITY,CLEAN,IMGPLAN,SCOUT,CONTENT,TITLE}_TIMEOUT_MS`、`AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS`（缺省值与含义）
- [ ] 7.4 回写本 change tasks 的 commit-sha / 部署注记（`<!-- <repo> <sha> 备注 -->` + `<!-- <date> deployed -->`）

## 8. Backlog（非本次目标，仅登记）

- [ ] 8.1 （换更慢 thinking 生图模型时再做）万相生图轮询次数/间隔与生图角色闸等比放大
- [ ] 8.2 （健壮性）`src/publish-agent/wanxiang-client.ts:120/164` submit/poll 加单请求 AbortController（~15-30s）快速失败走 fallback:'skip'
