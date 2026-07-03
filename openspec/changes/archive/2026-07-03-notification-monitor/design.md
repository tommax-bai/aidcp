## Context

边缘后台监测体检测「消息」未读 → 上报；云端用**事件驱动多角色巡视**处理，镜像浏览侧"评估→处理→回来再评估"的循环。本设计已多轮迭代收敛（取代早期"单协调器"与中途的粗粒度版本）：按浏览侧"一步一角色"的粒度拆，加一个**通知分诊**角色驱动"按优先级一类一类处理"的拟人循环，并把"进入不同分类的浏览"**按分类拆成独立角色**。

边缘侧已实现并提交（监测体基类、清单、协议 +3、未读监测体、`notification.open` 复合 handler）；本设计把 `notification.open` 复合 handler 改为**按分类原子命令**，并新增云端 11 个角色（+1 已有 SessionMonitor 改动）。

## Goals / Non-Goals

**Goals:** 拟人——进通知页后按优先级（评论和@ > 赞和收藏 > 新增关注）一类一类看，评论/@ 发飞书，三类都"看一眼"清未读（避免总红点不灭反复触发）；一步一角色、按分类拆，便于单独迭代；结束**纯事件驱动、不设巡视计时器**；恢复有单一出口、保证不卡死。

**Non-Goals（YAGNI / 已拍板）:** 不设巡视级总超时（靠事件 + 会话级看门狗兜底）；v1 赞收藏/新增关注只看一眼清未读、不发飞书、不抽取；不复用硬停 `pauseEdge`；不做中央仲裁器 / saga 引擎 / 引用计数暂停 / 状态持久化。

## Decisions

### D1 角色拆分（云端 12 个；按分类拆浏览）
| 角色 | 职责 | in → out | 命令 |
|---|---|---|---|
| `notification_gatekeeper` 准入 | 能否开巡视（未硬停 / 没在跑 / epoch 未处理） | `notification.detected.arrived` → `excursion.requested` / 忽略 | — |
| `browse_suspender` 暂停浏览 | 打开"暂停浏览"开关（存 ctx.excursion） | `excursion.requested` → `browse.suspended` | — |
| `notification_home_opener` 打开通知首页 | 安全点导航到通知首页 | `browse.suspended`/`action.completed` → 边缘报各类未读 | `notification.open`（仅导航首页） |
| `notification_triage` 分诊 | 挑优先级最高、本趟未处理的未读类；无则完成 | `notification.home.arrived` → `notification.category_selected{类}` / `notification.triage_done` | — |
| `notification_comment_browser` 评论和@浏览 | 进「评论和@」、决定滚动加载、边缘抽取原始项 | `notification.category_selected{comments}` → `notification.items.arrived` | `notification.browse_comments` |
| `notification_like_browser` 赞和收藏浏览 | 进「赞和收藏」、看一眼清未读（v1 不抽取） | `notification.category_selected{likes}` → `notification.category_handled` | `notification.browse_likes` |
| `notification_follow_browser` 新增关注浏览 | 进「新增关注」、看一眼清未读（v1 不抽取） | `notification.category_selected{follows}` → `notification.category_handled` | `notification.browse_follows` |
| `notification_classifier` 内容分类 | 挑值得通知的评论/@（校验 epoch） | `notification.items.arrived` → `notification.classified`/`classify_empty`/`classify_failed` | — |
| `notification_deduper` 去重 | 滤已通知、推进水位（仅成功路径） | `notification.classified` → `notification.worthy`/`all_seen` → `notification.category_handled` | — |
| `notification_notifier` 发飞书 | 推飞书（复用验证码告警原语） | `notification.worthy` → `notification.notified` → `notification.category_handled` | — |
| `notification_return_home` 返回首页 | 一类处理完返回通知首页，触发分诊下一轮 | `notification.category_handled` → 边缘重报各类未读 | `notification.back_home` |
| `excursion_resumer` 恢复浏览 | 收敛所有终止 → 关暂停 + 回信息流 | `notification.triage_done` / `classify_failed` / 任一命令回执 ok:false → `feed.entered{back_to_feed}` | `back`（复用） |

### D2 会话上下文新增 `ctx.excursion`（防竞态共享底座）
`{ active, epoch, phase, lastHandledEpoch, perCategoryUnread, processedCategories:Set, seenItemKeys:Set }`。跨角色真相只读这一份，**绝不偷看兄弟角色私有变量**（镜像 visited/sourcePageType）。`reset()`/`endSession`/`restartSession` **显式清** active/epoch/phase/lastHandledEpoch/processedCategories **和暂停开关**（断连/结束不残留），**保留** seenItemKeys。

### D3 分诊循环（拟人、必收敛）
分诊在通知首页按优先级挑"有未读 且 本趟未处理"的最高类；选中即记入 `processedCategories`（即使红点没清也不会重挑 → 最多 3 轮必收敛）；无可处理 → `triage_done`。处理完一类 → 返回首页 → 边缘重报未读 → 分诊再来。

### D4 按分类拆浏览 + 各自命令（已拍板）
三个 per-category 浏览角色各驱动各自命令（`browse_comments/likes/follows`，边缘 handler 各知各的选择器），端到端独立、互不影响迭代。代价：协议多几条（见 D9）。赞收藏/follows v1 仅"进入清未读"，边缘可共用 enter+mark-read 辅助。

### D5 下游只对评论这一类
`comment_browser` 抽出项 → 分类 → 去重 → 发飞书 → `category_handled`；赞收藏/follows 浏览角色看一眼直接 `category_handled`。

### D6 结束：纯事件驱动、无计时器；resumer 收敛（BackToFeed 同款）
不设巡视总超时。每步都有事件回来（成功回执 / `ok:false` / 分类 empty|failed），边缘 handler 内部有界等待、绝不无限挂。`excursion_resumer` 订阅所有终止事件（`triage_done` + 各失败），统一**一次**"关暂停 + 回信息流"，`ctx.excursion.active` 幂等。断连由 `edge.hello → restartSession`（必须清暂停开关）。真死挂（边缘啥都不回）由**已有会话级看门狗**兜底（健康巡视靠每步回执续命，真死才结束会话，也清暂停，不永久冻结）。

### D7 暂停 = 基础设施（要真建）
今天没有"发命令的统一出口"——`sendCommand` 在 ~10 个事件块各自直接调。要**真建** `send(cmd, 来源=browse|excursion)` 统一出口，巡视期扣 browse、放 excursion，连失败兜底滚动也走它；不复用 `pauseEdge`（它丢全部帧含巡视自己的命令）。`isHardPaused()` 注入闭包给准入读。

### D8 边轻云重 / 状态单写
边缘检测 + 抽**原始**项（同 page.cards/note.detail），云端判要不要通知。巡视是瞬时操作，**不**迁移账号风控态（仅验证码迁移，风控终态云端单写）。飞书走注入闭包、不走命令通道、不在恢复关键路径上。

### D9 协议（最终集）
- 复用/改：`notification.detected`（信号）、`notification.open`（改为"仅导航首页"）、`notification.items`（评论/@ 项）。
- 新增：`notification.home`（边缘报各类未读，喂分诊）、`notification.browse_comments`/`browse_likes`/`browse_follows`（cloud→edge 各分类进入+读取）、`notification.back_home`（返回通知首页）。
- `command-bridge` 加各 action→message 映射；两份 `protocol.ts` 逐字一致 + AC-PROTO 计数 + `docs/protocol.md` 同步；恢复复用 `feed.entered{back_to_feed}`→back，不新增命令。

## Risks / Trade-offs
- [协议条数偏多（per-category 命令）] → 这是 D4 拍板的独立性代价；可接受，AC-PROTO 计数同步即可。
- [真死挂只由会话级看门狗兜底，结束的是整个会话而非仅恢复浏览] → 仅 bug 场景；健康巡视每步回执会续会话命；不引入巡视计时器（按拍板）。
- [断连残留暂停开关 = 永久冻结] → **必须**在 restartSession/reset 清暂停开关 + ctx.excursion（最高优先须修）。
- [分诊死循环] → processedCategories 守卫，最多 3 轮收敛。
- [边缘复合 handler 已提交] → 需重构为按分类原子 handler（未上线，重构无碍）。

## Migration Plan（在已提交边缘基础上）
1. 协议扩展到最终集（+`home`/`browse_comments`/`browse_likes`/`browse_follows`/`back_home`，`notification.open` 改语义）；两端同步 + AC-PROTO + docs。
2. 边缘：复合 handler 重构为按分类原子 handler + 首页未读上报 + 返回首页；监测体不变。
3. 基础设施：`send(cmd,provenance)` 统一暂停出口 + `isHardPaused` + 共享飞书原语 + `ctx.excursion`。
4. 云端 11 角色逐个实现并单测（每个：喂入事件→断言出事件/命令）；SessionMonitor 兜底确认（健康巡视不误结束）。
5. 两仓回归 → §5 部署（真机校准各分类选择器、优先级、看一眼是否清未读）。

## Open Questions
- 赞收藏/新增关注 v1 确认为"看一眼清未读、不发飞书、不抽取"（已按此）；未来要 follows 也飞书 = 只动 `notification_follow_browser` + 接通知。
- 「评论和@」是否默认 tab：若是，`browse_comments` 内省一步。
- `notification.back_home` 能否复用带 targetPage 的 back：倾向独立命令（语义清晰），实装时再定。
