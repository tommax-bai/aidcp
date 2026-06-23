## Why

真机自驱复跑（2026-06-23，`docs/handoff-publish-submit-failure-2026-06-22.md` §3.5）坐实：发布唯一可复现的真实脆点是**配图超时**。wan2.7-image-pro 慢于万相轮询预算（18×5s=90s，受 ImageGenerator 角色闸 120s 上限约束）→ `ImageGenerator` 降级 `imageUrl:null` → `PublishExecutor` 以"无图"建序列（无 `upload_image`）→ 小红书图文编辑器**「先传图门控」下标题框根本不渲染** → `fill_field(title) no_target` → 整帖 failed（publish-13 实测）。净效果：① 失败原因误导（报"标题找不到"，真因是"没图"）；② 白白驱动 edge 导航/选模式后才在 fill_field 暴露；③ 旧"配图失败降级纯文字"路径在真实编辑器上**根本不可行**（图文帖必须有图）。

## What Changes

- **无图诚实失败（主）**：`PublishExecutor` 在驱动发布前判定——图文帖 `assembledContent.imageUrl` 为空（生图失败/降级）→ **提前诚实 `failed`**（清晰原因，不发审批卡、不驱动 edge 去 `no_target`、`images_attached=false`）。撤回"无图降级纯文字继续"的不可行路径（红线：不静默走必然失败的路径）。
- **配图给足时间**：`ImageGenerator` 角色闸超时 + 万相轮询次数**均 env 可调并调大默认**（两者保持 role 闸 > 轮询预算的约束），减少"慢图被砍断→无图"。
- **BREAKING（行为）**：无图不再降级为纯文字 draft，而是诚实 `failed`。同步更新断言"无图→draft"的既有单测为"无图→failed"。

## Capabilities

### New Capabilities
- `publish-image-required`: 图文帖必须有图——无图（生图失败/降级）时诚实失败而非驱动到 `no_target`；配图生成时长 env 可配且足够。

### Modified Capabilities
<!-- 无既有 spec 的 requirement 改写；publish-pipeline 当前仅覆盖标题。 -->

## Impact

- **cloud** `src/publish-agent/roles/image-generator.ts`：角色闸 `timeoutMs` env 化（`AIDCP_PUBLISH_IMAGE_TIMEOUT_MS`）+ 调大默认。
- **cloud** `src/publish-agent/wanxiang-client.ts` / `src/server.ts`：万相 `maxPollAttempts` env（`AIDCP_WANXIANG_MAX_POLL`，已接）+ 默认调大、与角色闸一致。
- **cloud** `src/publish-agent/roles/publish-executor.ts`：无图 → 提前诚实 `failed`（不发卡/不下发）。
- **cloud** `test/publish-agent/publish-executor.test.ts` / `publish-orchestrator.test.ts`：新增"无图→failed"用例；既有"无图→draft/降级"用例改为"无图→failed"或改走有图 happy path。
- **不动**：协议 v2、DB 结构、风控、同机 isales、标题链路（已归档）、submit 路径（已诊断健康）。
- 验证可用已部署的 mock 自驱（`AIDCP_MOCK_PUBLISH`）+ 信号文件审批真机复跑。
