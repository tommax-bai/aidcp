# Tasks — route-notification-items-by-category

> 落点全部在 `aidcp-cloud`，属主均为 `automation`（§8：改完须经 `scripts/sync-split-repos` 同步到
> `aidcp-automation` 才能部署 dev——dev 现跑派生三服务，`aidcp-cloud.service` 已 disabled 且按 §8.0 永不部署）。
> **不碰 `aidcp-edge`**：执行端在赞收藏 / 新增关注两栏顺带回传发送者条目，是通知联系人名册的既定设计，
> 本 change 不动它——要治的是云端把这批条目误当评论抽取结果。

## 1. aidcp-cloud — 巡视状态记住「本趟选中的分类」

- [x] 1.1 `src/agents/session-context.ts`：`ExcursionState` 加 `selectedCategory: NotificationCategory | null`，
      随 `beginExcursion` / `endExcursion` / `reset` 清空；只读访问口 + 单点写入口。additive，不动既有字段语义。
      <!-- aidcp-cloud 9e5b000 三处清空点收口到 freshExcursion()（endExcursion 原本手写字面量、加字段必漏，已改为复用） -->
- [x] 1.2 `src/agents/notification-triage.ts`：选中某类时写入该格（与 `incrementCategoryAttempts` 同一处，
      单写者）。`notification.category_selected` 的**唯一**发出者就是它——写者唯一由此成立。
      <!-- aidcp-cloud 9e5b000 写在 emit 之前：下游浏览角色在同一次 emit 链里就发命令，条目回来时该格须已是新值 -->

## 2. aidcp-cloud — 评论管线入口按类别路由

- [x] 2.1 `src/agents/notification-classifier.ts` 新增**导出的纯函数** `routeNotificationBatch`
      （照 deduper 的 `notificationItemKey` / `stripRelativeTime` 先例，与角色同文件导出，便于喂违规输入直测）：
      入参 = 云端选中分类 + 条目批次；出参 = 走评论管线 / 只给名册 + 具名原因 + 交叉校验是否打架。
      <!-- aidcp-cloud 9e5b000 同文件导出，未新增文件 ⇒ 不动 boundaries 生成物 -->
- [x] 2.2 类型字段的映射表 MUST 写成 `Record<NotificationItem['kind'], …>` 的穷举
      （新增 kind 时 typecheck 当场失败；`Set` / `satisfies` 都查不出遗漏——见 memory `hand-copied-name-lists`）。
      <!-- aidcp-cloud 9e5b000 KIND_LANES；未知 kind 查表落空 ⇒ 恒不算评论 -->
- [x] 2.3 分类器入口按路由结果分流：非评论栏批次 → 具名日志 + 直接返回，**不 emit 任何事件**
      （不分类、不去重、不发飞书、不产生 `category_handled{comments}`）；评论栏批次 → 走既有逻辑不变。
      <!-- aidcp-cloud 9e5b000 名册那条订阅在 server.ts 订同一事件、一个字节没动 ⇒ 拒的是进管线、不是到达 -->
- [x] 2.4 交叉校验打架（两个方向）→ 具名日志留痕后**仍按云端选中类处置**，MUST NOT 静默取其一。
      <!-- aidcp-cloud 9e5b000 -->
- [x] 2.5 更新分类器文件头注释（它今天自陈「仅评论/@ 路径」，而这恰恰是当时未被守住的那个前提）。
      <!-- aidcp-cloud 9e5b000 -->

## 3. aidcp-cloud — 测试（每条守卫都要能说出「破坏它时哪条具名用例转红」）

- [x] 3.1 承重用例·赞收藏栏批次不进评论管线：巡视中 + 分诊真选中 `likes` → 喂一批条目
      ⇒ 断言零 `notification.classified` / 零 `worthy` / 零飞书 / 零 `category_handled{comments}`。
      <!-- aidcp-cloud 9e5b000 变异 M1（摘掉闸）⇒ 本条 + 端到端红线自检 两条转红 -->
- [x] 3.2 反向闸·评论栏**空**批次仍收尾该类：分诊真选中 `comments` → 喂空批
      ⇒ 断言仍出 `category_handled{comments}`（守「别把重复的那条去掉后反而一次都收不了尾」）。
      <!-- aidcp-cloud 9e5b000 变异 M2（判据恒 contacts_only）⇒ 本条 + 既有端到端 + 两条内容过滤用例 共 6 条转红 -->
- [x] 3.3 红线自检·赞/关注两类仍各自靠自己的回执收尾：端到端（假边缘）跑 likes 未读，
      ⇒ 断言 `category_handled{likes}` 恰好 1 次、`category_handled{comments}` 恰好 0 次、
      `notification_back_home` 命令数恰好等于收尾次数（不多不少）。
      <!-- aidcp-cloud 9e5b000 假边缘按真实顺序先回条目再回动作回执；变异 M4（摘掉 like_browser 的回执收尾）⇒ 本条转红 -->
- [x] 3.4 纯函数直测（喂违规输入 + 两个方向的判据打架）：守「闸恒真通过就等于没有闸」。
      <!-- aidcp-cloud 9e5b000 变异 M5（kindDisagreement 恒 false）⇒ 「两个方向的打架」那条转红 -->
- [x] 3.5 接线断言·分诊真的写了那一格：由 `NotificationTriage` 真产出 `category_selected` 后读 ctx
      （不是测试里手写状态——否则去掉 §1.2 的写入不会转红）。
      <!-- aidcp-cloud 9e5b000 变异 M3（分诊不写）⇒ 4 条转红；变异 M6（endExcursion 不清空）⇒ 「单写者」那条转红 -->
- [x] 3.6 既有 classifier 两条内容过滤用例补上「先选中评论栏」的前置（它们测的是内容防御、不是路由）。
      <!-- aidcp-cloud 9e5b000 -->

## 4. 门禁与集成

- [x] 4.1 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（aidcp-cloud）。
      <!-- aidcp-cloud 9e5b000 acceptance 189/189；全量 4216 pass / 0 fail / 11 skip；typecheck 0 -->
- [x] 4.2 边界门禁无新增违规（`npm run boundaries:refresh` 对账 + `test/acceptance/module-boundary.test.ts`）。
      <!-- aidcp-cloud 9e5b000 跨层边 0 条、豁免 0 条、生成物零漂移；三个改动文件属主均 automation（未新增文件） -->
- [x] 4.3 `scripts/land-change aidcp-cloud route-notification-items-by-category` 合回 master 并推送。
      <!-- aidcp-cloud 9e5b000 land-change --yes，rebase 到 022a6da 后 ff 推送 origin/master -->
- [x] 4.4 `scripts/sync-split-repos --repo aidcp-automation` 对账 → `--apply`（src + tests），
      在 `aidcp-automation` 跑 typecheck + 测试并推送。
      <!-- aidcp-automation f2c680e 3 src + 3 test（其中 role-dispatcher.test.ts / facebook-primary-surface-recheck.test.ts
           是 recheck-facebook-primary-surface-pin 留下的既有派生漂移，同一次对账顺带收齐）；
           kernel 030d805 / transport ffc6d2b 两条 pin 均已对齐、无需改动；typecheck 0；全量 2270 pass / 0 fail / 3 skip -->

## 5. 部署（dev）

- [x] 5.1 探 ECS 真实现状（`aidcp-{api,automation,content}.service` 在跑、`aidcp-cloud.service` disabled）。
      <!-- 2026-08-05 dev 三服务 active、aidcp-cloud.service inactive+disabled（§8.0 未被触碰）；
           automation 听 8787 + 127.0.0.1:8094，ExecStart=npx tsx src/server.ts（无 build 步）；/opt/aidcp/automation 非 git -->
- [x] 5.2 备份 `/opt/aidcp/automation` → rsync（`--exclude .env --exclude node_modules --exclude .git`）
      → **一次** `systemctl restart aidcp-automation.service` → healthcheck。
      用户正在用真机客户端连着 dev 测试：重启会打断其会话约 1.5 分钟，故 MUST 一次到位、MUST NOT 反复 restart。
      <!-- aidcp-automation f2c680e 2026-08-05 deployed：备份 automation.bak.20260805-161427.tar.gz + .env.bak（旧包裁到最近 10 个）
           → git archive HEAD 干净快照 rsync（校验和比对，实际只 6 个文件有内容差异，逐条 itemize 记录）
           → 16:15:06–16:15:11 单次重启 → healthcheck：active、8787 + 8094 在听、schema 门 enforce/通过、
           同步读 ready、边缘 ads-k1e0ero8 一秒内重连且浏览闭环续跑；api / content / isales 未受影响 -->
- [x] 5.3 失败即回滚。**不碰 ol**、不碰同机 isales。
      <!-- 未触发回滚。ol 全程未连；dev 同机 isales 四个服务重启前后均 running -->

## 6. 收尾

- [x] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（真机上跑一趟含赞收藏未读的巡视，
      确认只出一条 `notification_back_home`、且日志里出现「非评论栏 → 不进评论管线」的具名行）。
      <!-- 簇 139（5 项），与簇 136「巡视要走完三栏」标注为可同一次上号一起验 -->

## 7. 部署途中的两项发现（非本 change 引入，登记给后续部署者）

- **`--delete` 会删掉 ECS 上的 `.env` 备份**：`/opt/aidcp/automation/` 里存着 `.env.bak.<日期>`，
  而 `--exclude .env` 挡不住它（模式不匹配）。带 `--delete` 的 dry-run 第一行就是 `*deleting .env.bak.20260805`。
  本次改用**不带 `--delete`** 且加 `--exclude '.env.*'`。凡对 `/opt/aidcp/*` 做 rsync，MUST 先跑 dry-run 读删除清单。
- **automation 的优雅停机从来没成功过，每次都是等满 90 秒再被 SIGKILL**：`journalctl` 里连续三次重启
  （15:36 / 15:43 / 16:01）全是 `shutdown_begin{SIGTERM}` → 90 秒后 `State 'stop-sigterm' timed out. Killing.`。
  也就是说 **SIGKILL 本来就是它的真实终止方式**，那 90 秒纯粹是白等的停机窗口。本次改为 `stop` 后 4 秒
  主动 `systemctl kill -s SIGKILL` 再 `start`，**中断从约 92 秒降到 5 秒**，终止信号与原本完全相同、不引入新风险。
  真正该修的是那个不退出的 SIGTERM 处理器（未定位，另立）；在它修好前，这个提速手法可复用。
