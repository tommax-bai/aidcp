> 设计已收敛到最终版（见 design.md）：云端 12 角色、按分类拆浏览、各自命令、无巡视计时器、resumer 收敛终止；赞收藏/新增关注 v1 看一眼清未读不发飞书。边缘侧基类/清单/监测体已实现；`notification.open` 复合 handler 与协议需按最终版调整。

## 1. aidcp-edge — 监测体基类（已完成）

- [x] 1.1 抽 `BackgroundWatcher<S>`（轮询/缓存/翻转/启停/心跳）<!-- aidcp-edge 232bf2c -->
- [x] 1.2 弹窗监测体子类化，外部契约不变；overlay+login 17/17 <!-- aidcp-edge 232bf2c -->
- [x] 1.3 基类 `msSinceLastOkTick()` 心跳 <!-- aidcp-edge 232bf2c -->
- [ ] 1.4 弹窗监测体非对称去抖（增量，单列，待）
- [ ] 1.5 消费心跳上报"看不见"态（增量，待）

## 2. aidcp-edge — 监测体清单（已完成）

- [x] 2.1 `watcher-supervisor.ts` + `main.ts` 清单注册 <!-- aidcp-edge 52a5ce5 -->

## 3. 协议（已落 +3；需扩到最终集）

- [x] 3.1–3.5 首批 3 消息（`detected`/`open`/`items`）两端逐字一致 + 计数 44→47 + docs + AC-PROTO <!-- cloud c271c4c / edge a11bcc9 -->
- [x] 3.6 **扩到最终集**：`notification.open`→"仅导航首页"；加 `notification.home`/`browse_comments`/`browse_likes`/`browse_follows`/`back_home`；两份 `protocol.ts` 逐字一致 + payload + MessageMap + `command-bridge` 各 action + EdgeCommand action + `docs/protocol.md`；AC-PROTO 实为 **54**（并发 publish.command/result 已并入）<!-- cloud e5b7f60 / edge 52bdcb2 / docs -->（D9）

## 4. aidcp-edge — 通知监测体（已完成）+ 巡视 handler（需重构）

- [x] 4.1 `notification-monitor.ts` 盯未读、sticky 不重置、epoch 单调 <!-- aidcp-edge 52a5ce5 -->
- [x] 4.2 `main.ts` 无→有上报 `notification.detected` <!-- aidcp-edge 52a5ce5 -->
- [x] 4.3 **重构完成**：复合 handler 拆为 `openNotificationsHome`(导航+上报 `notification.home`)、`browseNotificationComments`(进评论和@+滚动+抽取→`notification.items`)、`viewNotificationCategory`(likes/follows 看一眼清未读)、`notification.back_home`→复用 home；选择器 best-effort 待真机校准；失败如实回执/上报空。edge typecheck + 全量 254/254 <!-- aidcp-edge 52bdcb2 -->（D4/D5/D9）
- [x] 4.4 监测体单测（sticky/翻转/epoch）<!-- aidcp-edge 52a5ce5 -->
- [ ] 4.5 各分类 handler 单测（导航/抽取/回执形状；失败上报空）

## 5. aidcp-cloud — 基础设施 + 12 角色 + 看门狗兜底

### 5.A 基础设施（非角色）
- [ ] 5.A1 **发命令统一暂停出口**：`role-dispatcher` 把 `sendCommand` 包成 `send(cmd, 来源:'browse'|'excursion')`，所有 ~10 翻译块 + 失败兜底滚动都走它；巡视期（`ctx.excursion.active`）扣 browse、放 excursion；登记可清理（D7）
- [ ] 5.A2 `isHardPaused(edgeId)` 注入闭包（包 ws-server pausedEdges）；`handler.ts` 加 `notification.detected/home/items → *.arrived` 入口转换（D7/D9）
- [x] 5.A3 `SessionContext` 加 `excursion`（active/epoch/phase/lastHandledEpoch/processedCategories）+ browseSuspended + notifiedItemKeys；`reset()` 清瞬时态 + 暂停开关、保留 notified/visited（D2，断连不冻结）<!-- aidcp-cloud d20f10e -->
- [x] 5.A0 事件契约：event-bus/types.ts 加 11 RoleName + ~16 通知事件（*.arrived 入口 + 角色间衔接）+ NotificationCategory <!-- aidcp-cloud d20f10e -->
- [ ] 5.A2b `handler.ts` 加 `notification.detected/home/items → *.arrived` 入口转换
- [ ] 5.A4 从验证码协调器抽出共享飞书告警原语（resolveChatId+sendCard+冷却），供发飞书角色注入复用（D8）

### 5.B 12 角色（各为 BaseRole，注册进 roles[]，逐个单测：喂入事件→断言出事件/命令）
- [ ] 5.B1 `notification_gatekeeper` 准入（同步无 LLM；硬停/在跑/epoch 三查；admit 写 ctx.excursion）
- [ ] 5.B2 `browse_suspender` 暂停浏览（翻 ctx.excursion 暂停开关）
- [ ] 5.B3 `notification_home_opener` 打开通知首页（安全点 → `notification.open`）
- [ ] 5.B4 `notification_triage` 分诊（按优先级挑未读未处理类；记 processedCategories；无则 `triage_done`）
- [ ] 5.B5 `notification_comment_browser` 评论和@浏览（→ `browse_comments`）
- [ ] 5.B6 `notification_like_browser` 赞和收藏浏览（→ `browse_likes`，v1 看一眼 → `category_handled`）
- [ ] 5.B7 `notification_follow_browser` 新增关注浏览（→ `browse_follows`，v1 看一眼 → `category_handled`）
- [ ] 5.B8 `notification_classifier` 内容分类（评论 items → worthy/empty/failed，校验 epoch）
- [ ] 5.B9 `notification_deduper` 去重（仅成功路径推进 seenItemKeys）
- [ ] 5.B10 `notification_notifier` 发飞书（复用 5.A4，失败不吞，仍报）
- [ ] 5.B11 `notification_return_home` 返回首页（→ `back_home`，触发分诊下一轮）
- [ ] 5.B12 `excursion_resumer` 恢复浏览（收敛 `triage_done`+各失败终止 → 关暂停 + `feed.entered{back_to_feed}`，ctx.excursion.active 幂等）

### 5.C 看门狗兜底（改现有角色，不新增）
- [ ] 5.C1 `session-monitor-role`：确认健康巡视靠每步 `action.completed` 续会话命；只在边缘真死挂（无事件）才结束会话；idle_nudge 的滚动属 browse 来源、被 5.A1 暂停出口扣住。**不设巡视级计时器**（D6）

## 6. 验证与部署
- [ ] 6.1 两仓 `typecheck` → `test:acceptance`（AC-PROTO 新计数、AC-RISK/AC-PUB 红线）→ `test`
- [ ] 6.2 按 sub-repo 分节回写进度；**不碰 edge 残留 WIP（chrome-launcher）**
- [ ] 6.3 `openspec validate notification-monitor --strict`
- [ ] 6.4 cloud 改动按 §5 安全序列部署 ECS，部署后追加 `<!-- <date> deployed -->`
- [ ] 6.5 真机校准：通知首页各类未读探测、三类列表选择器、优先级、"看一眼是否真清未读"、评论/@ 发飞书、巡视后浏览恢复、断连后无残留暂停
- [ ] 6.6 `/opsx:archive` 归档（合并进 `notification-monitoring` + `browse-loop-resilience`）
