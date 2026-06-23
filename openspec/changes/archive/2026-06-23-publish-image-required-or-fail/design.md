## Context

`ImageGenerator`（`image-generator.ts`）角色闸 `timeoutMs:120000` 硬编码，注释明示「须 > 万相轮询总预算 18×5s=90s」——故**实际绑定约束是万相 90s**（先于 120s 砍断）。生图失败 → `imageDirective.imageUrl:null` → `ContentAssembler` → `assembledContent.imageUrl:null`。`PublishExecutor.handleAutoPublishViaSequencer` 以 `images: assembled.imageUrl ? [url] : undefined` 建序列；无图 → 无 `upload_image` → `fill_field(title) no_target`（图文编辑器先传图门控）。`command-sequencer.ts:154` 注释保留的"未请求配图→纯文字继续"路径在真实编辑器上不可行。

## Goals / Non-Goals

**Goals:**
- 无图（生图失败/降级）→ **提前诚实 failed**，原因清晰、不驱动 edge 去 `no_target`。
- 配图生成时长 env 可配且足够（减少慢图被砍断）。

**Non-Goals:**
- 不做配图重试（本期：给足时间 + 无图诚实失败；重试另议）。
- 不改 submit 路径（已诊断健康）、协议、DB、风控、isales、标题链路。
- 不实现真·纯文字帖（小红书图文编辑器先传图门控；若日后支持 text kind 再按 `contentType.kind` 放行）。

## Decisions

### D1：无图诚实失败注入点 = `PublishExecutor.handleAutoPublish` 起始（发卡/下发之前）
- **选**：在 `handleAutoPublish` 一进入就判 `!assembled.imageUrl` → 落库 `status:'failed'` + `markImagesAttached(false)` + 返回 failed，**不进 `handleAutoPublishViaSequencer`**（即不发审批卡、不驱动 edge）。**因为**这样在"问人审"之前就诚实失败，避免让人审一个注定 `no_target` 的图文帖，也避免白白驱动 edge。
- **弃**让 sequencer 在 fill_field 才 no_target 失败：原因误导、浪费 edge 往返。

### D2：配图时长 env 化 + 调大，保持「角色闸 > 轮询预算」
- 万相 `maxPollAttempts`：env `AIDCP_WANXIANG_MAX_POLL`（已接）默认 18 → 调大默认 34（≈170s）。
- `ImageGenerator` 角色闸：env `AIDCP_PUBLISH_IMAGE_TIMEOUT_MS` 默认 120000 → 调大默认 200000（>170s，留头）。
- 不传 env 时用新默认；ECS `.env` 现有 `AIDCP_WANXIANG_MAX_POLL=23`（与角色闸 120s 兼容）保持，部署后可按需调。

### D3：撤回"无图降级纯文字 draft"——更新既有测试
- 现有 `publish-orchestrator.test.ts`「配图失败降级…draft + imageUrl null」断言的是旧不可行路径；改为"无图→failed"或改走 `enableImage:true` 有图 happy path。`publish-executor.test.ts` 既有用例 `makeAssembledContent` 自带 imageUrl（不受影响），另加"无图→failed、不发卡、不下发"用例。

## Risks / Trade-offs

- **[误伤合法纯文字帖]** → 当前 `contentType.kind` 恒 `image_text`、编辑器先传图门控，无合法纯文字路径；判 `imageUrl` 为准、注释标注"图文帖假设"，日后 text kind 再按 kind 放行。
- **[配图时长调大 → 每帖更慢]** → 仍远小于 pipeline 18min 预算与人审窗口；env 可回调。角色闸与轮询预算须一致（角色闸 > 轮询×5s），否则角色超时先砍断（已在 D2 对齐）。
- **[既有测试断言反转]** → 显式更新为新诚实行为；红线回归 `AC-PUB/RISK/PROTO` 不破。

## Migration Plan

1. 实装 image-generator env 化 + executor 无图诚实失败 + 测试更新/新增。
2. cloud `test:acceptance` → `test` → `typecheck` 全绿。
3. 部署（安全序列；与并发会话错峰防竞态覆盖）。
4. mock 自驱验证：触发一帖；若配图成功 → 走到发布；若配图仍失败 → 诚实 `failed`（清晰原因，非 `no_target`）。
5. 回滚：解 `.bak` + restart。
