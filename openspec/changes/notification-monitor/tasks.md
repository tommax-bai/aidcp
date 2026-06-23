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
- [x] 4.5 各分类 handler 单测（导航/抽取/回执形状；失败上报空）：5 例离线逻辑级，cdp 桩；全量 259/259 <!-- aidcp-edge dbf1ba2 -->（D4/D5）

## 5. aidcp-cloud — 基础设施 + 12 角色 + 看门狗兜底

### 5.A 基础设施（非角色）
- [x] 5.A1 **发命令统一暂停出口**：`role-dispatcher` 把注入闭包改名 `rawSendCommand`，新增 `sendCommand` 方法做软暂停闸——巡视期（`ctx.browseSuspended`）扣 browse 类命令（含失败兜底滚动）、放行巡视命令 + session.end；全部 ~13 翻译块/兜底无侵入经此单点（D7）<!-- aidcp-cloud da5a74a -->
- [x] 5.A2 `isHardPaused(edgeId)` 注入闭包（server 接 `ws-server.isEdgePaused`）；gatekeeper 据此放弃巡视（D7）<!-- aidcp-cloud da5a74a -->
- [x] 5.A3 `SessionContext` 加 `excursion`（active/epoch/phase/lastHandledEpoch/processedCategories）+ browseSuspended + notifiedItemKeys；`reset()` 清瞬时态 + 暂停开关、保留 notified/visited（D2，断连不冻结）<!-- aidcp-cloud d20f10e -->
- [x] 5.A0 事件契约：event-bus/types.ts 加 11 RoleName + ~16 通知事件（*.arrived 入口 + 角色间衔接）+ NotificationCategory <!-- aidcp-cloud d20f10e -->
- [x] 5.A2b `handler.ts` 加 `notification.detected/home/items → *.arrived` 入口转换 <!-- aidcp-cloud da5a74a -->
- [x] 5.A4 发飞书原语：**偏离设计**——未从验证码协调器抽公共类，改为 server 注入 `notifyComments` 闭包（复用 `messenger.sendText` + `resolveDefaultChatId`），notifier 角色消费；更轻、不动 AC-RISK 验证码已测路径。无群则记错不吞（D8）<!-- aidcp-cloud da5a74a -->

### 5.B 12 角色（各为 BaseRole，注册进 roles[]；命令翻译：`notification.opening{open|back}`→open_notifications/notification_back_home，`notification.browse_category`→browse_notification_*）
> 全部 12 角色 + 命令翻译 + server 接线一并落在 <!-- aidcp-cloud da5a74a -->；单测见下 6.1。
- [x] 5.B1 `notification_gatekeeper` 准入（同步无 LLM；硬停/在跑/epoch 三查；admit 写 ctx.excursion）
- [x] 5.B2 `browse_suspender` 暂停浏览（翻 ctx 暂停开关 + browse.suspended）
- [x] 5.B3 `notification_home_opener` 打开通知首页（browse.suspended → opening{open}）
- [x] 5.B4 `notification_triage` 分诊（优先级 评论>赞>关注；选中即记 processedCategories 保收敛；无则 `triage_done`）
- [x] 5.B5 `notification_comment_browser` 评论和@浏览（→ browse_category{comments,scrollMax}）
- [x] 5.B6 `notification_like_browser` 赞和收藏浏览（→ browse_category{likes}；ok:true → category_handled；ok:false 交 resumer）
- [x] 5.B7 `notification_follow_browser` 新增关注浏览（→ browse_category{follows}；同上）
- [x] 5.B8 `notification_classifier` 内容分类（v1 评论/@皆 worthy、滤空；异常 → classify_failed）
- [x] 5.B9 `notification_deduper` 去重（新项→worthy；全已通知/空→all_seen+category_handled；水位仅 notifier 成功后推进）
- [x] 5.B10 `notification_notifier` 发飞书（成功推水位+notified；失败不吞、不推水位、仍 category_handled 收尾）
- [x] 5.B11 `notification_return_home` 返回首页（category_handled → opening{back}）
- [x] 5.B12 `excursion_resumer` 恢复浏览（收敛 triage_done + classify_failed + 巡视命令 ok:false → endExcursion 关暂停先于 feed.entered；幂等）

### 5.C 看门狗兜底（改现有角色，不新增）
- [x] 5.C1 `session-monitor-role`：让 `notification.detected/home/items.arrived` 也刷新最后活动时间——巡视期每步回执续会话命，不被 idle 误判；idle_nudge 滚动属 browse、被 5.A1 暂停出口扣住。**未设巡视级计时器**（D6）<!-- aidcp-cloud db250e5 -->

## 6. 验证与部署
- [x] 6.1 两仓回归全绿：cloud typecheck✓ / test:acceptance 18/18 / 全量 208/208（含 16 通知例）；edge typecheck✓ / test:acceptance 11/11 / 全量 259/259（含 5 通知例）<!-- aidcp-cloud db250e5 / aidcp-edge dbf1ba2 -->
- [x] 6.2 按 sub-repo 分节回写进度；edge WIP（chrome-launcher）未触碰 <!-- 本仓 -->
- [x] 6.3 `openspec validate notification-monitor --strict` → valid
- [x] 6.4 cloud 按 §5 安全序列部署 ECS：备份(cloud.bak.20260620-134048.tar.gz + .env.bak)→rsync(排除 .env/node_modules/.git，40 文件)→restart→健康检查全过（active / 8787 监听 / accounts 表自建 seed / RiskController·ConceptStore·AccountStore 就绪=PG 通 / RoleDispatcher 12 通知角色就绪 / 飞书长连接已建立 / 无 error / isales 未触碰）。**决策：用户选全量部署当前主干**——本次连带把面板(默认禁用)·账号主表·此前已合并主干一起上线，非仅 notification。<!-- aidcp-cloud db250e5 --> <!-- 2026-06-20 deployed -->
- [ ] 6.5 真机校准（本机，进行中）：本机 edge 连 ECS（ws://121.89.85.150:8787）跑真实小红书，校准——通知首页各类未读探测、三类列表选择器、优先级、"看一眼是否真清未读"、评论/@ 发飞书、巡视后浏览恢复、断连后无残留暂停
  - [x] 6.5.1 **接线漏修（首个校准发现）**：边缘入口 `edge-client.ts` 的 onMessage 主动命令白名单漏接 5 个 `notification.*`（open/browse_comments/browse_likes/browse_follows/back_home），命令在到达 `browseHandler` 前于"其他主动消息暂忽略"被静默丢弃 → 巡视无回执 → `excursion_resumer` 永不收敛 → 浏览永挂 → 会话级看门狗 idle≈240s 杀整会话（真机日志：count=0 触发巡视=fail-open 设计，非 bug；挂死才是 bug）。修：白名单补 5 个类型放行到 browseHandler（处理分支 4.3 / 协议 3.6 / command-bridge 映射均早已就位，唯入口路由漏同步）；加回归断言守"离开流程命令不得入口静默丢弃"红线（对齐 browse-loop-resilience spec §"放行该离开流程自身的命令"）。edge typecheck✓ / acceptance 11/11 / 全量 288/288（含 5 新通知路由例）<!-- aidcp-edge 0c28e32 -->
  - [x] 6.5.2 **闭环端到端真机验证通过**：edge 连 ECS 跑真账号，完整巡视链路跑通——`notification.open`→`notification.home`(真未读 评论1/赞1/关注1)→`browse_comments`(抽报50条)→`browse_likes`/`browse_follows`(看一眼清未读)→各 `back_home`→`excursion_resumer` 发 `navigation.back(back_to_feed)`→**恢复 feed 浏览 + 进笔记深读**；5 个 `notification.*` 命令全实地执行成功，无 242s 挂死。<!-- 2026-06-23 verified -->
  - [x] 6.5.3 **未读探测假阳性修复（校准发现）**：真机观察「没通知也频繁跳通知页」。活页面 CDP 诊断坐实——通知入口真实结构 `<a href="/notification"><div class="badge-container"><svg class="reds-icon"/><!----></div>…</a>`，旧探测用宽选择器 `[class*="badge"]`(命中常驻 `badge-container`)/`[class*="red"]`(命中常驻 `reds-icon`，小红书=RED 设计系统前缀 `reds-`)→ 几乎永远判「有未读」。改为结构判据：未读 = 通知入口角标容器内**图标 svg 之外的可见真实角标元素**（条件渲染，空槽=无未读；红点无数字也算未读 count:0，不漏真通知）。活页面双向验证（无角标→false/注入数字→true·count/注入红点→true·0/撤销→false）+ jsdom 回归单测（旧单测全用假 CDP 绕过选择器，故漏网）。edge typecheck✓ / acceptance 11/11 / 全量 292/292（含 4 新探测例）<!-- aidcp-edge 223cb01 -->
  - [ ] 6.5.4 余下校准项（三类列表选择器精度 / 优先级 / "看一眼是否真清未读"是否消红点 / 评论@发飞书内容质量）继续在真机走；另存疑：真机出现过 CDP 断连致页面关闭（`CDP 未连接`），待观察是否稳定复现。**真机校准包就绪**：探针 P-1~P-5 + 17 步清单 + 退出条件见 `calibration-kit-6.5.4.md`
  - [x] 6.5.5 **上真机前飞行审计 + 静态可修 bug 全修（多 agent workflow + 对抗性复审）**：对四项校准 + CDP 断连疑点做代码级审计（27 agent，12 bug 经独立 skeptic 核验），把**不需真机即可坐实**的缺陷全部修掉再上真机；提交前再过一道对抗性 diff 复审（5 维度），修掉复审揪出的 must-fix。落修：
    - **CDP-NOTIF-1（红线）**：三个通知 handler 的宽 catch 吞 `CdpDisconnectedError` → 断连时假报「无未读/空items/已看」并绕过自动重连 → 改为重抛冒泡到主循环重连；巡视中断连重连后发诚实 `action.completed{notification_back_home, ok:false, cdp_reconnect_aborted}` 触发云端 `excursion_resumer` 关暂停回 feed（否则 `excursionActive` 永真 → 发命令暂停出口扣住 feed → 看门狗 ~240s 杀会话 + gatekeeper 永久忽略新通知）。
    - **NB-1/NB-2/NM-C-3**：`notification.home` 的 per-tab 未读探测**原样复用了 6.5.3 删掉的宽选择器** `[class*="badge"]/[class*="red"]`（命中常驻 `reds-icon`/`badge-container`）+ `isNaN→1` 伪造 → 抽出共享结构判据 `realBadgeScanFnJs`（svg-skip + reds-icon 排除 + 可见性）单一真相复用、收紧到真实 tab、只认数字叶子角标（≤3 位）；清空账号诚实 0。
    - **NM-C-1**：「看一眼清未读」丢弃点击返回值、未命中也假报 `viewed` → 改为捕获命中、未命中诚实 `ok:false no_target`。
    - **CDP-NOTIF-2**：`cdp.unrecoverable` 后通知 watcher 仍轮询死 client 刷僵尸日志 → `main.ts` 订阅 unrecoverable 停 / reconnected 重启。
    - **NCQ-1/2 + NB-5**：正文缺失发空串（不回退整行 blob）+ code-point 安全截断（不劈裂 emoji）+ itemKey 排除 profile 链；云端 `notificationItemKey` 回退键仅剥**尾部**时间戳（复审 must-fix：早期未锚定正则会误剥内联数字/日期 → 不同评论撞键静默丢失）+ classifier 防御过滤（拒 正文==用户名 / 纯动作标签）。
    - **复审残留（诚实记入 item a 真机校准）**：per-tab 探针仍有「短数字叶子时间戳」与「多 category 标签拼接容器泄漏(NM-2)」的潜在假阳性——复审确认**生产 3 类布局下不触发**、blast radius 仅软优先级不碰访问门、不伪造成功；真机据真实 DOM 收口。
    - edge typecheck✓ / acceptance 11/11 / 全量 312/312；cloud typecheck✓ / acceptance 26/26 / 全量 329/329。<!-- aidcp-edge 83212e9 / aidcp-cloud f912f75 -->（真机 a/c 校准仍待 6.5.4）
- [ ] 6.6 `/opsx:archive` 归档（合并进 `notification-monitoring` + `browse-loop-resilience`）← 真机验收通过后
