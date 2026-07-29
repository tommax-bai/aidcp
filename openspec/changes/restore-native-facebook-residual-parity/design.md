## Context

### 迁移背景

2026-07 把浏览器页面智能从 TypeScript 迁进 Rust「Native Page Engine」，动机是防反编译。实质形态是：页面规则仍是 JS，构建期按清单拼接、异或混淆后编进二进制，运行时注入页面执行。小红书 2026-07-22 切生产（edge `317cd47`），Facebook 与微信 2026-07-23 跟进（edge `4f04e9c`），此后 07-25~07-28 有二十余个修复提交。明确决定：不双跑、不比对、不回退，回滚手段只有装包回滚。迁移主 change 是 `native-page-engine-production-cutover`（42/51，仍活跃）。

Facebook 侧已单独修过若干轮（含 `restore-native-facebook-feed-like-parity`、`restore-native-facebook-group-join-parity`、`restore-native-facebook-reels-interaction-parity`、`restore-native-facebook-localized-action-parity`、`preserve-native-facebook-capability-boundaries`），共同修法是「先拿退役执行器当行为判据（behavior oracle），再补 Native 侧的定位 / 提交 / 后验」。本 change 继续这一路径，收拾六处**已在代码里坐实**的残留。

### 六处残留的机械根因（逐条带证据）

1. **热度恒为 0**。计数取自 `reactionButton()`，它的判据是「可见按钮里第一个 accessible label 以 赞 / 讚 / like / me gusta / thích 开头」（`native/page-engine/src/facebook-router/08-reaction-semantics.js:28-31`），**没有任何「须含数字」的要求**；数字长在带计数的汇总控件上（中文形如「赞：N位用户」，其 label 因全角冒号既不匹配 `\b` 也不匹配 `\s|$`，被这条锚点排除）。**三处**取数点都从这个控件文本抽数、覆盖四类上报载荷：`cardOf`（`20-feed.js:12`，feed 卡与 Reels 卡同走它——`feedCards()` 在 Reels 面把 `activeReel()` 的根喂给它）、首帖卡（`:117`）、详情（控件解析 `:228`、取数 `:243`）。**`30-reels.js` 不产 `likeCount`**：它的 `:22` / `:94` 是动作见证包里的 `reactionText` 字符串，且该字段在云端**零消费者**（`grep -rn reactionText aidcp-cloud/src` 只命中协议注释 `protocol.ts:1742`），所以它既不是本 change 的读数点、也不该被当计数消费。**「恒为 0」只在已实测的中文版式上成立**——英文形态（如 `Like: 1.2K`）在 `\b` 下反而可能命中该锚点，届时读数是随机偏差而非恒零；本判断只用作动机，判据按两条合取写（见 Risks 与 tasks 9.4）。退役实现的判据相反且明确：`/^(赞|讚|Like|Me gusta|Thích)/i.test(lab) && /\d/.test(lab+' '+bt)`（`aidcp-edge/src/facebook/feed-reader.ts:203`）。有意思的是同一分片里已经写了「是否含数字」的语义判断用于点赞状态识别（`08-reaction-semantics.js:12,16,17`、`30-reels.js:9`），只是选控件那一步没用上。
   **关键约束**：`reactionButton()` **同时**是点赞执行器要按的那个控件的定位器（`90-dispatch.js:110`、`30-reels.js:116`）。改它的语义会直接动到刚落地的 Feed / Reels 点赞路径。
   **下游**：卡片热度进内容评估提示词（`aidcp-cloud/src/agents/content-evaluator.ts:199`）；详情热度进评论准入硬门槛「赞 > 300」（`aidcp-cloud/src/agents/comment-appraiser.ts:167-168`，常量 `COMMENT_MIN_LIKES = 300`）与精选准入比值闸（`src/publish-agent/curated-gate.ts:119-122`）。载荷侧 `likeCount` 在卡片与详情上都是**必填数字**（`aidcp-edge/src/comm/protocol.ts:832`、`:1622`），所以「缺失」今天在线上不可表达；同一份协议里评论级 `likeCount` 已经是可选并写明「抓不到为 undefined，不编造」（`:1715`），本 change 沿用这个已有先例。

2. **评论入口永不被点**。执行路径在拿不到编辑框时做的是最多 6 轮拟人滚轮 + 重探，滚完仍失败即回「找不到编辑框」（`native/page-engine/src/facebook/comment.rs:82-116`）。而注入脚本里的入口探针本身就是为通用目标写的、明确带非首帖分支（`facebook-router/50-comment.js:7-11`），Rust 侧唯一调用点却只在「打开群内首帖」那段编排里（`facebook/runtime.rs:361`），那里已经是「探针拿坐标 → 可信点击 → 重探编辑框」的完整形态、且用 `action_probed` 标志保证最多点一次。折叠态评论框需要一次点击才展开，而执行路径只会等和滚。

3. **迁移开帖空转 + 悬挂闩**。云端发的是 `{action:'open_note', params:{noteId, purpose:'navigate', thinkMs}}`（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:3057-3062`），不带 `url`。Native 的导航分支条件是 `NoteOpen(params) if params.url.is_some()`（`facebook/feed.rs:25`），不满足即落到 `evaluate_facebook_router`（`:62`）；注入脚本的 `note_open` 分支在 `p.surface!=='feed'` 时直接 `return done(currentDetail())`（`90-dispatch.js:75-82`），把当前页当详情读一遍就返回。用途标记在 Native 侧只有一处**写入**（`facebook/runtime.rs:196`）与一处字段声明（`command.rs:199`），**零读取点**。结果：返回的是详情输出而非动作完成回执，云端 `pendingMigration` 闩永远等不到它该等的那条回执（清理与消费的**准确**现状见下两段，**不是**「毫无清理」）。
   **闩的清理现状（已逐行核对，不是「毫无清理」）**：超时清理由 `armMandatoryCommentOutcomeTimer` 提供，但它**只对免审强制评论武装**——无审批 trace 即直接返回（`role-dispatcher.ts:1550-1551`），普通已批准交付在会话存活期内**没有**超时清理；会话重启 / 结束**有**清理（`:2264` / `:2339` / `:2400` → `settlePendingMandatoryCommentAsUnknown` `:1574-1581`）；抢占也清（`:3501-3505`）；评论支线硬超时**不**清（`expireCommentSubline` `:1311-1326`，只清 `commentInflight`）。
   **消费点的相关性现状**：进入条件只看「有闩 + 动作是 open_note」（`:3557`），但「落地」判据已经要求 `payload.noteId === mig.noteId` 且观测面为 detail（`:3567`）。**所以无关回执不会把已批准评论发到未经证实的页面上**（该红线今天已被守住）；真实危害是：无关回执把闩消费掉、走 else 分支按一条不相干的回执给本次迁移归因失败（`:3600-3618` 一带）。本 change 只补「闩的普通交付超时清理」与「消费的相关性准入」两处，不重复实现已存在的落地判据。
   **可达性已坐实**：FB 注册表声明 `read_content:'feed'` / `comment:'detail'`（`aidcp-cloud/src/platform/registry.ts:256`），版本偏斜闸只要求边缘声明 `inline_targeting`，而当前 Edge 构建正是声明它的（`aidcp-edge/src/facebook/driver.ts:46`）。所以这条路径在源码层面**是可达的**、不是结构不可达。
   **成本极低的修法已在手边**：Facebook 的卡片 `noteId` 本身就是绝对 permalink（`20-feed.js:4` 的 `noteId:href`，`href` 来自 `cleanPermalink()`，`00-shared.js:91-103` 返回 `clean.href`），所以导航所需信息其实已经在指令里，不需要新协议字段。

4. **非首页面到底被标成「找不到目标」**。滚动循环的前置守卫是 `if grew || !near_bottom || after.surface != "home" { continue; }`（`facebook/feed.rs:203`），因此到底确认在 `search` / `group` 上不可达；**而且它有两道锁不是一道**——确认本身的有效性判据也写着 `initial.surface != "home" || current.surface != "home"` 即判无效（`classify_facebook_bottom_confirmation` `:425-426`），无效即回 `None`（`:383-385`）。所以**只放开 `:203` 的守卫是空动作**，两处必须同改（见 Decision 6 与 tasks 4.1 / 4.1b）；耗尽后的原因分类是 `saw_any_card && surface == "home"` 才回 `feed_continuation_unconfirmed`、否则一律 `no_target`（`:475-485`）。而同文件的活动列表面判据接受 `home|search|group`（`:339`），两处不对称。云端对两者的处理完全不同：`feed_continuation_unconfirmed` → 继续普通 feed 滚动（`role-dispatcher.ts:3622-3632`，**但该分支另有 `sourcePageType === 'feed'` 前置条件**）；`feed_exhausted` → 授权 Reels 兜底握手（`:3635-3642`，**无任何列表面限定**，`authorizeFacebookReelsFallback` 自身也只校验平台 / 会话 / 幂等态，`:1721-1722`）；`no_target` 在 Reels 兜底 pending 态下 → 重发握手（`:3519-3520`、`recoverFacebookReelsFallback` 在 `:1740`）。
   **由此得出一条硬约束**：`feed_exhausted` 今天只从到底确认的显式终止态产出（`:381`），而到底确认被 `:203` 守卫与 `:425-426` 有效性判据双锁在首页面，所以它**今天不可能来自小组页 / 搜索页**。一旦按 Decision 6 让守卫放开，`feed_exhausted` 立刻可从这两个面产出，而云端那条无限定的 Reels 授权会把账号从定向面上带走；同时非首页面的 `feed_continuation_unconfirmed` 在**搜索面**上必定落不到任何分支——续滚分支要求 `sourcePageType === 'feed'`（`:3622-3629`），而搜索面上它是 `'search'`；既不恢复也不报错，退化成静默空转等看门狗。**小组面则连表达都没有**：`sourcePageType` 的值域只有 `'feed' | 'search'`（`src/agents/session-context.ts:17`、`:76`、`:80`），**没有 `group`**，所以云端唯一能判别小组面的途径就是 Decision 6 要边缘带上的那个回执观测面——这也决定了云端判据必须取观测面、而不是 `sourcePageType`。因此云端两处改动（Reels 授权加面别限定 + 非首页面的有界恢复）与边缘守卫放开**必须同批落地**，边缘先落地即为回归。滚动失败回执今天的 `observation` 恒为 `None`（`facebook_scroll_failure`，`facebook/shared.rs:822-840`），而动作完成回执的 `observation` 在协议里已是可选自由结构（`aidcp-edge/src/comm/protocol.ts:1744`）、`ActionEvidence` 已有 `surface` 字段（`native/page-engine/src/model.rs:285-287`），所以带上列表面不需要新协议字段。

5. **发布台账超前声明**。注入脚本对 `publish_set_cover` / `publish_add_with_candidate` / `publish_set_option` / `publish_set_schedule` 回 `kind_not_implemented`（`90-dispatch.js:184`），对 `publish_capture_scheduled` / `publish_reconcile_scheduled` 同样（`:193-195`）——共 6 个。能力台账却给**这六条全部**声明了行为判据「retired Publish executor」、目标见证、提交原语、校验见证与终态语义（`facebook/capability.rs` 的六条 entry 起始行分别是 `:355` / `:381` / `:394` / `:407` / `:446` / `:459`；FB 台账共 12 条发布 entry，另 6 条 `publish_navigate_entry` / `publish_select_mode` / `publish_upload_image` / `publish_fill_field` / `publish_submit` / `publish_capture_post_id` 是真实现的）。**核对退役实现后发现台账这条声明本身就是错的**：退役的 FB 发布执行器 switch 只实现 6 个 kind，其余同样回 `kind_not_implemented`（`aidcp-edge/src/facebook/publish-executor.ts:344-359`）——也就是说这不是迁移回归，而是台账凭空给了一个不存在的 oracle。命令清单的 `platforms` 段只有身份命令、没有逐平台支持矩阵（`native/page-engine/command-manifest.json`）。

6. **文本校验口径不对称**。评论侧三处都用「规范化后逐字相等」：回读（调用点 `facebook/comment.rs:199-205` → 谓词 `facebook_comment_editor_matches` 在 `:405-425`）、提交前重读（`:245-248`）、焦点复检（`:276-282`）；规范化只做空白折叠（`facebook/shared.rs:270-272`）。发布侧用「包含 + 10 字容差」（`facebook/publish.rs:727-735`，`FACEBOOK_PUBLISH_FILL_EXTRA_CHAR_TOLERANCE = 10` 在 `:19`）。退役评论实现用的是包含判定（`aidcp-edge/src/facebook/comment-executor.ts:1207`）并对联系方式分片段比对（`:1216`）。方向是失败关闭、不违反红线，但任何编辑器侧的增量（提及成为独立控件、链接自动化、尾随零宽字符）都会让三道闸之一失败，功能性阻塞。

## Goals / Non-Goals

**Goals：**

- 让 Facebook 的互动热度在能读到数字时读到真数字，在读不到时**可被区分为缺失**，且缺失不再被下游数值门槛当成低质量。
- 让评论执行路径覆盖折叠态目标：先点已识别的评论入口，再取编辑框。
- 让「切到详情面」的开帖指令要么真导航、要么诚实未开始；两端都不留悬挂等待闩。
- 让非首页列表面的「本批看完」按其真实语义上报，云端据所在列表面选恢复动作。
- 让 Facebook 不实现的发布命令在驱动浏览器之前就被拒绝，能力台账不再声明不存在的判据。
- 把各写动作的文本校验谓词收成一处声明，评论恢复退役实现的包含判据。

**Non-Goals：**

- 不改点赞 / 关注 / 加群的定位与提交路径（含 `reactionButton()` 自身语义）。
- 不改云端评论准入的**数值门槛本身**（`赞 > 300` 及其平台放宽规则不动），只改「缺失」的分类。
- 不改协议消息类型集合、不改动作名映射、不动风控状态机与配额记账。
- 不改 Reels 兜底握手的次数与状态机，只给它的触发条件补一个列表面限定。
- 不打安装包、不签名、不部署 dev / ol、不做任何真机写动作（评论 / 发帖 / 加群）验收。
- 不修「标签兼容形 / 分解形不被识别」——经复核那是**两代共有的既有盲区、不是迁移回归**，本 change 只把它作为低优先级既有缺口登记进真机验收清单（tasks 9.10），不写成要求。
- 不把 Facebook 定时发布的两步对账**真做出来**（需要定时贴管理页与到期对账语义，属新平台能力）。本 change 只解决「台账声明与现实不符」；实装另起 change，参照已归档的小红书原生定时发布口径。

**分派简报里明确不由本 change 承接的条目（逐条具名，不静默漏）：**

| 简报条目 | 归宿 |
| --- | --- |
| 小红书开帖是否真落 404（成功判据只看地址里还有笔记 id） | `restore-native-xiaohongshu-action-honesty`（其 Why 已逐行坐实该判据） |
| 看图命令不产动作回执 → 云端深读等待表永久挂起 | 同上（其 Why 已列 `deep-reader.ts` 无超时） |
| 小红书通知去重键折叠 / 行选择器退化的后果规模 | 同上（通知巡视三处退化条目） |
| 小红书提交窗口缺失（今天只表现为接管失败、不撕裂写入） | `restore-native-xiaohongshu-session-guards`（提交窗口与监测体归它） |
| 四处「找不到就退回文档主体」的空根塌陷 | `harden-native-engine-runtime-contracts`（空根 / 解码诊断归它，见下方边界表） |
| 跨环境错投（重连复用旧调试端点、选目标只按平台加端口） | 同上（其 Why 已坐实 `engine.rs:206-207` / `endpoint.rs:214-226`） |
| CI 上实际生效的 Rust 编译器版本、产物不记录编译器版本 | `enforce-native-engine-artifact-gates`（构建期闸与产物事实源归它） |
| 七个簇里「维持原判」的条目只有编号、无正文与原始状态（`F-IPC-*` / `INJ-*` / `TXT-*` / `PACE-*` / `GEST-*` / `TIME-*` / `RETRY-*` / `PLAT-OBS-*` / `BUILD-*` / `DRIFT-*`） | 不属任何单个 change：这是**分派流程的输入缺陷**（正文缺失 ⇒ 无法判定是否与本 change 重叠）。按简报自己的建议，补齐正文后再做一次并案；本 change 不按编号猜测其内容、不据此新增任何要求 |

## Decisions

### 1. 新增独立的「计数见证」解析，绝不改 `reactionButton()`

在反应语义分片里新增一个只用于读数的解析：在目标卡 / 详情根内找 accessible label 或渲染文本**含数字**、且属于反应汇总语义的控件，从它的文本里抽数（沿用既有的 k / m / 万 / 萬 / w 单位解析）。三处取数点改用它（覆盖四类上报载荷）。

- **被否决方案 A：直接给 `reactionButton()` 加「须含数字」条件。** 它同时是点赞执行器的控件定位器（`90-dispatch.js:110`、`30-reels.js:116`），带数字的往往是汇总按钮而不是可点的中性按钮，改了会让点赞去点汇总控件——正是 `facebook-note-scoped-targeting` 里明令禁止的那件事（「反应计数控件 MUST never be treated as a like toggle」）。
- **被否决方案 B：只在读数时对同一个控件多加一层「文本含数字才采信、否则回 0」。** 那只是把恒 0 换成显式 0，真零与缺失仍不可区分，红线不解。

### 2. 缺失用「可选未观测标记」表达，不把必填数字改成可选

卡片与详情载荷各加一个**可选布尔/枚举标记**表示「热度未观测」；`likeCount` 字段形状与必填性不动。标记存在时，该数字**不是**测量值，下游不得据它做数值判断。

- **被否决方案 A：把 `likeCount` 改成可选。** 云端多处把它当 `number` 用（`content-evaluator.ts:33`、`edge-steps.ts:133`、`server.ts:4022`），改必填性会引发一轮跨仓类型返工，且 `handler.ts:502` 现成的 `(p.likes as number) ?? (p.likeCount as number) ?? 0` 会把缺失重新塌回 0，改了也没用。
- **被否决方案 B：用哨兵值（如 `-1`）表示缺失。** 哨兵会被任何忘记判它的比较运算当成「极低热度」，比 0 更危险。
- **先例**：同一份协议的评论级 `likeCount` 已是「抓不到为 undefined，不编造」（`aidcp-edge/src/comm/protocol.ts:1715`），精选准入闸也已经用 `!= null` 守卫（`aidcp-cloud/src/publish-agent/curated-gate.ts:119`）。本决定与该先例同形。
- **代价与串行要求**：这两个可选字段落在两份 `protocol.ts` 上（CLAUDE §2 的热点文件、§7 的单写者），必须与 fleet 串行；additive-optional，老边端省略即等于今天行为。

### 3. 缺失指标的门槛结论改成点名缺失的独立原因，**不**放宽门槛

评论准入的硬门槛在指标缺失时，MUST NOT 回「低于门槛」，MUST 回一条点名缺失指标的独立拒绝原因。行为上仍然跳过（失败关闭不变），但误诊变成可观测事实。

- **被否决方案 A：指标缺失时跳过硬门槛、直接交 LLM 判定。** 那是把「不知道热度」当成「热度够」，等于用一条未经证实的通行证替换掉一条既有安全门；而且它会把 Facebook 的评论量在读数修好之前就先放开一次，风险与本 change 的目标无关。
- **被否决方案 B：留在「低于门槛」原因里不动、只靠日志区分。** 已经证明这条路会让「整平台不评论」看起来像正常的门槛过滤，两周内没有人能从原因码上发现它。

### 4. 评论编辑框获取循环接入「最多一次入口点击」，镜像首帖编排

在既有的有界重探循环里，当探针给出的原因是「找不到编辑框」时，调用已有的入口探针；拿到坐标后走**可信指针点击**，每条命令**最多一次**，随后在剩余轮次内继续重探编辑框。入口探针返回「目标不唯一」或「待审入群闸」时按既有终态直接收敛，绝不点击。

- **被否决方案 A：把探针的两个分支合并、让编辑框探针自己顺手点。** 探测与提交混在一起会让「只读探测」不再是只读，取消点与提交窗口的边界随之模糊；首帖编排已经证明「探针给坐标 + 编排负责点」这个分工可行。
- **被否决方案 B：不设次数上限、每轮都点一次。** 评论入口在部分版式下是切换语义，反复点会把已展开的编辑框收起来，且多次点击是明显的机器味。

### 5. 导航用途开帖：用途标记必须被读取，目标从命令自身派生

Native 侧必须真正读取用途标记：用途为「导航」时，MUST 解析出可导航的规范目标（Facebook 的 `noteId` 本身即 permalink，必要时也接受显式地址），导航并等待就绪后回**动作完成回执**（带独立观测与页面派生的规范帖 id）；解析不出可导航目标、或落地页身份与命令不符时，MUST 回「未开始」，**MUST NOT** 用当前页合成一份详情。

- **被否决方案 A：让云端在迁移指令里补 `url`。** 也可行，但它把「边缘必须读用途标记」这个真缺口留在原地：任何未来的、不带地址的用途指令会以同样方式静默退化。何况 Facebook 的 `noteId` 已经是绝对 permalink，云端补的字段与它同值。
- **被否决方案 B：把不带地址的开帖直接判非法命令。** 会同时打死浏览闭环里按卡片 id 开帖那条正常路径（该路径今天就依赖 `noteId` 而非 `url`）。
- 云端一侧同时补两件事：迁移指令必须携带足以导航的目标（对 Facebook 即规范 permalink），以及迁移等待闩必须有**有界清理**——超时或会话终止时清闩并把「已批准未送达」报给操作员，且闩只接受与之相关联的那条回执，**MUST NOT** 被任意后续同名回执消费。
- **本条的云端 delta 只有两处，不要重复实现已有行为**：①「落地」判据的 noteId + detail-surface 相关性今天已经在（`role-dispatcher.ts:3567`），本 change 不动它；② 缺的是「普通已批准交付的超时清理」（今天只对免审强制评论武装，`:1550-1551`）与「闩的**消费准入**」（今天任何 `open_note` 回执都能进分支并把闩消耗掉，`:3557`）。

### 6. 列表面到底：守卫按「是否列表面」判，原因分类按所在面分类

到底确认的可达性判据从「是不是首页面」改成「是不是**已声明的列表面**」（首页 / 搜索结果 / 小组，与同文件的活动列表面判据一致）。**这一改必须落在两处**：循环前置守卫（`:203`）与确认有效性判据（`:425-426`）；后者还要额外要求确认期间**不许换面**，以免「从小组页滚到别的面」被当成同一批的到底证据。确认采用固定五样本序列：进入确认的初始探针是 `t=0`，后续在 `t=5s / 7.5s / 10s / 12.5s` 探测。五次必须始终同 URL、同非零 document time origin、同 generation、相邻样本 document age 不倒退、同一已声明列表面、非加载、近底（剩余距离不大于**实际滚动容器**的一个视口，无需精确到底）、相对首样本增高不超过 100px（`>100px` 失效）、卡身份有序向量不变；只有第五次后才能产生终态。依据后续 change `confirm-facebook-feed-exhaustion-structurally` 的真机决策，仅当命令列表上下文从首页开始、且本命令已在同一首页 URL 与 document time origin 上观察到真实 canonical 帖子时，第五个结构稳定样本即确认 marker-free `feed_exhausted`，`explicit_end` 缺失或抖动不再阻断；搜索与小组面及其命令中途跳到首页的情形仍需既有完整显式终止证据，不因 marker-free 的近底稳定获得首页 Reels 授权。结构证据失效则立即取消本轮确认。首页空态确认按定义只服务首页，继续沿用独立时序。耗尽后的原因分类：在任一列表面上「见过卡但没翻出新的」MUST 回「翻页未确认」这类非终态原因，**MUST NOT** 回「找不到目标」；「找不到目标」保留给真的一张卡都没有的情形。滚动回执 MUST 在既有可选观测里带上所在列表面。云端的 Reels 兜底授权 MUST 限定在首页面到底，非首页面到底走各自的恢复动作。

固定五样本会把单次到底确认拉到 12.5 秒，而一个滚动命令最多可经历八轮确认失效后重试。旧 45 秒外层预算会把合法路径提前合成为 `CdpTimeout`。因此 Facebook 的 `browse_scroll` / `page_scroll` 使用独立 180 秒预算，并在请求值、Edge 准入和 Rust 引擎天花板三层对齐；既有 Facebook 会话与协议准入已经是 180 秒，不再新增第四个数值。等待按 `t=0` 的绝对偏移调度，探针耗时不得累积漂移；等待必须监听 cancellation 与命令 deadline，避免 5 秒任务让位窗口被新增的长睡眠占满。

- **被否决方案 A：把非首页面的到底也当首页面处理。** 会把搜索结果页 / 小组页的「本批看完」直接授权成 Reels 兜底，账号被从定向面上带走。
- **被否决方案 B：只改原因分类、不动守卫。** 到底确认在非首页面仍不可达，「翻页未确认」与「已到底」这两个状态在那两个面上永远无法区分。
- **云端两处是必配项、不是可选优化**（依据见 Context 第 4 条）：守卫一放开，`feed_exhausted` 就能从小组页 / 搜索页产出，而云端的 Reels 授权无面别限定（`role-dispatcher.ts:3635-3642`、`:1721-1722`）⇒ 账号被从定向面带走；同时搜索面的 `feed_continuation_unconfirmed` 因该分支的 `sourcePageType === 'feed'` 前置条件落不到任何分支 ⇒ 无恢复命令、无失败上报，退化成静默空转等看门狗；小组面在 `sourcePageType` 里无法表达（值域只有 `'feed' | 'search'`），所以云端判据 MUST 取回执观测面而非 `sourcePageType`。**边缘守卫先落地、云端未跟上 = 引入回归**，两侧必须同批。恢复动作的**取舍**（回首页 / 换关键词 / 停）可留真机后再定，但「必须有一个有界且可观测的终局」不可延后。
- **边界（本次复核修正）**：`facebook/feed.rs` 的到底证据链归 `repair-facebook-feed-exhaustion-continuation`（已 ✓ Complete）。本 change 对其有三类具名调整：放开两处面别谓词、把增高抗噪阈值恢复为 100px、把到底确认改为上述固定五样本序列。其余证据谓词、epoch 状态机与首页空态确认逐条不动。集成期按 fleet 串行 rebase，并在 tasks 里显式登记每个调整的理由。

### 7. 不支持的命令在驱动浏览器之前拒绝；台账不许声明不存在的判据

Facebook 不实现的发布命令（封面 / 候选图追加 / 选项 / 定时设置 / 定时对账两步，共 6 个）MUST 在页面求值之前返回既有的「能力不支持」前置拒绝，与现行「不支持的通用命令不碰页面」同口径。能力台账 MUST 把这些命令记成显式「本平台不支持 + 理由」，**MUST NOT** 给它们声明行为判据、目标见证、提交原语或校验见证。

- **被否决方案 A：把两步对账真做出来。** 那是一条新平台能力（需要 Facebook 的定时贴管理页与到期对账语义），属于独立 change 的体量；本 change 只解决「声明与现实不符」。
- **被否决方案 B：只删台账里的判据文字、保留运行期的页内未实现错误。** 云端仍然得把命令发出去、开提交窗口与截止时间才知道不支持，浪费一次浏览器驱动并占掉命令槽位。
- **边界**：`command-manifest.json` 的回执列 / 契约列对账归 `harden-native-engine-runtime-contracts`；本 change 只涉及「逐平台支持与否」这一维，必须与它串行。

### 8. 文本校验谓词逐写动作声明；评论恢复包含判据

每个 Facebook 写动作 MUST 在能力台账里声明它使用的文本接受谓词。评论的三道提交前检查 MUST 共用**同一个**谓词，且该谓词按「规范化后包含命令文本 + 有界额外字数容差」判定（与发布同形，恢复退役实现的包含语义）；命令文本缺失或被截断时仍 MUST 拒绝。若最终仍保留任何跨写动作的不对称，MUST 连理由一起记进台账。

- **被否决方案 A：反过来把发布也改成逐字相等。** 那会让发布在编辑器补零宽字符 / 自动链接化时整体失败，比现状更脆，且与退役实现的判据反向。
- **被否决方案 B：评论改成纯包含、不设容差。** 与退役实现逐位一致，但会接受「上一次失败残留的草稿 + 本次文本」这种拼接态，可能发出比批准文本更多的内容；有界容差是比退役实现更严的一层，成本极低。
- **注**：两代打字方式实际相同（都是逐码位插入，`native/page-engine/src/input.rs`），所以「换行被编辑器整段吞掉」那类最小复现不成立；本条只改校验谓词，不动输入原语。

## Risks / Trade-offs

- **[计数见证在某些版式上仍抽不到数字]** → 结果是显式「未观测」而不是 0，下游据独立原因拒绝且可观测；不会退回静默零。真机核验哪些版式有汇总控件、其 label 形态如何，列为验收项。
- **[某些版式的中性控件文本里恰好带数字]** → 若「须含数字」成为唯一判据，读数会从恒零变成随机偏差。因此判据是「含数字**且**属反应汇总语义」两条合取，且点赞控件定位器不复用；不确定版式一律回未观测。
- **[反向风险：某些版式的反应汇总控件反而被 `reactionButton()` 选中]** → 该锚点是 `/^(赞|讚|like|me gusta|thích)(\b|\s|$)/i`（`08-reaction-semantics.js:30`）。中文汇总标签「赞：N位用户」因全角冒号既不匹配 `\b` 也不匹配 `\s|$` 被排除，但英文形态 `Like: 1.2K` 在 `\b` 下**会**命中，且该函数取的是 DOM 序第一个命中项——若汇总控件先于中性控件出现，点赞执行器就会去按一个非切换控件，正是 `facebook-note-scoped-targeting` 明令禁止的那件事。**这是既有状态、不是本 change 引入**，本 change 也**不**改该锚点；但它把「读数」从这个函数上摘走后，后续单独收紧该锚点就不再有「会打坏读数」的顾虑。作为真机采样项登记（tasks 9.4），采样若证实命中，需另起 change 修点赞定位。
- **[评论入口点击把已展开的编辑框收起]** → 每条命令最多点一次、且只在探针明确回「找不到编辑框」时点；点后仍在既有轮次内重探，失败仍是诚实未开始。
- **[评论校验放宽到包含后误发拼接内容]** → 有界额外字数容差 + 失败路径仍清空编辑器；容差取值须与发布侧一致并写进台账。
- **[两份 `protocol.ts` 的可选字段与 fleet 撞车]** → 该文件是热点单写者（CLAUDE §2 / §7），必须串行；additive-optional，老边端省略即今天行为，回滚只需忽略该字段。
- **[边缘守卫放开与云端恢复不同批 ⇒ 引入回归]** → 到底确认在小组页 / 搜索页可达后，`feed_exhausted` 与 `feed_continuation_unconfirmed` 都会从新的面产出，而云端一边会把账号切走 Reels、一边让非首页面的续滚落不到任何分支。**两侧必须同一批集成**（tasks §4 与 §4B 成对），不接受「边缘先合、云端后补」。
- **[`facebook/feed.rs` 与 `facebook/comment.rs` 与并行 change 重叠]** → 见下节边界，提交保持隔离，集成期按 fleet 串行 rebase。
- **[Native 改动只在重编译引擎 + 重打包客户端后才在运营机生效]** → 本 change 不出包；行为在运营机的生效时点由后续显式授权的发版决定。

## Rollback

- 三仓改动各自是独立提交，回滚即回退提交；无数据库迁移、无协议消息增删。
- 协议侧只增可选字段：回滚后老 / 新两端互操作仍成立（省略即视为已观测）。
- Native 引擎产物回滚随 Edge 提交回滚重建；已发出的安装包不受影响（本 change 不出包）。

## 与其他并行 change 的边界（本 change **不碰**的文件与语义）

| 并行 change | 它拥有的 | 本 change 的边界 |
| --- | --- | --- |
| `restore-native-actuation-humanization-and-locating` | `native/page-engine/src/input.rs` 指针 / 滚轮原语、`facebook/shared.rs` 点击原语、`facebook/feed_like.rs` 对齐滚动、`facebook/reels.rs` 兜底滚动、时间字段消费接线 | **不改**指针 / 滚轮原语与点击原语实现。评论入口点击复用它们提供的可信点击；`facebook/comment.rs:90` 的滚轮调用点由它拥有，本 change 只在同一循环里**新增**入口点击分支，集成期必须串行 rebase |
| `harden-native-engine-runtime-contracts` | `command-manifest.json` 的回执 / 契约 / 效果 / 取消列对账、`facebook/capability.rs` 的提交窗口常量单一事实源、`00-shared.js` / `20-feed.js` / `40-group-join.js` 的空根与解码诊断 | **不改**回执列语义、不改提交窗口常量、不改空根 / 解码诊断。本 change 只在 `capability.rs` 增「逐平台支持与否 + 文本谓词」两维、在 `20-feed.js` 改四处读数取值；同文件必须串行 |
| `enforce-native-engine-artifact-gates` | `manifest.txt` 作为防泄漏事实源、剪枝 / 打包闸、Rust 门禁脚本位置 | **不新增也不删除**任何路由分片文件，`manifest.txt` 内容不动；只改既有分片内部实现 |
| `repair-facebook-feed-exhaustion-continuation`（✓ Complete） | `facebook/feed.rs` 首页面 settle / 显式终止证据 / 「翻页未确认」原因，以及云端 Reels 兜底 epoch | **不改** epoch 状态机与首页空态确认。**会改**两行面别谓词、100px 增高抗噪阈值，以及到底确认的固定五样本计划（`t=0 / 5 / 7.5 / 10 / 12.5s`）；依据后续 `confirm-facebook-feed-exhaustion-structurally`，本命令已见真实 canonical 帖子的 canonical 首页以五次结构稳定确认耗尽，不再硬依赖显式结束标记。其余为原因分类、回执带列表面、云端 Reels 授权加列表面限定 |
| `facebook-first-post-comment-confirmation` | `50-comment.js` 的服务器确认判据（`comment_id` 形态）、自动路径不得带快返开关 | **不改**服务器确认判据与快返开关。本 change 只消费 `50-comment.js` 已有的入口探针（无需改动该分片），并改 `comment.rs` 的**提交前**文本校验谓词——与提交后的服务器确认是两段互不重叠的判据 |
| `restore-native-facebook-feed-like-parity`（✓ Complete） | Feed / Reels 点赞的精确卡、DOM 提交、浮层坐标提交、同卡后验 | **不改** `reactionButton()` 语义与任何点赞路径；读数走独立解析 |
| `native-page-engine-production-cutover`（活跃，42/51） | 迁移主线（含未勾的定位三闸移植 3.2、输入原语 3.3） | 本 change 是它的残留补齐，不认领 3.2 / 3.3 两条任务 |
| `add-managed-automation-runtime` | 统一自动化运行模型（§24 处置映射表） | 本 change 触及 `comment-interaction` 的一条**新增**要求（缺失指标的分类），不动其准入门槛数值与审批语义；如与 §24 的收编条目冲突，以该 change 的 delta 生效时点为界 |

## Open Questions

- 中文以外版式（英文 / 越南语 / 西语）的反应汇总控件 accessible label 与渲染文本的确切形态，需真机采样后才能定「属反应汇总语义」的判据边界；采样前判据须偏保守（宁可回未观测）。
- 非首页列表面「本批看完」在生产上的实际发生频率未知，恢复动作的取舍（回首页 / 换关键词 / 停）留给真机观察后再定，本 change 只保证语义不再被标成红线词。
- 评论包含判据的额外字数容差取值是否应与发布侧同为 10，需一次真机采样（看编辑器实际会补多少不可见字符）后确认。

## 覆盖漏洞收口（参照书合并后追加）

合并同目录 `oracle.md` 时查出四条「参照书里有、tasks 里没有对应任务」的漏洞。四条全部判为**就地补任务**（落点在本 change 影响面内、不需要新能力），无一条外包；其中一条内含一个必须由人先裁定的取舍，另立「待裁定」。**没有交接给其他 change 的条目**——若后续复核发现有，须在此处补一张具名交接表，不得静默漏掉。

| 漏洞 | 处置 | 落点 |
| --- | --- | --- |
| A. Facebook cookie 同意策略与失败分档整条零覆盖（含**作用域自伤**与 present 门缺按钮合取项） | 就地补任务 + 规格增量 | tasks §10；`facebook-consent-overlay` 能力增量（新增四条要求） |
| B. 懒加载增高阈值 1px vs 退役实现 100px，且被 4.5 明令锁死 | 就地补任务（开 4.5 的显式例外） | tasks 4.6 + 真机项 9.12；`native-facebook-behavior-parity` 增「抗噪阈值」要求 |
| C. 越南语兼容形 / 分解形盲区会被 1.1 新写的解析原样继承 | 就地补任务（只约束新写的那段，不扩大到既有词表） | tasks 1.7 / 1.8；`native-facebook-behavior-parity` 增「新见证先归一再匹配」要求 |
| D. 「正文进去了但联系方式没进去」这一档独立失败面消失 | 就地补任务（台账记差异 + 用例锁红线） | tasks 2.7；写动作谓词要求下补一条场景 |

### A 的立论修正与已坐实的事实（照抄参照书前必须先看）

外界常见前提「新版只会点接受全部」在当前 HEAD **不成立**：策略枚举、环境变量键名与三个别名、验证码优先、登录门优先、点后复探、有界三次重试全都在（`native/page-engine/src/facebook/shared.rs:426-434` 一带）。按「补一个策略枚举」去做等于重做已有的东西。真正缺的是下面四条，均已逐行坐实：

1. **作用域自伤（新引入，退役实现没有这个失效模式）**：`facebook-router/05-session.js:18` 把按钮采集框到 `first(['[role="dialog"]','[aria-modal="true"]'])||document`，取的是**首个可见对话框且不校验它含 cookie 文案**。退役实现在整个文档上采集、取首个命中（`src/facebook/consent.ts:114-124`）。该行随迁移重构一次性引入（edge `073eadc`），提交信息里没有为收窄作用域给出理由。
2. **present 门缺「至少一个可点接受按钮」这个合取项**：`05-session.js:22` 是 `cookieCopy&&!captcha&&!loginPath`；退役实现的纯判定要求四条同时成立（`consent.ts:67-80`）。**额外后果（本次新查出）**：同一分片的阻断分类里，登录分支以 `!consent.present` 为条件（`05-session.js:46`），所以 present 假成立不只误阻动作，还会把「带 cookie 文案的登录墙」挡在登录门结论之外。
3. **探测失败没有降级**：`shared.rs:419-422` / `:455-458` 把探测错误经 `?` 上抛成引擎错误；退役实现明文当作「无同意条」继续（`consent.ts:188-195`）。
4. **失败分档折叠**：`shared.rs:445-452` 与 `:455-462` 把「策略所需按钮定位不到」和「点三次清不掉」收敛成同一个 `blocked_by_consent`；退役实现前者报 `no_target`、后者报 `blocked_by_consent`（`consent.ts:200-206`、`:223-224`），回执还带 handled / cleared / attempts 三项。

**影响面为什么是「今天就可能出事」**：同意闸是 `ensure_facebook_action_gate` 的统一前置，调用点覆盖评论、首帖开帖与加群、feed 滚动 / 刷新 / 开帖、feed 点赞、Reels、发布五处（共 17 处）。作用域一落错，present 仍成立而两个策略点位都为空 ⇒ 这些动作**全部**收敛到同一条被同意条阻断的失败上。

**已核对、判为非缺口的两处**（避免下一个人重复排查）：① `05-session.js:14` 的 `loginPath` 正则不含 `/checkpoint`，而已合并规格把 `/checkpoint` 列进登录 / 验证路径——但阻断分类里 `/checkpoint` 走的是更前面的一档（`:48`，判为未归类阻断），且阻断分类在同意闸里先于同意探测执行（`shared.rs:405-417`），因此这不是活的漏洞，只是判据分散；② 三次有界重试、点后复探、拟人点击都在，与退役实现同形。

**方向相反的一处疑点、未坐实**：`05-session.js:11` 的正文取样是 `text(document.body,5000)`（截断 5000 字符），退役实现读完整 innerText（`consent.ts:95`）。长页面上同意文案若落在截断之外，判定会偏向「无同意条」并放行——这与作用域自伤方向相反（漏判而非误阻）。**未经真机确认，不写成既成事实**，登记为 tasks 9.11 的同批采样项。

### B 为什么必须开 4.5 的显式例外

判据 `facebook_feed_height_grew`（`facebook/feed.rs:409-413`）由**同一个函数**支撑两处：循环前置守卫（`:202`）与到底确认有效性判据里的「无增高」（`:430`）。4.5 把「无增高」列进不许改的证据链清单，所以不开例外就等于禁止修阈值。例外的边界写死在 tasks 4.6：只动阈值取值这一个常量，语义与证据链其余条件逐条不动。不修的后果是 4.1 / 4.1b 变成空动作——面别守卫放开了，但任何一次重排都算「还在长」，三个列表面都走不到到底确认。到底确认的五样本时序是 tasks 4.7 的另一条独立例外；首页显式标记从硬门降为辅助观测是后续 tasks 4.9 的再覆盖，两者都不改变本节的高度判据。

### C 的边界（不与 Non-Goals 冲突）

Non-Goals 里「不修标签兼容形 / 分解形不被识别」指的是**既有词表与既有反应控件定位器**的全局盲区，仍按 tasks 9.10 登记为既有缺口。C 只约束 1.1 **新写**的那段计数见证解析：新代码在匹配前先归一，且复用同一批分片里已经存在的那个变换（`20-feed.js:178`），不新写第二份判据、不改既有词表。两者并不冲突：一个是「不扩大修复范围」，一个是「新增的那段不原样继承盲区」。

### D 的红线归属

红线「只有正文进去、联系方式没进去时绝不裸发正文」在新形态下**仍然守住**：正文与联系方式被拼成一串一次打完（`facebook/comment.rs:72-80`），2.4 的包含谓词按整串判定，正文-only 的编辑器值不包含整串 ⇒ 拒绝 + 清场。丢掉的只是**诊断粒度**（旧实现对这一档有独立失败面与独立用例）。因此 D 的处置是台账记差异 + 用例锁红线，而不是把两段追加的形态搬回来。

## 待裁定（实装前必须有人决定，否则任务无法验收）

### 1. 同意条出现多个同文案接受按钮时：取首个，还是保持「不唯一即停手」

- **决定什么**：`05-session.js:25-26` 要求策略所需按钮的命中数**恰好为 1**，大于 1 时只置歧义标志、不给点位，`shared.rs:435-443` 据此放弃点击并收敛为失败；退役实现是**取首个命中即用**（`consent.ts:114-124`）。tasks 10.1–10.6 不改这条，是否放宽须先裁定。
- **走法一（恢复退役的宽容：取首个符合当前策略的按钮）**：多语言并存 / 多容器渲染出两个同文案接受按钮时不再卡死；代价是放宽了本项目「目标不唯一就不动手」的通行模式（本 change 自己的评论入口要求就是「歧义 → 零点击」）。可辩护之处在于两个候选都属于**同一策略类**，点哪个后果相同——但这一点在 Facebook 的真实版式上**未经真机确认**。
- **走法二（保持现状的严格唯一）**：与歧义铁律一致、无误点风险；代价是同文案按钮一旦并存，全部受闸动作被判成被同意条阻断（与 A 的作用域自伤是同一种"全线阻断"后果，只是触发条件更窄）。
- **不裁定会怎样**：10.7 的阻塞标记生效——实装者要么擅自放宽（可能违反歧义铁律），要么保留严格唯一却在验收时无法回答「这是不是又一条全线阻断的引信」。真机项 9.11 会采样「同文案接受按钮是否会并存多个」，可作为裁定输入，但**采样结论不等于裁定**：即使真机上没见过并存，选严格唯一仍意味着接受这条引信继续存在。
- **本轮处置（`aidcp-edge 9176dcb`）**：裁定仍未下，按走法二（保持严格唯一）落地，并**新增用例把现状锁住**——将来无论裁定走哪一支，改动都会撞到一条明写的断言，不会被人默默放宽。

## 实装实测订正（2026-07-28，edge 半边 `aidcp-edge 9176dcb`）

以下六条是**实装实测得出**、与本 change 原有文档不符之处，已同步订正 tasks.md 对应条目；此处汇总，避免下一个人重复排查。

1. **`oracle.md` 覆盖漏洞 A 已 stale**。它写着「Cookie 同意策略整条无任何任务」，但 tasks.md 已有完整的 §10 承接（10.1–10.7）。oracle.md 该段与 ③ 条目的「对应任务」行均已标 stale，只保留作为立论记录。
2. **tasks 1.7 的原验收自相矛盾**：它要求「`git diff` 断言 `08-reaction-semantics.js` 零改动」，而 1.1 明写要在**该文件**新增计数见证——1.1 一落地该文件必然有 diff。订正为「断言该文件的**既有词表与 `reactionButton()` 反应控件查找函数**逐字未动」，这才是 Decision 1 真正想守的不变量（文件级零改动从来不是）。
3. **tasks 4.3 的原措辞在实现上做不到**：`facebook_scroll_failure` 被引擎主体的单测以两参形式调用，给既有函数加面别参数必然要动本轮白名单外的文件。订正为「**新增带面别的变体，旧签名保留为薄壳转调**」，行为与调用点逐位不变。对应 Decision 6 的「滚动回执 MUST 带上所在列表面」这条结论不变，变的只是落地形态。
4. **同意闸失败分档的云端归宿已实测**（服务 tasks 10.4，口径同 4B.4）：`blocked_by_consent` 在 `aidcp-cloud/src` 上 grep **零命中**——它今天在云端**没有任何专属归宿**；而 `no_target` 在评论链路上有具体语义，把同意闸的失败改报 `no_target` 会与那套语义串味。因此按「保留 `blocked_by_consent` + 两档落回执诊断 / 观测字段」落地，**不新增原因码**。
5. **Decision 2 的落点是三个文件、不是两个**：除两份 `protocol.ts` 外，`native/page-engine/src/model.rs` 的卡片载荷与详情载荷两个结构体**对未知字段严格拒绝**，标记不同批加进去就会直接反序列化失败。tasks 1.3 / 1.4 已显式点名它。该条因此整体被协议热点单写者窗口阻塞（10.5 的「点了几次」精确计数同一落点、同一窗口）。
6. **Decision 7 的「页内最后防线」是两类形状、不是一类**：`90-dispatch.js` 原来只对六条里的**四条**走未实现分支，另两条走的是发布回执分支，两类回执形状不同。Rust 侧前置拒绝必须与各自对应的那一类逐位一致，验收按两类分别对账，MUST NOT 假设六条同形（已写进 tasks 5.3）。
