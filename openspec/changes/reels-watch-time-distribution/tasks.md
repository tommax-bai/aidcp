# Tasks: reels-watch-time-distribution

## 1. aidcp-automation — 采样函数与 scroll 出口分流

- [x] 1.1 `src/risk/pacing.ts`:新增 `REELS_WATCH` 常量表(三段加权混合:55% [10s,20s) / 35% [20s,45s) / 10% [45s,90s])与 `computeReelsWatchMs({ status, quotaLevel, progress, random? })`——段选择 + 段内均匀采样,乘 `effectiveTempo` 与 `fatigueMultiplier`,clamp [10_000, 90_000];`random` 缺省 `Math.random`、可注入。 <!-- aidcp-automation 0b64998 -->
- [x] 1.2 `src/orchestrator/role-dispatcher.ts`:`sendScrollCommand` 先解析 surface,`resolved === 'reels'` 时 dwell 走 `Math.max(floorMs, computeReelsWatchMs(...))`,其余面走既有 `scrollDwellParams`;`sendBrowseRedrive` 保持不带 dwell。 <!-- aidcp-automation 0b64998 RoleDispatcherOptions 新增 random 注入口(测试确定性) -->
- [x] 1.3 单测:`computeReelsWatchMs` 边界(随机源取 0 / 趋近 1 时输出均在 [10s, 90s];确定性随机源下段选择与取值可复现;warned/restricted tempo 只放大不缩小);dispatcher 层 reels 面 scroll 命令携带采样 dwellMs ≥ 10s 且非恒定、feed 面命令行为与既有断言逐字不变。 <!-- aidcp-automation 0b64998 新增 risk-pacing 3 条;两处既有断言「reels 恒 11_000」更新为注入 random=0.5 下的确定值 18_000(快划 15s × 热身 fatigue 1.2);feed 面 11_000 断言未动(证明 feed 路径零回归) -->
- [x] 1.4 `npm test` + `npm run typecheck` 全绿(改动波及的既有 reels/feed scroll 断言一并核对)。 <!-- aidcp-automation 0b64998 全量 2434/0(skip 3) + acceptance 305/0 + typecheck 干净 -->

## 2. 集成与部署

- [x] 2.1 worktree 集成回 `master`(rebase + ff),push origin。 <!-- aidcp-automation master 0b64998 已推;worktree/分支已清 -->
- [x] 2.2 部署 dev(aidcp-automation.service,按派生服务部署序列:备份 → diff 已部署树定 blast radius → rsync → 重启 → 体检);无迁移、无协议变更。 <!-- 2026-08-10 deployed:备份 automation.bak.20260810104433.tar.gz;dry-run blast radius 恰为本 change 5 文件(不捎带他人改动);重启后 active/NRestarts=0/schema 契约门通过(账本 0116)/8787 监听/isales 未受影响;package.json 未动、共享包无需随包送 -->
- [x] 2.3 控制仓 tasks.md 回写 sha,`openspec validate reels-watch-time-distribution --strict`。 <!-- 本次提交 -->

## 3. 观察(非阻塞)

- [ ] 3.1 dev 真机观察一段时间:Reels 会话的每条停留分布覆盖 10–90s、无看门狗误触、无空转恶化 → 已登记 `docs/real-machine-acceptance-backlog.md` 簇 156。
