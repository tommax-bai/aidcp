# Tasks

## 1. aidcp-cloud — 迁移在途闸（role-dispatcher）

- [x] 1.1 新增 `isCommentSublineCommand(command)` 判据：`action==='comment'` 或 `action==='open_note' && params.purpose==='navigate'`（迁移支线自己的命令，MUST 豁免迁移在途抑制）。<!-- aidcp-cloud 865a788 -->
- [x] 1.2 `sendCommand` 增加迁移在途抑制闸：`pendingMigration != null && !isQuotaSleepBypass(command) && !isCommentSublineCommand(command)` → 丢弃（return false）。放在 `commentInflight` 闸之后、excursion 租约块之前。<!-- aidcp-cloud 865a788 -->
- [x] 1.3 回归测试：迁移在途（`comment.approved` 后 FB 账号已 emit 迁移 open_note）时，并发 `page.scroll` / feed 命令被抑制（sendCommand 返回 false / 边缘桩未收到）；迁移 `open_note{purpose:'navigate'}` 与落地后 `comment` 仍下发；`pendingMigration` 终局清空后抑制解除。<!-- aidcp-cloud 865a788 test/integration/platform-browse-protocol.test.ts 新增「迁移在途 ⇒ 并发 page.scroll 被扣住」-->
- [x] 1.4 `npm run typecheck` + `npm test`（含 `test:acceptance`，AC-PROTO/AC-PUB/AC-RISK 全绿）。XHS 路径（读评 surface 相等、迁移不可达）零回归。<!-- aidcp-cloud 865a788: typecheck 过; test 2274 pass/0 fail/5 skip; test:acceptance 54 pass/0 fail -->

## 2. aidcp-edge — 详情探测窗放宽（post-reader）

- [x] 2.1 `FacebookPostReader` DEFAULTS `surfaceProbeRounds` 14→22（`2500 + 22×700 ≈ 18s`，覆盖 FB 详情水合上界 12s + 余量）；更新注释说明窗口与理由；诚实失败语义不变（超窗仍 `open_failed`）。<!-- aidcp-edge 678bdc6 -->
- [x] 2.2 `npm run typecheck` + `npm test`。<!-- aidcp-edge 678bdc6: typecheck 过; test 1508 pass/0 fail; test:acceptance 22 pass/0 fail; 无测试断言旧探测轮次、无需改测 -->

## 3. 集成 / 部署 / 验收

- [x] 3.1 两 worktree 分支各自 `land-change`（fetch + rebase 最新 master + `test:acceptance` + `test` + `typecheck` + ff 合入 master）。rebase 均干净、各领先 origin/master 1 提交 → **证实与 `browser-slot-scheduling` 无文件冲突**（本 change 只碰 `role-dispatcher.ts`+`post-reader.ts`）。<!-- cloud 865a788 / edge 678bdc6 -->
- [x] 3.2 cloud 部署 dev：机器 `role-dispatcher.ts` md5 核对 == 改动前 master（无本机改动）→ **外科式单文件部署**（避免顶掉并发 session 未入库的 `src/panel/downloads-manifest.ts`）：备份 `role-dispatcher.ts.bak.20260716-161751` → scp → md5 核对 `6f781dce` → restart → healthcheck 全绿（active / NRestarts=0 / 8787+8090 监听 / PG 锚点就绪 / 飞书长连接已建立）。<!-- 2026-07-16 deployed (dev) 865a788 -->
- [x] 3.3 edge 推 master；canonical edge checkout 已 ff 同步（用户在其上跑 electron:dev，重跑后生效；本 change 非出安装包）。<!-- aidcp-edge 678bdc6 -->
- [x] 3.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md` **簇 82.10**（FB dev 车队，同测试号 `ads-k1ei3dbi`）：① 热帖评论迁移期间浏览器不再"闪回首页"；② 慢水合详情页（>12s）评论能发出、不再误 `open_failed`；③ 会话不钉死；④ XHS 零回归。<!-- 2026-07-16 登记簇82.10 -->
- [x] 3.5 `openspec validate fb-comment-migration-hold --strict` 通过 → archive。<!-- 2026-07-16 -->

