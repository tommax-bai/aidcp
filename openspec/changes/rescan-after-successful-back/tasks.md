# Tasks

## 1. aidcp-cloud — 返回成功后主动续扫

- [x] 1.1 在动作回执处置段加入：返回成功 → 下发一次续扫滚动，原因名 `rescan_after_back`；与返回失败兜底互斥。 <!-- aidcp-cloud 022a6da；互斥由提前 return 做成**结构**保证，而不是靠 ok===true / ok===false 两处条件恰好对上 -->
- [x] 1.2 排除三种情况：会话已结束、浏览暂停期（巡视）、就地读平台。 <!-- aidcp-cloud 022a6da：会话态由 sessionActive 判掉；暂停期由发命令统一出口扣住（那道闸的具名丢弃日志刚由 guard-excursion-stall 补上，可核对，不是这里假设的）；就地读平台根本不产生返回回执 -->

## 2. 测试

- [x] 2.1 补用例：返回成功 → 恰好一次续扫、原因名正确、不伴随失败兜底。 <!-- aidcp-cloud 022a6da test/integration/role-dispatcher.test.ts；原因名逐字断言、不用 includes -->
- [x] 2.2 补用例：返回失败仍走原兜底，且不发续扫（守互斥）。 <!-- 同上 -->
- [x] 2.3 变异验证。 <!-- 2026-08-05 两次变异各自归因到 2.1 那条具名用例：① 整段删掉 → 红；② 原因名改成 rescan_after_back_v2 → 红（原因名是日志与回执里唯一能把两条路径分开的东西）。2.2 在两次变异下都保持绿——它守的是另一件事，符合预期 -->

## 3. 收口

- [x] 3.1 `openspec validate rescan-after-successful-back --strict` 通过。
- [x] 3.2 cloud 测试与门禁。 <!-- 2026-08-05 acceptance 189/189；全量 4212 pass / 0 fail / 11 skip；typecheck 0；module-boundary 12/12 -->
- [x] 3.3 合回 cloud `master` 并推送；同步派生仓并部署 dev。 <!-- aidcp-cloud master 022a6da；scripts/sync-split-repos --repo aidcp-automation 对账只差这一个文件（两个组装根按设计不同步），派生仓 aidcp-automation master 02c644d，typecheck 0。dev 部署 2026-08-05 16:00：先 tar 备份 /opt/aidcp/automation.bak.20260805-155948.tar.gz + .env.bak；**只 rsync 这一个文件**（同仓另有一条已合未部署的 change，整树 rsync 会把它一并带上线），部署前已逐字比对服务器上的旧版 == 本次改动的父版本；restart 后 active / NRestarts=0 / 8787 + 127.0.0.1:8094 在听 / schema 门 enforce 通过。 --> <!-- 2026-08-05 deployed -->
- [x] 3.4 登记真机验收。 <!-- 簇 137。另：部署后即在生产日志中观测到闭环恢复连续——16:02:19 起 back → rescan_after_back → scroll → open_note → browse_images → scroll_comments → back … 30 秒内跑完三轮，此前是每 4 分钟一条 -->
- [x] 3.5 登记边缘侧缺口（不在本 change 修）。 <!-- 见簇 137 的 137.4；命令清单声明的回执里写着 page.cards，Facebook 侧产出、小红书侧不产出，两平台取并集后对账恰好通过，per-platform 缺口被并集掩盖 -->

## 4. 运维观察（非本 change 范围，登记）

- [ ] 4.1 `aidcp-automation.service` 每次 restart 都会卡在优雅关停、约 90 秒后被 systemd `stop-sigterm` 超时 SIGKILL（2026-08-05 一小时内四次，次次如此）。后果：每次部署给连着 dev 的真机客户端造成约 1.5 分钟中断，且强杀意味着在途状态没有走完关停路径。值得单独查是谁没关（WS server / PG 池 / 定时器）。
