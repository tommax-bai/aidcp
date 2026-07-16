# Tasks — fb-comment-open-hydration-window

## 1. aidcp-edge — 定向放宽评论链路的详情水合窗

- [x] 1.1 `src/facebook/comment-executor.ts`：`FacebookCommentExecutorOptions` 新增 `postDetailProbeRounds?: number`，`DEFAULTS` 置 **22**，注释写明依据（真机实测 7–12s；对齐 `post-reader.ts:56` 同源证据）与「为何不复用 `surfaceProbeRounds`」（后者在 `editorScrollRounds=6` 循环内，放宽即 6×22×600ms≈79s 炸步超时）。 <!-- aidcp-edge ff6c1e1 postDetailProbeRounds=22 + 不可合并理由入注释 -->
- [x] 1.2 `probeStructureUntil` 支持按调用点指定轮数（加一个 rounds 参数，缺省仍取 `surfaceProbeRounds`），**不改变**其「按迭代计数限界」的形态（勿引入墙钟，见 memory `edge-poll-helpers-iteration-bounded`）。 <!-- aidcp-edge ff6c1e1 加可选 rounds 参数，迭代计数形态不变 -->
- [x] 1.3 `openPost` 的 article 等待（`:442`）改用 `postDetailProbeRounds`；**搜索候选探测（`:394/:397`）与评论框催拉（`:452`）保持 `surfaceProbeRounds: 4` 逐字节不变**。 <!-- aidcp-edge ff6c1e1 另两处调用点逐字节未动 -->
- [x] 1.4 单测：慢水合（article 第 N 轮才出现，N>4 且 ≤22）→ `openPost` 成功；从不出现 → 仍如实 `open_failed`；断言评论框催拉循环未被放宽（防回归）。 <!-- aidcp-edge ff6c1e1 4 用例：慢水合接住/退回4轮复现open_failed/永不水合仍诚实/催拉未外溢 -->
- [x] 1.5 `npm run typecheck` + `npm test` <!-- aidcp-edge ff6c1e1 typecheck 干净；npm test 1545 全绿 -->

## 2. aidcp-cloud — 开帖步超时容纳边缘窗口

- [x] 2.1 `src/comment-agent/facebook-edge-steps.ts`：新增 `FACEBOOK_OPEN_STEP_TIMEOUT_MS`，注释写明「边缘先答」的分工与预算算式（2.5s settle + 22 轮×600ms + 评论框催拉 + CDP 往返）。 <!-- aidcp-cloud f4a831e FACEBOOK_OPEN_STEP_TIMEOUT_MS=45s + 顺手修过期注释 -->
- [x] 2.2 `readNote` 的 `timeout` 改用开帖步专用上界；**搜索步继续 `FACEBOOK_STEP_TIMEOUT_MS`（28s）逐字节不变**；提交步的长度感知超时不动。 <!-- aidcp-cloud f4a831e 搜索步/提交步逐字节未动；用 ?? 形态保注入优先 -->
- [x] 2.3 单测：开帖步用新上界；搜索步仍 28s（防误伤）。 <!-- aidcp-cloud f4a831e 3 用例：上界覆盖边端最坏/搜索步仍28s/注入优先 -->
- [x] 2.4 `npm run test:acceptance` → `npm test` → `npm run typecheck`（协议/风控/发布回归纪律，CLAUDE.md §4） <!-- aidcp-cloud f4a831e acceptance 54 全绿；npm test 2308 pass 0 fail；typecheck 干净 -->

## 3. 集成与部署

- [x] 3.1 两仓分别 land 回 master（fetch + rebase + ff） <!-- edge ff6c1e1 + cloud f4a831e 均 ff 推 origin/master -->
- [x] 3.2 部署 cloud 到 **dev**（安全序列：备份 → rsync → restart → healthcheck） <!-- 2026-07-16 deployed 备份 cloud.bak.20260716-202311.tar.gz；git archive 纯净快照 rsync；healthcheck 全过（active/8787/飞书长连接/评论调度器就绪）；isales 四服务未受影响 -->
- [x] 3.3 边缘需重新 build dist（`electron:dev` 不含 build，见 memory `standby-restart-loop-stale-build`）——运营机需重启客户端才生效 <!-- aidcp-edge ff6c1e1 主 checkout 已 ff + npm run build:dist 已重建；产物验证 postDetailProbeRounds:22 且 surfaceProbeRounds:4 未外溢；**待运营重启客户端才生效** -->
- [x] 3.4 回写 sha 台账（格式 `<!-- <repo> <sha> 备注 -->`） <!-- 两 sha 均以 merge-base --is-ancestor 验证在 origin/master 上，非悬空提交 -->

## 4. 真机验收（解耦到 backlog）

- [x] 4.1 登记 `docs/real-machine-acceptance-backlog.md` <!-- 已登记为 82.11，与 82.10（同一现场的另一半）交叉引用、须合并验收 -->：`/comment <账号> --join` 真机跑，核 `facebook_comment_audit` 不再出现 `open_failed`（或占比显著下降）；确认开帖步未改判成 `timeout`。归入 FB 评论真机簇。

## 备注 — 本次排查发现但**不在本 change 范围**的问题（各自另起）

- **卡片文案说谎**：`mapFacebookOpenOutcome`（`comment-scheduler.ts:323-332`）把 `open_failed / editor_not_found / not_facebook / timeout / preempted_by_task / handler_error` 等 7+ 种真因塌成 `no_strong_candidate`，`:143-144` 一律渲染成「群内未找到合适的可评论帖子」——真因在发卡那刻就在内存里（`RunResult.reason`），只是渲染层不读。已有活跃 change `delegated-terminal-failure-reason` 疑似覆盖，需先对账。
- **事件总线无任务归属**：评论任务的 `page.cards` / `note.detail` 与浏览闭环共用会话级总线（`handler.ts:473-490` emit 不带 taskId），浏览闭环把评论任务的空标题搜索结果当 feed 卡评估 → 白烧 LLM 调用 + view 配额（24h 内该账号 `content_evaluator` 跑了 251 次）；云端状态被推进而边缘被租约挡下 → 云-边状态分叉。
- **`cancelledBrowse` 在 FB 恒为 0**：`facebook-session.ts:418` 硬编码 `return 0`（XHS 的 `browse-session.ts:970` 是真计数）——「无法计量」与「计量为零」不可区分，每次真机取证都会踩。宜在 FB 路径打 `n/a`。
- **边缘挡下命令不回执**：`main.ts:1071-1077` 只打 warn 就 return，云端 `sent=1` 读作「已生效」（publish 路径 `main.ts:715-724` 已回诚实回执，浏览路径没有）。
- **垃圾模板可直达真发**：配置写入（`panel-server.ts:1386` → `sanitizeInput`）零内容校验；`enabled` 闸只数个数；kill switch 在 `overrideContainerUrl` 非空时被写死绕过（`comment-scheduler.ts:742-744`）；相关性闸「零 token 重叠才拒」形同虚设 → 唯一拦得住的只有飞书人审。
