# Tasks

## 1. aidcp — OpenSpec 规格

- [x] 1.1 在 `comment-search-command` 规格新增要求：云端开笔记/读正文步 MUST 竞速消费边缘的开笔记失败信号（`open_note ok:false` 或重报的 `page.cards`），一失败即快速返回、MUST NOT 干等满单步超时；失败措辞如实、MUST NOT 把在线诚实失败冒充「边端离线」。 <!-- aidcp: specs/comment-search-command ADDED 一条要求 + 三 scenario；本收尾提交 -->

## 2. aidcp-cloud — readNote 快速失败竞速（独立 worktree）

- [x] 2.1 `edge-steps.ts` `readNote`：`sendAndAwait('note.detail.arrived')` → `sendAndRace` 竞速三路（`note.detail.arrived` 成功 / `action.completed{open_note,ok:false}` 失败带 reason / `page.cards.arrived` 失败 `target_not_on_page`）；成功路读正文不变（`readCurrentNote`）。 <!-- aidcp-cloud 5529c87 -->
- [x] 2.2 失败/超时日志措辞中性化：真超时用「无回执（超时/结果未就绪）」，诚实失败用真实 reason，不再无条件写「（超时/边端离线）」。 <!-- aidcp-cloud 5529c87 -->
- [x] 2.3 补单测：`readNote` 收到 `open_note ok:false` 立即返回 null（1.3ms 不等超时）、收到重报 `page.cards` 立即返回 null（0.2ms）、匹配 `note.detail` 正常读正文；计时断言不干等。 <!-- aidcp-cloud 5529c87: edge-steps.test 12→14，全过 -->

## 3. aidcp-cloud — 验证

- [x] 3.1 `npm run test:acceptance` + 全量 `npm test` + `npm run typecheck` 全过（安全红线 AC-PROTO/AC-RISK/AC-PUB 不破）。 <!-- aidcp-cloud 5529c87: land-change 跑 test 2153/2153 + typecheck 全过 -->

## 4. 集成与部署

- [x] 4.1 land 到 `aidcp-cloud` master（rebase + 全量测试 + ff-push）。 <!-- aidcp-cloud 5529c87 pushed origin/master + 主 checkout 已 ff 同步 -->
- [x] 4.2 部署 dev ECS。 <!-- 2026-07-15 deployed dev：先探 ECS(deployed edge-steps.ts md5=parent 151462c，清洁前进步)；外科备份 edge-steps.ts.bak.20260715-181302 + rsync 单文件(md5 daed66 已核) + restart；healthcheck 全绿(active / :8787 LISTEN / PG 锚点就绪 / 飞书长连接 onReady / 无错误)。并发方 17:38 另有部署，本次外科单文件不越界。 -->
- [x] 4.3 提交并推送 `aidcp`（main）；`openspec validate comment-readnote-fastfail --strict` 通过后归档。 <!-- 本收尾提交 -->
- [x] 4.4 真机项登记 `docs/real-machine-acceptance-backlog.md` 簇34：dev 观察开笔记失败时回执/日志即时且带真实原因、不再 28s 干等、不再误报离线。
