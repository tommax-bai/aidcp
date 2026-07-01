# Tasks

> 落点仓：aidcp-cloud（`master`）。实装后按 `<!-- <repo> <commit-sha> 备注 -->` 回填，部署后追加 `<!-- <date> deployed -->`。

## 1. aidcp-cloud — 入口 fast-ack 接线

- [ ] 1.1 改 `src/feishu/ws-receiver.ts` 的 `handleMessage`：把「`await commandRouter.handle(...)` → 发结果卡」从阻塞改为**后台 fire-and-forget**（`.then()` 发终态卡、`.catch()` 记日志），处理器受理后立即返回；表情回应 `void addReaction` 保持不变。
- [ ] 1.2 确认 `im.message.receive_v1` 处理器（`buildDispatcher`）在 `handleMessage` 快速返回后即触发 SDK 回帧；不再有任何路径 await 到命令执行完成。
- [ ] 1.3 保证后台 promise 的 `.catch()` 兜住所有异常（杜绝 unhandledRejection），与改动前「异常记日志、不发卡」的行为对齐（不新增/不吞终态卡）。
- [ ] 1.4 不新增启动中间卡、不新增 `message_id`/`event_id` 去重、不改 honest-status 判级与并发闸——仅动入口接线（人工核对 diff 面）。

## 2. aidcp-cloud — 测试

- [ ] 2.1 单测：`handleMessage` 在命令执行未完成时即 resolve（受理即返回不阻塞）——用一个「久不 resolve」的 commandRouter 桩验证处理器已返回。
- [ ] 2.2 单测：后台执行完成后仍发送终态结果卡（内容/配色不变）；受理与终态卡之间无中间卡。
- [ ] 2.3 单测：后台执行抛错被 `.catch()` 捕获记日志、不外溢、不发意外卡。
- [ ] 2.4 回归纪律：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；安全红线 `AC-PUB-*` / `AC-RISK-*` / `AC-PROTO-*` 仍绿（本次不触碰这些路径，须无回归）。

## 3. 部署与验证（ECS，标准安全序列）

- [ ] 3.1 部署前 §0 检查：私钥 `~/codes/isales-4.pem` 存在且 `chmod 600`；探测 ECS 现役版本，确认无并发方半程改动冲突。
- [ ] 3.2 ECS 先备份（`cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ `systemctl restart aidcp-cloud.service`。
- [ ] 3.3 Healthcheck：`active (running)` + 8787 监听 + 飞书长连接已建立（`飞书长连接已建立` 日志）+ PG `select 1`；失败即回滚。绝不碰同机 isales。
- [ ] 3.4 现场验证：飞书发一次 `/publish <account>`，确认**只触发一次**（journalctl 中同一窗口仅一条 `starting pipeline`、无 `pipeline already running`），且终态/审批卡照常到达。

## 4. 收尾

- [ ] 4.1 `openspec validate feishu-message-fast-ack --strict` 通过。
- [ ] 4.2 回填 tasks commit-sha / deployed 注记；`git commit` + `push`（cloud `master`、本仓 `main`）。
- [ ] 4.3 archive：`/opsx:archive feishu-message-fast-ack`（delta 合并进 `openspec/specs/`）。
