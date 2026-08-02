## Context

### 迁移形态

2026-07 边缘把浏览器页面智能从 TypeScript 迁到 Rust「Native Page Engine」，动机是防反编译；实质是页面规则仍为 JS、构建期拼接并混淆后编进二进制、运行时注入页面执行（`aidcp-edge/native/page-engine/build.rs:13,39` 读取 `src/xhs-command-router.js`）。小红书于 `317cd47`（2026-07-22）切生产。明确决定是不双跑、不比对、不回退，回滚手段只有装包回滚。

### 机械约束（本 change 的全部结论建立在这几条上）

1. **小红书命令面几乎全部落在一个通配求值分支**。`native/page-engine/src/engine.rs` 的小红书分发（`execute_xhs_command_once`，`:598` 起）只对验证码抓取 / 点击、带 URL 的开帖、读自身主页、搜索、上传图片、进入发布入口、定时稿抓取与对账这几支写了平台语义（实读为 8 个 match 臂，其中定时稿抓取与对账合并一臂），其余 `_ => evaluate_router(session, command).await`（`engine.rs:708`）。即命令 JSON 塞进内嵌 JS、求值一次、拿结果。

2. **云端开帖不带 URL**。`aidcp-cloud/src/orchestrator/role-dispatcher.ts:3278-3288` 组装的 `open_note` 参数只有 `index` / `noteId` / `thinkMs`（迁移评论用的那次在 `:3058-3062`，参数为 `noteId` / `purpose` / `thinkMs`）。因此 `engine.rs` 那条「带 URL 才走导航 + 页型轮询」的分支在现役闭环里不成立，开帖恒走页内路由的合成点击路径。

3. **详情上报即浏览计数**。`aidcp-cloud/src/comm/handler.ts:667-690` 是浏览计数的唯一必经入口：收到详情就入队一笔 `view` 风控事实并 emit 互动事件，且不判详情是否空壳。所以「开帖判据松」直接等价于「假浏览进账本」。

4. **详情输出不产动作回执**。`aidcp-edge/src/native-page-engine/browse-session.ts` 的 `note_detail` 分支只调 `reportNoteDetail`，不发 `action.completed`（Facebook 分支另有 UI 旁白，与回执无关）。看图命令返回的是带 `refreshOnly` 的详情（`xhs-command-router.js:206-209`），云端 `handler.ts:670-673` 见 `refreshOnly` 只广播一条图片快照事件即返回，而深读角色只在 `action.completed` 且动作名为 `browse_images` 时清等待表（`aidcp-cloud/src/agents/deep-reader.ts:122-124`），且该等待表没有超时。

5. **联系方式串码在最后一步丢失**。云端下发（`aidcp-cloud/src/comment-agent/edge-steps.ts:341-352`）→ 边缘 TS 转发（`src/native-page-engine/command-mapper.ts:67`）→ Rust 声明并校验（`native/page-engine/src/command.rs:296,698`）三段都在，页内路由的评论分支只读正文一个字段（`xhs-command-router.js:236`，全文件对该字段零命中）。Facebook 侧在 Rust 里正确拼接（`native/page-engine/src/facebook/comment.rs:72-79`），小红书无对应物。

6. **本仓自己的真机文档已写死开帖结论**。`aidcp-edge/docs/xhs-layout-states.md:59-60` 记录：首页封面是不带访问令牌的裸链，直接导航得到错误页 `error_code=300031`；正确路径是真实点击（CDP 鼠标事件，**明确点名不是 `el.click()` 裸 anchor 导航**）触发单页应用就地开弹层、地址才补上令牌。该两行由 `aidcp-edge f3c51d5`（2026-06-30）写入，即**早于**小红书 Native 化（`317cd47`，07-22），因此是迁移前的真机结论、未在 Native 路径上复核。当前实现走的是被点名的那一种（对锚点调页面内点击），且成功判据「地址里能解析出笔记 id」在错误页上同样成立（`xhs-command-router.js:187-196`）。

7. **旧实现留下了可对照的诚实基线**。点赞 / 收藏：结构选择器 + 有界轮询到状态翻转（上限 1500ms，注释记录真机翻转多在 300–600ms）+ 未翻转回 `state_unchanged`（`317cd47^:src/browse/browse-session.ts:2296-2352`）。看图：`no_target` 与 `browsed=N` 两种诚实回执（`317cd47^:src/browse/browse-session.ts:2817-2833`）。通知抽取：真机 dump 校准的行结构、正文只取正文容器且缺失发空串、去重键刻意排除主页链（`317cd47^:src/browse/notification-monitor.ts:126-170`，原因注释白纸黑字）。

8. **现有小红书路由测试的保护是空的**。`aidcp-edge/test/native-page-engine/router-contract.test.ts:37-39` 在 `HTMLElement.prototype` 上全局钉死 `getBoundingClientRect`（返回 100×40），于是路由里的可见性判断（`xhs-command-router.js:7-12` 要求宽高 > 1）在测试里恒真——同一写法在 Facebook 契约测试里也存在，已被独立认定为「保护从没被测过」。

9. **一条命令只能回一个输出**。Rust 侧 `evaluate_router` 返回单个 `(EffectPhase, CommandOutput)`，宿主 `src/native-page-engine/browse-session.ts` 按输出 `kind` 走互斥分支（`note_detail` 在 `:310`、`action_receipt` 在 `:341`）。因此「看图改成回动作回执」在结构上就意味着不再回详情投影——而当前那条 `refreshOnly` 详情在云端有两个真实消费方：精选库参考图刷新（`aidcp-cloud/src/agents/curated-note-evaluator.ts:98,114-118`）与灵感 / 观测笔记的 `referenceImages` 更新（`aidcp-cloud/src/server.ts:4914`）。只改回执、不安排图片证据的去处，会把「翻页后新加载到的图」静默弄丢，等于用一个静默丢数据换掉一个静默挂起。

10. **滚动评论区同样恒报成功**。`xhs-command-router.js:211-213` 无条件 `action('scroll_comments', true, …)`，真实位移只以字符串形式塞进 `observation.reactionText`，`observation.articleIndex` 直接回报请求值 `p.count`。云端 `aidcp-cloud/src/agents/comment-reviewer.ts:106-110` 读 `payload.ok` 后按 `parseScrolledCount(reason, 1)` 取值，而回执不带 reason ⇒ 一次没滚动的评论区也被记成「已读 1 条评论」。这正是红线里点名的 `count||1`。

### 规格侧现状

- 小红书至今没有与 `openspec/specs/native-facebook-behavior-parity/spec.md` 对等的平价能力，这本身就是缺口：Facebook 的每一次退化都有一份可对照的行为契约，小红书没有。
- 发布正文填写与提交判据已有权威规格且已并入主 spec：`openspec/specs/publish-pipeline/spec.md`「边缘指令运行时逐条执行并每条后置校验如实回报」写明了逐字输入、每个换行独立派发真实 Enter、语义相似度 ≥ 0.90 放行；`openspec/specs/publish-submit-integrity/spec.md`「成功判定锚定真实成功信号」写明了成功须锚定真实平台信号。这两条**不需要重写**，缺的是「执行搬进 Native 后这些契约仍然适用」这层约束。
- `openspec/specs/notification-monitoring/spec.md` 真实存在且有 7 条要求，其中「通知去重且不丢真消息」只说「稳定 itemKey」而未定义什么算稳定——正是本次退化钻的空子。

## Goals / Non-Goals

**Goals**

- 建立 `native-xiaohongshu-behavior-parity`，把小红书 Native-only 路径上的目标绑定、提交证据、后验证据与终局语义写成可验证契约，与 Facebook 平价能力对等。
- 消除已坐实的两条 critical：评论联系方式串码丢失、开帖以「地址里有笔记 id」判成功。
- 消除五类「先动作、再宣称」：看图无回执且无前进校验、返回恒真、滚动评论区恒真且把请求条数当实测条数、点赞类单次采样 + 「已」字兜底、通知抽取三处退化。
- 把不产出真实度量的兼容分支按死代码清除，而不是给死代码补测量。
- 把「测试夹具使可见性判断恒真」这类使保护失效的写法写成规格约束。

**Non-Goals**

- 不改协议 v2、命令信封、结果形状、动作名口径。
- 不改云端选卡概率、配额、节奏系数、风控记账口径。
- 不重写 `publish-pipeline` / `publish-submit-integrity` 已有的发布填写与成功判据契约，只约束它们在 Native 执行位上不得被豁免。
- 不做 Facebook 侧的修复（简报 G11 第 ③ 条的轮播计数属 Facebook 路由，归 Facebook 平价 change）。
- 不含 Cloud / automation 三进程改造，不含部署、安装包与真机动作。提案最初的 spec-only 边界已按用户“继续迁移修复”的明确裁定扩为 Edge 实装，偏离与提交逐项记录在 tasks 6.4。

**分派简报里明确不纳入本 change 的条目（逐条给归宿，避免静默漏掉）**：

| 简报条目 | 处置 |
| --- | --- |
| G11③ Facebook 图片轮播计数统计「点击派发成功」次数；契约测试把尺寸全局钉死 | 不做。属 `facebook-router/**`，归 Facebook 平价系列 change。本 change 只修**小红书**那份契约测试的同款夹具写法（`router-contract.test.ts`），不动 `facebook-router-contract.test.ts`。 |
| 「Facebook 热度恒 0 的正则判定」及其「所有布局下中性按钮不含数字」未核验 | 不做。Facebook 路由，归 Facebook 平价系列。 |
| 小红书提交窗口缺失（写命令被抢占撕裂的可能） | 不做。归同批 `restore-native-xiaohongshu-session-guards`（其 `edge-task-execution-coordination` delta 已写「每处不可逆小红书页面写入须开提交窗口」）。 |
| 跨环境错投（重连复用旧端点） | 不做。属边缘多环境 / 云端端点选择面，与页面动作诚实无关；本 change 不产出该面的规格，也不登记真机项（其真机项归属该面的 change）。 |
| 四处「找不到就退回文档主体」的空根塌陷 | 不做。本 change 的要求覆盖的是**判据**（正面证据、结构化定位），不改 `detailRoot() || document` 这类回落写法本身；该写法一旦被真机确认造成跨面误操作，另起 change。已在此具名，不算漏项。 |
| CI 上实际生效的 Rust 编译器版本无法事后对账 | 不做。属构建 / 产物门禁面，归 `enforce-native-engine-artifact-gates` / `harden-native-engine-runtime-contracts` 一类 change。 |
| 简报 C 段第 1 条：七个簇里「维持原判」条目（F-IPC-*/INJ-*/TXT-*/PACE-* 等）只有编号、正文缺失 | 不做，但**记为已知风险**：本 change 的缺口清单据其他条目交叉引用推断，若那批条目正文补齐后出现与小红书页面动作相关的新条目，需对本 change 做一次并案复核。本 change 不据编号推测其内容、也不据推测写要求。 |

**覆盖漏洞的范围外交接（2026-07-28，合并退役实现参照书后新增；具名交接，不静默漏掉）**：

| 漏洞 | 为什么不在本 change 做 | 建议承接方 | 不做的后果 |
| --- | --- | --- | --- |
| 未读监测体的**宿主侧**半边：周期调用未读读数、维持 sticky 状态、在「无→有」翻转时发一次未读信号、持有单调翻转的批次序号 | 落点是宿主装配（`aidcp-edge/src/main.ts` 里 `if (false && …)` 短路掉的那段、`src/native-page-engine/browse-session.ts` 的周期探针当前写死只服务 Facebook）。D6 已把宿主装配面整体划给同批 change，本 change 的单写区是页面规则；两个 change 同时改同一段装配会撞车 | `restore-native-xiaohongshu-session-guards`（其 1.2 周期探针按平台分类适配、6.1 恒假装配块逐条对账、6.4 退役监测体去留结论）；若该 change 拒收，则须单起 change，并在本 change 4.6 记录为阻断依赖 | 云端整条通知巡视链的**唯一**触发源就是这个未读信号（`aidcp-cloud/src/agents/notification-gatekeeper.ts:48`、`src/orchestrator/role-dispatcher.ts:2062`），而边缘全仓当前只有协议定义、没有发送方。不做则本 change 的通知抽取 / 清零 / 计数 / 去重键修复**全部实装了也不通电**；更坏的分支是承接方 6.4 按「仅被恒假块引用」把退役监测体当孤儿删掉，通电路径被永久抹掉 |
| 云端深读等待表的超时兜底 | 已在 D3「否决 A」定性为给假成功加止血带，且属云端角色面 | 真机 5.2 复现后单独登记的跟进项（`aidcp-cloud/src/agents/deep-reader.ts`） | 看图回执若又回归缺失，深读会重新变成无上限等待（本 change 的 2.3 已从边缘侧堵住，云端兜底只是纵深） |

上表第一行的**页面判据那一半留在本 change**（任务 2.9）：结构化角标读数、双布局取可见入口、读不到不得当「无未读」，这些都在页面规则里，与宿主周期无关。切分理由见 D8。

**交接收口（2026-08-02）**：归档的 session-guards change 完成了周期探针平台化并删除恒假旧装配，但没有消费 `notificationUnread`。在该共享区已无活跃单写者后，本 change 以 Edge `a2d0c74` 在现役 `NativeBrowseSession.observeProbe` 上补齐发送方，不恢复 `CdpNotificationMonitor`、不新增第二套定时器；原交接事实保留，最终通电结论见 D14。

## Decisions

### D1. 新增独立能力，而不是把要求塞进现有能力

选：新增 `native-xiaohongshu-behavior-parity`（ADDED），并只对 `notification-monitoring` 做一处收紧（MODIFIED）。

否决 A：把全部要求写进 `native-page-engine`。理由：`openspec/specs/native-page-engine/spec.md` 是当初可行性验证阶段的只读探针规格（opt-in / read-only），不是生产运行时规格，塞生产行为进去会把两种性质混在一条能力里。

否决 B：写进活跃 change `native-page-engine-production-cutover` 的 `native-page-engine-production`。理由：该能力尚未归档、尚未并入主 spec，跨 change 引用未落地能力会造成两处都不权威。本 change 与它的关系写在 D6。

否决 C：把评论串码丢失写成 `group-chat-injection` 的 MODIFIED。理由：该能力的「边缘保真——人审文本可被边缘原样送达」已经完整覆盖这条不变量，当前是实现违反既有规格、不是规格缺口；重述一遍只会制造两处权威。缺的是「Native 平台适配器是这条不变量的执行位」这层约束，它属于新能力。

### D2. 开帖按「失败关闭的证据要求」写，不把 404 写成既成事实

真机文档给出的是 2026-06-27 的结论，Native 化后单页应用是否恰好拦截程序化点击、导航是否仍走内部路由，**未在 Native 路径上真机复核过**。因此规格只写可无条件成立的那一半：成功必须有正面详情证据（详情容器存在，且标题 / 正文 / 图片至少有一项非空），错误页语义命中即诚实失败，未确认打开一律不上报详情。执行方式（页内点击 vs 可信指针输入）不在规格里钉死，而是作为真机验收项 + 条件式实装任务：真机若确认裸链落错误页，实装改用可信指针输入。

否决：直接把「MUST 使用可信指针输入」写成要求。理由：那是把一条未在当前路径复核的推断当结论；而且证据要求这一层已经足以堵住「假成功 + 假浏览计数」，是更小且更稳的不变量。

### D3. 看图的终局落在动作回执上，不落在详情输出上

规格要求看图必须产出一条带真实前进张数的动作回执（或 `no_target`），因为云端深读的等待表只认动作回执。同时要求每一步重新解析翻页控件并校验图序真前进——当前实现（`xhs-command-router.js:206-209`）在循环外只取一次控件引用、循环里对同一节点连点 N 次、全程不看图序，并且**根本不回报张数**（返回的是 `refreshOnly` 详情）。前进张数实际是多少，代码里推不出来：节点若在首次翻页后被替换，后续点击会被可见性判定静默拒绝；节点若是常驻箭头，连点可能真前进。所以本 change 只断言「无度量」，不断言「恒为 0」——真实分布留真机验收项 5.2。

否决 A：改云端深读等待表加超时来兜底。理由：那是给假成功加止血带，不是把回执改诚实；超时兜底作为独立跟进项登记（见 tasks 第 5 节），不进本 change 的实装范围。

**采纳的补充约束（否决 B 的修正）**：机械约束 9 已确认一条命令只能回一个输出，且当前那条 `refreshOnly` 详情是云端参考图刷新与灵感池图片更新的唯一来源。因此规格不能只写「改回回执」——必须同时要求「翻页过程中观察到的图片证据仍到达云端」，机制不在规格里钉死（可由回执携带、或由宿主在回执后补一次详情读取），但**静默丢掉该证据不算满足本要求**。原先的否决理由（「两条输出语义重叠难对账」）只对「两条都当终局」成立；终局唯一落在回执上、图片证据作为附带观测，不构成两条终局。

否决 B'：把图片证据也砍掉、只留回执。理由：那是用一个静默丢数据换掉一个静默挂起，两条都在红线内。

### D4. 点赞类的确认窗口写成「有界轮询到状态翻转」，而不是写死毫秒数

旧实现的注释记录真机翻转多在 300–600ms、上限 1500ms。规格写「MUST 在有界窗口内轮询到状态翻转才可判成功；固定单次采样 MUST NOT 作为判据」，把具体上限留给实现，避免把一个真机标定值冻进规格后随平台改版失效。同时明确禁止「控件文本含通用完成词即判成功」这条兜底——它是把定位退化（可能命中大容器）放大成假成功的那一步。

否决：规格里钉死 1500ms。理由：数值属实装细节，且旧值本身是一次真机标定的快照。

### D5. v1 兼容分支按死代码清除

`xhs-command-router.js:241-243` 的 `plan_execute` 滚动步骤不做任何测量就写「已确认」。复核结果（比初判更弱，按弱的写）：

- 云端确实仍有 `plan.response` 的产出点（`aidcp-cloud/src/comm/handler.ts:1334-1340` 的 `onPlan`、`src/comm/like-command.ts:60`），都属 v1 兼容 / CLI 触发。
- 规则式规划器（`src/planner/simple-planner.ts:24-48`）产出的四个动作标识里，`note.like_button` 与 `note.follow_button` **与路由映射表是对得上的**；只有收藏那条对不上（规划器产 `note.favorite_button`，路由表只有 `note.collect_button`）。所以「标识全对不上、路径必然跑不通」这条初判**不成立**。
- 更关键的是规划器还有 LLM 兜底分支（`simple-planner.ts:68-78`），它接受模型自由产出的 `actionId` 且允许 `op:'scroll'`（`:16` 的 `VALID_OPS`）。即「`page.scroll` 步骤永远不会被产出」在代码上也证明不了。

因此本 change **不断言这条路径不可达**。规格写成「任何保留下来的小红书滚动步骤 MUST 按实测位移回报；无法满足的兼容分支 MUST 移除而不是保留虚假确认」——删除与修正都能满足；哪一条落地由 tasks 2.8 的前置判据决定，而那道判据（是否真有活跃产出方）在此是**载荷性的**，不是形式手续：若判不清，默认走「补测量」而不是删。

否决：单独给它补测量。理由：给一条无人跑通的路径补测量等于给死代码续命，且会让后续读者误以为它是活路径。

### D6. 与其他并行 change 的边界

**不碰的文件**（其他 change 或热点单写者所有）：

- `aidcp-edge/native/page-engine/src/facebook-router/**`、`native/page-engine/src/facebook/**`、`facebook.rs`、`test/native-page-engine/facebook-*`：属 Facebook 平价 / 边界系列 change。简报 G11 第 ③ 条（Facebook 轮播计数统计的是点击派发次数）**不在本 change 范围**。
- `aidcp-edge/native/page-engine/src/wechat.rs`：属微信系列 change。
- `aidcp-cloud/src/comm/protocol.ts`、`aidcp-edge/src/comm/protocol.ts`、`aidcp-cloud/src/comm/command-bridge.ts`、`event-bus/types.ts` 的角色枚举、`src/risk/risk-state-machine.ts`：协议四处同步与风控热点文件，本 change 不动。
- `aidcp-edge/src/main.ts`、`src/native-page-engine/browse-session.ts` 的宿主装配：属同批 change `restore-native-xiaohongshu-session-guards`（见下）。
- `openspec/specs/` 下任何已合并 spec 文件：只经归档流程合并。

**与同批 `restore-native-xiaohongshu-session-guards` 的关系（必须串行集成的一处）**：该 change 处理宿主侧——按平台装配阻断监测、把提交窗口下沉到真正执行写入的运行时、验证码键入取证、平台中立诊断、清除恒假短路装配；它已声明**不碰 `xhs-command-router.js`**（本 change 的单写区）。两者的交集有三处，集成时按此处理：

1. `native/page-engine/src/engine.rs` 的小红书执行入口：它加提交窗口参数，本 change 只可能改分发臂 / 输出装配。**同一文件两个写者 ⇒ 后 land 的一方先 rebase 再跑 `cargo test`，不并行改同一函数体。**
2. `test/native-page-engine/`：两边都加文件。本 change 只新建 `xhs-behavior-parity.test.ts` 并改 `router-contract.test.ts` 的夹具，其余文件不动。
3. 语义耦合：该 change 要求「小红书评论提交必须开提交窗口，窗口拿不到即诚实判未开始」；本 change 要求「评论必须提交合成后的完整文本、回读不含串码即提交前诚实失败」。两条同向、不冲突，但**实装顺序上窗口在外、文本合成在内**：窗口没拿到就不该走到编辑器写入。若两条实装落在不同提交里，后落地的一方须确认另一条已生效、未被自己的改写绕过。

本 change 的 Why 里「小红书侧此前零个修复 change」指的是**页面动作平价**这一面；宿主侧那面由上述 change 承接，不是本 change 的遗漏。

**与 `native-page-engine-production-cutover` 的关系**：那是迁移主 change（42/51 仍活跃），其真机验收项 9.4 / 9.5（真机只读矩阵、真机写动作验收）至今未勾——小红书的能力压平从未被真机检验过，这正是本 change 的成因。本 change 不修改它的 `tasks.md`，也不引用它尚未归档的能力名；本 change 的真机验收项与它的 9.4 / 9.5 存在共享真机环境的依赖，收拢办法是登记进 `docs/real-machine-acceptance-backlog.md` 的对应簇，由 fleet 层统一编排。

**与 `add-managed-automation-runtime` 的关系**：该 change 在运行模型层取代约 60 份已上线 spec，其 `design.md` §24 处置映射表覆盖 browse / publish / 风控配额等能力。本 change 新增的是**执行端页面行为**契约（Native 小红书如何证明一个页面动作真发生），不涉及排期 / 仲裁 / 配额 / 客户投影这些运行模型面；对 `notification-monitoring` 的修改也只收紧去重键定义、不动巡视触发与恢复语义。若 §24 后续把 `notification-monitoring` 判为取代，本 change 的那一处收紧应随之并入承接要求，而不是各写一份。

**与 Facebook 平价规格的关系**：新能力对照 `openspec/specs/native-facebook-behavior-parity/spec.md` 的 7 条要求写小红书对等版，但**不复制 Facebook 的能力边界结论**（例如 Facebook 把看图 / 评论点赞 / 通知列为不支持，小红书这些是支持的活路径）。

### D7. 把「滚动评论区」与「返回列表」并成同一条判据，而不是只修返回

复核时新发现（不在分派简报里）：滚动评论区（`xhs-command-router.js:211-213`）与返回列表是同一个缺陷的两个实例——`ok` 硬编码为真、真实结果只写进一个更弱的旁路字段。滚动评论区还多一层：`observation.articleIndex` 直接回报请求条数，云端据此把「已读评论数」记成 1（机械约束 10）。它是浏览闭环上每篇笔记都跑的活路径，不是兼容分支。

选：在「页面效果必须来自实测」这条要求下同时约束两者，并把「不得把请求值当实测值」写成显式禁令。

否决：只修返回列表、把评论区滚动留给后续 change。理由：两处判据同源、同文件、同一次改动面，分开只会让第二处继续以「有个观测字段」的样子留在红线外；而且「已读评论数恒 1」直接进云端阅读投影，比返回列表那条影响面更大。

### D8. 未读检出按「页面判据留本 change、周期与信号交接」切分，并把「不通电不算修好」写成对账门

复核（2026-07-28）坐实的现状：Native 运行时没有任何未读探测——`aidcp-edge/src/main.ts:1043` 用恒假条件短路掉整段浏览器态装配，块内原有的未读监测注册在当前树里已不存在；Native 侧唯一的周期探针（`src/native-page-engine/browse-session.ts` 的 `scheduleProbe`）第一行就按平台判定只服务 Facebook；页面探针 `native/page-engine/src/xhs-page-probe.js` 只数「通知入口元素个数」供页型分类用，与「有没有未读」无关。边缘全仓 `notification.detected` 只出现在协议定义与协议穷举测试里，**没有发送方**。

选：把这条漏洞按执行位切成两半——页面判据（结构化角标读数、宽/窄双布局取可见入口、读不到回「读不到」而非「无未读」、页面规则不得自造批次序号）落本 change 的规格与任务 2.9；周期调用、sticky 状态、翻转一次上报、单调批次序号具名交接给宿主装配的属主 change，并在本 change 加一道**通电对账门**（任务 4.6）：承接方未落地时，本 change 的通知类修复必须记成「已实装、生产未通电」，不得按已生效结案。

否决 A：整条都交接出去。理由：角标判据是页面规则里的东西（本 change 的单写区），交出去等于让宿主属主去写页面规则；而且那份 2026-06-23 真机校准的结构判据、双布局遍历告警与旧版宽 class 假阳性教训，都在本 change 的参照书里，换个 change 做会丢上下文。

否决 B：整条都在本 change 做（含宿主周期与信号发送）。理由：会与同批 change 争夺同一段宿主装配（它正要删那个恒假块、并把周期探针改成按平台分类），两个 change 同改同一函数体是 D6 明令要避免的；且它的 6.4 正在给退役监测体做去留判定，本 change 越过它单方面恢复会让那条判定失去意义。

否决 C：只在本 change 的规格里写「必须有未读检出」，不加对账门。理由：那正是「修了但不通电」的成因——页面判据齐备、无人周期取用，链路照样全黑，而任何机械手段都不会报错。故规格里显式写明「无人取用的读数不算满足契约」，任务里配一道对账门。

**通电复核（2026-08-02）**：历史分工结论不变，但阻断已由 Edge `a2d0c74` 关闭。现役 lifecycle-managed `page_probe` 调用 `NativeBrowseSession.observeProbe`，后者只为小红书消费未读三态并发送 `notification.detected`；静态装配门同时钉死 `src/` 中恰有一个生产发送点且不实例化退役监测器。波次、账号、Cloud 会话与阻断顺序的细化见 D14。

### D9. 通知类退化按「Native 是既有契约的执行位」写，不重述已合并的通知规格

已合并的 `openspec/specs/notification-monitoring/spec.md` 已经写死了三件事：监测体软中断 + fail-open + 绝不把未读重置为无、翻转只上报一次；「评论/@ 浏览滚到底 / 直到不再有新项或角标清零，不因固定屏数遗留未清未读」；分诊每处理完一类要重读三栏未读计数、循环到清零、有界且诚实放弃。本次查出的四条通知漏洞（滚到底循环消失、per-tab 计数退成整页正则、分类栏点击退成全页文本查找、截断退成 UTF-16 切片）都是**实现违反了已生效的规格**，不是规格缺口。

选：与 D1「否决 C」同一口径——不去改 `notification-monitoring` 的既有要求，而在本 change 的平价能力里写「Native 执行位仍受这些契约约束」以及那几条既有规格没定义到的判据（角标从哪读、栏目怎么选、计数怎么算、字段怎么截断）。这样权威只有一处，且改的是「谁来执行」这层。

否决：把四条写成 `notification-monitoring` 的 MODIFIED。理由：MODIFIED 要整条重述既有要求，会把「加一条判据」变成「重写三条已上线要求」，评审时看不见真正的改动，也容易与 `add-managed-automation-runtime` 对该能力的后续处置撞车。

### D10. 定时模式绑定使用 Native 会话真态，不扩 Cloud 协议

E4 的危险不只在 `set_schedule` 自证：即使该原子当时读对，后续 `submit_publish` 仍会把页面上文案为「发布」或「定时发布」的叶子混在一起按横坐标取最右，丢掉退役实现的 `scheduleModeConfirmed` 绑定。最坏结果是平台立即发布、Cloud 却按既定序列记成 scheduled。

选：在 Native `EngineSession` 内维护发布模式三态（unknown / immediate / scheduled(target minute)）。只有确认进入新发布页才把状态置为 immediate；只有 `set_schedule` 的开关、目标分钟、精确「定时发布」提交控件三项正证据全部成立才置为 scheduled。`submit_publish` 把该内部期望注入页面规则，页面规则在不可逆点击前重新读取开关与目标分钟，并只解析与期望模式逐字相等的叶子提交控件。unknown、模式漂移、分钟漂移、目标按钮缺失都在点击前失败，`submitDispatched=false`。导航新稿、失败的定时设置与已派发提交都不得把旧 scheduled 状态带给下一稿。

同时，`set_schedule` 先读开关三态：明确 on 时保持幂等、不再点击；明确 off 才点击并有界等 on；读不到不猜。时间统一按 Asia/Shanghai 格式化到 `YYYY-MM-DD HH:mm`，后置读数必须精确到分钟，且必须与仍为 on 的开关和「定时发布」提交控件同时成立。

否决 A：给 Cloud → Edge 的 `submit_publish` 新增 `scheduled=true` 参数。理由：序列里确有该意图不等于平台真态；直接信任上游字段仍可能在开关没生效时去点立即发布，而且会无谓扩大协议四处同步面。

否决 B：在页面 `sessionStorage` / DOM 上写一个「定时已确认」标记。理由：这是执行端自造证据，跨稿或页面重水合后可能陈旧；它不能证明提交前平台仍处于同一模式。

否决 C：只把 `set_schedule` 的小时前缀改成分钟等值，不改 submit 绑定。理由：两条命令之间平台状态仍可能漂移，且提交路径依旧能按文本排序选中错误模式，未关闭不可逆风险。

### D11. H.5 复验改按当前可执行边界穷举，并把“命令已交给运行时”拆成“会话获取”与“记录已写入”

初始缺口清单只保留了“69 条候选、首轮复验 16 条、余 53 条”三个汇总数，**没有保留那 53 条的逐条原始明细**。因此本轮不能假装完成一次不存在的逐项勾销。可复核的替代口径是按当前可执行边界重新穷举：页面规则的所有终局、Rust typed-output 转换与会话状态、宿主 transport/runtime/browse/publish 的回执和重试转换点；并与 `command-postconditions.json` 已归零的写命令 unread 棘轮对账。这样覆盖的是今天仍可执行的表面，不把已经删除、重复登记或永远没有生产者的旧候选算成现役缺口。

复验坐实了一个共享机制错误：宿主过去在调用 `runtime.execute()` 之前就把 `dispatch.started=true`，但运行时首先要启动进程并获取 session，之后才可能把 command record 写入 stdin。于是 session 获取失败这种零派发会被误报成 ambiguous；相反，发布命令记录已经写入后若进程超时 / 退出，异常又不携 `submitDispatched`，会被上游当作提交前失败并安全重试。两条方向相反，根因却是同一个事实边界没被表达。

选：以 transport 的“命令记录写入成功”回调作为共享 dispatch 事实。回调之前的失败保持 not_started；回调之后丢失终局保持 ambiguous。对 `submit_publish` 再加不可逆写保护：除非 Native 明确返回 not_started，记录已写入后丢终局就保守投影 `submitDispatched=true`。这会把“引擎收到命令但尚未来得及点击就崩溃”的一小部分情况也归入禁止重投，代价是可能需要人工确认；相比双发不可逆内容，这是正确的失败方向。

同批收紧三处转换边界：① search 的 page-card 观测不再自动等于成功动作；②动作 / 发布回执优先保留 Native 具体原因，而不是在跨层时改写成无信息的 generic ambiguity；③ submit 与三条发布身份抓取命令必须返回 typed publish receipt，generic action receipt 缺少 `submitDispatched` / identity / URL，不能由 Rust 机械补字段后当作成功。提交成功信号也只在结果 / toast / message 等提示作用域内，按 DOM 节点与可见文本建立点击前基线；只有新节点或同一节点发生终态成功变化才确认，陈旧 toast、全页正文与进行态「发布中」均不能证明本次提交。另把 `notification_back_home` 的目标与后置都从包含 `/explore` 收紧为精确 feed surface，避免详情页被当成回首页。

D6 当时把 `src/native-page-engine/browse-session.ts` 交给并行的 session-guards change；该 change 已于 2026-08-01 归档，当前无活跃单写者。本轮触碰的是 H.5 新坐实的共享诚实性边界，不重开其周期探针 / 装配范围，也不触碰 Cloud automation 三进程拆分。

### D12. E7 把立即发布身份、定时内部句柄、到期公开身份拆成三种证据

现役 `publish_capture_post_id` 从全页取第一条笔记链，拿不到再从 creator 地址任意 `id` 参数兜底；这不是抓本稿，而是在抓“此刻最先看见的某个 id”。定时 capture / reconcile 又共用同一条“含定时文案即成功”分支：旧日期同标题稿、UI `data-id` 可以冒充内部句柄，仍在待发布的行反而可被到期对账报成公开发布。这三种对象不能再共用一条宽松选择器。

选：立即发布在 submit 点击前为成功提示节点建立基线，只从点击后新增 / 变化的成功结果作用域提取唯一笔记身份；Native session 以 `recordId` 持有该证据，下一条 `capture_postId` 只消费它，不再重新全页猜。页面 marker / sessionStorage 被否决，因为那是执行端自造证据且会跨稿陈旧。抓不到身份不会否定已经确认的提交，只让 Cloud 保持 `submitted_unconfirmed`。

定时内部句柄仍属于“待发布记录”，按平台内部 id 优先，否则冻结标题 + Asia/Shanghai 完整日期分钟 + 定时态合取后唯一匹配；泛 `data-id` 不是平台证据。到期 reconciliation 先判仍在定时并回 pending，再判已发布唯一行；只有公开 post id 与同 id、含非空 `xsec_token` 的 HTTPS 小红书详情 URL 同时存在才确认。该收紧会增加诚实的 pending / submitted-unconfirmed，但不会导致自动重投或丢稿，也不需要扩 Cloud 协议。

### D13. E2 在真机结构未标定前 fail-closed，不在桩上发明成功判据

`topic` 已有迁移前实机校准过的结构信号，并由现役 Rust 特化按真实话题 token、隐藏后缀剔除与精确相等确认；`mention` / `location` / `collection` 没有同等级证据。退役实现对后三支也只使用通用锚点与页面子串，照搬或在 jsdom 里现编一个 token 类名，只会把一个自证循环换成另一个自证循环。

选：保留三支的候选定位与一次点击，但在独立平台接受信号完成真机标定前移除所有 confirmed 出口。编辑器 / 入口 / 候选未命中或点击未派发，仍按零派发事实回具体 `not_started`；候选点击已经派发但结果无法独立确认，固定回 `ambiguous / publish_candidate_unconfirmed`。Cloud 将该原子视为 best-effort，故稿件仍可继续提交；代价是候选即使真实绑定也会得到悲观回执。这一代价优于把裸 `@`、候选自身 selected 外观或入口回显报成平台实体已绑定。

backlog 123.34 因此从“阻断诚实性收口”改为“恢复 positive confirmation 的真机标定”。标定完成后只能以真实页面结构信号恢复成功出口，并补相应 failure-first 夹具；不得把本次 fail-closed 解释为三支功能已真机恢复。

### D14. 未读物理波次与 Cloud 投递状态分离，复用现役周期探针而不恢复第二套时钟

选：`NativeBrowseSession` 只在小红书的现役 `page_probe` 结果中消费 `notificationUnread`。`clear -> unread` 才推进会话内单调的物理波次；`unread -> unread` 的数字变化不推进，`unreadable` / 缺字段保持 sticky，不把未知当清零。账号切换撤销旧账号的投递资格并为新账号重新建立状态，但波次序号在同一 Native 会话内保持单调。

物理波次与 Cloud 投递分开记账：同一波次对当前 `client.getSessionId()` 最多发送一次；Cloud 重连后允许用**同一波次序号**向新会话补发一次，发送失败不记已投递、下一次探针重试。这样避免每个探针重复触发，也不谎称传输已经 exactly-once。缺 accountId、会话已 blocked / closed、观测暂停或停止中的晚到探针既不发送也不消费波次。

验证码 / 登录阻断帧不得吞掉未读：阻断存在时先保持波次未消费；恢复帧先发配对的 `risk.captcha_cleared`，再发送 `notification.detected`，避免 Cloud Gatekeeper 仍处于 hard pause 时直接丢掉信号。实现复用 session-guards 已落地的 lifecycle-managed 定时器，不实例化退役 `CdpNotificationMonitor`，因此没有两个时钟竞争 sticky 状态或重复发信号。

未解决边界也必须保留：`EdgeClient.send()` 没有 Cloud 应用层 ACK，无法证明 exactly-once；Cloud Gatekeeper 在 `selfCaptureInFlight` 等本地准入状态下仍可能无 ACK 地拒绝信号。当前实现通过发送失败重试与新 Cloud session 的同波次补发降低永久丢失，但不能把这些机制写成平台已处理或云端已接受。

## Risks / Trade-offs

- **真机结论与规格假设不符**（开帖并未落错误页）→ 规格只要求正面详情证据，这一半在任何情况下都成立；执行方式的选择留在实装任务里按真机结论决定，不需要改规格。
- **结构化定位随平台改版失效** → 失败关闭：控件解析不到即诚实 `control_not_found`，不回落到「文本含该词的第一个元素」。代价是平台一改版动作会先停摆再被发现，这优于把没生效的动作报成成功。
- **评论改为合成完整文本后，长文本可能触发编辑器行为变化** → 提交前回读必须覆盖合成后的完整文本，回读不含串码即在提交前诚实失败；比现在「悄悄少发一段」可观测。
- **把看图终局搬到回执时把图片证据一起弄丢** → 这是本 change 最容易「修一个红线踩另一个红线」的地方（机械约束 9）：规格显式要求图片证据仍到达云端，实装先定机制（tasks 2.3a）再改判据，并以云端参考图刷新的既有用例作为回归判据。
- **一个 290 行文件承载全部命令面，改动面集中** → 本 change 只出规格；实装阶段建议按命令族分批提交并各自带失败优先的表征测试，避免一次大改盖掉语义冲突。
- **测试仍是 jsdom 桩** → 桩只能证明目标绑定与编排，证明不了真实页面事件行为；凡桩验不了的一律转真机验收项，规格里不写成已验证。
- **定时控件或提交按钮落在闭合 shadow 内** → 本轮 E4 只恢复状态与模式绑定；当前 3.2 已登记的闭合 shadow 定位偏离仍然存在。命中不了会在提交前诚实失败，不会退化为立即发布；是否补 CDP DOM 穿透仍由真机簇 125 的结构复核决定。
- **未标定候选可能真实生效但统一回 ambiguous** → 这是 E2 的有意失败方向：三支属于 Cloud best-effort，不阻断稿件发布，但会失去正向元数据确认。恢复 confirmed 必须先完成 backlog 123.34 的真机结构标定，不能用桩造证据换取绿回执。
- **未读信号没有 Cloud 应用层 ACK** → Edge 只能证明发送尝试与按 Cloud session 去重，不能证明 Gatekeeper 已接纳；新连接的同波次补发会在“旧连接已接纳但 ACK 不可见”时产生至多一次跨会话重复。Cloud 的 `selfCaptureInFlight` 无 ACK 拒绝仍是后续准入 / receipt 风险，不在本 Edge-only 收口中改三进程代码。

## Rollback

本 change 不涉及数据、协议或部署迁移。规格回滚是回退本 change 的控制仓提交；实装回滚是对应 Edge 提交的 revert。已安装客户端若未来交付，还需要按桌面发布流程重建并替换产物；本次未打包或安装。

## Open Questions

- 小红书开帖在 Native 路径上是否真的落到错误页，需真机判定（开帖后地址是否带访问令牌、返回详情正文是否为空）。若单页应用拦截了程序化点击、导航仍走内部路由，则该条降级为纯指纹问题，而证据要求那一半不变。
- 看图命令导致深读永久挂起、直到会话看门狗杀场，是从代码路径推出的，未在真机日志里确认过实例；云端等待表超时兜底是否需要，取决于该实例是否复现。
- 通知去重键折叠与行选择器退化每天实际漏掉多少条通知，没有线上数据支撑，只有代码与旧注释的对照。
- 未读入口的角标结构判据出自 2026-06-23 真机校准（窄布局曾实测漏报 10 条未读），分类栏与行结构出自 2026-06-24 dump，均距今一月余；本 change 只把它们当**待复核的起点**，真机项 5.8 / 5.5 未跑完前不得当已验证事实。
- 未读信号发送方已由 Edge `a2d0c74` 在源码中通电，但已安装客户端与真实账号仍未验证；另外 `EdgeClient.send()` 无应用层 ACK、Cloud `selfCaptureInFlight` 可能无 ACK 拒绝的准入风险仍待后续 Cloud/receipt 设计裁定，不能把源码发送等同于巡视已被 Cloud 或平台接受。
