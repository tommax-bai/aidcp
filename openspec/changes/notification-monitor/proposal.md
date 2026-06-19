## Why

需要一个"通知监控"：后台发现"消息"有未读 → 暂停浏览、去通知页看「评论和@」→ 把评论/@ 的用户名与内容上报云端并发飞书；点赞/收藏/新增关注一律忽略。它与已上线的验证码监测同构（边缘后台监测体 → 上报 → 云端协调 → 飞书），应复用同一套骨架。

借此把监测体子系统做**健壮 + 可扩展**（设计见 design.md，业界模式分析详见 2026-06-19 workflow）：当前有 3 个"监测体形状"的东西、各写各的契约，两套各自为政的暂停（边缘本地软闸 + 云端传输硬停 `pauseEdge`），无"谁此刻拥有执行端"的单一约束，新增一个要手工穿多处文件。本 change 取**务实最小版**：抽出统一后台监测体基类 + 监测体清单、引入"临时离开式"软中断原语（区别于验证码的"阻塞式"），按 YAGNI 砍掉超前抽象、留干净扩展缝。

## What Changes

- **edge / 监测体基类（行为不变重构）**：从现有弹窗监测体抽出统一的后台监测体基类（自走时钟轮询、状态缓存、翻转才上报一次、启停幂等），子类只填"检测什么 + 怎么归类"；现有弹窗监测体改为其子类，外部契约逐字不变（现有测试护栏）。补两项健壮性：① 自身存活——记录"上次成功检测时间"，长时间没成功就上报一个"看不见"的独立态，**绝不把检测不了当成没情况**；② 非对称去抖——进入阻塞态快、退出慢（防半渲染弹窗刷"出现→消失"风暴）。
- **edge / 监测体清单**：用一个小的监测体清单（启动全部 / 停止全部）替掉 `main.ts` 里手工接线块；新增监测体只登记一行，关停不漏。
- **edge / 通知监测体（新）**：按基类实现，盯"消息"未读标记；fail-open（漏一条评论无所谓）、软中断（误触发去看通知会打断浏览，故不可用验证码那套 fail-closed 硬闸）；探测失败保持上次计数、**绝不把未读重置为 0**；翻转（无→有）只上报一次 `notification.detected`。
- **edge / 通知巡视命令（新，仿 `profile.open` 复合命令）**：收到 `notification.open` → 导航通知页 → 切「评论和@」tab → 抽取**原始结构化**评论/@ 项（用户名 / 内容 / 笔记标题 / 稳定 itemKey）→ 上报 `notification.items`；分类与是否通知由云端判，边缘不决策。
- **cloud / 通知协调器（新）**：订阅 `notification.detected` → 若**未被验证码硬停**（一次 `isHardPaused` 读）→ 在"发命令给执行端的统一出口"挂**抑制开关**（扣住浏览类命令、放行巡视类命令，命令打来源标记）→ 等执行端当前动作报完成 → 发 `notification.open` → 收 `notification.items` → 对评论/@ 去重后发飞书（复用从验证码协调器抽出的统一告警发送）→ **无论成功/空/超时/被验证码抢占，都执行"回 feed + 解除抑制"**。
- **cloud / 看门狗感知巡视**：让"长时间无动静自动结束会话"的看门狗在巡视期间知道"是有意暂停、不算空闲"，巡视结束再恢复计时（否则会在巡视半路把会话结束）。
- **协议（三处同步，+3 消息类型，44→47）**：`notification.detected`（edge→cloud 信号）、`notification.open`（cloud→edge 命令，加 `open_notifications → notification.open` bridge 映射）、`notification.items`（edge→cloud 上报）。两份 `protocol.ts` 逐字一致 + `Record<MessageType,true>` + AC-PROTO-02 计数 44→47 + `docs/protocol.md`。
- **不做（YAGNI，留到第 3 个中断源 / 第 4-5 个监测体再做）**：集中中断仲裁器、多状态流程机 + 每步超时、引用计数暂停登记、流程状态持久化、合并轮询、通用 `watcher.signal` 信封。本次用"线性巡视函数 + try/finally + 一个总超时 + 正在巡视布尔"。

## Capabilities

### New Capabilities
- `notification-monitoring`: 通知监测体 + 临时离开式巡视 + 评论/@ 提取与飞书通知；忽略赞/藏/关注；保证恢复、去重、不丢真消息、不被自动结束误伤。

### Modified Capabilities
- `browse-loop-resilience`: 新增「临时离开式软中断：在统一命令出口安全点暂停浏览、跑有界巡视、保证恢复；自动结束看门狗在有意暂停期间不得开火」。

## Impact

- **edge（aidcp-edge）**：`src/browse/overlay-monitor.ts`（抽基类 + 子类化 + 去抖 + 心跳）；新 `src/browse/notification-monitor.ts`、新 `src/browse/watcher-supervisor.ts`（或同义小件）；`src/main.ts`（清单接线替手工块 + 接 `notification.detected`）；`src/browse/browse-session.ts`（`notification.open` 复合命令 handler，仿 `profile.open`）；`src/comm/protocol.ts`（3 消息）。
- **cloud（aidcp-cloud）**：新 `src/orchestrator/notification-coordinator.ts`（或 `src/comm/`，仿验证码协调器）作为 EventBus 订阅者注册；`src/orchestrator/role-dispatcher.ts`（命令出口抑制开关 + 命令来源标记 + `isHardPaused` 读）；`src/agents/session-monitor-role.ts`（巡视感知）；`src/comm/command-bridge.ts`（`open_notifications → notification.open`）；`src/comm/handler.ts` + `src/server.ts`（接线 detected/items）；`src/feishu/`（评论通知卡 + 抽出统一告警发送）；`src/comm/protocol.ts`（3 消息，与 edge 逐字一致）。
- **docs**：`docs/protocol.md`（3 消息 + 头部计数 47）。
- **风险面**：协议三处同步（AC-PROTO 47、typecheck）；不得破坏验证码阻塞式路径与 `AC-RISK-*`/`AC-PUB-*` 红线；巡视命令必须仍走执行端正常通道（通知页若也弹验证码仍被硬闸）；状态单写——通知巡视是瞬时操作，**不**迁移账号风控态（仅验证码迁移）。
