## Why

评论链在「**边缘租约根本没拿到**」时会给运营发一张自相矛盾的红卡：「选中笔记（未获取标题）已选中，但发布未确认成功」。事实是**零命令下发**——没搜索、没选中、没开笔记、没发评论。这是 CLAUDE.md §2「MUST NOT 静默假成功」的反面用例：不是把失败说成成功，而是把「**根本没开始**」说成「在最后一步失败」，运营会去平台上找一条根本不存在的评论。

附带的第二重损失更实：小时格回流闸只对 `not_started` 生效，被误判成 `post_failed` 后**该账号这一小时的排期评论名额白烧、且不重试**。

dev 线上取证（2026-07-14，账号 `63e2ff05…`／edge `ads-k1e0ero8`）：日浏览配额 300/300 正常打满 → 冷待机关闭浏览器 → 排期评论到来 → 边缘回 `cdp_unhealthy` → 云端抛 `edge_unhealthy` → **该码不在白名单** → 落 `post_failed` → 发出上述假回执。当日同一账号命中 4 次。

根因在 spec 层面：现行要求把接管失败的原因**逐条枚举**（「acquire timeout、edge 离线或连接断开」），代码白名单照抄该枚举，因此每新增一个租约错误码都必然漏一次——`edge_unhealthy` 已经漏了，这是它第二次从同一位置漏出来（`browser_wake_failed` 是上一次补的）。**修法是把要求改成与原因无关**，而不是再补一个枚举项。

## What Changes

- **排期／按需评论链**：租约接管失败的判定改为**与错误码无关**——凡「租约未取得」即 `not_started`，不再维护一张会漂移的码白名单。回执如实说明未搜索、未选中、未发布，并按语义分档说明原因（浏览器控制面不可用 / 待机唤不醒 / 边端离线），使运维不会去查一个根本没断的连接。
- **定向评论链**：当前 catch **完全没有租约分类**，六种租约错误码全部压成 `post_failed`（且带上具体笔记 ID），比排期链撒谎更彻底。为其引入 `not_started` 终态与对应的诚实回执分支。
- **受理超时接线修正**：change `browser-slot-scheduling` 的 task 3.3 声称把云端受理超时 45s → 200s（理由：边缘为停泊账号原地重开浏览器，死线 180s，45s 会在**正常唤醒途中**先超时），但该提交只改了类默认常量、**未改注入点**，注入点仍硬写 45s 且 dev 未设覆盖 env → **该修复至今一行未生效**。本 change 补上接线，并把「默认值与注入点不得漂移」写进要求。
- **回归断言**：`typecheck` 抓不到这类漏洞（往联合类型里加成员是**变宽**不是变窄），必须用测试钉死。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `content-schedule`: 「排期评论在 edge 接管失败前如实报告未开始」由**枚举原因**改为**与原因无关**——任何租约取得失败一律 `not_started`。
- `curated-note-actions`: 新增要求——定向评论的租约接管失败同样 MUST 归为「未开始」终态，MUST NOT 复用「已选中／发布未确认」措辞。
- `edge-task-execution-coordination`: 新增要求——云端受理超时 MUST 容得下一次浏览器唤醒，且**生效值**（注入点）与声明的默认值 MUST NOT 漂移。

## Impact

**仅 `aidcp-cloud`。**

- `src/comment-agent/comment-scheduler.ts`：租约失败判定（`isEdgeTaskAcquireFailure`）、排期链 catch 与原因分档、定向链 catch、`targetedOutcomeToReceipt` 穷举分支。
- `src/comment-agent/comment-task-runner.ts`：`TargetedCommentOutcome` 增补 `not_started` 成员。
- `src/server.ts`：`EdgeTaskLeaseClient` 的 `acquireTimeoutMs` 注入点。
- 测试：`test/comment-agent/comment-scheduler.test.ts`、`comment-scheduler-targeted.test.ts`。

**不碰任何热点文件**（`protocol.ts` 两份 / `command-bridge.ts` / `event-bus/types.ts` 的 `RoleName` / `role-catalog.ts` / `risk-state-machine.ts`），可与其他 session 并行。

**运维**：dev `.env` 无需新增 env（接线修正后默认即 200s）；部署后 `browser-slot-scheduling` 的唤醒路径才真正获得完整的受理窗。
