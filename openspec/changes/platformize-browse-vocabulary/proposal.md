## Why

词汇蓝图批 4（`docs/edge-command-grammar.md` §6.2「浏览词汇平台化 + 拆分」、§6.3 批次表）：14 条浏览命令加平台段、`page.scroll` 按面拆分。这是协议改名最大的一批；批 2 已把出入两道平台段闸休眠就位，本批改名后闸自动转正。

前置核实（2026-08-06，两仓全量探查，结论已回写蓝图行）：

- **`page.scroll` 实际在用的面 = feed / search / reels 三个**。Reels 今天靠 `targetSurface:'feed'|'reels'` + reason 族（`resume_redrive`、`continue_after_reels_*`、`facebook_reels_primary` 等）区分，没有独立消息；`feed_scroll` / `search_scroll` 两个字面量边缘根本不认（只活在协议注释里）。
- **群没有协议级滚动面**：找首条可评论帖的群内滚动是引擎把 `note.open{selection:'first_commentable_group_post'}` 内部分解成 `FeedRefresh`+`BrowseScroll` 子命令完成的（`facebook/runtime.rs:222-229`），云端从不单独指挥群内滚动。**由此发现批 1 遗留不能全删**：`browse_scroll` Rust 变体是这条内部路径的活载体，本批只删真死的 `browse_next`、`browse_scroll` 改注记留任。
- **notification 五条结构性只在小红书**：12 巡视角色的注册被平台能力表拦（FB `patrol/notification` unsupported），FB 端引擎也无对应臂。
- **FB search 成立**：search 三角色恒注册、registry 声明 FB search `supported:true` 且有真实执行器 ⇒ `facebook.search.execute` / `facebook.search.scroll` 都建。
- **`note.close` 云端零发送点**（`close_note` bridge 映射是死路径，回列表实际走 `navigation.back`）。仍按蓝图改名保留，分工留批 6 裁。

## What Changes

- **14 条旧名 → 22 条平台段新名**（xiaohongshu 14 + facebook 8，名表见 design §1）；协议消息 95 → 103，两份登记表 44 → 52 条。直接切换：旧名从两份协议穷举表直接删，无别名、无墓碑（语法规格第 6 要求）。
- **`page.scroll` 拆为 `{p}.feed.scroll` / `{p}.search.scroll` / `facebook.reels.scroll`**；`targetSurface` 载荷字段删除（维度进名、不双编码），`reason` 保留承载意图/因由。无面语义的发送点（idle nudge / 配额醒来 / 回退后重扫等）由云端按其追踪的当前面解析择名——把「云端对当前页的推定」变成每条命令自带的可证伪声明（语法第 1 条的落地）。
- **两道休眠平台段闸转正**（云出口 `ws-server` + 边入口 `edge-client`，`PLATFORM_SEGMENTS={xiaohongshu,facebook,wechat_channels}` 同源同值）；边缘 `FACEBOOK_UNSUPPORTED_COMMANDS` 手抄拒集删除——平台存在性改由名表 + 平台闸推导（蓝图预言的「消一份手抄」）。
- **云端 command-bridge 改为 (action, platform[, surface]) → MessageType 的穷举组合表**，平台经连接层闭包穿入；不存在的组合响亮 throw（结构性不可达的后备，非第二道支持闸）。`group.join` 直发点改名 `facebook.group.join`。
- **动作关联键零改动**（协议第 5 处同步点）：两侧映射表只改键（22 新名），值（`scroll`/`open_note`/`join_group`…）原样——对象化改名是批 5。
- **引擎侧单 kind 不拆**：Rust `page_scroll` 等 nativeKind 与快照/时长/后置校验三张 kind 表不动；TS mapper 从信封名解析 platform+surface 下传（`target_surface` 二值 → `surface` 三值）。manifest schema `routeKey`/`edgeType` 标量 → `edgeTypes` 数组（kind 1:1 条目守恒、排除表算术闸不变），重钉 capabilityDigest（1 生产常量 + 4 测试位点）。
- **批 1 引擎遗留清账（修正版）**：删 `browse_next` 变体全链（真死）；`browse_scroll` 保留、排除表理由与 postconditions 证据改写为「首帖探测内部载体，非协议类型」。
- `docs/protocol.md` §2 表与载荷节、`docs/edge-command-grammar.md` 批 4 行随改同步。
- **BREAKING（内部协议，预期内）**：automation 部署后、新客户端出包装机前，旧客户端对 22 条新名 fail-closed 拒收（拒收在执行前，无「已派发未确认」）。按语法规格「云端部署与客户端更新连续完成」，部署后立即提请用户出包（出包动作仍由用户显式触发）。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities

手写 delta（语义真变）：
- `platform-browse-surface`: ①「新增平台不得改协议消息集/桥映射/白名单」按平台段编法翻转——共享编排（角色/风控/节奏/事件翻译）仍不许动，但平台自己的命令声明成为准入平台的显式组成；②「不得新增消息类型、面走可选字段」的历史范围约束翻转——滚动命令的列表形态改由命令名的面段承载（`feed/detail` Surface 联合＝是否离开列表上下文，概念不变、与面段两词两义）。
- `platform-page-command-routing`: `profile.open` 只存在于 xiaohongshu 前缀下；「FB 收到本人主页命令」的防线从 Native 拒收前移为平台段闸 `platform_mismatch`（Native 按会话平台再校验仍在）。
- `facebook-reels-native-scroll`: Reels 滚动命令名化为 `facebook.reels.scroll`；面路由从「边缘观测现场自判」变为「名字声明意图 + 执行点核对现场」，跨面到达诚实拒绝、MUST NOT 静默改执行另一面的执行器。
- `feed-depth-refresh`: 刷新协议消息名平台段化（`{p}.feed.refresh`），执行方式两平台各自要求不变。

机械改名 delta（纯名字提及，语义零变）：其余 ~29 个引用旧名的 capability（`command-pacing` 21 处、`native-facebook-behavior-parity` 13 处等，全名单见 tasks 6.1）在集成期脚本化生成、归档前对当时最新 spec 文本重生成一遍（防与并行 change 的 delta 撞车）。

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`、`src/client/{operation-registry,edge-client,command-diagnostics}.ts`、`src/native-page-engine/{command-mapper,browse-session}.ts`、`src/electron/renderer/renderer.js`、`src/electron/native-page-engine-artifact.cjs`（digest 常量）、`native/page-engine/command-manifest.json` + `src/command.rs`（排除表/镜像断言）+ fb/xhs 两路由 JS + `facebook/feed.rs`、退役但仍编译的 `src/{browse,facebook}/**` 与其测试、`test/acceptance/protocol-contract.test.ts`（计数 95→103）、digest 两个夹具文件。
- `aidcp-automation`：`src/comm/{protocol,command-bridge,operation-registry,handler,ws-server}.ts`、`src/orchestrator/{role-dispatcher,connection-runtime}.ts`、`src/automation-connection-dispatcher.ts`、`src/automation-main.ts`、`src/comment-agent/{edge-steps,facebook-edge-steps,facebook-group-join-edge-steps}.ts` + 约 20 个测试文件（protocol-contract 计数同步）。
- 控制仓：`docs/protocol.md`、`docs/edge-command-grammar.md`、spec delta 两批。
- **并行注意**：`restore-native-facebook-residual-parity`（49/61，动 native FB）与 `blocking-overlay-dom-capture`（0/56，刚开工）正在飞，与本批在引擎文件 + `native-facebook-behavior-parity` spec 上可能重叠——协议热区本批串行，集成时后到者 rebase；两份 protocol.ts + 登记表 + bridge 是单写热点，绝不与他人同时碰。
- **不出包不算完**：改名两端才能会师，出包装机前 dev 车队浏览停摆（fail-closed 窗口）。真机验收项照例登记 backlog。
