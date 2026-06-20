## Why

需要一个"通知监控"：后台发现"消息"有未读 → 暂停浏览、去通知页看「评论和@」→ 把评论/@ 的用户名与内容上报云端并发飞书；点赞/收藏/新增关注一律忽略。它与已上线的验证码监测同构（边缘后台监测体 → 上报 → 云端协调 → 飞书），应复用同一套骨架。

借此把监测体子系统做**健壮 + 可扩展**（设计见 design.md，业界模式分析详见 2026-06-19 workflow）：当前有 3 个"监测体形状"的东西、各写各的契约，两套各自为政的暂停（边缘本地软闸 + 云端传输硬停 `pauseEdge`），无"谁此刻拥有执行端"的单一约束，新增一个要手工穿多处文件。本 change 取**务实最小版**：抽出统一后台监测体基类 + 监测体清单、引入"临时离开式"软中断原语（区别于验证码的"阻塞式"），按 YAGNI 砍掉超前抽象、留干净扩展缝。

## What Changes

- **edge / 监测体基类（行为不变重构）**：从现有弹窗监测体抽出统一的后台监测体基类（自走时钟轮询、状态缓存、翻转才上报一次、启停幂等），子类只填"检测什么 + 怎么归类"；现有弹窗监测体改为其子类，外部契约逐字不变（现有测试护栏）。补两项健壮性：① 自身存活——记录"上次成功检测时间"，长时间没成功就上报一个"看不见"的独立态，**绝不把检测不了当成没情况**；② 非对称去抖——进入阻塞态快、退出慢（防半渲染弹窗刷"出现→消失"风暴）。
- **edge / 监测体清单**：用一个小的监测体清单（启动全部 / 停止全部）替掉 `main.ts` 里手工接线块；新增监测体只登记一行，关停不漏。
- **edge / 通知监测体（新）**：按基类实现，盯"消息"未读标记；fail-open（漏一条评论无所谓）、软中断（误触发去看通知会打断浏览，故不可用验证码那套 fail-closed 硬闸）；探测失败保持上次计数、**绝不把未读重置为 0**；翻转（无→有）只上报一次 `notification.detected`。
- **edge / 通知巡视命令（新，按分类拆成原子命令，仿 open_note/browse_images/scroll_comments）**：`notification.open`（仅导航通知首页 + 上报各类未读 `notification.home`）、`notification.browse_comments`（进评论和@ + 滚动 + 抽**原始结构化**项 → `notification.items`）、`notification.browse_likes`/`notification.browse_follows`（进入 + 看一眼清未读，v1 不抽取）、`notification.back_home`（返回通知首页）；分类与是否通知由云端判，边缘只抽原始项不决策。
- **cloud / 事件驱动多角色巡视（12 角色，镜像浏览侧；非单协调器）**：进通知首页后由**通知分诊**按优先级（评论和@ > 赞和收藏 > 新增关注）一类一类处理、处理完返回首页再分诊的拟人循环；"进入不同分类的浏览"**按分类拆成独立角色**（评论/赞收藏/关注各一）；评论/@ 走分类→去重→发飞书，赞收藏/关注 v1 看一眼清未读不发飞书。详见 design.md 的 12 角色表。
- **cloud / 暂停与恢复**：在**发命令的统一出口**（需真建）挂"暂停浏览"开关 + 命令来源标记（巡视期扣 browse、放 excursion），不复用硬停 `pauseEdge`；**不设巡视计时器**——结束纯事件驱动，`excursion_resumer` 收敛"分诊完成 + 各失败终止"统一一次"关暂停 + 回信息流"（幂等）；断连由会话重启清暂停开关兜底，真死挂由**已有会话级看门狗**兜底（不永久冻结）。共享状态放 `ctx.excursion`，角色间只经事件 + 该状态协调。
- **协议（三处同步，最终集）**：首批已落 `notification.detected`/`notification.open`/`notification.items`（44→47）；最终再加 `notification.home`（各类未读上报）、`notification.browse_comments`/`browse_likes`/`browse_follows`、`notification.back_home`，并把 `notification.open` 改为"仅导航首页"语义（约 47→52）。两份 `protocol.ts` 逐字一致 + `Record<MessageType,true>` + AC-PROTO-02 计数 + `command-bridge` 各 action 映射 + `docs/protocol.md`。恢复复用 `feed.entered{back_to_feed}`→back，不新增命令。
- **不做（YAGNI，留到第 3 个中断源 / 第 4-5 个监测体再做）**：集中中断仲裁器、多状态流程机 + 每步超时、引用计数暂停登记、流程状态持久化、合并轮询、通用 `watcher.signal` 信封。本次用"线性巡视函数 + try/finally + 一个总超时 + 正在巡视布尔"。

## Capabilities

### New Capabilities
- `notification-monitoring`: 通知监测体 + 临时离开式巡视 + 评论/@ 提取与飞书通知；忽略赞/藏/关注；保证恢复、去重、不丢真消息、不被自动结束误伤。

### Modified Capabilities
- `browse-loop-resilience`: 新增「临时离开式软中断：在统一命令出口安全点暂停浏览、跑有界巡视、保证恢复；自动结束看门狗在有意暂停期间不得开火」。

## Impact

- **edge（aidcp-edge）**：`src/browse/overlay-monitor.ts`（抽基类 + 子类化 + 去抖 + 心跳）；新 `src/browse/notification-monitor.ts`、新 `src/browse/watcher-supervisor.ts`（或同义小件）；`src/main.ts`（清单接线替手工块 + 接 `notification.detected`）；`src/browse/browse-session.ts`（`notification.open` 复合命令 handler，仿 `profile.open`）；`src/comm/protocol.ts`（3 消息）。
- **cloud（aidcp-cloud）**：新增 11 个角色文件（`src/agents/notification-*.ts`：gatekeeper/home-opener/triage/comment-browser/like-browser/follow-browser/classifier/deduper/notifier/return-home + `excursion-resumer`），各为 BaseRole 注册进 `role-dispatcher` 的 roles[]；`role-dispatcher.ts`（发命令统一暂停出口 `send(cmd,provenance)` + 各角色事件→命令翻译 + ctx.excursion）；`src/agents/session-context.ts`（excursion 状态 + reset 清瞬时态/暂停）；`src/agents/session-monitor-role.ts`（兜底确认，不新增计时器）；`src/comm/command-bridge.ts`（各 notification action 映射）；`src/comm/handler.ts` + `src/server.ts`（接线 detected/home/items 入口 + isHardPaused）；`src/feishu/`（评论通知卡 + 抽共享告警原语）；`src/comm/protocol.ts`（最终消息集，与 edge 逐字一致）。
- **docs**：`docs/protocol.md`（3 消息 + 头部计数 47）。
- **风险面**：协议三处同步（AC-PROTO 47、typecheck）；不得破坏验证码阻塞式路径与 `AC-RISK-*`/`AC-PUB-*` 红线；巡视命令必须仍走执行端正常通道（通知页若也弹验证码仍被硬闸）；状态单写——通知巡视是瞬时操作，**不**迁移账号风控态（仅验证码迁移）。
