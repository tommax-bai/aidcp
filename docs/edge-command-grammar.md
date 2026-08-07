# 云边命令语法与目标词汇蓝图

> **本文回答的是：归了账号层（云端决策）之后，命令这门语言本身怎么设计。**
>
> 三份产物分工，互为消费方，MUST NOT 互相复制：
>
> | 产物 | 回答什么 |
> | --- | --- |
> | [`edge-addressing-layers.md`](edge-addressing-layers.md) | 这件事**归谁**（本地四层 vs 云端） |
> | 本文 | 归了账号层之后，**命令怎么设计**（拆不拆、什么进名字、归哪类） |
> | 操作说明书（`aidcp-edge/src/client/operation-registry.ts` 等三份副本） | **每条命令的声明**（类别 / 传输 / 身份 / 浏览器 / 留痕） |
>
> **本文与蓝图 MUST NOT 派生第二张运行时表**——运行时逐命令声明的唯一落点仍是操作说明书。

> **快照声明**：本文行号、命令清单与判例结论为 **2026-08-06** 对代码的核对快照
> （Cloud→Edge 登记表 46 条）。fleet 高度活跃，**引用前请自己重核**；
> 规则本身不随行号失效，失效的只是指路的坐标。

---

## 1. 为什么需要语法

命令词汇没有语法时，每次新增全凭当时那个人的手感，而手感不能被检查。代价已在代码里：

- **同样「原语 / 面 / 目标 / 意图」四维，存量有四种编码**：`page.scroll` 只有原语（面塞在
  `PageScrollPayload.reason?: string` 一个裸字符串加注释里，`aidcp-cloud/src/comm/protocol.ts:1492`）；
  `note.scroll_comments` 原语+面；点赞 / 评论点赞按目标展开成两条；`note.open` 原语 + 参数面 + 参数意图。
- **「surface」三处三义**，其中一处不得不加注释「不是那个 surface」。
- **七条根本不是页面动作的命令被归进页面自动化**（详见 §4 判例四），身份闸只好手工挖六个洞当补丁。

**用户裁定（2026-08-06）**：后续每次新增浏览器操作，必须先按本语法讨论维度归属；
核心目标是 **CLI 层功能清晰**；存量 46 条不是保护对象，按 §6 蓝图分批迁移。

---

## 2. 六条规则

### 规则一 · 类别按「在编址什么」分，不按「怎么执行」分

一条命令归说明书哪一类，看它服务的对象是机器、分身、「环境→账号」的翻译，还是账号——
不看它要不要浏览器、走哪条连接。**「需要浏览器」≠「以页面账号名义动作」，这是两件事。**

### 规则二 · 命令是发令方写下的完整意图，执行层不补空

期望执行面必须由云端说出来（进名字或必填参数）。参数不完整的命令直接拒收报格式错误，
与未登记命令同族处理（fail-closed）。

**为什么**：「没说在哪个面就用当前的」——「用当前的」是执行层在替发令方做决定。
补空即决策，决策归上层。**拒收不是防御，是拒绝替上层做决定。**
期望写进命令，服务的是发令方自己的可调试性：不带期望，发错的命令会被照常执行并报成功，
发令方永远不知道自己错了。

### 规则三 · 语义差异才冒泡成新命令

四条判据**任一不同 ⇒ 拆成不同命令**：

| # | 判据 | 典型例 |
| --- | --- | --- |
| ① | **回执语义**：同一结果让云端做不同决定 | 信息流滚到底⇒刷新换批；搜索页滚到底⇒该词穷尽换词 |
| ② | **失败原因集合** | 群组页有「未加入看不到」，信息流没有 |
| ③ | **平台留痕 / 可重放性** | 合并只能按最坏一档，安全的那面被锁死 |
| ④ | **决定权落点**：边缘须自判上下文才知道怎么做 | 决策下沉，违反边轻云重（判例一） |

四条全同、只是页面长得不一样（选择器 / 布局）⇒ **MUST NOT 冒泡到协议**，差异留在引擎平台适配层。

**防爆炸的闸不是「少建命令」，是「无语义差异的组合不许建」**：条目按「每个面下真正不同的能力」
线性增长；会爆炸的是不问差异的面×原语笛卡尔积。
**「简洁」＝职责单一，不是条数少**——一条命令四个面打天下不是简洁：分支没有消失，
只是挪进实现内部和边缘的隐式状态机（会漂，出过事）。命令表少一条、边缘多一个隐式状态机，净亏。

### 规则四 · 同族同编码，一词一义

同一语义维度在同族命令里只用一种编码：要么都进名字，要么都进**结构化**参数——
绝不塞进自由字符串加注释（写错要在编译期或对表闸可见）。
新词入协议前先查这个词已经指什么；同一个词 MUST NOT 承载多个概念。

族间编址维度不同（手势编址面、互动编址对象）是语义差异，**不算违反一致性**。

### 规则五 · 期望不符，报错分两态

「**确认到不在**期望的面上」（读到了真实状态）与「**没能确认**在哪」（读不出来）必须是
两个原因值，端到端保留。前者要云端重新规划；后者可有界自愈复测。
压成一态，云端分不清该改路线还是该重试——三态不得压成一态，红线的既有要求在此的具体形态。

### 规则六 · 对错的账在云端，执行层只欠照做与如实回报

该不该做、做多少、做错了怎么办（风控 / 配额 / 人审 / 绝不重投）全在云端。
执行层对「这条命令是不是发错了」没有意见——它只在合同履行不了时如实说：
「你让我滚群组页，我找不到群组页」与「你让我点赞，我找不到那张卡」是同一件事（`no_target` 的既有形态）。

---

## 3. 三段对账

云端凭自己发过的命令**能推定**当前页（打开群组页成功 ⇒ 在群组页 ⇒ 可发加群），因果链成立。
但推定是**开环**的：任何一次非云端发起的跳转（平台自跳、弹层、重定向、断连重上、人碰了一下）
都会让它与现实脱节，且脱节无人上报。所以推定必须配对账，三段缺一不可：

```
① 命令带期望（名字或必填参数）   ← 让边缘有得可比；没有①，②永不发生
② 不符如实报错，两态分开         ← 规则五
③ 云端以观察命令问真相、重规划   ← 没有③，报错之后没有出路（该命令今天不存在，见蓝图批3）
```

面进命令词汇的真实作用：**把云端的推定变成每条命令自带的一次可证伪声明**，成本为零
（不占往返、不加延时）。

---

## 4. 判例（两正、一反、一混合）

### 判例一（正）· Reels 点赞的分叉 ⇒ 「在哪个面」该由下发时指定

云端下发同一条点赞命令、不说在哪个面；边缘靠自维护的会话状态分叉两套实现
（`aidcp-edge/src/facebook/facebook-session.ts:982`，`listMode === 'reels'` 三元分支）。
该状态**漂过**：浏览面开场钉一次、之后静默回落信息流，新号整场 11 次全进不了 Reels，
三条早退路径全不打日志。回执里的独立见证只在信息流面挂、云端归账仲裁只在那个面激活——
**「在哪个面」已经在影响云端记账，却是事后从回执里读到的。** 按规则三判据②④命中。

### 判例二（正）· 打开群组页 → 加群 ⇒ 期望最该进名字的一类

群组页约 7 秒才渲染完，节奏又刻意有停顿——推定与现实之间有真实窗口。而加群**不可逆、留痕**，
重复加群是付过代价的错误。命令名里那个「群组」给了边缘说「我不在你以为的地方」的机会；
反过来，可重放的滚动漏了面最多白滚一屏。

### 判例三（反）· 滚动的面区分早已存在，落成了裸字符串

「信息流滚 / 搜索页滚」这个区分不是没人想到——它已经在协议里，
落在 `reason?: string` 一个自由字符串字段加一句注释。不是穷举类型，写错了两边都编译得过。
**区分存在、语法缺席，就退化成这个样子**——规则四要防的正是这个形态。

### 判例四（混合）· 七条按执行载体归错类，救援清单是补丁

读身份（翻译层）、验证码协助（环境层）、租约与收尾（执行权编排）——七条全被登记为
`page_automation`，唯一共同点是**都需要浏览器**。类别错了，身份闸按类别一拦全拦，
只好手工挖六个洞（`IDENTITY_RESCUE_OPERATIONS`）。**那张救援清单的存在，本身就是分类错误的补丁。**
根治见蓝图批 2；MUST 等本语法立起来后做，否则改完仍无判据挡住下一次归错。

---

## 5. OpenCLI 借鉴清单

`github.com/jackwener/OpenCLI`（把网站变成 CLI、跑在已登录的本地 Chrome 上）。
用户定调：非常值得借鉴，要充分参考。**借四项，不借一项**：

| 借什么 | 它的形态 | 落到我们 |
| --- | --- | --- |
| **两层分离** | 语义命令与浏览器原语两个命名空间，不平级混放 | 协议层全语义；坐标级原语只活在引擎内部——比它更严：它的原语暴露给现场 agent，我们的决策者远程，原语不出引擎 |
| **命名空间化** | `<站点>.<命令>`，站点即目录 | `平台.面/对象.能力`——**站点＝顶层命名空间，与它同构**（用户裁定编法 A，见 §6.1）。页面长相差异仍留引擎适配器——它的 site adapter 正对应 Native 引擎的平台分片，规则三仍是「什么进适配器、什么进协议」的分界 |
| **只读 / 交互分组** | Get（read-only）与 Interact 两组动词 | 即「平台留痕」维（change `close-account-layer-operation-manual` 实装）——它画在文档分组里，我们画进机读描述符 |
| **观察命令** | `state`（带元素引用的页面快照） | 蓝图批 3 新增「问现状」（面 + 身份一次回），三段对账第③段 |
| **不借** | 每步快照循环（snapshot-and-act） | 它的决策者在现场、看是免费的，即便如此快照到动作之间页面照样会变；远程决策者照抄＝每个动作多一次往返。「前提随命令走 + 执行点核验」更新鲜（动手前最后一刻）且零往返 |

它能纯本地还有一个原因：只有前两层、账号层是空的（「账号」就是用户本人，无额度 / 风控 / 记账）。

---

## 6. 目标词汇蓝图（46 条逐条 + 新增 1 条）

### 6.1 命名空间：平台段（编法 A，用户 2026-08-06 裁定）

**凡以页面账号名义在平台上执行的能力，命令名顶层段＝平台**：`平台.面/对象.能力`。

裁定理由：平台间差异预期会持续扩大（小红书没有 group / reels，FB 没有收藏，视频号纯 API），
显式优于隐式，日志与沟通直观。**裁定时已摆明并接受的代价**：跨平台同语义的能力按平台各留一条
同构名（`xhs.note.like` / `facebook.note.like`），此刻语义逐字相同也不合并。

换回的收益：

1. **「哪条命令在哪个平台存在」由名字直接声明**。出入闸只需校验「平台段 = 账号所属平台」，
   不符拒发 / 拒收。引擎测试里那张手抄的「FB 独有命令排除清单」改由前缀推导——又消一份手抄。
2. **说明书可按平台声明差异化描述符**——失败原因集合、留痕细节本就可能按平台不同，
   同构名各自登记后有了落点。
3. **横向扩充天然显式**：新平台＝新前缀下的一组命令声明，缺什么、独有什么，一眼可见。

**适用边界（防笛卡尔积的新形态）**：

- 平台段声明的是**存在性与差异化声明位**；同一平台内，面×原语无语义差异仍不许建（规则三不变）。
- **宿主 / 环境 / 翻译 / 编排 / 传输域不带平台段**——任务租约、验证码协助、读身份、会话收尾、
  心跳、节奏、界面快照不编址任何平台。**§6.2 那七条改类命令恰好全在此列**：
  它们不带平台段，与判例四「它们不是页面动作」互为印证。
- 平台段取值 MUST 与代码平台枚举一致（本文以 `xhs` / `facebook` / `wechat` 行文，实装批以代码为准）。

### 族约定

| 族 | 命名形态 | 例 |
| --- | --- | --- |
| 手势 | `平台.面.动作` | `xhs.feed.scroll` · `facebook.reels.scroll` |
| 互动 | `平台.对象.动作` | `xhs.note.like` · `facebook.comment.like` |
| 导航 | `平台.目标.动作` | `xhs.note.open` · `facebook.profile.open` |
| 观察 | `域.动作`（无平台段） | 「问现状」（翻译层） |
| 非平台域 | `域.动作`（无平台段） | `edge.task.acquire` · `captcha.assist.capture` · `session.end` |
| **留痕写 durable-outbox 往返族**（批 6a 定案，批 7 豁免的到期裁决） | 请求 MAY 带历史名词尾段（`.request`/`.command`/`.batch`），应答＝`.result`，出箱确认＝`.ack`（cloud→edge，「exact accepted/duplicate 后才清 outbox」） | `wechat_channels.inbox.reply.send → .reply.result → .reply.result.ack` · `{p}.publish.command → .result` |

**第三族为何不并入前两族**（2026-08-07 批 6a 裁定实录）：三条 `.ack` 全是 cloud→edge 方向，「edge→cloud 应答＝过去分词」规则语义不适用；`wechat_channels.inbox.reply.result` 一型两用（fire-and-forget 上报与等 ack 的 correlated request 共用）；嵌套尾段结构被 edge 侧前缀匹配依赖。豁免成员：IM 三条往返链、`{p}.publish.command.result`、`publish.approval_action.result` / `publish.draft_image_remove.result`、`captcha.assist.click_result`（assist 子族本就整体保留）。

「note」一词全程恒指**内容单元**（打开它、作用于它、在它里面的手势都编址同一单元），一词一义成立。

### 6.2 逐条处置

**迁移＝直接切换**（用户裁定：不考虑老客户端、无双名并行、无别名映射）：
一批 = 两端同批改名 → 测试 → 部署云端 → 出包装机；旧名从两份协议穷举表**直接删除**，
类型穷举即迁移守卫（漏改任一端、任一消费方，typecheck 当场红）。
切换窗口内旧客户端对新名 fail-closed 拒收是**预期行为**；拒收在执行前，无重复对外写入风险。

#### 删除（4 条 → 批 1）

| 命令 | 理由 |
| --- | --- |
| `browse.next` | 已 `@deprecated`，被角色驱动路径取代 |
| `browse.scroll` | 同上 |
| `publish.request` | 协议墓碑，生产无处理器；无兼容层裁定下墓碑一并清 |
| `plan.response` | ~~待核实~~ **已核实（2026-08-06 批 1 实装）：有活发送点**（v1 应答构造 + 点赞触发工具）——留待 v1 路径整体退役，不在词汇批里删 |

#### 保留名 + 改类（7 条 → 批 2，即判例四的根治）

| 命令 | 现类 | 应归 |
| --- | --- | --- |
| `identity.read_current` / `identity.read_self_profile` | `page_automation` | 翻译层观察（需浏览器、不代表账号动作） |
| `captcha.assist.capture` / `captcha.assist.click` | `page_automation` | 环境层处置 |
| `edge.task.acquire` / `edge.task.release` | `page_automation` | 执行权编排 |
| `session.end` | `page_automation` | 编排收尾 |

说明书的类别词汇大概率要扩（如「页面观察」「环境处置」），身份闸随之不再需要救援清单打洞——
这正是根治的定义。**改类改变身份闸实际拦截范围，属行为变更，独立 change。**

#### 浏览词汇平台化 + 拆分（14 条 → 批 4）✅ 已实装（2026-08-06，change `platformize-browse-vocabulary`）

页面手势 / 导航 / 面命令全部加平台段；`page.scroll` 同批按面拆分。平台段取值＝代码枚举
（`xiaohongshu` / `facebook`，非本文行文的 `xhs`）。**14 旧名 → 22 新名**，前置核实结论：

| 现名 | 落地名 | 核实结论 |
| --- | --- | --- |
| `page.scroll` | `xiaohongshu.{feed,search}.scroll` + `facebook.{feed,search,reels}.scroll` | 面=feed/search/reels 三个：Reels 是真面（原靠 `targetSurface`+reason 族区分，字段已删）；**群不是面**（群内找首帖的滚动是引擎对 `note.open{selection}` 的内部分解，协议层从不单独指挥）；FB search 成立（三搜索角色恒注册 + 真实执行器） |
| `note.open` `note.close` `note.browse_images` `note.scroll_comments` | open/close 双平台、browse_images/scroll_comments 仅 xhs | `note.close` 云端零发送点（回列表走 `navigation.back`），仍改名保留、分工批 6 裁 |
| `feed.refresh` `search.execute` `profile.open` | refresh/search 双平台、profile 仅 xhs | FB 结构性不访作者主页（C4） |
| `group.join` | `facebook.group.join` | 引擎测试的手抄「FB 独有排除清单」已由 manifest `edgeTypes[]` 前缀推导取代 |
| `notification.*` 五条 | `xiaohongshu.notification.*` | 结构性 xhs-only：12 巡视角色注册被平台能力表拦、FB 引擎无臂 |

**顺手清账（据实修正批 1 遗留）**：`browse_next` 全链删除（真死）；`browse_scroll` **保留**——
它是首帖探测的引擎内部载体（`facebook/runtime.rs` 构造），排除表理由与 postconditions 证据已改写。

#### 互动平台化 + 按对象改名（5 条 → 批 5）✅ 已实装（2026-08-07，change `objectify-interaction-vocabulary`）

**5 旧名 → 9 新名**（协议 103→107、登记表 52→56），落地名与实装核实结论：

| 现名 | 落地名 | 核实结论 |
| --- | --- | --- |
| `interaction.like` | `xiaohongshu.note.like` + `facebook.note.like` + `facebook.video.like` | 按对象拆不按位置拆：**video 对象两个位置都合法**（Reels 活动视频 + feed 视频帖，后者即 0.25 概率赞的对象）；xhs 视频笔记仍是 note。执行点核对：note 对象到达 Reels ⇒ `object_mismatch_observed_reels` 诚实失败（Reels 上的对象只能是视频）；video 声明由云端两类发送点（Reels 节奏赞 / feed 视频概率赞）经 `EdgeCommand.likeObject` 落 bridge 组合表 |
| `interaction.collect` | `xiaohongshu.note.collect` | 仅小红书（FB 无收藏；平台段取代码枚举 `xiaohongshu`，蓝图行文 `xhs` 不采用） |
| `interaction.follow` | `xiaohongshu.user.follow` + `facebook.user.follow` | 对象＝用户；FB 执行语义不变（Reels 绑定、Feed/主页关注 `capability_unsupported`） |
| `interaction.comment` | `xiaohongshu.note.comment` + `facebook.note.comment` | 对象＝内容单元（FB 含群帖 keep-open 流） |
| `interaction.like_comment` | `xiaohongshu.comment.like` | 对象＝评论；FB 无评论点赞。名序反转（like_comment→comment.like）随对象编址消失 |

**关联键口径的据实修正（推翻交接文档「批 5 必须动值」预判）**：全量消费面探查坐实——关联键值与
风控动作名 `RISK_ACTIONS` 逐字同名**是设计**（cloud `protocol.ts` 明写「可直读、零映射」，`handler` 直接
强转入风控 outbox），被 kernel 跨仓枚举 + 9 张 DB CHECK 钉死。**批 5 只换键、值不动**：三张映射表
（edge `actionNames` / 退役 `FB_COMMAND_ACTION_NAMES` / cloud `LEGACY_ACTION_COMPLETION_ALIASES`）键
5→9、值原样映回既有五词（`facebook.video.like`→`like`）；~120 个值消费点 + kernel + DB 零改动。
两个命名空间**本该脱钩**（CLAUDE.md §2 早已写明「该字段是角色关联键，不是协议消息名」），本批把脱钩
坐实。机器闸：控制仓新增 `scripts/action-key-parity` 三表跨仓对账（键集 ⊆ / 同键同值 / 不对称须显式
豁免）；两仓各有穷举断言杀 `?? type` 静默回落。`FACEBOOK_UNSUPPORTED_COMMANDS` 手抄拒集按批 4 注记归零删除。

#### 新增（1 条 → 批 3，无平台段）

| 命令 | 说明 |
| --- | --- |
| 「问现状」（名称候选 `state.read`，实装批定） | 面 + 身份一次回，三段对账第③段；属翻译层观察，不编址平台 |

#### IM 族、发布与收尾（批 6）

| 现名 | 目标 | 说明 |
| --- | --- | --- |
| ✅ IM 族全部 15 条（实核修正蓝图「10 条」旧计数：sync 3 + reply 5 + offboard 3 + auth.status/auth.reopen + browser.control + runtime.controls） | `wechat_channels.inbox.*`（**已落地 2026-08-07**，change `platformize-inbox-vocabulary`；平台段取值＝代码枚举 `wechat_channels`，非行文简写 `wechat`） | 纯前缀换名、尾段逐字保留；「interaction」一词从协议消息命名空间整体退役，一词一义恢复。`.result`/`.ack` 同批定案为第三族约定（见 §6.1 族约定表）。换名后 IM 族**首次**落入平台段出入闸辖区（旧名不过闸）——生产侧 sidecar hello 已声明 `wechat_channels`，行为正确。`reply.send` 仍是唯一不经页面身份闸的留痕写（豁免已结构化为说明书类别推导，无手抄清单；已登记待议） |
| `publish.command` | 平台段化（`{p}.publish.command`，原子 kind 表分平台） | 发布是平台间差异最大的流程 |
| `navigation.back` | 与 `note.close` 定分工后平台段化 | 语义重叠则合并，不同则 back 带目标面 |
| `edge.task.acquire` / `edge.task.release` | 可选顺带改 `task.*` | 非平台域，无平台段；`edge.` 前缀冗余 |

#### 非平台域词汇收口（批 7 · 2026-08-07 据实立项）

~~保留不动（4 条）：`ui.snapshot` · `pacing.update` · `ping` · `pong`——域.动作已符~~
——**该判断已推翻**：只有 `pacing.update` 真的符合。复核（2026-08-07）发现非平台域这 14 条内部有四类不齐，
其中两类有真实代价、两类只是不好看。**按「不改的代价」排序，不按「改起来便不便宜」排序**（规则见 §5 加闸准入同源纪律）。

✅ **已实装（2026-08-07，change `normalize-nonplatform-vocabulary`）**：5 条改名、总数 103→（经批 5）107 不变本批份额。

| 问题 | 落地 | 不改的代价（立项依据） |
| --- | --- | --- |
| **同一主题两个家** | `risk.captcha_detected`→`captcha.detected`、`risk.captcha_cleared`→`captcha.cleared`；`captcha.assist.*` 保留三段（真子族） | **高**：名字不该编码「消费方拿它干什么」（当初进 `risk.` 正是这个错） |
| **应答命名三套约定** | **族约定定案：请求＝祈使动词，edge→cloud 应答与自发事实上报＝过去分词/过去式事实形**（observed / acquired / released / detected / cleared）。存量唯一孤例 `state.report`→`state.observed`（向 `identity.observed` 靠齐）；`identity.observed`、`edge.task.acquired/released` 本就合规不动。显式豁免：`ping`/`pong`（传输惯例）、`.result`/`.ack` 族（留痕写外发 durable-outbox 应答——**批 6a 已定案为第三族约定**，见 §6.1 族约定表）、`captcha.assist.click_result`/`.snapshot`（assist 子族整体保留） | **高**：下一对请求/应答三选一凭手感 |
| **方向靠名字判不出** | `ui.snapshot`→`ui.push_snapshot`（前置核实：单向推送、无应答无配对，四子项里最干净） | **中** |
| **第二段不平行** | `identity.read_current`→`identity.read_current_page`（动词＋地点宾语，与 `read_self_profile` 平行）；能力串 `identity_read_current_v1` 刻意不改（握手协商串与消息名脱钩，已加注释坐实）；`edge.task.*`→`task.*` 仍归批 6 | **低** |

**实装修正（前置核实结论的据实更新）**：「批 7 不需要出 kernel 新版本」只对传输豁免名单成立、
**对类型面不成立**——kernel `platform-types` 的 `IdentityCaptureCommand` 钉着旧字面量，已出
**kernel v0.1.3** 收编（automation pin 随升）。

**明确不做（记录理由，防后人重开）**：

- **`ping` / `pong` 保持单段**。传输层通用惯例，零歧义、跨系统可识别；套 `域.动作` 只会让它更难认。
  **本条是族约定的显式豁免**，不是遗漏——传输层惯例名 MUST NOT 被本语法强行规整。
- **`plan.response` 不改**。v1 兼容路径，随 v1 整体退役一并消失；给一条将死的路径改名零收益。
- `session.end` / `pacing.update` / `state.read` 三条**本就合规**，不动。

**注**：`navigation.back` **不属于本组**——它是以账号名义在页面上产生的手势，批 6 定完与 `note.close` 的分工后
按编法 A 平台段化（见上文批 6 行），此前误列入「非平台域」的说法作废。

### 6.3 迁移批次（一批一个 change，批次串行走协议热点）

| 批 | 内容 | 性质 |
| --- | --- | --- |
| **1** | ✅ **已完成（2026-08-06）**：删 3 条（`plan.response` 核出活发送点、留待 v1 退役）；迁移流程首跑坐实——类型穷举逐个点名残留直到全绿，Rust 侧留排除表过渡 | 纯减法（change `drop-dead-cloud-edge-commands`） |
| **2** | 7 条改类 + 说明书类别词汇扩容 + 身份闸摘救援补丁 + **出入闸的平台段校验落地** | 行为变更（闸的拦截范围），不动协议名 |
| **3** | 新增「问现状」观察命令 | 协议新增，三段对账闭环 |
| **4** | ✅ **已实装（2026-08-06）**：14 → 22 平台段名（协议 95→103、登记表 44→52）；`page.scroll` 拆三面、`targetSurface` 字段删；两道休眠平台段闸转正；`FACEBOOK_UNSUPPORTED_COMMANDS` 收缩到两条共享名互动命令（批 5 归零）；manifest `edgeTypes[]` 取代手抄排除清单；跨面到达诚实失败 `surface_mismatch_*` | 协议改名最大的一批（change `platformize-browse-vocabulary`） |
| **5** | ✅ **已实装（2026-08-07）**：5 → 9 平台段对象名（协议 103→107、登记表 52→56）；like 按对象拆（video=Reels+feed 视频帖）、执行点核对对象；**关联键只换键值不动**（据实修正：值＝风控动作名是设计，脱钩坐实）；`FACEBOOK_UNSUPPORTED_COMMANDS` 归零删除；新增 `scripts/action-key-parity` 三表对账闸 | 协议第 5 处同步点所在批（change `objectify-interaction-vocabulary`） |
| **6** | 两 change 并行开发、串行集成：**6a ✅ 已实装（2026-08-07，change `platformize-inbox-vocabulary`）**——IM 族 15 条 → `wechat_channels.inbox.*`（计数不变 107）、`.result`/`.ack` 第三族约定定案；**6b 实装中（change `platformize-publish-navigation-vocabulary`）**——发布平台段化（XHS 12 / FB 6 kind 分表、删载荷 `platform` 字段、automation 静默缺省清零）、`{p}.note.close` 删除（分工裁决＝合并进 back，云端零发送点）、`navigation.back` 平台段化（XHS 形 `targetPage` 必填）、`edge.task.*` → `task.*`、kernel v0.1.4（107→108） | 收尾清账 |
| **7** | ✅ **已实装（2026-08-07）**：`captcha.detected`/`captcha.cleared` 归一家、应答族约定定案（过去分词事实形，`state.report`→`state.observed` 唯一归一）、`ui.push_snapshot`、`identity.read_current_page`；`ping`/`pong` 与 `plan.response` 明确不动；kernel v0.1.3（类型面收编） | 纯内部词汇（change `normalize-nonplatform-vocabulary`，与批 5 并行开发、串行集成实证可行） |

---

## 7. 讨论中作废的结论（别重走）

1. **「云端看不到页面，所以面必须编进命令名」**——云端凭上一条回执**能推定**，因果链成立。
   真理由：推定开环，见 §3。
2. **「CLI 宽容文化（默认值 / 猜意图）危险，因为错了会留痕」**——拿后果定归属，
   与 addressing-layers 判例二同一错误形态。站得住的理由见规则二：补空即决策。
3. **「简洁（条数少）与定位清晰冲突」**——简洁＝职责单一，见规则三。
4. **「命令名 + 回执是云端的全部输入」**——已作废的第 1 条**经 OpenCLI 对照漏回来一次**、二次被抓。
   教训：对照与摘要文字是作废结论回流的通道，写对照时对照本节自查。
5. **「存量不重命名，因为要出包才生效」**——出包随时可做，不是障碍（用户裁定）。
6. **「那就双名两阶段并行」**——用户裁定：不考虑老客户端、不需要并行。直接切换；
   删旧名反而启用类型穷举守卫；别名兼容层才是前科所在（动作名两侧各 21 条手抄映射表，
   typecheck 抓不到，错一条＝角色永远等不到回执）。

---

## 8. 待决（登记，不裁决）

- **观察命令的最终形态与命名**：独立「问在哪个面」vs 并进身份读取成「问现状」（倾向后者，一次往返拿全）。批 3 定。
- **期望面进名字还是进必填参数**：报错能力上等价；规则三四条全同才允许参数形态。逐命令裁决。
- **`navigation.back` 与 `note.close` 的分工**：批 6 按代码坐实。
- **视频号 API 写路径不经页面身份闸**（`interaction.reply.send`）：已在 `close-account-layer-operation-manual` 登记，属身份闸判据范围，不在本语法内。
