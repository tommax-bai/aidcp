## Why

按需评论的「开笔记 / 读正文」这一步（云端 `edge-steps.ts` `readNote`）只监听一个信号——`note.detail.arrived`——并用 `sendAndAwait` 死等到 28s 单步超时。可开笔记是会失败的（目标卡被虚拟列表回收、弹层不弹 `modal_timeout`、正文抽取失败、边缘墙钟预算耗尽）。这些失败边缘其实都会诚实回报，只是回报的**不是** `note.detail`：

- `modal_timeout` / `extract_failed` / `open_timeout` / 无 noteId 的 `card_not_found` → 边缘发 `action.completed{action:'open_note', ok:false, reason}`；
- 带 noteId 但卡被回收（有界滚回仍找不到）→ 边缘**重报当前 `page.cards`**（供自治浏览重规划）。

云端 `readNote` 这两种都不听，只能干等满 28s，且超时后把原因记成「（超时/边端离线）」——**边缘明明在线、也诚实回报过失败**，这是把在线诚实失败误报成离线的假归因，也是运营看到的那张「开笔记/读正文失败」回执延迟 28s 的来源。对照：搜索采卡步（`searchAndHarvest`）早已用 `sendAndRace` 竞速消费 `page.cards.arrived` 与 `action.completed{search,ok:false}`、一失败即快速空候选。开笔记步一直没享受同款整改。

## What Changes

- **`aidcp-cloud` `comment-agent/edge-steps.ts` `readNote`**：把 `sendAndAwait('note.detail.arrived')` 换成 `sendAndRace`，同时竞速三路：
  - `note.detail.arrived`（且 noteId 匹配）＝成功，照常读正文；
  - `action.completed{action:'open_note', ok:false}`＝边缘诚实回失败 → **立即返回失败**，日志带真实 `reason`；
  - `page.cards.arrived`＝边缘重报卡片（=目标卡已不在当前页、开不了）→ **立即返回失败**，reason `target_not_on_page`。
- 三路都没到（真超时/无送达）→ 返回失败，措辞中性（`无回执（超时/结果未就绪）`），**不再断言「边端离线」**。
- **不改边缘**：边缘现有回报（`open_note ok:false` / 重报 `page.cards`）已覆盖全部失败模式；云端竞速消费即可。故对自治浏览闭环（其 `open_note ok:false` 走既有 `recover_after_open_note_failed` 滚动兜底、`page.cards` 走重规划）零影响、零协议改动、零边缘重启。

## Impact

- `aidcp-cloud`：`src/comment-agent/edge-steps.ts`（`readNote` 一处）；相关单测。惠及 `runTask`（排期/`--force`）与 `runTargetedTask`（定向评论）所有调用者。
- **不改**边缘、协议、风控、发布链；无新增/删除 MessageType。
- 修好什么：开笔记失败从「干等 28s + 误报离线」变成「即时失败 + 回执/日志带真实原因」。**不修**「为什么开不开」（那是定位/快照新鲜度问题，另属真机项）。
- 部署：cloud 改动，默认部署 dev ECS（走安全序列）。
