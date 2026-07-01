# Tasks

> 落点仓：aidcp-cloud（`master`）。实装后按 `<!-- <repo> <commit-sha> 备注 -->` 回填，部署后追加 `<!-- <date> deployed -->`。

## 1. aidcp-cloud — 入口 fast-ack 接线

- [x] 1.1 改 `src/feishu/ws-receiver.ts` 的 `handleMessage`：把「`await commandRouter.handle(...)` → 发结果卡」从阻塞改为**后台 fire-and-forget**（`.then()` 发终态卡、`.catch()` 记日志），处理器受理后立即返回；表情回应 `void addReaction` 保持不变。<!-- aidcp-cloud a430e70 -->
- [x] 1.2 确认 `im.message.receive_v1` 处理器（`buildDispatcher`）在 `handleMessage` 快速返回后即触发 SDK 回帧；不再有任何路径 await 到命令执行完成。<!-- aidcp-cloud a430e70 handleMessage 现受理即 resolve，buildDispatcher 仍 await 它但秒回；无路径 await 命令完成 -->
- [x] 1.3 保证后台 promise 的 `.catch()` 兜住所有异常（杜绝 unhandledRejection），与改动前「异常记日志、不发卡」的行为对齐（不新增/不吞终态卡）。<!-- aidcp-cloud a430e70 -->
- [x] 1.4 不新增启动中间卡、不新增 `message_id`/`event_id` 去重、不改 honest-status 判级与并发闸——仅动入口接线（人工核对 diff 面）。<!-- aidcp-cloud a430e70 diff 仅 ws-receiver.ts + 其测试，2 文件 -->

## 2. aidcp-cloud — 测试

- [x] 2.1 单测：`handleMessage` 在命令执行未完成时即 resolve（受理即返回不阻塞）——用一个「久不 resolve」的 commandRouter 桩验证处理器已返回。<!-- aidcp-cloud a430e70 'fast-ack — 命令未完成时 handleMessage 即返回' -->
- [x] 2.2 单测：后台执行完成后仍发送终态结果卡（内容/配色不变）；受理与终态卡之间无中间卡。<!-- aidcp-cloud a430e70 '终态卡随 honest-status（未产出=黄⚠️）' -->
- [x] 2.3 单测：后台执行抛错被 `.catch()` 捕获记日志、不外溢、不发意外卡。<!-- aidcp-cloud a430e70 '后台执行抛错被 catch 记日志' -->
- [x] 2.4 回归纪律：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；安全红线 `AC-PUB-*` / `AC-RISK-*` / `AC-PROTO-*` 仍绿（本次不触碰这些路径，须无回归）。<!-- aidcp-cloud a430e70 acceptance 27/27、npm test 1015/1015、typecheck exit 0 -->

## 3. 部署与验证（ECS，标准安全序列）

- [x] 3.1 部署前 §0 检查：私钥 `~/codes/isales-4.pem` 存在且 `chmod 600`；探测 ECS 现役版本，确认无并发方半程改动冲突。<!-- 2026-07-01 pem 600 ✓；探测发现 ECS 落后 master 一批已提交未部署改动（seedream/multi-image/panel-quota/comment-search），dry-run -c 会误伤 → 改外科式单文件部署 -->
- [x] 3.2 ECS 先备份（`cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ `systemctl restart aidcp-cloud.service`。<!-- 2026-07-01 偏离：因 ECS 落后 master、全量 rsync 会连并发方未部署改动一起推，故只 rsync 单文件 src/feishu/ws-receiver.ts（先核 ECS 该文件 md5==基线 1c1f8da，落地后 md5==工作版 4a871562）。备份 cloud.bak.20260701-120318.tar.gz + ws-receiver.ts.bak.20260701-120318 -->
- [x] 3.3 Healthcheck：`active (running)` + 8787 监听 + 飞书长连接已建立（`飞书长连接已建立` 日志）+ PG `select 1`；失败即回滚。绝不碰同机 isales。<!-- 2026-07-01 active since 12:04:10；8787 监听(pid 1604777)；12:04:12 飞书长连接已建立；pg_isready 接受连接；无 error 日志 -->
- [x] 3.4 现场验证：飞书发一次 `/publish <account>`，确认**只触发一次**（journalctl 中同一窗口仅一条 `starting pipeline`、无 `pipeline already running`），且终态/审批卡照常到达。<!-- 2026-07-01 用户验收通过。ECS 实证：12:12:13 手动 /publish → 单条 starting pipeline run=evop0xf3 → 12:14:58 completed（2m45s），全程无第二次触发、无 pipeline already running。ECS ws-receiver.ts md5 仍==4a871562（fast-ack 版，未被并发方 12:05 重启覆盖） -->

## 4. 收尾

- [x] 4.1 `openspec validate feishu-message-fast-ack --strict` 通过。<!-- 2026-07-01 valid -->
- [x] 4.2 回填 tasks commit-sha / deployed 注记；`git commit` + `push`（cloud `master`、本仓 `main`）。<!-- cloud a430e70 pushed；本仓 propose c5c1529 + tasks 回填本次提交 -->
- [x] 4.3 archive：`openspec archive feishu-message-fast-ack`（delta 合并进 `openspec/specs/`）。<!-- 2026-07-01 用户验收通过后归档；新 capability feishu-command-ingestion 合并入库 -->

## 5. 部署观察记录（deployed）

<!-- aidcp-cloud a430e70 2026-07-01 deployed（外科式单文件 ws-receiver.ts，非全量；ECS 落后 master 一批并发方未部署改动，未随本次一起推）。ECS active since 12:04:10，飞书长连接 12:04:12 已建立，healthcheck 全绿。 -->
