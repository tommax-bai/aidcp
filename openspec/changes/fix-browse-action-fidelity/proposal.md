## Why

2026-06-17 部署后真机运行又暴露 3 个动作保真 / 决策正确性问题（fix-browse-loop-resilience 已修死锁，但这些是相邻缺陷）：
1. **评论"假滚动"**：`scroll_comments` 命中一个未校准、不可滚动的容器，`scrollBy` 成空操作，但代码**从不校验 scrollTop 位移**就回报 ok:true「滚动完成 N 次」——深读的"看评论"实际从未发生（33s 全是每次滚动前的 `cardGap` 空等）。
2. **关注误 skip**：小红书主页**不公开作品数**（live DOM 实证：只有 关注/粉丝/获赞与收藏），`postsCount=0` 是"无此数据"；但 follow-agent prompt 仍摆着"作品数"项、LLM 仍据此 skip 掉 130 粉丝/6707 获赞的真创作者；而真正能判质量的"获赞与收藏"从未被抽取、未进决策。
3. **back→404 + 返回页型错**：搜索来源会话 `history.back()` 退回到 token 过期的搜索笔记 → 小红书 404（瞬态，由 back_to_feed 的 `Page.navigate(/explore)` recover）；更深层是 cloud 发 back 时**丢掉 `sourcePageType`**，搜索会话被错误拽回 /explore 而非搜索结果。

这些让深读链路"看起来在做、其实没做对"，必须修复以保证动作真实、决策正确、返回页型正确。

## What Changes

- **[edge] 评论滚动真执行**：运行时按 overflow 能力定位真正可滚动祖先（从评论节点上溯 `scrollHeight>clientHeight && overflowY:auto/scroll`），记录滚动前后 `scrollTop`，**按实测位移如实回报**（有位移→`scrolled=N/total`；无位移→`no_scroll`，区别于 `no_target`）；滚动间隔由 `cardGap(3-12s)` 改为 `scroll(0.4-2s)` 预设。
- **[both] 关注决策只用真实信号**：follow-agent prompt **移除"作品数"项**（平台永不提供），改以 粉丝数 + 获赞与收藏 + 内容相关性判定；edge 从 `.user-interactions` **新增抽取"获赞与收藏"**，经协议串到 follow-agent。`postsCount` 字段保留在线协议（向后兼容）但不再进决策。
- **[both] back 按页型返回 + 404 健壮**：cloud 在 `feed.entered(back_to_feed)` 把 `pageType` 透传为 `targetPage`；edge `navigateBack` 硬化——`search` 分支补 recover、新增 404/坏页探测（命中"笔记不见了"等标记或 0 卡即 `Page.navigate(exploreUrl)` 兜底并校验健康后再上报），消除瞬态 404 与"recover 失败→静默 0 卡→再死锁"的漏洞。

## Capabilities

### New Capabilities
- `follow-decision`: 关注决策契约——只依据平台真实提供的信号（粉丝数、获赞与收藏、内容相关性）判定是否关注，MUST NOT 依赖平台不提供的字段（作品数）。
- `deep-read-fidelity`: 深读子动作保真契约——评论滚动 / 多图浏览等动作 MUST 按实测效果（如 `scrollTop` 位移）如实回报成功 / 失败，MUST NOT 命中即假报成功。

### Modified Capabilities
- `browse-loop-resilience`: 新增"按 sourcePageType 返回正确列表页"与"返回后 404/坏页健壮性（探测坏页 + 导航兜底 + 健康校验再上报）"两条要求（ADDED，不改原有要求）。

## Impact

- **edge（aidcp-edge）**：`src/browse/browse-session.ts`（`scrollNoteComments` / `navigateBack` / `extractAuthorProfile` 主页统计抽取 / 404 探测）、`src/comm/protocol.ts`（`ProfileDetailPayload` 加 `likesCollects?`）、`test/browse/*`。
- **cloud（aidcp-cloud）**：`src/agents/follow-agent.ts`（prompt 去作品数、加获赞收藏）、`src/orchestrator/role-dispatcher.ts`（back 透传 targetPage）、`src/comm/protocol.ts` + `src/event-bus/types.ts`（`ProfileDetailData`/`ProfileBrowsedPayload` 加 likesCollects）、`src/agents/profile-browser.ts`、`test/*`；改动走 ECS 部署安全序列（不碰 isales）。
- **协议**：`navigation.back` 复用既有可选 `targetPage`（向后兼容）；profile 新增可选 `likesCollects` 字段，需 edge+cloud 两侧同步加，避免单侧静默丢值。
- **验收**：重跑真机，验证评论真滚动（scrollTop 变）、健康创作者被关注、搜索会话返回搜索结果、无 404 滞留。
