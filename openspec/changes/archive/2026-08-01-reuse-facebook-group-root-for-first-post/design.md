## Context

`first_commentable_group_post` 当前在 Edge Native 入口无条件执行 `Page.navigate(canonical_group_url)`。加群与首帖读取是两个独立任务，Native session 状态不能跨任务证明页面连续性，但浏览器页面本身通常保留在刚完成加群的群根页。因此优化只能依据评论任务取得当前 CDP target 后的实时页面证据，不能依据加群回执或缓存 URL。

Facebook 群页还存在子路由、虚拟化帖子列表、嵌套滚动容器和站内自主换面。只比较 URL 前缀会把帖子详情或其他群误当成可复用页；只看 `window.scrollY` 会把已经滚动的嵌套 feed 误当成顶部。

## Goals / Non-Goals

**Goals:**

- 在当前 target 被实时证明为目标群根页且首帖读取起点可复用时，跳过冗余根页导航。
- 任一证据缺失、异常或不匹配时，回到现有的单次规范群根页导航。
- 在首帖候选接受前继续约束精确目标群根页上下文，防止探测后的站内换面导致错群。
- 保持现有首帖总滚动预算、详情绑定、失败诚实性和协议形状不变。

**Non-Goals:**

- 不把加群成功、成员态文案或 Cloud handoff token 当成页面可复用证据。
- 不跨任务复用 DOM 节点、点击坐标、帖子候选或内容引用。
- 不处理同一 AdsPower 浏览器内多个 Facebook page target 的长期固定；没有观测到该故障前不扩展 target 选择协议。
- 不修改评论提交、配额、风险控制或客户端安装包发布。

## Decisions

### 1. 在 Edge 当前 target 上做一次原子复用探测

新增仅供 Native 内部使用的 `first_post_group_root_probe`。探针在一次 `Runtime.evaluate` 内返回 origin、pathname、query/hash、router surface、document readyState、blocking kind、可见主区域与对话框数量、群作用域解析结果、feed loading 以及真实滚动容器位置。

只有以下条件全部成立才复用：

- 当前 origin 与规范目标群 URL 的 `https://www.facebook.com` origin 精确相等；
- pathname 归一尾斜杠后精确等于目标 `/groups/<group>`，query/hash 为空；
- router surface 为 `group`，群标识相等；
- document 为 `interactive` 或 `complete`，无 login/captcha/unknown blocker；
- 可见主区域唯一，目标群作用域已解析且不歧义；
- 无可见 modal/dialog，feed 未加载中；
- `feedScrollMetrics()` 返回的真实滚动位置不大于 1 CSS pixel。

不满足或普通探针解码/CDP 异常只表示不能复用，不直接形成业务失败；入口导航规范群根页一次。选择 1 CSS pixel 仅吸收浏览器子像素取整，不做配置项。探针返回后、任何回退导航前都重新检查 cancellation；已观察到取消或 task takeover 时原样终止且不导航。

替代方案是复用 `join_probe` 或串行调用现有 page/feed probes。前者只证明 URL 可推导为同群，不能排除子路由、滚动和加载状态；后者会组合多个时间点的页面证据。独立原子探针更容易形成可测试的单一判据。

### 2. 不引入 Cloud handoff token

加群和首帖读取会切换任务 owner 并重建 Native session。跨 Cloud token 即使记录旧 target，也不能证明当前文档未换面、未重载或未出现阻断，因此不能替代实时探测。当前优化不修改协议；若未来有多个 Facebook page target 的已观测问题，再单独设计 Edge target pin，且仍保留实时探测。

### 3. 两个分支进入同一首帖读取状态

无论复用还是导航，入口都更新 canonical `active_list_url`、清空 `seen_post_ids`、执行现有 ready/action gate，再按原有固定总滚动预算重新探测首帖。加群阶段的 DOM、坐标和帖子候选不进入评论任务。

### 4. 候选探测在同一次页面执行内证明精确根页上下文

Native 只在首帖专用的内部 `feed_refresh` / `browse_scroll` 表达式中注入 canonical `container`，不扩展协议结构。Router 在生成候选前后都校验当前 origin、pathname、query/hash、surface 和群作用域仍是精确目标群根页；首次 `feed_refresh` 还要求真实滚动容器仍在起点，后续主动 `browse_scroll` 不要求回到顶部。不匹配时丢弃本次临时候选并返回 `target_context_mismatch`，候选不会被 Native 接受或向 Cloud 外泄。

若最初走复用分支且在候选接受前发生上下文变化，Native 导航规范群根页一次并继续使用该命令尚未消耗的滚动轮次；整个命令累计仍不超过现有固定滚动上限。若已经导航过仍不匹配，则诚实返回 `target_context_mismatch`，不循环导航。候选一旦被 Native 接受，继续沿用现有 permalink same-group 校验或 bound-reference 页面内绑定与失败语义，不再导航回根页或改选其他帖子。

### 5. 记录有界复用决策

Edge stderr 记录一条结构化决策，包含 `strategy=reuse|navigate`、固定 reason、target ID、期望/观测 path、surface、readyState、blocking kind、loading、scrollY 和 fallback count。不得记录完整 query、阻断正文或 DOM。

## Risks / Trade-offs

- [保守判据可能产生额外导航] → 这是性能优化的安全回退；未知状态保持原行为，不放宽为成功。
- [探测后页面自主换面形成 TOCTOU] → 候选生成前后在同一次 Router 执行内校验精确根页，复用分支在接受候选前最多回退导航一次。
- [Facebook DOM 变化导致群作用域解析失败] → 仅失去复用机会；根页导航和现有首帖失败语义保持可观察。
- [新增内部探针遗漏 fake CDP 白名单] → 同步更新 router kind 夹具并增加解码与集成回归。

## Migration Plan

1. 先在 Edge worktree 完成内部探针、判据和测试。
2. 运行 Native fake CDP、router contract、acceptance、全量测试、typecheck 与 Native 构建输入验证。
3. 快进集成到 Edge `master`；该变更不需要 ECS 部署。
4. 不自动构建或发布安装包。回滚只需回退该 Edge 提交，恢复无条件根页导航。

## Open Questions

无。多 Facebook target 固定和非空 benign query 仅在出现真实失败证据后另立变更。
