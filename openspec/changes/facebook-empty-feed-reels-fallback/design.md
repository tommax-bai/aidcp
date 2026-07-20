## Context

Facebook 首页当前有两个被混在一起的事实：浏览器是否已经稳定落在可用的首页，以及首页是否存在可抽取的帖子卡片。`ensureFeed` 只有在 feed 容器存在时才把页面视为目标，导致新账号的真实空 Feed 被反复导航；反过来，单凭 0 卡又无法区分未完成加载、未知布局、登录/checkpoint/consent/captcha 页面和真实空态。

真机 So La 环境还显示 Reels 与普通 feed 的 DOM 完全不同：它没有 `role=feed/article`，当前卡由视口内活动 `<video>` 决定，摘要位于左下覆盖层，点赞位于右侧动作轨，下一条由最右侧全局下导航按钮切换。Cloud 仍应拥有列表选择和互动授权，Edge 只负责页面观察和受命执行。

## Goals / Non-Goals

**Goals:**

- 只在真实 Facebook 首页完成水合且显式空态稳定出现时确认空 Feed。
- 由 Cloud 明确授权从首页列表切换到 Reels，不让 Edge 自主改变浏览策略。
- 在 Reels 上诚实读取当前视频摘要、点赞并验证选中态、导航下一条并验证身份变化。
- 保持现有消息类型、`feed/detail` surface、风险授权与记账链向后兼容。

**Non-Goals:**

- 不把无卡、未知布局或超时一律当成空 Feed。
- 不改变 LLM 选帖、内容价值判断、互动概率、配额或 RiskController 状态机。
- 不支持 Reels 评论、分享、音频或作者关注，不构建 Edge 安装包。

## Decisions

### 1. 首页 readiness 与内容状态分层

Edge 探针先确认顶层 `facebook.com` 首页 URL、认证态、可用主区域、无登录/checkpoint/consent/captcha 阻断，再观察内容。首页在场不再依赖 feed 容器或卡片；搜索/群组列表仍沿用原有容器判据。

真实空态必须满足：同一 URL 与同一 `performance.timeOrigin` generation、document age 至少 8 秒、没有受支持卡片和 loading 信号、同一紧凑容器内命中成对的中/越/英文空态语义，并以约 600ms 间隔连续命中 3 次。确认前再做一次完整复检；任何卡片、loading、URL/generation 变化或阻断都会清零。总确认窗口约 15 秒，超时但证据不足返回 `feed_unknown`，而不是空态。

选择显式空态证据而非“0 卡超时”，是为了让 Facebook 新布局和慢加载 fail-closed；选择 generation guard 是为了避免导航/刷新前后的样本被错误累计。

### 2. 使用现有消息传递观察和授权

`page.cards` 增加可选 `listKind: 'feed' | 'reels'` 与 `listState: 'ready' | 'empty'`。缺省等价于当前 `feed/ready`。Edge 对首页明确空态上报一次 `cards: [] + feed/empty`；Cloud handler 将其翻译为内部 `feed.empty.confirmed`。当 Facebook 活跃会话收到该事件，或收到 Edge 在浏览过真实卡片后返回的 `action.completed{action:'scroll',ok:false,reason:'feed_exhausted'}` 时，RoleDispatcher 都发送现有 `page.scroll{reason:'empty_feed_reels_fallback'}`，且每场至多授权一次。Edge 只有收到该原因才进入 Reels。

`empty_feed_reels_fallback` 是已部署的兼容握手名；它现在表达“Facebook Feed 已无可继续浏览内容”，既包括从一开始明确为空，也包括非空列表确认到底。沿用该 reason 可让新 Cloud 直接驱动现有 Edge，避免新增 reason 导致未升级客户端把命令误当普通 Feed 滚动。其他平台的 `feed_exhausted` 继续走原有 `refresh` 自愈。

不新增协议消息或命令，也不把 `reels` 加入 `feed/detail` surface。后者继续只表达读取是否离开列表；Reels 仍是 feed-surface 就地读取。旧 Cloud 忽略可选字段，旧 Edge 不产生空态观察，混合版本不会自动切换。

### 3. Reels 使用独立的活动卡模型

Edge 新增 Reels reader：只接受规范 `/reel/<id>` 路由；在预加载的多个 `<video>` 中选择视口交集最大、再以中心距离决胜的活动视频。摘要从活动视频左下覆盖层的最深内容块抽取，过滤作者、关注、音频和动作标签；展开控件只有在仍绑定同一 Reel 时才可点击。抽不到完整摘要时只上报真实可见片段。

该活动卡以规范 Reel URL 为 `noteId`，以摘要为 title/content，`mediaType='video'`。普通 `page.cards → note.open(surface=feed) → note.detail` 链保持不变，Edge 根据当前已授权列表模式分流到 Reels reader。

### 4. Reels 写动作和翻页均以页面后验验证

点赞只在命令 `noteId` 与当前活动 Reel 身份一致时执行。定位优先使用活动视频右侧动作轨的结构关系（大号首动作按钮及相邻反应控件），locale 文本只作为辅助；按钮歧义、已赞、身份漂移均 fail-closed。一次可信 CDP 鼠标点击后，只有同一 Reel 上出现明确取消赞语义或选中反应图标时才回 `ok:true`，圆整计数变化不作为成功证据。成功后继续走现有 `action.completed → RiskController` 记账。

Reels 的 `page.scroll` 不使用页面 wheel（该页面 `scrollY` 不变）；Edge 点击最右侧全局下导航按钮，并要求规范 Reel URL 或活动 video identity 变化后才上报新卡。按钮缺失/禁用、身份不变或出现歧义都诚实失败。

### 5. 模式生命周期

会话初始和普通首页/搜索导航将列表模式重置为 feed；只有 Cloud 对明确空态或确认到底的授权可进入 reels。Reels 内 `note.open`、`interaction.like`、`page.scroll` 就地工作。返回、重连或非 Reels URL 会重新探测并收敛，绝不凭陈旧内存对错误页面执行 Reels 动作。

## Risks / Trade-offs

- [Facebook DOM/翻译变化导致空态文案未命中] → 只是不触发 fallback，保留 `feed_unknown` 诊断；不得扩大到任意 0 卡。
- [重复/延迟的 `feed_exhausted` 回执导致多次切换] → Cloud 复用会话级 Reels fallback 幂等闸；一旦授权便吞掉重复到底回执，不再刷新普通 Feed。
- [预加载视频导致读错卡] → 路由身份、视口交集和动作前后身份三重绑定。
- [结构相似按钮导致误赞/误翻页] → 限定活动视频相对区域、唯一候选和后验状态；歧义即失败。
- [新 Cloud 与旧 Edge / 新 Edge 与旧 Cloud 混跑] → 全部新增字段可选，fallback 由特定现有命令 reason 双向握手。
- [Reels 内容分布改变浏览质量] → 继续复用 Cloud 内容评价、节奏和互动风险决策；本 change 不提高互动概率或额度。

## Migration Plan

1. 先合入 Edge/Cloud 协议镜像与测试，再合入控制仓协议文档/OpenSpec。
2. 运行协议漂移、Facebook focused/full tests 与 typecheck。
3. 合并默认分支并部署 Cloud `dev`；Edge 仅提交源码，不打包客户端。
4. 回滚时先回滚 Cloud fallback 授权，Edge 新字段和 Reels 分支因没有特定 reason 不再触发；随后可独立回滚 Edge。

## Open Questions

- 无；So La 真机探针已确认活动视频、摘要、点赞选中态与全局下一条按钮的可用结构。
