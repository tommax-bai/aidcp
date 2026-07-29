## Why

Facebook 侧在 Native 引擎切换（edge `4f04e9c`）后已连修十余个提交，但还剩六处「读数假 / 动作缺 / 语义标错 / 声明超前」的残留，六处都能在代码里坐实。第一，首页卡片与详情的互动热度取自「标签恰好是 赞 / Like / Thích」的中性动作按钮（`aidcp-edge/native/page-engine/src/facebook-router/08-reaction-semantics.js:28-31`），而数字只长在带计数的汇总控件上——退役实现的判据正相反、要求标签或文本里含数字才采信（`aidcp-edge/src/facebook/feed-reader.ts:203`），于是三处取数点（`20-feed.js:12` 的 `cardOf`——feed 卡与 Reels 卡同走这一处、`:117` 首帖卡、`:243` 详情）在**已实测的中文版式**上热度恒为 0（其余界面语言的汇总控件形态待真机采样，见 tasks 9.4）；云端评论准入的主门槛是「赞 > 300」（`aidcp-cloud/src/agents/comment-appraiser.ts:168`，常量 `COMMENT_MIN_LIKES = 300` 在 `:29`），读到 0 即机械落入「低于门槛」，缺失被当成真值零，正撞「数据缺失不得误判为低质量」这条红线（「整平台被判为不值得评」这一后果规模尚未在生产日志里实证，见 tasks 9.6）。第二，评论执行路径拿不到编辑框时只做最多 6 轮滚动重探、从不点那个已能被识别的折叠态评论入口（`aidcp-edge/native/page-engine/src/facebook/comment.rs:82-116`），而现成探针只被「打开群内首帖」那段编排调用（`facebook/runtime.rs:361`），折叠态目标必然失败。第三，云端在「读用首页、评论用详情」配置下每次都先下发一条只带笔记 id 与用途标记、不带地址的开帖指令（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:3057-3062`），而 Native 的导航分支要求带地址（`facebook/feed.rs:25`）、用途标记全仓只写不读（`command.rs:199`、`facebook/runtime.rs:196`），于是落到注入脚本把当前首页当详情读一遍就返回（`facebook-router/90-dispatch.js:75-81`）——既没导航、也不发动作完成回执。云端的迁移等待闩因此永远等不到它该等的那条回执，而它的清理只覆盖一部分情形：超时清理只对「免审强制评论」这类交付武装（无审批 trace 即直接返回，`role-dispatcher.ts:1550-1551`），普通交付在会话存活期内没有超时清理；会话重启 / 结束有清理（`:2264` / `:2339` / `:2400` → `:1574-1581`），评论支线硬超时不清（`:1311-1326`）。落地判据已带 noteId 相关性（`:3567`），所以无关回执**不会**把已批准评论放到未经证实的页面上；但它仍会消费掉那个闩（`:3557-3559`）并把失败归因到与本次迁移无关的一条回执上。第四，小组页与搜索结果页因一道「非首页面直接进入下一轮」的前置守卫（`facebook/feed.rs:203`）使到底确认不可达，滚到底被上报成红线词「找不到目标」（`facebook/feed.rs:481`），而云端对这两种状态的恢复动作完全不同（`role-dispatcher.ts:3622-3643`）。第五，六个发布类命令（封面 / 候选图追加 / 选项 / 定时设置 / 定时对账两步）在注入脚本里直接回「未实现」（`facebook-router/90-dispatch.js:184`、`:193-195`），能力台账却逐条给它们声明了属主、判据与终态语义（`facebook/capability.rs` 的 `:355` / `:381` / `:394` / `:407` / `:446` / `:459` 六条 entry），云端只能试了才知道。第六，同一引擎内评论要求规范化后逐字相等且提交前连查三次（`facebook/comment.rs:199-205`、`:245-248`、`:276-282`），发布只要求包含加 10 字容差（`facebook/publish.rs:727-735`），退役实现用的是包含判定（`aidcp-edge/src/facebook/comment-executor.ts:1207`、`:1216`），两套口径无成文说明。

## What Changes

- 把 Facebook 互动热度的取数改成「只认真的带数字的见证」：计数只从含数字的反应汇总控件文本里抽，绝不从点赞执行器要按的那个中性控件里抽；点赞执行用的控件定位口径逐位不动。
- 让「没读到数字」与「真的零」在上报里可区分：卡片与详情载荷带一个可选的「未观测」标记，云端的数值门槛不得把未观测算成低于门槛，改回一条点名缺失指标的独立拒绝原因。
- 让评论执行路径在拿不到编辑框时先点一次已识别出的评论入口（每条命令最多一次、走可信指针提交），再在既有轮次内重探编辑框；探针本身与首帖编排的调用点不变。
- 让「切到详情面」的开帖指令要么真的导航到目标帖、要么诚实回「未开始」：用途标记必须被真正读取，绝不用当前页冒充目标页；云端一侧的迁移等待闩必须对**每一次**已批准交付都有有界清理（今天只对免审强制评论武装），且不得被无关回执消费（「落地」判据的 noteId 相关性今天已在，不重复实现）。
- 让小组页与搜索结果页也能走到底确认（**两处面别谓词必须同改**：循环前置守卫与到底确认自身的有效性判据，只改前者是空动作），并把「本批看完没翻出新的」按所在列表面如实分类，不再退化成红线词「找不到目标」；滚动回执带上所在列表面。到底确认改为固定五样本序列：进入确认时立即采样，随后在第 5、7.5、10、12.5 秒采样；只有五次证据均有效且均出现显式结束标记，才可在第五次后确认耗尽，前四次不得提前成功。Facebook 滚动命令的请求值、准入上限与引擎天花板同步为 180 秒，确保合法的多轮确认路径不被旧 45 秒外层预算截断；新增等待继续服从任务取消与命令截止时间。云端同批配上两件事：Reels 兜底授权加列表面限定（否则非首页面到底会把账号从定向面带走），以及非首页列表面每一个终态原因都有有界且可观测的归宿（否则退化成无命令无终态的静默空转）。
- 把 Facebook 不实现的发布类命令改成在驱动浏览器之前就诚实拒绝，并把能力台账里对这些命令的属主与判据声明改成显式的「本平台不支持」。
- 把同一引擎内各写动作的文本校验口径收成一条一条声明清楚的谓词：评论的三道提交前检查共用同一谓词、按包含加有界字数容差判定（恢复退役实现的判据），发布保持现状，任何残留的不对称必须连理由一起记进台账。

## Capabilities

### New Capabilities

<!-- No new capabilities. -->

### Modified Capabilities

- `native-facebook-behavior-parity`: 补齐 Facebook 残留的读数见证、评论入口执行、列表面到底语义、不支持命令的前置拒绝，以及写动作文本校验谓词的成文口径。
- `facebook-feed-browse`: 把「导航用途开帖不上报决策笔记」从「不许上报详情」扩到「必须真的导航、否则诚实未开始」。
- `platform-browse-surface`: 给两步评论迁移补齐「指令须自带足以导航的目标」与「等待闩有界清理、不可被无关回执消费」。
- `comment-interaction`: 明确缺失的热度指标不是「低于门槛」的判决。
- `facebook-consent-overlay`（参照书合并后追加）：把同意条接受按钮的采集作用域改由同意语义自身界定（不再是「首个可见对话框」），补回「无可点接受按钮即不成立同意条」这一合取项，探测失败降级为「无同意条」，并把失败分档与回执可观测性写成要求。

## Impact

- `aidcp-edge/native/page-engine/src/facebook-router/08-reaction-semantics.js`（新增计数见证解析，反应控件定位不动）
- `aidcp-edge/native/page-engine/src/facebook-router/20-feed.js`（三处取数点改用计数见证，覆盖 feed / Reels / 首帖 / 详情四类载荷；`30-reels.js` 无计数、其 `reactionText` 观测串不动）
- `aidcp-edge/native/page-engine/src/facebook-router/90-dispatch.js`（导航用途开帖分支、不支持发布命令的前置拒绝）
- `aidcp-edge/native/page-engine/src/facebook/comment.rs`（编辑框获取循环接入入口点击；三道文本校验共用谓词）
- `aidcp-edge/native/page-engine/src/facebook/feed.rs`（列表面到底确认可达性——守卫 `:203` **与**有效性判据 `:425-426` 两处面别谓词、原因分类 `:475-485`；滚动回执带列表面在 `shared.rs:822-840`）
- `aidcp-edge/native/page-engine/src/facebook/capability.rs`（不支持命令的显式声明与谓词记账）
- `aidcp-edge/native/page-engine/src/command.rs`、`src/facebook/runtime.rs`（用途标记被真正读取）
- `aidcp-edge/src/comm/protocol.ts` 与 `aidcp-cloud/src/comm/protocol.ts`（卡片 / 详情载荷各新增一个**可选**「热度未观测」标记，两份逐字一致；老边端省略即等于今天）
- `aidcp-cloud/src/orchestrator/role-dispatcher.ts`（迁移指令携带可导航目标、迁移闩有界清理与相关性消费、Reels 兜底授权加列表面限定、非首页列表面「本批看完」的有界恢复——这两条是边缘让到底确认在小组页 / 搜索页可达之后的**必配项**，不是可选优化）
- `aidcp-cloud/src/agents/comment-appraiser.ts`（未观测指标的独立拒绝原因）
- `aidcp-edge/native/page-engine/src/facebook-router/05-session.js`（同意条采集作用域与存在性判定的合取项——参照书合并后追加）
- `aidcp-edge/native/page-engine/src/facebook/shared.rs`（同意闸的探测失败降级与失败分档；**只调用不改**点击原语，该原语归 `restore-native-actuation-humanization-and-locating`）
- `aidcp-edge/test/native-page-engine/`、`aidcp-edge/native/page-engine/tests/`、`aidcp-cloud/test/`（回归门禁）
- 本 change **不含**：协议消息类型的新增或删除、数据库迁移、Console 改动、Edge 安装包打包与签名、dev / ol 部署、任何真机写动作验收（评论 / 发帖 / 加群一律不在本 change 内执行）。
