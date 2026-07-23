<!--
设计草案（design draft）。落成后经 openspec change 拆分实施；本文不代表已实现、已部署或已接入生产。
证据：本仓已合并的平台抽象代码（edge/cloud 实读）、native-page-engine 立项 design、douyin 研究/探针 change、5 路并行代码调研（2026-07-23）。
-->

# 抖音生产接入设计（Douyin Production Integration）

- 状态：设计草案
- 日期：2026-07-23
- 范围：把抖音从「独立研究探针」接成生产平台，并给「后续持续加平台」定一条可复用的架构边界
- 关联：change `douyin-cdp-research-and-probes`（研究/探针，上游）、`native-page-engine-production-cutover`（引擎立项）
- 上位文档：`docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md`

---

## 0. 结论摘要

1. **平台抽象缝早已就绪**，抖音接入的架构改动很小：云端是一张 typecheck 全覆盖的声明式平台注册表，协议平台中立，边端有中立会话契约。加平台 ≈ 加声明 + 加实现，不是改架构。
2. **决定边端策略的是「反编译 / 防拷贝」这条业务级诉求**，不是工程省事。桌面客户端会发到客户手里，**核心页面驱动逻辑不能以可读 JS 躺在安装包（asar）里被 AI 工具快速 copy**。这正是 Native 引擎（Rust、编译、staged 在 asar 之外）的立项理由。
3. → **抖音的页面驱动逻辑应落进 Rust Native 引擎（`douyin-v1` 适配器），不再写明文 TS 会话。** 现有 TS 探针不浪费——它变成「照着实现」的 DOM 契约规格，但**必须从发布产物里排除**。
4. **反编译诉求给出一条天然的三层职责边界**（Rust 引擎 / TS 宿主 / 云端），它同时就是「怎么加第 N 个平台」的答案。
5. **发布是一条独立的新缝**：抖音发布必须走开放平台 OAuth（`video.upload`→`video.create`），塞不进现有「浏览器 composer」发布模型 → **单独立 change，v1 先声明不支持**。
6. **一笔要标记的债**：Facebook 目前仍是纯 TS（约 20 个文件、175 处 DOM 读取全在 asar 里），在本诉求下是现成泄露口，应排期迁引擎。

---

## 1. 驱动约束（为什么边端非引擎不可）

### 1.1 反编译 / 防拷贝（一等诉求）
- `native-page-engine-production-cutover/design.md` 立项原话：小红书执行分散在 `src/browse` 约 11000 行 TS，「Ordinary Electron packaging compiles all of those modules into `dist/**/*` inside **readable ASAR**」——把这块从可读 asar 挪走即立项目的。
- 引擎是 **Rust**（`AIDCP_CARGO_BIN` / `npm run build:native-page-engine`），编译成宿主二进制、**staged 在 asar 之外**（`docs/native-page-engine-spike.md`）。
- **诚实边界**（同 design 明文）：**不**声称 Native 代码无法逆向或动态观测、**不**做完整二进制混淆。目标是**抬高抄袭门槛**，不是绝对不可破。设计里任何「因为进了引擎所以安全」的断言都不成立。

### 1.2 护城河在哪（决定「什么必须藏」）
- 竞争壁垒 = LLM 语义决策 + 指纹防关联 + 质量比例闸 + 自建微观行为层（`docs/research/llm-agent-paradigm-deepdive-2026-06-28.md`）。
- 决策 / 闸 / 风控 / 人设**在云端**，本就不下发、天然安全。
- **边端的敏感部分 = 页面理解 + 微观拟人**（选择器、卡片身份、状态判定、拟人点击/输入、反检测）。这才是引擎要藏的东西。

### 1.3 已就绪、不要重造的抽象
- 云端 `PLATFORM_REGISTRY: Record<PlatformId, PlatformRegistryEntry>`（`aidcp-cloud/src/platform/registry.ts:286`）：全覆盖声明，typecheck 逼每格表态；`surface.ts` 纯 fail-safe 解析器是唯一读者；角色平台无关，靠读能力声明 gate。
- 协议平台中立（两份 `protocol.ts`）：`page.cards`/`note.detail`/`note.open`/`interaction.*`/`page.scroll`/`navigation.back`/`action.completed` 不带平台名，平台经 `HelloPayload.platform`→`session.platform` 带外。
- 边端中立会话契约 `EdgeBrowseSession`（`aidcp-edge/src/browse/edge-browse-session.ts`）：`main.ts` 用一个 `browse` 变量同时握住引擎会话与 FB 会话。

### 1.4 必须遵守的红线
- **绝不静默假成功**（贯穿全 spec）：找不到目标报 `no_target`、回查不明报 `postcondition_unknown`、单向不反悔、按实测回报。
- **风控最终状态单写**：新平台只提交事件 / 读投影，绝不加状态或改状态机（`risk-state-machine.ts`）。
- **协议五处同步 + 三处 typecheck 抓不到的漂移**：两份 `protocol.ts` 逐字一致、命令桥动作映射、`docs/protocol.md`、边端主动命令路由白名单、动作名别名（两侧裸字符串）。
- **两份 `PlatformId` 跨仓无编译联锁**（edge `driver.ts` ↔ cloud `registry.ts`）——手工纪律。

---

## 2. 三层职责边界（这就是「怎么加第 N 个平台」的答案）

反编译诉求恰好给出一条清晰、可复用的分层，也是最好的扩展边界：

| 层 | 放什么 | 为什么在这 | 抖音对应 |
|---|---|---|---|
| **Rust 引擎（编译、隐藏）** | 每个平台的**页面理解 + 微观拟人**：选择器、卡片身份、状态判定（赞没赞）、拟人点击/输入、反检测、内部滚动容器推进 | 护城河，发给客户也不能读 | `douyin-v1` 适配器 |
| **TS 边端宿主（可留 asar）** | **平台中立会话管线**：`NativeBrowseSession`（云端命令↔引擎命令↔协议上报）、租约/槽位、driver **元数据**（目标 URL、能力清单） | 通用编排，读了看不出「怎么理解页面」，泄露无所谓 | 复用 `NativeBrowseSession` + 新增薄 `douyin/driver.ts` |
| **云端（服务端，永不下发）** | 决策 / 质量闸 / 风控 / 人设 / 注册表声明 | 在服务器，天生安全 | 注册表加一条 `douyin` 条目 |

**关键推论**：对「引擎平台」，TS 侧**几乎不用新写会话类**——`NativeBrowseSession` 是通用转发器，不含平台 DOM 逻辑（那在 Rust 适配器里）。所以加抖音在 TS 侧基本是复用它；真正的活是引擎里的 Rust 适配器。这比 FB 那条「每平台一套 TS 读取器」更省、更闭合：**一个通用 TS 宿主 + N 个编译适配器**。

---

## 3. 当前状态基线（grounded，2026-07-23 实读）

**边端**
- XHS = **唯一在引擎**上的平台（`NativeBrowseSession` + `command-mapper` 转发到 Rust 二进制）。
- FB = **纯 TS**（`FacebookFeedReader`/`PostReader`/`LikeExecutor`/`InlineReader`/`ReelsReader`，约 20 文件 175 处 DOM 读取，全在 asar）→ **本诉求下的泄露口 / 迁引擎债**。
- WeChat = API-only（`runtimeKind:'interaction'`，不驱动浏览器）。
- 执行分发是 `main.ts` 一条 **硬编码 if 梯**：`main.ts:672` 写死 `platform==='xiaohongshu'` 才起引擎；`usesFacebookBrowseSession` 起 FB 会话。driver **不出厂会话工厂**——这是要收的疣。

**引擎**
- Rust 二进制，manifest = `{engineVersion, platformAdapterVersion, capabilityDigest}`；加载器**写死** `platformAdapterVersion !== 'xiaohongshu-v1'` 即判非法（`native-page-engine/runtime.ts:47`）。
- 单个 `platformAdapterVersion` 字段 → 现状像「一个二进制 = 一个适配器」。多适配器打包是**未决设计题**（见 §5.1）。

**云端**
- `PLATFORM_REGISTRY` 三平台条目齐全；`normalizePlatformId` 别名漏斗；发布 = 浏览器 composer 模型，`PublishPlatformProfile.platform = Exclude<PlatformId,'wechat_channels'>` 明确排除 API-only；定时发布 `schedule-policy.ts` 仅允许 xiaohongshu。

**抖音探针（上游 change，约 15–20% 到生产）**
- TS，`src/douyin/probes/interaction-probe.ts`（约 488 行）+ 手动 runner；复用 `browse/cdp-util.ts` 拟人原语。
- 已做：AdsPower 归属自证 + attach、开当前卡进 `?modal_id=` 详情、门控单向单次 like/follow/collect、「我知道了」浮层关闭、私聊/群聊分类、直播普通发言。
- 未做：精选流**内部 overflow 滚动容器**的有界推进、评论 fill-only、发布页只读探针。
- **页面模型差异**（相对 XHS/FB 已烘焙的假设）：`window.scrollBy` 无效、须驱动内部纵向容器；卡片身份 `data-aweme-id`；详情是同页 `modal_id` 浮层非路由变化；`.click()` 不可靠须 trusted pointer；首触「我知道了」全屏浮层。

---

## 4. 分层实施设计

### Layer 0 — 引擎多适配器化（必做，一次性投资）
把「加平台」从「改热文件」降成「加声明 + 加适配器」：
1. **解开引擎对单平台的写死**：`runtime.ts` 的 `xiaohongshu-v1` 校验改为「接受 manifest 声明的、driver 期望的 adapter 版本」；`client.ts` 的期望 manifest 比对同理参数化。
2. **执行分发去硬编码**：`main.ts:672` 的 `platform==='xiaohongshu'` 门改为「driver 声明 `runtimeKind==='native-engine'`（或等价能力位）即起引擎」；理想是给 `BrowserPlatformDriver` 加可选 `createBrowseSession(deps)` 工厂，`main.ts` if 梯收成 `driver.createBrowseSession?.(deps) ?? <既有分支>`。
3. **打包 / digest 容纳第二适配器**（见 §5.1 待决题）。
4. **护栏（治 typecheck 抓不到的漂移）**：加一条 **两份 `PlatformId` parity 断言测试**（edge/cloud 清单一致），作为跨仓漂移的兜底。

> 克制点：**不做**跨仓共享协议包、**不做** TS 侧「跨平台 Feed 接口」抽象。见 §6。

### Layer 1 — 抖音浏览 v1（`douyin-v1` 适配器 + 云端声明 + 薄 driver）

**引擎（主体新工作，Rust）——`douyin-v1` 适配器**
- 精选流 `data-aweme-id` 卡片枚举 + 去重。
- **内部 overflow 纵向容器的有界推进**（不是 `window.scrollBy`），按实测位移 / 新卡数如实回报，无新增报 `no_change`。
- 详情绑定：`modal_id` 等于来源 `data-aweme-id` + ready 结构，`/video/<id>` 直链不作唯一路径（超时报 `page_not_hydrated`）。
- trusted pointer 进详情；like/follow/collect 状态判定（用固定结构 + active state 组合，白色本身不判定）；单向不反悔。
- 「我知道了」首触浮层：唯一可见、文本精确、最多点一次、确认消失再动作。
- 拟人点击/输入、反检测（引擎内，复用引擎既有微观行为层）。

**探针的定位**
- TS 探针 = **可执行的 DOM 契约规格**，Rust 适配器照它实现；聚焦测试作为契约回归。
- ⚠️ **探针不得进发布产物**：它本身就是要防的那类明文页面逻辑，必须 build-exclude 出客户端 asar（否则等于把护城河随包发出）。

**边端 TS 宿主（复用为主）**
- 新增 `aidcp-edge/src/douyin/driver.ts`：`BrowserPlatformDriver`，仅**元数据 + 身份 + 浮层**；`capabilities:['identity','overlay','browse','interact']`（**不含** publish/comment/join）；target host `douyin.com`。
- 复用 `NativeBrowseSession` + `command-mapper`（按需扩 allowed kinds）；`main.ts` 走 Layer 0 泛化后的引擎分支，不新增平台 if。
- 两份 `PlatformId` + `normalizePlatformId` 加 `douyin`（别名 `dy`/`抖音`），由 Layer 0 parity 测试兜底。

**动作名（零额外税）**
- 抖音会话发**既有规范名**（`open_note`/`like`/`follow`/`collect`/`scroll`/`back`）→ 云端 `handler.ts` 已认识，**不加别名表、不加路由白名单、不加协议消息**。这是相对 FB 的净省（FB 有历史消息名漂移才需别名）。

**云端注册表条目（诚实声明 = v1 的「简洁」）**

| 维度 | 抖音 v1 | 理由 |
|---|---|---|
| `noteActions` | read_content ✓、like ✓、collect ✓；comment ✗ `fill_only_not_production`、comment_like/browse_images/scroll_comments ✗ `v1_unimplemented` | 只放真做的 |
| `noteSurfaces` | read/like/comment = `detail` | 精选流开 `modal_id` 详情，与 XHS 同形 |
| `capabilities` | browse ✓、feed_refresh ✓、follow ✓；reel_follow/profile_visit/patrol/notification/search/group_join ✗（各带 reason） | 巡视/主页/搜索/群 v1 不做 |
| `scheduledAutomation` | 全 ✗（`official_api_only`/`v1_unimplemented`） | 发布走 OAuth，Layer 2 |
| `delegatedActions` | publish_*/comment_* 全 unsupported | 同上 |

- **风控**：抖音与 XHS 一样**暂无真实封号/限流信号接入** → v1 诚实地只靠配额档 gate，状态停 `normal`、tempo 1.0。**不投机造信号管线**；出现真实限流文案后，照 FB 的「加一个词库文件 → 喂 `applySignal`、绝不碰状态机」补。
- **console**：平台展示是安全兜底（未知平台渲染灰底原值，不白屏），补 `douyin` label/color 属**打磨**、非阻塞；仅当引入新风控/配额/模型枚举才会白屏（抖音 v1 不引入）。

### Layer 2 — 抖音发布（单独 change，OAuth，与浏览完全解耦）
```
用户本次批准 → 抖音 OAuth → /video/upload/ → /video/create/ → item_id → /video/data/ 回查
```
- 一条**新的云端出站 API 发布器**（与 edge-command 发布路径并列），按 publish-mode 分流；**edge 不持有 client secret**。
- **网页 CDP 最终提交明确禁止兜底**（缺应用/scope/OAuth/批准就报 `official_api_unavailable`，不静默降级）——正好契合「绝不静默假成功」。
- 与 Layer 1 无依赖，浏览 v1 不等它。

---

## 5. 未决问题（需拍板）

### 5.1 引擎单二进制 vs 多适配器打包
现状单个 `platformAdapterVersion` → 「一个二进制 = 一个适配器」。抖音有两条路：
- **A：每平台一个二进制**（最小改动，打包/签名/digest 各一份，客户端按 `AIDCP_PLATFORM` 选二进制）。
- **B：一个引擎二进制托管多适配器**（`platformAdapterVersion` 升为多值 / 数组，一次签名，运行时按平台选 adapter）。
- 倾向：**先 A 落地抖音**（改动局部、不动引擎架构），**B 作为引擎侧演进目标**（平台变多后签名/分发成本才划算）。二选一直接决定 Layer 0 打包工作量。

### 5.2 Rust 适配器工作量取决于引擎「适配器 SDK」成熟度（未知）
引擎内部是否已有可复用的 adapter 脚手架 / 微观行为层供 XHS 之外复用，本次未探明。这是 Layer 1 引擎工作量的最大不确定项，实施前需在引擎侧坐实。

### 5.3 v1 是否要评论 fill-only
建议**否**：探针已把评论限定 fill-only/no-submit，产品价值低、且引入输入路径。v1 只做浏览 + like/follow/collect，评论留后续。

---

## 6. 对抗性评审

- **过度设计 A：在 TS 侧抽「跨平台 Feed 接口」。** 页面读取都进引擎后，TS 侧几乎不读 feed，更无必要；「多平台怎么组织」问题搬进 Rust 引擎，而引擎 `platformAdapterVersion` 本就是为多适配器留的缝。→ **不抽**，扩展单元 = 引擎适配器边界。
- **过度设计 B（已收回的旧结论）：为省事把抖音写成明文 TS 会话。** 违反反编译诉求，等于把护城河随包发出。→ **走引擎适配器。**
- **过度设计 C：提前抽 OAuth 发布抽象 / 造网页发布兜底。** → v1 声明不支持，单独立项，永不加网页兜底。
- **失败模式（最贵、typecheck 抓不到）：动作名回错名** → 角色永远等不到回执、调度器在详情页下发 feed 滚动（FB 踩过）。规避：抖音复用既有规范名、不新增别名。
- **失败模式：两份 `PlatformId` 漂移** → 边端声明 `douyin`、云端不认 → `getPlatform()` 静默回落小红书 → 抖音账号跑成 XHS 养号曲线。规避：Layer 0 parity 断言。
- **失败模式：注册表某格误声明 `supported:true` 或漏 reason** → surface 解析器 fail-open 让抖音悄悄继承 XHS 默认而非报错。规避：逐格显式核对，不支持必带非空 reason。
- **失败模式：探针明文随包发出** → 反编译诉求自我击穿。规避：build-exclude + 发布产物校验。
- **认知红线：不得把「进了引擎」当「不可逆向」。** 引擎抬高门槛、非绝对锁；设计与话术都不许依赖「引擎 = 安全」的假设。

---

## 7. Facebook 迁引擎债（backlog 标注）
- FB 浏览逻辑（约 20 文件 175 处 DOM 读取）目前明文在 asar，是本诉求下的现成泄露口。
- 建议：把「FB feed/reels/inline/like 迁 `facebook-v1` 引擎适配器」登记进 `docs/real-machine-acceptance-backlog.md` 或独立 change；抖音走通引擎第二适配器（Layer 0 + 5.1）后，FB 迁移可复用同一多适配器机制。

---

## 8. 信息源
- 平台抽象实读：`aidcp-edge/src/platform/{driver,registry}.ts`、`aidcp-edge/src/browse/edge-browse-session.ts`、`aidcp-edge/src/facebook/{driver,facebook-session}.ts`、`aidcp-edge/src/native-page-engine/{runtime,client,command-mapper,browse-session}.ts`、`aidcp-edge/src/main.ts`、`aidcp-cloud/src/platform/{registry,surface}.ts`、`aidcp-cloud/src/comm/{protocol,command-bridge,handler}.ts`、`aidcp-cloud/src/publish-agent/{platform-profile,schedule-policy}.ts`。
- 立项理由：`openspec/changes/native-page-engine-production-cutover/design.md`、`native-page-engine-spike/design.md`、`aidcp-edge/docs/native-page-engine-spike.md`。
- 护城河定义：`docs/research/llm-agent-paradigm-deepdive-2026-06-28.md`、`social-media-automation-landscape-2026-06-28.md`。
- 抖音现状：change `douyin-cdp-research-and-probes`、`docs/research/douyin-web-cdp-research-2026-07-23.md`（研究稿）、探针 commits edge `11022ec`/`49aeb4e`。
