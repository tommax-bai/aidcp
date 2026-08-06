# Design — 词汇批 4：浏览词汇平台化 + page.scroll 按面拆分

## 1. 名表（14 旧 → 22 新，唯一权威）

平台段取值＝代码平台枚举 `PlatformId`（`xiaohongshu` / `facebook` / `wechat_channels`），与批 2 两道休眠闸的 `PLATFORM_SEGMENTS` 同源同值。蓝图行文的 `xhs` 不采用（蓝图自己声明「实装批以代码为准」）。

| 旧名 | xiaohongshu | facebook | 依据 |
| --- | --- | --- | --- |
| `page.scroll` | `xiaohongshu.feed.scroll`<br>`xiaohongshu.search.scroll` | `facebook.feed.scroll`<br>`facebook.search.scroll`<br>`facebook.reels.scroll` | 面枚举见 §2；xhs 无 reels |
| `feed.refresh` | `xiaohongshu.feed.refresh` | `facebook.feed.refresh` | 两平台都有真实刷新执行（FB=顶栏首页图标换批） |
| `search.execute` | `xiaohongshu.search.execute` | `facebook.search.execute` | FB 全站/容器搜索真实执行器 + search 角色恒注册 |
| `note.open` | `xiaohongshu.note.open` | `facebook.note.open` | 双平台现役 |
| `note.close` | `xiaohongshu.note.close` | `facebook.note.close` | 引擎双平台支持；**云端零发送点**（回列表走 `navigation.back`），与 `navigation.back` 的分工按蓝图留批 6 裁 |
| `note.browse_images` | `xiaohongshu.note.browse_images` | — | FB 引擎无臂（原手抄拒集成员） |
| `note.scroll_comments` | `xiaohongshu.note.scroll_comments` | — | 同上（FB 评论走详情页迁移，不滚评论区） |
| `profile.open` | `xiaohongshu.profile.open` | — | FB 结构性不访作者主页（C4） |
| `group.join` | — | `facebook.group.join` | 仅 FB 有群 |
| `notification.open` ×5 | `xiaohongshu.notification.{open,browse_comments,browse_likes,browse_follows,back_home}` | — | 12 巡视角色注册被平台能力表拦（FB/视频号 unsupported），引擎 FB 无臂 |

协议消息 95 → **103**；两份操作登记表 44 → **52**（描述符逐条继承旧值；`facebook.group.join` 独有 `platformFootprint:'account_visible'`）。wechat_channels 本批零命令（无浏览面；IM 族是批 6）。

## 2. page.scroll 的面枚举与无面发送点（决策）

**面 = {feed, search, reels}**，从云端全部发送点的 reason 取值坐实：

- feed：`feed_scroll` / `feed_inline_continue` / `feed_continuation_unconfirmed` / `rescan_after_stale_target`
- search：`search_scroll`（SearchScroller，页型权威 `sourcePageType==='search'`）
- reels：`resume_redrive+targetSurface:'reels'` / `continue_after_reels_*` / FB 规则观影续场 `source==='reels'`
- **群不是面**：群内找首帖的滚动是 `note.open{selection:'first_commentable_group_post'}` 的引擎内部分解（`facebook/runtime.rs:222-229` 构造内部 `FeedRefresh`+`BrowseScroll` 子命令），协议层从不单独指挥。

**无面语义的 reason**（`idle_recover_nudge` / `resume_after_view_quota` / `rescan_after_back` / `recover_after_*_failed`）：由发令方单点解析器 `currentScrollSurface()` 按其已追踪状态（`sourcePageType`、FB reels 在场态）择面命名，默认 feed。这不是执行层补空——是**发令方把自己本就持有的推定显式化**，语法第 1 条「期望声明服务发令方自己的可调试性」的正身；边缘核对不符时按语法第 5 条三态回报。

**`targetSurface` 字段删除**：面进名后再留即双编码（语法第 4 条）。`reason` 保留——它承载**意图/因由**（节奏、诊断、引擎特殊路径 `initial_scan` / `resume_redrive` 的导航语义），与面是两个维度。`resume_redrive` 缺 `targetSurface` 的诚实失败臂 `resume_target_missing` 随之结构性不可达，删。

## 3. 引擎侧：协议拆名、kind 不拆（决策)

Rust `NATIVE_COMMAND_KINDS` 与三张 kind 表（manifest 算术、`command-postconditions.json`、`command-timing.json`）**全部不动**。TS mapper（`nativeCommandKindByEnvelopeType`）从信封名解析 (platform, surface)，surface 以参数下传（Rust `PageScrollParams.target_surface: Option<FacebookBrowseSurface{Feed,Reels}>` → `surface: BrowseSurface{Feed,Search,Reels}` 必填）。协议层无双编码；TS↔Rust 边界是内部表示，不受语法第 4 条约束。

- FB 路由：面分派从「观测现场自判」改为「名字声明 + 执行点核对」——`facebook.reels.scroll` 的进入型 reason（`resume_redrive` 等三个）照旧先导航进 Reels；推进型到达时观测不在 Reels ⇒ 诚实失败（确认到不符），MUST NOT 静默滚 feed。`facebook.feed.scroll` 对称。
- xhs 路由：feed/search 同函数执行（现状），拆名只改回执语义的解释权，不改执行行为。

**manifest schema**：每条目 `routeKey`/`edgeType` 标量 → **`edgeTypes: string[]`**（该 kind 的全部平台段信封名）。条目仍 1:1 于 kind，`NATIVE_COMMAND_KINDS.len() == manifest.len() + excluded.len()` 算术闸原样；manifest 测试改断「mapper 表 = 各条目 edgeTypes 并集」。改 manifest 后重建引擎重钉 capabilityDigest：**生产常量 `src/electron/native-page-engine-artifact.cjs:19`（漏改=启动硬失败）** + `test/electron/native-page-engine-artifact.test.ts` 三处 + `test/electron/macos-signed-artifact.test.ts` 一处。

## 4. 两道平台段闸转正 + 手抄拒集退役（决策）

批 2 休眠闸零改动自动生效（云出口 `ws-server.ts:342` / 边入口 `edge-client.ts:721`，`split('.')[0]` ∈ `PLATFORM_SEGMENTS` 且 ≠ 会话平台 ⇒ `platform_mismatch` 拒）。随之：

- 边缘 `FACEBOOK_UNSUPPORTED_COMMANDS`（8 条手抄拒集）**删除**——xhs 专属命令没有 facebook 变体、FB 会话收到 `xiaohongshu.*` 在入口闸即拒，语义等价且由类型系统+名表推导。Rust `supports_platform` 留作引擎内纵深。
- 云端 bridge 组合表（§5）承担出口侧存在性——不存在的 (action, platform) 组合编译期即不可表达。

## 5. 云端 bridge：平台成为翻译输入（决策）

`edgeCommandToEnvelope(command)` → `edgeCommandToEnvelope(command, platform: PlatformId)`。平台穿入点＝连接层闭包（`automation-connection-dispatcher.ts:580` 已握 `ctx.platform`，经 `automation-main.ts` 的 `sendCommand` 转手）。桥内是 **(action, platform[, surface]) → MessageType 的穷举组合表**，以 `satisfies` 钉在 `MessageType` 上——写错名编译期红；运行时不存在的组合（如 facebook + `browse_images`）响亮 throw。该 throw 是结构性不可达的后备（FB 的深读/主页/巡视角色本就不注册或被注入闸短路），**不是**第二道支持闸——`platform-browse-surface` 的单点审计拒发闸照旧唯一。

scroll 的面：`EdgeCommand` 增可选 `surface`；显式面的发送点直接标（redrive/reels 续场/search_scroll/feed_*），无面发送点经 `currentScrollSurface()` 解析（§2）。`group.join` 与 comment-agent 三个直发点按构造已知平台，就地改名。

## 6. 动作关联键零改动（红线）

`action.completed.action` 的关联键命名空间本批**不动**：边缘 `actionNames`（live）与 `FB_COMMAND_ACTION_NAMES`（退役但仍测试）只改键（22 新名）、值原样；云端 `LEGACY_ACTION_COMPLETION_ALIASES` 同样只换键——直接切换语义下旧键即删（旧客户端根本不会执行新名命令，不存在旧回执窗口）。所有按动作名判定的逻辑（`isExcursionCommand`、风控记账、角色关联、`noRecoverScroll` 集）零改动。对象化改键是批 5 的活，本批混入即撞第 5 处同步点的雷区。

## 7. 批 1 引擎遗留清账（据实修正）

原计划「删 `browse_next`/`browse_scroll` 变体全链」修正为：

- `browse_next`：**真死**（唯一疑似构造点 `xhs_initial_scan_command` 是入什么还什么的改写，不无中生有）。删：变体、排除表条目+镜像断言集、postconditions 条目、xhs 路由 modal-close 死臂、renderer 死标签 `browse.next`、相关分派臂与 Rust 集成测试引用。
- `browse_scroll`：**内部活体**（首帖探测载体，`facebook/runtime.rs:227` 构造）。留：变体与全部分派臂；改：排除表理由与 postconditions 证据文本改写为「引擎内部子命令载体（首帖探测），非协议类型、envelope 不可达」；renderer 的 `browse.scroll` 协议标签仍删（信封层早已无此类型）。

## 8. 切换窗口与部署形态

直接切换（语法第 6 要求）：automation 部署 dev 后，旧客户端对新名 fail-closed 拒收（未出包客户端连批 2 的闸都没有，落在 `operation_unclassified` 同样拒收）——两种旧态都拒在执行前，无重复对外写入风险。**部署后 dev 车队浏览停摆直至出包装机**，属「连续完成」窗口：部署完成即提请用户出包（打包动作仍由用户显式触发，本 change 不代打）；真机验收登记 backlog 现有簇。

## 9. 风险登记

| 风险 | 处置 |
| --- | --- |
| 盲 sed 撞同形异义字面量 | 两个 `page.scroll` 是 v1 `PlanStep.actionId`（`command.rs:973`、`xhs-command-router.js:910,912`）**不改**；EventBus 内部事件名（`feed.refresh.needed`、`notification.opening` 等）与协议名同形**不改**——逐文件按清单改，不做仓级替换 |
| digest 五位点漏改 | 生产常量优先核（启动硬失败）；`shasum -a 256` 重算后五处一次换齐 |
| 并行 change 撞引擎/规格文件 | 协议热区本批串行；`restore-native-facebook-residual-parity` 与 `blocking-overlay-dom-capture` 在飞，集成后到者 rebase；机械 spec delta 归档前重生成 |
| 边缘白名单 if-链 typecheck 不可见 | 22 条逐一入链后，跑批 1 建立的路由回归断言 + 每平台一条真实新名命令的端到端测试 |
| 计数断言散点 | 两份 protocol-contract 的 95→103、automation 登记表头注「46 条」陈述性笔误一并修为实数 52 |
