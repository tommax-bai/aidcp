## 1. aidcp-edge — 监测体基类（行为不变重构）+ 健壮性

- [x] 1.1 从 `src/browse/overlay-monitor.ts` 抽出统一后台监测体基类 `BackgroundWatcher<S>`（自走时钟轮询、状态缓存、翻转 diff 只上报一次、启停幂等）；抽象点仅 `probe()` + `equals()`；容错旋钮 `onProbeError:'sticky'|'reset'` + 始终抛出的 `probeNow()`（D1）<!-- aidcp-edge 232bf2c -->
- [x] 1.2 弹窗监测体改为 `BackgroundWatcher<OverlayKind>` 子类，外部契约 `{state; probeNow(); start; stop; tick}` 逐字不变；overlay+login 测试 17/17、typecheck 绿（D1）<!-- aidcp-edge 232bf2c -->
- [x] 1.3 基类加自身存活 `msSinceLastOkTick()`（暴露度量，是否升级告警交上层）；不把"探测不了"并入 none（D2）<!-- aidcp-edge 232bf2c -->
- [ ] 1.4 弹窗监测体加非对称去抖：进入阻塞态快、退出连续 2-3 次确认（内联每类计数）（D2）<!-- 改变 captcha 翻转时机，单独做、避免混进纯重构 Task 1；待 -->
- [ ] 1.5 消费 `msSinceLastOkTick`：长时间看不见 → 上报"看不见"态（degraded 信号）<!-- 待，可与协议阶段合并 -->

> Task 1 已落地核心（基类 + 子类化 + 心跳，行为不变、已验证）。1.4/1.5 为增量行为，单列。

## 2. aidcp-edge — 监测体清单

- [ ] 2.1 新增小清单件持 `Watcher[]` + `startAll/stopAll`；替掉 `src/main.ts` 手工接线块（仅弹窗监测体，行为保持）（D3）

## 3. 协议三处同步（+3 消息，44→47）

- [x] 3.1 `aidcp-cloud/src/comm/protocol.ts`：加 3 消息 + payload（含 `NotificationItem`）+ MessageMap <!-- aidcp-cloud c271c4c -->
- [x] 3.2 `aidcp-edge/src/comm/protocol.ts`：与 cloud 逐字一致 <!-- aidcp-edge a11bcc9 -->
- [x] 3.3 `command-bridge.ts`：`open_notifications → notification.open`；EdgeCommand action += open_notifications <!-- aidcp-cloud c271c4c -->
- [x] 3.4 `docs/protocol.md`：3 消息行 + 头部计数 44→47 <!-- control repo -->
- [x] 3.5 两仓 typecheck + acceptance（AC-PROTO-02=47，两端一致；cloud 18/18、edge 11/11） <!-- 2026-06-19 -->

## 4. aidcp-edge — 通知监测体 + 巡视命令

- [ ] 4.1 新 `src/browse/notification-monitor.ts`：按基类盯"消息"未读标记；软中断 + fail-open + sticky（探测失败保持上次、**绝不重置未读为 0**）；epoch=每次无→有翻转单调 +1；翻转只上报一次 `notification.detected`（D5/D7）
- [ ] 4.2 清单登记通知监测体（一行）；`main.ts` 接 `notification.detected` 上报（D3）
- [ ] 4.3 `src/browse/browse-session.ts`：加 `notification.open` 复合命令 handler（仿 `profile.open`）——导航通知页 → 切「评论和@」tab → 抽**原始** items（用户名/内容/笔记标题/itemKey）→ `notification.items` 上报；选择器 best-effort、标注待真机校准（D5/D9）
- [ ] 4.4 edge 单测：通知监测体 sticky 不重置、翻转上报一次、epoch 单调；`notification.open` handler 抽取与上报形状

## 5. aidcp-cloud — 通知协调器 + 软中断 + 看门狗感知

- [ ] 5.1 `src/orchestrator/role-dispatcher.ts`：在统一命令出口（`sendCommand`/`pushToEdges` funnel）加 browse 抑制开关 + 命令来源标记（browse/excursion）；暴露 `isHardPaused(edgeId)` 读（D4）
- [ ] 5.2 新通知协调器（EventBus 订阅者，注册进 roles[]）：收 `notification.detected` → 若未硬停 → 置"正在巡视"布尔 + 挂抑制 → 等当前动作报完成 → 发 `notification.open` → 收 `notification.items` → 评论/@ 去重后飞书 → 发 `navigation.back` 回 feed；`try/finally` + 总超时保证"解除抑制 + 回 feed + 清布尔"（D4/D5）
- [ ] 5.3 已通知水位/已见集合**仅在确认收到 items 后推进**；超时/失败不推进（D7）
- [ ] 5.4 `src/agents/session-monitor-role.ts`：巡视期间视为有意暂停——不发 nudge、不结束会话，结束后恢复计时（**correctness blocker**，须先于 5.2 生效）（D6）
- [ ] 5.5 `src/feishu/`：评论/@ 通知卡；从验证码协调器抽出统一告警发送（去重/冷却）复用（D5）
- [ ] 5.6 cloud 单测：detected→巡视一次（重复 epoch 不并发）；巡视任意出口都解除抑制+回 feed；巡视期看门狗不开火；失败不推进已通知水位；巡视不迁移风控态

## 6. 验证与部署

- [ ] 6.1 两仓 `npm run typecheck` → `test:acceptance`（AC-PROTO 47、AC-RISK/AC-PUB 红线）→ `test`
- [ ] 6.2 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）；**不碰 edge 残留 WIP（chrome-launcher）**
- [ ] 6.3 `openspec validate notification-monitor --strict` 通过
- [ ] 6.4 cloud 改动按 §5 安全序列部署 ECS（备份→rsync→restart→healthcheck→回滚），部署后追加 `<!-- <date> deployed -->`
- [ ] 6.5 真机校准：通知页/「评论和@」选择器、去抖阈值、巡视总超时；确认评论/@ 发飞书、赞/藏/关注忽略、巡视后浏览恢复
- [ ] 6.6 `/opsx:archive` 归档（delta 合并进 `notification-monitoring` + `browse-loop-resilience`）
