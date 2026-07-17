## Why

Facebook 客户端「今日进展」显示「收藏 0」「关注 0」。FB 没有收藏概念、边缘没有关注执行器 —— 这两个 0 永远不会变。前一个 change 已摘掉它们的上限与进度条，却**刻意保留了计数**，还把「本规则不改客户端渲染几行」写进法条。那条法条是错的：永远为 0 的计数不是「今天还没做」，而是「这个平台没有这件事」，它与那条永远 0% 的进度条是同一个谎的两半。

反过来，FB 每天真在做、真受日限约束的**加群**，客户端一格都没有：计数早在风控计数器（`join_group`）里、后台用量表已按「加群 用了/上限」展示，唯独面向客户的那块屏幕看不见。

## What Changes

- **规则从「摘上限」扩到「摘整个指标」**（**BREAKING**：推翻 `platform-honest-usage-caps` 的「摘上限 MUST NOT 摘计数、不改客户端行数」一段）。平台结构上做不到的动作，客户端不再有那一格 / 那一行。
- **新增客户端指标键 `join_group`（标签「加群」）**：只发给显式声明支持加群的平台。口径 = 用量面（今日发出去几次加群申请，点了就算、含待审批），与后台用量表同一个计数器、同一个分母（均衡档 3/天）；**不是**「今天成功进了几个群」。
- **registry 新增编排能力词 `group_join`**：facebook 支持；小红书 `no_group_concept`；视频号 `interaction_inbox_only`。
- **投影的 fail-open 方向 = 保持现状**（不是「一律发」也不是「一律不发」）：既有六键只有显式 `supported:false` 才摘；新键只有显式 `supported:true` 才加；平台未知 / 查表抛异常 ⇒ 两边都维持今天的形状。
- **客户端 KPI 格按云端下发的键集合渲染**，布局不再假设恒为 6 格；无云端用量载荷时回落到今天的本机六格。
- **不做（YAGNI）**：不新建第二张「展示表」（判据只来自 registry 既有声明）；不给加群做边缘乐观 bump；不引入 UI↔风控键别名；不动 console；不碰 `dm_reply` / `comment_like`。

平台效果：FB = 浏览 / 点赞 / 评论 / 发帖 / **加群**；小红书 = 六格逐位不变；视频号 = 只剩发帖（其注册表已声明浏览 / 点赞 / 收藏 / 评论 / 关注全不支持）。

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities

- `edge-companion-ui`: 「摘上限不摘计数、不改行数」被推翻 —— 不支持的动作整格不渲染；客户端指标集合由云端按平台投影后下发决定，不再是写死的六项；新增 `join_group` 指标键与其展示口径。
- `platform-browse-surface`: 编排能力矩阵新增 `group_join`；并允许一个能力词的唯一消费者是**非闸的只读投影**（今天该法条要求能力词必须闸住角色注册，`platform-honest-usage-caps` 已为逐帖动作矩阵开过同样的口子，这里补齐对称）。

## Impact

- **协议热点（§2 四处同步中的两份 `protocol.ts`，须单写者串行）**：edge + cloud 两份 `src/comm/protocol.ts` 的 `UiDailyUsageAction` 加 `join_group`，逐字一致。**注意这个联集的漂移 `Record<MessageType,true>` 穷举抓不到**（它不是消息类型），本 change 用「联集从 `as const` 数组派生」把它变成 typecheck 可抓。
- cloud：`src/platform/registry.ts`（`group_join` 能力词）、`src/platform/surface.ts`（上限投影泛化为指标投影）、`src/server.ts`（`UI_DAILY_USAGE_ACTIONS` 改为派生、totals 各面接投影）。
- edge：`src/comm/protocol.ts`、`src/electron/main.cjs`（键清单 + 计数清洗保留缺席 + 乐观 bump 不复活缺席键）、`src/electron/renderer/renderer.js`、`renderer/index.html`（加群静态格）、`renderer/styles.css`（网格不再写死 6 列）。
- **部署**：cloud 走 dev 安全序列。**客户端改动落 master 但默认不出安装包**（用户 2026-07-17 明确：先不出包）⇒ 运营机在出包前只会看到云端那一半（窗口明细行已诚实、顶部 KPI 格仍是老样子）。
- 真机验收登记 backlog（簇 90 的 FB 环境）。
