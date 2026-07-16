# Tasks

## 1. aidcp-cloud — 迁移在途闸（role-dispatcher）

- [ ] 1.1 新增 `isCommentSublineCommand(command)` 判据：`action==='comment'` 或 `action==='open_note' && params.purpose==='navigate'`（迁移支线自己的命令，MUST 豁免迁移在途抑制）。
- [ ] 1.2 `sendCommand` 增加迁移在途抑制闸：`pendingMigration != null && !isQuotaSleepBypass(command) && !isCommentSublineCommand(command)` → 丢弃（return false）。放在 `commentInflight` 闸之后、excursion 租约块之前。
- [ ] 1.3 回归测试：迁移在途（`comment.approved` 后 FB 账号已 emit 迁移 open_note）时，并发 `page.scroll` / feed 命令被抑制（sendCommand 返回 false / 边缘桩未收到）；迁移 `open_note{purpose:'navigate'}` 与落地后 `comment` 仍下发；`pendingMigration` 终局清空后抑制解除。
- [ ] 1.4 `npm run typecheck` + `npm test`（含 `test:acceptance`，AC-PROTO/AC-PUB/AC-RISK 全绿）。XHS 路径（读评 surface 相等、迁移不可达）零回归。

## 2. aidcp-edge — 详情探测窗放宽（post-reader）

- [ ] 2.1 `FacebookPostReader` DEFAULTS `surfaceProbeRounds` 14→22（`2500 + 22×700 ≈ 18s`，覆盖 FB 详情水合上界 12s + 余量）；更新注释说明窗口与理由；诚实失败语义不变（超窗仍 `open_failed`）。
- [ ] 2.2 `npm run typecheck` + `npm test`（若有 post-reader 探测轮次相关断言则同步更新到 22）。

## 3. 集成 / 部署 / 验收

- [ ] 3.1 两 worktree 分支各自 `land-change`（fetch + rebase 最新 master + 解冲突 + `test:acceptance` + `typecheck` + ff 合入 master），确认与 `browser-slot-scheduling` 无文件冲突。
- [ ] 3.2 cloud 从主 checkout master 部署 dev（安全序列：`deploy-target dev --check` → 备份 → rsync → restart → healthcheck）；探 ECS 现状避免顶掉并发 session 未入库工作。
- [ ] 3.3 edge 推 master；ff 更新 canonical edge checkout（用户在其上跑 electron:dev，重跑后生效）。
- [ ] 3.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：① FB 热帖评论迁移期间浏览器不再"闪回首页"；② 慢水合详情页（>12s）评论能发出、不再误 `open_failed`。归入共享真机簇（FB dev 车队）。
- [ ] 3.5 `openspec validate fb-comment-migration-hold --strict` → 全部完成后 archive。
