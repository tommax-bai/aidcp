## Why

Facebook 评论链路的「开帖」步骤给帖子详情的水合预算约 **4.9s**，而真机实测 FB 详情 article 水合要 **7–12s**。慢帖必然被误判成 `open_failed`，评论发不出去。

**这是 `fb-comment-migration-hold` 修漏的那一半**。该 change 的 edge 提交 `678bdc6`（2026-07-16 16:06）自述目标逐字是「so **slow-hydrating permalinks don't drop approved comments**」——意图明确指向**评论**链路。但它只改了 `aidcp-edge/src/facebook/post-reader.ts:56`（`surfaceProbeRounds` 14→22，≈18s），而**评论链路根本不走 post-reader**：

- `aidcp-edge/src/facebook/comment-handler.ts:125` → `this.executor.openPost(url)`（`FacebookCommentExecutor`）
- `aidcp-edge/src/facebook/comment-executor.ts:431 openPost()` → `:442 probeStructureUntil(...)` → `:446 if (structure.articleCount === 0) return open_failed`
- 其 `surfaceProbeRounds` 是**另一份常量**（`comment-executor.ts:197`），值 **4**，未被 `678bdc6` 触及

| 链路 | 实现 | 帖子 article 水合预算 |
| --- | --- | --- |
| 阅读 / 浏览 | `post-reader.ts`（已修） | 2.5s settle + 22 轮 ≈ **~18s** |
| **评论** | `comment-executor.ts`（**漏修**） | 2.5s settle + 4 轮×600ms ≈ **~4.9s** |
| 真机实测水合耗时（`678bdc6` 自述） | | **7–12s** |

dev 取证（2026-07-16，账号 `61591701813509`，edge `ads-k1ej3o8f`）：`facebook_comment_audit` id 52 = `outcome=no_strong_candidate / reason=open_failed`，16:54:05，距 `comment_prepare` 租约取得仅 14s；容器 `groups/435744902071070`。搜索已返回该 permalink（否则走不到开帖步）⇒ 帖子存在，是**打不开**。非 100% 必挂（历史 id 27/29/30 有 `commented`）——水合快的帖子侥幸过关，故表现为 flaky。

**运行版本已核实**：边缘 `dist/facebook/post-reader.js:19` = 22（构建 16:47:47，早于 16:54 失败），而 `dist/facebook/comment-executor.js:70` = 4 —— 跑的确实是「一边修好、一边没修」的状态。

**不能盲改 4→22**。`surfaceProbeRounds` 被 4 处共用，其中两处在 `editorScrollRounds=6` 的循环里（`comment-executor.ts:397`、`:452`）：盲改后最坏 6×22×600ms ≈ **79s**，远超开帖步 28s 超时 → 只是把 `open_failed` 换成 `timeout`（经 `mapFacebookOpenOutcome` 仍塌进 `no_strong_candidate`，卡片文案一模一样）。故必须**定向**给「等 article 水合」一个独立预算。

**同批必须一起动云端**：开帖步超时是**固定 28s**（`aidcp-cloud/src/comment-agent/facebook-edge-steps.ts:18` + `:139`，注释逐字「search/open 仍用固定 28s」）。放宽后的边缘窗口最坏 ≈ 2.5s settle + 12.6s article + 12s 评论框催拉 + CDP 往返 ≈ **30s** > 28s。**只改边缘 = 把「打不开」换成「超时」**，用户看到的卡片不变。提交步早已有先例按需脱离 28s（`facebookCommentSubmitTimeoutMs`，`:37-41`），本 change 对开帖步照此办理。

## What Changes

- **边缘：给「等帖子详情 article 水合」一个独立的探测预算**（新增 `postDetailProbeRounds`，默认 22，对齐 `post-reader.ts` 的实测依据），**只用于 `openPost` 的 article 等待**（`comment-executor.ts:442`）。搜索候选探测（`:394/:397`）与评论框催拉（`:452`）**继续用 `surfaceProbeRounds: 4`**，逐字节不变——它们在 6 轮循环里，放宽即炸预算。
- **云端：开帖步超时脱离固定 28s**，新增 `FACEBOOK_OPEN_STEP_TIMEOUT_MS`，让边缘放宽后的有界窗口能真正跑完、由**边缘先答**（与提交步同构：边缘自我掐表，云端只做兜底上界）。搜索步继续 28s，**逐字节不变**。
- **诚实闸不变**：超窗仍如实 `open_failed`，MUST NOT 静默假成功；窗口仍有界，绝不无界等待。

## Capabilities

### Modified Capabilities

- `facebook-scheduled-comment`: 新增 1 条要求——评论链路的开帖等待预算必须覆盖真机实测的详情水合耗时，且与阅读链路同源依据；云端开帖步上界必须容纳边缘的有界窗口，使边缘先答。**ADDED**。

## Impact

- `aidcp-edge/src/facebook/comment-executor.ts`（新增选项 + `openPost` 用新预算）
- `aidcp-cloud/src/comment-agent/facebook-edge-steps.ts`（开帖步超时常量 + `readNote` 用它）
- 影响面仅限 Facebook 评论链路的开帖步；XHS 与 FB 浏览/发布路径逐字节不变。
- **风险**：开帖步最坏耗时从 ~18s 抬到 ~30s，评论任务整体变慢（`comment_prepare` 租约 `KEEP_OPEN_LEASE_MS` 为 6min，余量充足）。收益是不再丢掉慢水合的帖子。
