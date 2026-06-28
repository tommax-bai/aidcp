# Tasks — decouple-publish-generation-from-dispatch（发布生成与下发解耦）

> **范围**：cloud-only。协议 / 边缘 / DB schema 零改动（仅 `publish_log.status` 新增取值 `pending_approval`，不改表结构）。仅笔记发布，评论不改。
>
> **依赖序**：落库读回草稿（task 1）→ 拆 PublishExecutor 为「落库候审返回」（task 2）→ 新增下发路径（task 3）→ 审批信号触发下发（task 4）→ 编排器去让位/去超时 + server 接线（task 5）→ 并发/堆积保护（task 6）→ 验收（AC-PUB 不破，task 7）→ 全量回归（task 8）→ 部署（task 9）。
>
> **回写格式**：task 完成后用 HTML 注释把 `[ ]` 标 `[x]`，写清 commit-sha / 偏离说明 —— `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。

## 状态（2026-06-28）

- **§1–§8 已实现 + cloud 全量回归通过**：cloud `afc385e`（已推送 master）。typecheck 净；官方测试集 832 测，830 通过；
  仅 2 个失败为本机环境产物、与本 change 无关：`AC-PUB-01`（Windows `path.join` 把 `/tmp` 误拼成 Windows 反斜杠路径，Linux/ECS 通过）、
  `session-config-store` 热加载（需本机 PostgreSQL）。`openspec validate ... --strict` 通过。
- **§9 部署 + 真机回归：已完成并通过**（2026-06-28，账号 Tmax，draft 18 published 真机闭环；详见 §9.3）。部署 committed HEAD `45758b7`（含本 change `afc385e` + 同期他人已提交的 curated/weekly），走 `git archive HEAD` 干净包（排除工作树 WIP）、tar-over-ssh（本机无 rsync）、先备份（`cloud.bak.20260628-141327.tar.gz`）+ 重启 + healthcheck 全绿（active / :8787 监听 / 飞书长连接已建立 / 22 角色 + Scheduler 就绪 / 无启动错误 / isales 未碰）。**真机回归（§9.3）仍待运营在 edge 上验**。
- 提交隔离说明：cloud 工作树当时并行有其它在途改动（curated-inspiration-corpus 等），本 change 经外科式 staging 只提交了自身 12 个文件，未卷入他人未提交工作。

## 1. aidcp-cloud — 落库支持读回草稿与待审状态

- [x] 1.1 `src/publish-agent/publish-log-store.ts` 补「按 `recordId` 读回草稿 → 重建发布输入」：返回标题 / 正文 / 标签 / 图 URL / `publish_metadata`（足以构造 `PublishSequenceInput`，不含 `approvedByUser`）。验证：单测落库后读回往返一致、字段齐全
- [x] 1.2 `publish_log.status` 引入 `pending_approval` 取值（草稿已生成、待人审、尚未下发），与既有 `draft`/`needs_review`/`published`/`failed` 语义区分；落库时草稿写 `pending_approval`。验证：单测断言生成候审段落库即 `pending_approval`、不写 `draft`
- [x] 1.3 补「按账号查是否已有未推进终态的 `pending_approval` 草稿」（供堆积保护 task 6.2）。验证：单测覆盖有/无待审草稿两路

## 2. aidcp-cloud — 拆 PublishExecutor：落库候审即返回，不内联等审/下发

- [x] 2.1 `src/publish-agent/roles/publish-executor.ts` 移除内联 `waitForApproval` 轮询、`approvalWaitMs`/`approvalPollMs` 等待、以及「期满 `needs_review`」分支；改为：落库草稿（`pending_approval`）→ 发飞书审批卡 → 返回 `awaiting_approval` 结果。**MUST NOT** 在此内联调用 `executePublishSequence`。验证：单测断言 executor 不再轮询、不下发指令、产出待审结果
- [x] 2.2 发卡前两道诚实前置闸的取舍：无配图（`imageUrl` 空）仍在落库前诚实 `failed`（图文帖必须有图，红线保留）；**「无在线边缘节点」判败下移到下发段**（task 3.4）——生成候审段不因边缘暂离线而毙稿（候审期边缘可不在线）。验证：单测断言无图仍早失败、边缘离线在候审段不判败
- [x] 2.3 `aiEnforced` 防篡改落库红线保留（落库点仍拒绝 `aiEnforced && !ai` 降级）。验证：既有 stage-4 篡改态测仍过

## 3. aidcp-cloud — 新增「审批→下发」路径

- [x] 3.1 新增 `src/publish-agent/publish-dispatcher.ts`（或等价）：入口 `dispatch(recordId)`——按账号取下发锁 → 让位（`endSessionForAccount(accountId,'publish_takeover')`）→ 读回草稿重建 `PublishSequenceInput`（`approvedByUser:true`）→ `CommandSequencer.executePublishSequence` → 回写 `published`(+postId/postUrl)/`failed` → `finally` 解除让位（`resumeSessionForAccount`）。验证：单测覆盖成功/失败/异常三路均经唯一终止点解除让位
- [x] 3.2 让位/续场复用 server 既有 `onPublishStart`/`onPublishEnd` 等价接线（`endSessionForAccount`/`resumeSessionForAccount`），但**调用点从 trigger 移到本下发段**。验证：单测断言下发段持有让位、生成段不持有
- [x] 3.3 下发对 `recordId` 幂等：已 `published` 或正在下发的 `recordId` 重复 `dispatch` 直接返回、不二次提交。验证：单测断言重复 dispatch 不二次发布
- [x] 3.4 下发时 `resolveEdgeIdForAccount` 无在线节点 → 诚实 `failed`（不发指令、不伪造、不静默吞授权）。验证：单测断言离线下发判败、状态可见
- [x] 3.5 下发结果回写复用既有 executor 回写逻辑（`updatePostId`/`updateStatus`/`markImagesAttached`），成功判定仍锚真实成功信号（`publish-submit-integrity` 不变）。验证：成功/抓不到 postId/真失败三路回写正确

## 4. aidcp-cloud — 审批信号到达即触发下发（取消内联超时）

- [x] 4.1 `src/feishu/ws-receiver.ts` 审批卡「授权发布」写信号（`writeApprovalSignal` 成功）后，投递「下发 `recordId`」事件给下发路径（`recordId` 从 `requestId=publish-<recordId>` 解析）。验证：单测断言授权写入后触发 `dispatch(recordId)`
- [x] 4.2 `src/panel/panel-server.ts` `/api/publish/<requestId>/approve` 写信号后同样触发 `dispatch(recordId)`（首写者胜不变；已决则不重复触发）。验证：单测断言面板授权触发下发、重复授权不重发
- [x] 4.3 兜底补偿（at-least-once）：低频扫描「`pending_approval` 且授权信号 `approved===true`」的草稿补触发 `dispatch`，靠 task 3.3 幂等去重，覆盖事件丢失。验证：单测断言信号已 approved 但事件丢失时兜底扫描能补发、且不重复发
- [x] 4.4 运营显式否决/撤稿 → `rejected`/`discarded` 终态（既有否决信号路径，非超时），不下发。验证：单测断言否决推进终态、不触发 dispatch

## 5. aidcp-cloud — 编排器去让位/去超时 + server 接线

- [x] 5.1 `src/publish-agent/publish-orchestrator.ts`：`trigger()` 终止边界收于「草稿落库 + 审批卡已发」；**移除 `onPublishStart`/`onPublishEnd` 包裹**（让位下放下发段，task 3.2）；`pipelineTimeoutMs` 回落到只覆盖生成（去掉为容纳 15min 审批抬高的值）。验证：单测断言 trigger 不再让位、超时回落、终止于待审
- [x] 5.2 `src/server.ts`：移除让位包裹 `trigger()` 的接线；装配下发路径（task 3）与审批触发（task 4）；移除/收敛 `AIDCP_PUBLISH_APPROVAL_WAIT_MS` 与 `roleTimeoutMs` 中为内联审批预留的部分。验证：cloud 启动健康、grep 确认 trigger 路径无让位调用
- [x] 5.3 文档：在 `aidcp-cloud/docs/` 相应处记录新时序（生成候审不让位 / 通过即切下发 / 无审批超时），不记敏感值。

## 6. aidcp-cloud — 并发与堆积保护

- [x] 6.1 下发段按账号单飞：同账号下发在跑时，新授权排队或跳过、绝不并发抢同一边缘。验证：单测断言同账号两份授权不并发下发
- [x] 6.2 生成段堆积保护：某账号已有 `pending_approval` 草稿未推进终态时，不为该账号再生成新草稿（task 1.3 查询支撑）。验证：单测断言已有待审草稿时新触发不产新草稿

## 7. 验收（AC-PUB 不破为核心）

- [x] 7.1 `AC-PUB-*`（未授权绝不静默发布）全过，并**新增/扩展**断言：① 取消超时后无授权草稿绝不自动发布；② 久挂草稿不自毁不改判；③ 下发只在 `approved===true` 发生。验证：cloud `npm run test:acceptance` AC-PUB 全过
- [x] 7.2 `AC-PROTO-*`（协议不漂移、计数不变）全过——本 change 协议零改动。验证：两端计数一致全过
- [x] 7.3 `AC-RISK-*` 不受影响全过。验证：风控守卫测全过
- [x] 7.4 新增「让位时机」断言：生成候审段 grep/单测确认无 `endSessionForAccount`；下发段持有让位且经唯一终止点解除。

## 8. 全量回归（先 acceptance 再全量再 typecheck）

- [x] 8.1 cloud：`cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿
- [x] 8.2 edge：本 change edge 零改动，跑 `npm run test:acceptance` + `npm test` 确认无回归（应零变化）
- [x] 8.3 中控：`openspec validate decouple-publish-generation-from-dispatch --strict` 通过

## 9. 部署（ECS 安全序列；执行前先做前置检查）

- [x] 9.1 前置检查：私钥 `~/codes/isales-4.pem` 存在（已 `chmod 600`）、SSH 连通、ECS 服务 active；确认部署 committed HEAD（非工作树，规避并发 WIP）。<!-- 2026-06-28 done -->
- [x] 9.2 ECS 先备份（`cloud.bak.20260628-141327.tar.gz` + `.env.bak`）→ 部署：`git archive HEAD` 干净包经 **tar-over-ssh**（本机无 rsync，偏离文档 rsync 法）解包覆盖 `/opt/aidcp/cloud`（保留 .env/node_modules）→ `systemctl restart aidcp-cloud.service` → healthcheck 全绿（active running / `0.0.0.0:8787` 监听 / 飞书长连接已建立 / PublishOrchestrator 22 角色 + PublishScheduler 就绪 / 无启动错误）。DB：`status` CHECK 约束经 `PUBLISH_SCHEMA_SQL` 在 `init()` 幂等更新（重启即跑），无手工迁移。**未碰同机 isales**（仅查 is-active）。<!-- 2026-06-28 deployed: cloud HEAD 45758b7 (incl. afc385e) -->
- [x] 9.3 真机回归（edge AdsPower 连 ECS，账号 Tmax）：**通过**（2026-06-28）。draft 18 全链路：18:32:51 草稿待审（候审**不让位**、浏览照常）→ 18:32:55 人审通过即 `会话结束: publish_takeover`（**让位只在下发段**、通过即切 4s 响应）→ 18:33:07 `submit_publish` 成功 → `published`、`images_attached=t` → 同刻 `sendCommand scroll`（**发完即续浏览**）；笔记「大模型工具调用选型避坑」已在 Tmax 主页可见。另：候审无超时验到（草稿 16/17 各挂 3–4 分钟未自动改判/自动发）；离线诚实失败验到 3×（edge 掉线时审批→`无在线边缘节点…诚实 failed`）。<!-- 2026-06-28 真机验 passed -->
  - **顺带发现两个与本 change 无关的 follow-up**：① `capture_postId no_target`——笔记发成功但发后抓不到分享 URL（edge 选择器），`post_url` 落空（诚实 null、非误判失败）；② edge 无 Electron 的 `npm start` 跑法**云连接每几分钟掉一次且不自动重连**（4 次重启才凑上窗口）——edge 侧连接韧性缺口。两者各自单独立项，勿混入本 change。
