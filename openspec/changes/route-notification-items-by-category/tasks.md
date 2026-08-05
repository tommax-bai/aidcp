# Tasks — route-notification-items-by-category

> 落点全部在 `aidcp-cloud`，属主均为 `automation`（§8：改完须经 `scripts/sync-split-repos` 同步到
> `aidcp-automation` 才能部署 dev——dev 现跑派生三服务，`aidcp-cloud.service` 已 disabled 且按 §8.0 永不部署）。
> **不碰 `aidcp-edge`**：执行端在赞收藏 / 新增关注两栏顺带回传发送者条目，是通知联系人名册的既定设计，
> 本 change 不动它——要治的是云端把这批条目误当评论抽取结果。

## 1. aidcp-cloud — 巡视状态记住「本趟选中的分类」

- [ ] 1.1 `src/agents/session-context.ts`：`ExcursionState` 加 `selectedCategory: NotificationCategory | null`，
      随 `beginExcursion` / `endExcursion` / `reset` 清空；只读访问口 + 单点写入口。additive，不动既有字段语义。
- [ ] 1.2 `src/agents/notification-triage.ts`：选中某类时写入该格（与 `incrementCategoryAttempts` 同一处，
      单写者）。`notification.category_selected` 的**唯一**发出者就是它——写者唯一由此成立。

## 2. aidcp-cloud — 评论管线入口按类别路由

- [ ] 2.1 `src/agents/notification-classifier.ts` 新增**导出的纯函数** `routeNotificationBatch`
      （照 deduper 的 `notificationItemKey` / `stripRelativeTime` 先例，与角色同文件导出，便于喂违规输入直测）：
      入参 = 云端选中分类 + 条目批次；出参 = 走评论管线 / 只给名册 + 具名原因 + 交叉校验是否打架。
- [ ] 2.2 类型字段的映射表 MUST 写成 `Record<NotificationItem['kind'], …>` 的穷举
      （新增 kind 时 typecheck 当场失败；`Set` / `satisfies` 都查不出遗漏——见 memory `hand-copied-name-lists`）。
- [ ] 2.3 分类器入口按路由结果分流：非评论栏批次 → 具名日志 + 直接返回，**不 emit 任何事件**
      （不分类、不去重、不发飞书、不产生 `category_handled{comments}`）；评论栏批次 → 走既有逻辑不变。
- [ ] 2.4 交叉校验打架（两个方向）→ 具名日志留痕后**仍按云端选中类处置**，MUST NOT 静默取其一。
- [ ] 2.5 更新分类器文件头注释（它今天自陈「仅评论/@ 路径」，而这恰恰是当时未被守住的那个前提）。

## 3. aidcp-cloud — 测试（每条守卫都要能说出「破坏它时哪条具名用例转红」）

- [ ] 3.1 承重用例·赞收藏栏批次不进评论管线：巡视中 + 分诊真选中 `likes` → 喂一批条目
      ⇒ 断言零 `notification.classified` / 零 `worthy` / 零飞书 / 零 `category_handled{comments}`。
- [ ] 3.2 反向闸·评论栏**空**批次仍收尾该类：分诊真选中 `comments` → 喂空批
      ⇒ 断言仍出 `category_handled{comments}`（守「别把重复的那条去掉后反而一次都收不了尾」）。
- [ ] 3.3 红线自检·赞/关注两类仍各自靠自己的回执收尾：端到端（假边缘）跑 likes 未读，
      ⇒ 断言 `category_handled{likes}` 恰好 1 次、`category_handled{comments}` 恰好 0 次、
      `notification_back_home` 命令数恰好等于收尾次数（不多不少）。
- [ ] 3.4 纯函数直测（喂违规输入 + 两个方向的判据打架）：守「闸恒真通过就等于没有闸」。
- [ ] 3.5 接线断言·分诊真的写了那一格：由 `NotificationTriage` 真产出 `category_selected` 后读 ctx
      （不是测试里手写状态——否则去掉 §1.2 的写入不会转红）。
- [ ] 3.6 既有 classifier 两条内容过滤用例补上「先选中评论栏」的前置（它们测的是内容防御、不是路由）。

## 4. 门禁与集成

- [ ] 4.1 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（aidcp-cloud）。
- [ ] 4.2 边界门禁无新增违规（`npm run boundaries:refresh` 对账 + `test/acceptance/module-boundary.test.ts`）。
- [ ] 4.3 `scripts/land-change aidcp-cloud route-notification-items-by-category` 合回 master 并推送。
- [ ] 4.4 `scripts/sync-split-repos --repo aidcp-automation` 对账 → `--apply`（src + tests），
      在 `aidcp-automation` 跑 typecheck + 测试并推送。

## 5. 部署（dev）

- [ ] 5.1 探 ECS 真实现状（`aidcp-{api,automation,content}.service` 在跑、`aidcp-cloud.service` disabled）。
- [ ] 5.2 备份 `/opt/aidcp/automation` → rsync（`--exclude .env --exclude node_modules --exclude .git`）
      → **一次** `systemctl restart aidcp-automation.service` → healthcheck。
      用户正在用真机客户端连着 dev 测试：重启会打断其会话约 1.5 分钟，故 MUST 一次到位、MUST NOT 反复 restart。
- [ ] 5.3 失败即回滚。**不碰 ol**、不碰同机 isales。

## 6. 收尾

- [ ] 6.1 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（真机上跑一趟含赞收藏未读的巡视，
      确认只出一条 `notification_back_home`、且日志里出现「非评论栏 → 不进评论管线」的具名行）。
