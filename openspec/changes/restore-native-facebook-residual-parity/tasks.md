> 实装前先读同目录 `oracle.md`：本 change 多数条目在退役 TypeScript 实现里有可直接对照的正确写法与真机经验。

## 1. aidcp-edge — Facebook 互动热度取数

- [x] 1.1 在 `native/page-engine/src/facebook-router/08-reaction-semantics.js` 新增一个**只用于读数**的反应计数见证解析：在给定根内选出「accessible label 或渲染文本含数字」**且**属反应汇总语义的可见控件，返回其文本；判据是两条**合取**（只判含数字会把带数字的中性控件误采），不确定一律回空 = 未观测。验收：`reactionButton()`（当前 `:28-31`）的正则与返回值逐字不变（用 `git diff` 断言该函数零改动），且 1.5 的语料上其选中结果不变（参照 src/facebook/feed-reader.ts:203-206；旧判据是「前缀 AND 含数字」且没数字就跳过继续找，取值文案优先、空退标签 — 见 oracle.md ①；新写的标签匹配须去变音符归一，见 oracle.md 覆盖漏洞 C） <!-- aidcp-edge 9176dcb 新增只读见证，判据是「含数字 AND 反应汇总语义」两条合取、不确定回空；reactionButton() 的正则与返回值逐字未动 -->
- [x] 1.2 把**三处**计数取数点改用 1.1 的见证（已逐行核对，覆盖四类上报载荷）：`20-feed.js` 的 `cardOf`（控件 `:7`、取数 `:12`；feed 卡与 Reels 卡**同走这一处**，因 `feedCards()` 在 Reels 面把 `activeReel()` 的根喂给 `cardOf`）、首帖卡（`:117`）、详情（控件 `:228`、取数 `:243`）。**`30-reels.js` 无 `likeCount`**——它的 `:22` / `:94` 是动作见证包里的 `reactionText` 字符串（`grep -rn reactionText aidcp-cloud/src` 只命中协议注释、**零云端消费者**）；本 change **不改**这两处取值，只在台账/注释里注明它是观测串、MUST NOT 被当计数消费。验收：改后 `grep -n likeCount native/page-engine/src/facebook-router/*.js` 三处全部指向 1.1 的见证，`reactionButton` 在读数路径零命中（仅剩 `90-dispatch.js:110` / `30-reels.js:116` 两个点赞执行点与 `30-reels.js:22`/`:94` 的观测串）（参照 src/facebook/feed-reader.ts:519；另注数字所在的汇总控件常在 `[role=toolbar]` 内、被 10-feed-like.js:3-6 排除，扫卡侧从不查 toolbar — 见 oracle.md ①） <!-- aidcp-edge 9176dcb feed/Reels 卡、首帖卡、详情三处取数点全改走 1.1 的见证；30-reels.js 的两处观测串按台账口径未动 -->
- [ ] 1.3 在两份 `protocol.ts`（`aidcp-edge/src/comm/protocol.ts` 卡片 `:1618-1626` / 详情 `:828-836`，与 `aidcp-cloud/src/comm/protocol.ts`，两份逐字一致）为卡片载荷与详情载荷各新增一个**可选**「反应计数未观测」标记，并写明「省略 = 已观测 = 老边端零回归」；MUST NOT 改 `likeCount` 的必填性，MUST NOT 新增或删除任何消息类型。**热点单写者文件（CLAUDE §2 / §7），集成期必须与 fleet 串行。** 验收：`AC-PROTO-*` 全过（两份不漂移）+ 断言 `likeCount` 仍是必填 `number`。**（实装实测订正）第三个文件必须同批改**：`native/page-engine/src/model.rs` 的卡片载荷与详情载荷两个结构体**对未知字段严格拒绝**，只加两份 `protocol.ts` 而不加它，标记一进载荷就会直接反序列化失败——所以本条的改动文件是**三个**，不是两个
    - **阻塞**：三个文件（两份 `protocol.ts` + `model.rs`）都在本轮 edge 白名单外，且协议是热点单写者（CLAUDE §2 / §7），必须与 fleet 串行；解锁条件＝拿到协议文件的单写窗口后与 1.4 同批落地。主症状（热度恒 0）已由 1.1 / 1.2 修掉，本条只影响「未观测 vs 真零」的可区分性
- [ ] 1.4 让 Native 引擎在无法解析计数见证时置该标记；已观测为 0 时不置标记。**机械要点**：共享的 `count()`（`00-shared.js:23-29`）在无匹配时 `return 0`，把「没数字」直接塌成 0——所以「未观测」判定 MUST 在**进 `count()` 之前**由见证解析返回空来表达，MUST NOT 依赖 `count()` 的返回值区分。另注：`count()` 只认 `k|m|万|萬|w`，无越南语等其他量级词；采样若发现其他单位，按 9.4 结论补进单位表（补不了的一律回未观测，绝不回 0）。验收：见 1.5 的三档语料断言（未观测置标记 / 真零不置标记 / 有数字不置标记）（参照 src/facebook/feed-reader.ts:148 的 parseFacebookCount，与 00-shared.js:23-29 覆盖已对齐、非缺口 — 见 oracle.md ①）。**（实装实测订正）落点同 1.3**：标记要落进载荷，`model.rs` 的两个结构体必须与两份 `protocol.ts` 同批改
    - **部分完成** <!-- aidcp-edge 9176dcb 见证侧已可表达未观测 -->：见证解析已经能表达「未观测」——无匹配时返回**空串**而不是进 `count()`，符合本条「MUST 在进 `count()` 之前表达」的机械要求；**差的是把它落成载荷上的标记**，那要改 1.3 点名的三个白名单外文件（两份 `protocol.ts` + `model.rs`），随 1.3 一并解锁
- [x] 1.5 加路由特征测试：中性控件无数字 → 未观测；汇总控件带 `1.2万` / `1.2K` → 解析为 12000 / 1200；真零 → 已观测 0 且无标记；断言点赞控件定位器的选中结果在同一语料上不变（可 port 旧用例：feed-reader.test.ts『轻量视频动作按钮内含数字 866 + 越南语汇总 toolbar 825』与 cta-labels.test.ts 数字守卫反向用例 — 见 oracle.md ①） <!-- aidcp-edge 9176dcb 新增 facebook-reaction-count.test.ts：中性控件不再盖住汇总计数、单位折算、真零、含数字的非反应控件不采信 -->
- [x] 1.6 运行 `cd ../aidcp-edge && npm run typecheck`，并跑 1.5 的聚焦用例与 Native Rust 用例 <!-- aidcp-edge 9176dcb typecheck 通过；gate:native（fmt + clippy -D warnings + test，工具链 1.97.1）通过 -->
- [x] 1.7 **（覆盖漏洞收口）** 让 1.1 新增的计数见证解析在**匹配之前**做一次去变音符归一：复用同一批分片里**已经存在**的那个变换（`20-feed.js:178` 的 `normalize('NFD')` + 去组合记号），把它提到 `00-shared.js` 的共享工具位供读数路径调用，MUST NOT 改它在首页空态文案处的既有行为。MUST NOT 改 `08-reaction-semantics.js:1-7` 的既有词表与 `reactionButton()`——标签盲区的**全局**修复仍按 Non-Goals 与 9.10 留作既有缺口，本条只保证**新写**的这段不原样继承它。验收：同一越南语标签的预组合形与分解形在新解析上得到同一判定；**（实装实测订正）原验收写的是「`git diff` 断言 `08-reaction-semantics.js` 零改动」，与 1.1「在该文件新增计数见证」直接冲突——1.1 一落地该文件必然有 diff。订正为：断言该文件的既有词表与 `reactionButton()` 反应控件查找函数逐字未动**（参照 src/facebook/cta-labels.ts:19-28 与 :96-98 —— 旧实现靠手工并列 `Thích` / `Bay to cam xuc thich` 穷举而非归一，两代唯一做过 NFD 的只有空态文案，分解形两代都不认 — 见 oracle.md ⑥ 与覆盖漏洞 C） <!-- aidcp-edge 9176dcb 去变音符归一提到 00-shared.js 共享工具位，见证匹配前经它；既有词表与 reactionButton() 未动 -->
- [x] 1.8 **（覆盖漏洞收口）** 在 1.5 的语料上追加两条分解形越南语用例：分解形（`Thi` + U+0301 组合尖音符 + `ch`）的汇总控件带 `825` → 解析出 825；分解形的中性控件无数字 → 未观测。两条结论须与既有预组合形用例逐位一致。验收：两条用例在 1.7 实装前红灯、实装后绿灯（可 port：feed-reader.test.ts『支持语言共用动作栏分类，数字汇总 toolbar 不成为第二个 react 控件』的四语种循环加一轮分解形 — 见 oracle.md ⑥） <!-- aidcp-edge 9176dcb 预组合形与分解形结论逐位一致 -->

## 2. aidcp-edge — 评论入口执行与文本校验谓词

- [x] 2.1 在 `native/page-engine/src/facebook/comment.rs` 的编辑框获取循环里，当探针原因为「找不到编辑框」时调用已有的入口探针（`facebook/shared.rs` 的 `probe_facebook_comment_action`），拿到坐标后用可信指针点击**一次**，随后在剩余轮次内继续重探编辑框；用一个「已探过」标志保证每条命令最多点一次（镜像 `facebook/runtime.rs:355-372` 首帖编排的形态）（⚠️ 退役实现**也不点**，只有 6 轮催拉——它靠先按 permalink 整页导航到详情页绕开折叠态（src/facebook/comment-executor.ts:633-679），照抄旧代码拿不到点击能力，只能照抄 runtime.rs — 见 oracle.md ②） <!-- aidcp-edge 9176dcb 探不到编辑框时探一次入口、用可信指针点一次，「已探过」标志保证每条命令最多一次 -->
- [x] 2.2 让入口探针回「目标不唯一」/「目标或上下文不符」/「待审入群闸」时直接按对应终态收敛，且不派发任何点击（分诊映射已现成于 runtime.rs:362-367；comment.rs:117-126 今天把 editor.reason 原样吐出、失败面只一档 — 见 oracle.md ②） <!-- aidcp-edge 9176dcb 四种终态直接收敛、零点击派发；用例 an_ambiguous_comment_entry_dispatches_no_click_at_all / a_pending_group_approval_entry_converges_on_its_own_terminal -->
- [x] 2.3 入口点击后仍取不到编辑框时保持「未开始」终态并沿用既有原因码；MUST NOT 上报任何已提交评论（红线同源：作用域内 0 个编辑框绝不回落 document 第一个，点开后新出现的编辑框仍须受同一套作用域收窄，port fb-editor-scope 全组 — 见 oracle.md ②） <!-- aidcp-edge 9176dcb 点开后仍取不到编辑框保持「未开始」、零提交 -->
- [x] 2.4 把评论侧三处文本判据（回读调用点 `comment.rs:199-205` → 谓词 `facebook_comment_editor_matches` `:405-425`、提交前重读 `:245-248`、焦点复检 `:276-282`）收成**同一个**共享谓词，按「规范化后包含命令文本 + 有界额外字数容差」判定；容差取值与 `facebook/publish.rs:19` 的发布容差取同一常量或显式声明差异理由（参照 src/facebook/publish-executor.ts:226-236 —— 旧值 **4** 有成文立论「零宽/不间断空格是无害残留，超出即被 typeahead 塞了 @提及」，新引擎的 10 无对应记录；另注 shared.rs:270-272 的归一不去零宽字符，正是相等判据失败的直接机制 — 见 oracle.md ⑤） <!-- aidcp-edge 9176dcb 三处判据收成同一谓词 facebook_comment_text_accepted，容差与发布侧收口到同一常量 -->
- [x] 2.5 在 `native/page-engine/src/facebook/capability.rs` 的行为台账里为每个支持的写动作增加「文本接受谓词」一维，并加完整性断言：谓词缺失、或跨写动作谓词不同却未记理由即测试失败（另须记一条：评论的正文与联系方式不再分两段各自验收，旧实现有此独立失败面 — 见 oracle.md ⑤ 与覆盖漏洞 D） <!-- aidcp-edge 9176dcb 台账加「文本接受谓词」一维 + 完整性断言（谓词缺失 / 跨写动作谓词不同却无理由即失败） -->
- [ ] 2.6 加 Rust 用例：编辑器值 = 命令文本 + 容差内额外字符 → 接受；被截断 / 超出容差 → 拒绝且清空编辑器、回未开始；入口点击最多一次；探针回不唯一时零点击（可 port：comment-executor.test.ts『受控输入未被接受 → marker_not_accepted 不提交』『评论框催不出 → editor_not_found 不提交』『联系方式逐字符追加』；publish-executor.test.ts 长正文回读可作 4 vs 10 容差基准，content_polluted 用例需新写 — 见 oracle.md ②⑤）
    - **部分完成** <!-- aidcp-edge 9176dcb 谓词层与入口层用例已落 -->：谓词层四条已落（容差内接受 / 截断拒绝 / 超容差 typeahead 污染拒绝 / 清空判据是严格空而非包含），入口层两条已落（最多点一次 / 探针回不唯一时零点击）；**差「拒绝后清空编辑器并回未开始」这一条端到端断言**——现只由既有桩间接覆盖，未新写显式用例。补它不需要任何解锁，属可直接续做的收尾
- [x] 2.7 **（覆盖漏洞收口）** 在 2.5 的台账条目里把「评论的正文与联系方式合成一串一次打完、不再分两段各自验收」连**理由**与**代价**记成文：红线（只有正文进去、联系方式没进去时绝不发出）在 2.4 的包含谓词下仍然守住——编辑器值不包含整串即拒绝并清场；丢掉的是**诊断粒度**，旧实现对这一档有独立失败面与独立用例，新实现只会给出一个笼统的「文本未被接受」。同时加一条 Rust 用例：编辑器只含正文、缺联系方式 → 拒绝、清场、未开始、零提交。若要把该档做成可区分的原因码，MUST 先确认云端对它有归宿，MUST NOT 新增无归宿的原因码（现状：`native/page-engine/src/facebook/comment.rs:72-80` 把正文与群号 `format!("{body}\n{code}")` 拼成一串；旧实现分两段逐字符追加、两次验收，src/facebook/comment-executor.ts:778-799 与片段包含判据 :1211-1219 — 见 oracle.md ⑤ 与覆盖漏洞 D） <!-- aidcp-edge 9176dcb 台账记成文；用例 a_body_without_its_contact_line_is_rejected_as_one_string 锁住红线（谓词层判定，清场的端到端断言同 2.6 待补）；未新增无归宿的原因码 -->

## 3. aidcp-edge — 导航用途开帖

- [x] 3.1 让 `native/page-engine/src/command.rs:199` 的用途字段被真正读取：在 `facebook/feed.rs` 的开帖分发里按用途分流，用途为「导航」时进入导航路径 <!-- aidcp-edge 9176dcb -->
- [x] 3.2 导航路径按命令自身解析可导航规范目标（Facebook 的 `noteId` 即绝对 permalink，见 `facebook-router/00-shared.js:91-103`；也接受显式 `url`），导航后等待就绪，并校验落地页规范帖 id 等于命令 id <!-- aidcp-edge 9176dcb -->
- [x] 3.3 导航路径回**动作完成回执**（带独立观测与页面派生的规范帖 id）；解析不出目标、导航失败或身份不符时回「未开始」回执并点名原因 <!-- aidcp-edge 9176dcb 回执观测带面别 -->
- [x] 3.4 移除「用途为导航却落到注入脚本读当前页」这条退化路径：`facebook-router/90-dispatch.js:75-82` 的 `note_open` 分支在缺面别参数且用途为导航时 MUST NOT 返回当前页详情 <!-- aidcp-edge 9176dcb -->
- [x] 3.5 加 Rust / 路由用例：只带 permalink 的导航用途 → 真导航 + 动作完成回执；无可导航目标 → 未开始且零导航；落地身份不符 → 未开始且不上报详情；MUST 断言导航用途下永不产出详情输出 <!-- aidcp-edge 9176dcb 新增 tests/facebook_note_navigation.rs -->

## 4. aidcp-edge — 列表面到底语义

- [x] 4.1 把 `native/page-engine/src/facebook/feed.rs:203` 的前置守卫从「是否 `home`」改为「是否已声明的列表面（`home|search|group`，与 `:339` 的活动列表面判据同源）」。**⚠️ 本条一落地，`feed_exhausted`（`:381`）就能从非首页面产出，MUST 与 §4B 同批集成**（参照 src/facebook/facebook-session.ts:1008-1098 —— 旧滚动逻辑是**面无关**的，home-only 只加在「空态确认」上、从不加在到底判定上；面白名单 feed-reader.ts:106-109 — 见 oracle.md ④） <!-- aidcp-edge 9176dcb 守卫改为 facebook_list_surface() -->
    - **⚠️ 集成闸未满足**：edge 侧代码已落，但本条自带的「MUST 与 §4B 同批集成」尚未满足——§4B 全部未做（见该节说明）。**合入主干前必须先落 4B.1 / 4B.2**，否则会引入「非首页面到底也被授权切短视频面」的新回归
- [x] 4.1b **必须与 4.1 同改，否则 4.1 是空动作（本次复核发现）**：到底确认的有效性判据也必须接受已声明的列表面，并要求固定五样本序列中的每个样本都留在同一列表面；任一样本换面即 `Invalidated`。验收：单测断言 group / search 面在满足全部证据条件时能到 `ExplicitEnd` / `WindowStable`，且确认期间换面仍判 `Invalidated`。 <!-- aidcp-edge 9176dcb 有效性判据放开到已声明列表面 + 确认窗内换面仍判无效；用例 every_declared_list_surface_can_reach_a_terminal_bottom_state / a_surface_change_inside_the_confirmation_window_still_invalidates_it -->
- [x] 4.2 把 `facebook_unconfirmed_scroll_reason`（当前 `:475-485`）的分类改为：任一列表面上见过卡但未翻出新卡 → 非终态「翻页未确认」；一张卡都没见过 → 「找不到目标」（旧口径更进一步：轮次耗尽但见过卡时直接报 feed_exhausted 换批；「从未见卡」才兜底 no_target — 见 oracle.md ④） <!-- aidcp-edge 9176dcb 见过卡→feed_continuation_unconfirmed，零卡→no_target -->
- [x] 4.3 让 `facebook/shared.rs:822-840`（`facebook_scroll_failure`，`observation` 今天恒 `None`）的滚动失败回执在既有可选 `observation` 里带上所在列表面（复用 `model.rs:285-287` 的 `ActionEvidence.surface`，不新增协议字段）。**（实装实测订正）原措辞写「让既有函数的回执带上列表面」，实测做不到**：`facebook_scroll_failure` 被引擎主体的单测以两参形式调用，改签名必然要动本轮白名单外的文件。订正为：**新增一个带面别的变体 `facebook_scroll_failure_on_surface`，旧签名保留为薄壳转调**，行为与调用点逐位不变（旧实现整段吃 activeFeedUrl、面别天然在手，无此缺口可照抄 — 见 oracle.md ④） <!-- aidcp-edge 9176dcb 新增带面别变体 + 旧签名薄壳；没有面别可报时 observation 保持 None、不臆造 -->
- [x] 4.4 加 Rust 用例：group / search 面近底不增长 → 走到底确认并能形成终止态；group / search 面见过卡未翻新 → 「翻页未确认」而非「找不到目标」；零卡 → 「找不到目标」；三种情形的回执都带列表面（可 port 语料：facebook-session.test.ts 的 scrollY=5000 / scrollHeight=5900 / innerHeight=900，以及『还在长/未到底时绝不提前判到底』反例 — 见 oracle.md ④） <!-- aidcp-edge 9176dcb 三面终止态 / 见过卡续滚 / 零卡 no_target / 回执带面别四条全落，另加「没有面别可报时不臆造」反向断言 -->
- [x] 4.5 除 4.1b 的面别条件、4.6 的增高阈值与 4.7 的固定采样计划外，MUST NOT 改既有显式终止证据链：同代、近底、无增高、卡身份集合不变以及首页空态确认逐条保持不变。**首页空态确认按定义只服务首页，且不复用 4.7 的时序。**
- [x] 4.6 **（覆盖漏洞收口）4.5 的第一条具名例外**：把懒加载增高判据的抗噪阈值从 1px 恢复到退役实现的 100px。只改阈值取值，仍是「页面还在长就继续下滚、绝不判到底」。验收：单测断言 1–99px 的高度抖动不算增长、≥100px 算增长，且 group / search 面在存在小幅重排时仍能走到终止态。 <!-- aidcp-edge 9176dcb 1px → 具名常量 100px；用例 lazyload_growth_needs_to_clear_the_reflow_noise_floor / small_reflow_never_blocks_a_group_or_search_bottom_confirmation -->
- [x] 4.7 **4.5 的第二条具名例外，仅调整到底确认的采样数、节奏和窗口**：新增到底确认专属采样计划 `t=0 / 5 / 7.5 / 10 / 12.5s`，初始探针即第一个样本。五次结构证据均有效且五次均有 `explicit_end` 时，才可在第五次后返回 `feed_exhausted`；前四次不得提前成功。任一样本结构失效立即 `Invalidated`；结构稳定但显式结束标记不齐时，第五次后返回 `WindowStable / feed_continuation_unconfirmed`。验收：生产逻辑使用绝对偏移调度以避免探针耗时累积漂移；等待监听 cancellation 与命令 deadline；Rust 用例锁定五个偏移、五次完成门、每个样本位缺少显式标记的反例，以及 loading / 增高 / 新卡 / 换面 / 换代 / 取消 / 到期反例。首页初始空态的独立确认链不改。 <!-- aidcp-edge 9a21df6 固定五样本状态机、绝对偏移调度与取消/deadline 安全点；Feed 聚焦 20/20、Native fmt/clippy/full test 全通过 -->
- [x] 4.8 给 Facebook `browse_scroll` / `page_scroll` 增加专属 180 秒命令预算，并同步请求值、Edge 准入上限、Rust 引擎天花板；既有 180 秒 Facebook 会话与协议准入不改。验收：跨语言源码契约测试锁住三层相等且不高于会话预算；BrowseSession 用例锁住两类请求值；Client 用例断言 180 秒可准入、180001 毫秒拒绝；Rust 用例锁住两类 ceiling 与 session-min 行为。 <!-- aidcp-edge 9a21df6 三层 180s 对齐；TS 聚焦 48/48、typecheck 与 Rust ceiling 用例通过 -->

## 4B. aidcp-cloud — 列表面恢复与 Reels 授权闸（与 §4 成对，MUST 同批集成）

> **为什么是必配项而非可选优化**（已逐行核对）：`feed_exhausted` 今天只从到底确认的显式终止态产出（`facebook/feed.rs:381`），而到底确认被 `:203` 守卫 + `:425-426` 有效性判据双锁在首页面 ⇒ **今天不可能来自小组页 / 搜索页**。4.1 / 4.1b 一放开，它立刻可从这两个面产出，而云端 `authorizeFacebookReelsFallback` 只校验平台 / 会话 / 幂等态、**无任何面别限定**（`role-dispatcher.ts:3635-3642`、`:1721-1722`）⇒ 账号被从定向面带走。
> **另一半（本次复核修正）**：云端 `sourcePageType` 的值域只有 `'feed' | 'search'`（`src/agents/session-context.ts:17`、`:76`、`:80`），**没有 `group`**。所以：① 搜索面上 `sourcePageType === 'search'`，续滚分支的 `sourcePageType === 'feed'` 前置条件（`:3622-3629`）**必定不成立** ⇒ 该原因落不到任何分支、无命令无终态、静默空转等看门狗，这条是确定的；② 小组面云端**无法用 `sourcePageType` 表达**，只能靠 4.3 加进回执的观测列表面来判别——这正是 4.3 必须先落地、且本节必须按**回执观测面**而不是 `sourcePageType` 做判据的原因。**只合 §4 不合本节 = 引入回归。**
>
> **本轮状态（轨 B 实装，2026-07-28）**：本节四条**全部未做**——本轮改动只落在 `aidcp-edge`，云端半边一行未动。§4 的 4.1 / 4.1b 已在 edge 侧落地并合到集成分支 `native-migration-repair`，所以**上面那条「只合 §4 不合本节 = 引入回归」现在是活的、不是假设**：合入主干前必须先补齐 4B.1 / 4B.2。解锁条件＝一个 `aidcp-cloud` 的实装流（本 change 的云端半边，与 §6 / §7 同批更省事）。

- [ ] 4B.1 给 `authorizeFacebookReelsFallback` 的 `feed_exhausted` 入口加列表面限定：只有**回执观测到的列表面**是首页面才授权切 Reels；非首页面的到底 MUST NOT 授权 Reels。MUST NOT 用 `sourcePageType` 当判据（它无 `group` 值，见上）。验收：用例断言观测面为 group / search 的 `feed_exhausted` 回执产生零 Reels 握手命令（旧实现的三面等价列表面口径见 feed-reader.ts:106-109 与用例『ensureFeed 幂等：搜索页放行搜索、不被带回首页』 — 见 oracle.md ④）
    - **阻塞（与已落的 4.1 / 4.1b 成对）**：阻塞于「本 change 的 `aidcp-cloud` 半边尚未开工」，需一个 cloud 实装流解锁。判据所依赖的**回执观测面**已由 edge 侧 4.3 落地提供（`aidcp-edge 9176dcb`），云端侧无前置缺口
- [ ] 4B.2 给非首页列表面的 `feed_continuation_unconfirmed` / `feed_exhausted` 定义**有界且可观测的终局**：产出一条恢复命令（回首页 / 换关键词 / 停，取舍见 9.9）或落一条显式记录的终态；MUST NOT 出现「无命令 + 无终态记录」。判据一律取回执观测面。验收：用例断言观测面为 search / group 时这两个原因都产出恢复命令或显式终态，且恢复次数有界；另断言观测面缺失（老边端不带）时行为逐位等于今天（旧实现给搜索面 0 卡的终态口径是 `no_results` 成功终态、不是 no_target，可作恢复语义参考 — 见 oracle.md ④）
    - **阻塞（与已落的 4.2 成对）**：同 4B.1，阻塞于云端半边未开工。4.2 已让非首页面的「本批看完」产出 `feed_continuation_unconfirmed`，该原因码在云端**目前无归宿**，本条不落＝新原因码落进静默空转
- [ ] 4B.3 核对 `:3519-3520` 的 Reels pending 恢复入口：它今天认 `reels_pending` / `no_target`；4.2 把非首页面的「本批看完」从 `no_target` 改成 `feed_continuation_unconfirmed` 后，确认该恢复路径的触发面未被意外收窄（若被收窄，须在同批补齐）。验收：用例覆盖 Reels pending 态下收到新原因码时的行为
    - **阻塞**：同 4B.1，阻塞于云端半边未开工
- [ ] 4B.4 加一条覆盖式断言：Facebook 滚动回执的**每一个**终态原因码都有云端归宿（命令或显式终态），新增原因码而不接线即测试失败（原因码清单来源可参 feed-reader.test.ts settleCards 四条锁定的 feed_still_loading / no_feed / no_target 分档 — 见 oracle.md ④）
    - **阻塞**：同 4B.1，阻塞于云端半边未开工。**注**：本条也是 10.4 的判据依据（同意闸原因码是否有云端归宿），实测结论已回写 design.md，见 10.4

## 5. aidcp-edge — 不支持命令的前置拒绝

- [x] 5.1 在 `native/page-engine/src/facebook/capability.rs` 增加逐命令的「Facebook 是否实现」判定，并把六个未实现的发布命令（`publish_set_cover` `:355` / `publish_add_with_candidate` `:381` / `publish_set_option` `:394` / `publish_set_schedule` `:407` / `publish_capture_scheduled` `:446` / `publish_reconcile_scheduled` `:459`）记为显式不支持 + 理由 <!-- aidcp-edge 9176dcb 台账加 supported / unsupported_reason 两列，六条标 supported=false 并各带理由 -->
- [x] 5.2 把这六个命令的行为台账条目改为不带 oracle / 目标见证 / 提交原语 / 校验见证 / 终态语义；加完整性断言：不支持的命令若仍声明行为证据即测试失败 <!-- aidcp-edge 9176dcb 完整性断言双向锁：支持的必须无理由且有证据、不支持的必须有理由且无证据；facebook_publish_declares_six_supported_and_six_unsupported_entries 按 6+6 对账 -->
- [x] 5.3 让这六个命令在页面规则求值、导航、输入、点击、提交窗口与写截止时间**之前**返回既有「能力不支持」结果；`facebook-router/90-dispatch.js:184` 与 `:193-195` 的页内未实现分支不再是这六个命令的实际归宿（分片代码可保留作最后防线，但验收要求实际归宿在 Rust 侧）。**（实装实测订正）「最后防线」在页内是两类形状、不是一类**：`90-dispatch.js` 原来只对其中**四条**走未实现分支，另两条走的是发布回执分支，两类回执形状不同。Rust 侧前置拒绝必须与**各自对应的那一类**逐位一致，验收断言按两类分别对账，MUST NOT 假设六条同形 <!-- aidcp-edge 9176dcb 六条在任何求值 / 导航 / 输入 / 点击 / 提交窗口 / 写截止之前返回能力不支持 -->
- [x] 5.4 加 Rust 用例：这六个命令零 CDP 调用、零提交窗口请求，返回能力不支持；`publish_navigate_entry` / `publish_select_mode` / `publish_upload_image` / `publish_fill_field` / `publish_submit` / `publish_capture_post_id` 六个仍支持的命令行为不变（FB 台账共 12 条发布 entry，6 支持 + 6 不支持，完整性断言按此对账） <!-- aidcp-edge 9176dcb 新增 tests/facebook_publish_unsupported.rs：零求值零输入，回执形状与页内最后防线逐位一致 -->
- [x] 5.5 MUST NOT 改 `command-manifest.json` 的回执列 / 契约列 / 效果列 / 取消列语义（归 `harden-native-engine-runtime-contracts`）；若逐平台支持矩阵需落在该文件，集成期与它串行 <!-- aidcp-edge 9176dcb 约束已守：该文件零改动，支持矩阵落在 capability.rs -->


## 6. aidcp-cloud — 迁移指令与迁移闩

> **先读现状再动手（已逐行核对，勿重复实现已有行为）**：① 落地判据**已经**要求 `payload.noteId === mig.noteId` 且观测面为 `detail`（`:3567`）⇒ 无关回执**不会**把已批准评论发到未经证实的页面，该红线今天已守住，6.3 只补「消费准入」不补「落地判据」；② 超时清理**已经**存在但只对免审强制评论武装（`armMandatoryCommentOutcomeTimer` 在无审批 trace 时直接 return，`:1550-1551`）；③ 会话重启 / 结束**已经**清闩（`:2264` / `:2339` / `:2400` → `settlePendingMandatoryCommentAsUnknown` `:1574-1581`），抢占也清（`:3501-3505`）；④ 评论支线硬超时（`expireCommentSubline` `:1311-1326`）**不**清闩。
>
> **本轮状态（轨 B 实装，2026-07-28）**：本节六条**全部未做**——本轮只动 `aidcp-edge`，云端一行未改。解锁条件＝一个 `aidcp-cloud` 实装流；6.1 的对侧（导航用途开帖的边缘执行）已就绪（§3，`aidcp-edge 9176dcb`），云端只需把可导航规范目标带上，无前置缺口。

- [ ] 6.1 在 `src/orchestrator/role-dispatcher.ts:3055-3062` 的迁移下发处，让 `open_note{purpose:'navigate'}` 携带可导航的规范目标（Facebook 即规范 permalink），并加注释写清「用途标记不是边缘唯一需要读的字段」
- [ ] 6.2 把 `pendingMigration` 的有界超时清理扩到**每一次已批准交付**（今天只对免审强制评论武装）：无审批 trace 的普通交付也必须有超时清闩 + `reportApprovedNotDelivered` + emit 终局事件（与 `:3064-3079` 的抑制路径同口径）。验收：断言普通交付武装后，在超时预算内不给回执，闩被清、操作员收到「已批准未送达」、评论支线时钟解冻
- [ ] 6.3 给闩的**消费准入**加相关性判据：`:3557` 的进入条件除「有闩 + 动作是 open_note」外，还须该回执与武装它的那次迁移相关联（至少 noteId 匹配）；不相关的 `open_note` 回执 MUST NOT 进入该分支、MUST NOT 清闩、MUST NOT 触发本次迁移的失败归因（今天它会走 `:3600` 的 else 分支把失败归到不相干的回执上）
- [ ] 6.4 让评论支线硬超时（`expireCommentSubline` `:1311-1326`）在清 `commentInflight` 时同时清迁移闩并回报操作员，二者不再各清一半
- [ ] 6.5 加 Cloud 用例：迁移指令带规范目标；**普通（无审批 trace）交付**超时 / 会话结束 / 断连三路各清闩并回报操作员；异 noteId 的 `open_note` 回执既不解除闩、不发评论、也不产生本次迁移的失败归因；同 noteId + detail 观测的回执正常解除并发评论（回归断言 `:3567` 的既有落地判据未被削弱）

## 7. aidcp-cloud — 缺失指标的门槛结论

> **本轮状态（轨 B 实装，2026-07-28）**：本节五条**全部未做**，且 7.1 / 7.2 **另有硬前置**——它们消费的「反应计数未观测」标记要靠 1.3 / 1.4 落进载荷，而 1.3 / 1.4 本轮被协议热点单写者阻塞（见 §1）。所以解锁顺序是：先解 1.3 / 1.4 的协议窗口，再做 7.1 / 7.2。**主症状（Facebook 热度恒 0 → 整平台被判不值得评）已由 1.1 / 1.2 在边缘侧修掉**，本节修的是残下的「未观测 vs 真零」不可区分。

- [ ] 7.1 让 `src/comm/handler.ts:496-505` 的字段映射（今天是 `likeCount: (p.likes as number) ?? (p.likeCount as number) ?? 0`，`:502`）在把边缘卡片 / 详情映射进内部笔记结构时保留「反应计数未观测」标记，MUST NOT 用 `?? 0` 把它塌成 0。验收：用例断言带标记的载荷进来后，内部笔记结构上标记仍在、下游能区分「未观测」与「测量到 0」（旧口径：解析不出即 0 且明文「绝不臆造」，缺失从不冒充 — 见 oracle.md ①）
- [ ] 7.2 在 `src/agents/comment-appraiser.ts:167-168` 的硬门槛处区分「已测量」与「未观测」：未观测时 emit 一条点名缺失指标的独立 `comment.skipped` 原因，MUST NOT 用 `below_comment_threshold`，MUST NOT 调 LLM，MUST NOT 放行
- [ ] 7.3 保持门槛数值与「无收藏概念平台放宽收藏合取项」的既有规则逐字不变；真零仍走既有 `below_comment_threshold`（旧实现明文：Facebook 无收藏概念、collect 一律诚实 0，绝不用反应数冒充；collectCount:0 两代一致、非缺口 — 见 oracle.md ①）
- [ ] 7.4 加 Cloud 用例：未观测 → 独立原因、零 LLM 调用、不放行；测量 0 → 既有 below_comment_threshold；测量 500 → 照常进 LLM 判定
- [ ] 7.5 运行 `cd ../aidcp-cloud && npm run test:acceptance`（须含 `AC-PROTO-*` 全过，证明两份 protocol.ts 未漂移）→ `npm test` → `npm run typecheck`

## 8. 控制仓 — 规格与台账

- [ ] 8.1 把本 change 的四个能力 delta 与实装偏离逐条回写本 `tasks.md`，格式 `<!-- <repo> <commit-sha> 备注 -->`，sha 一律取自**已推送**的提交。验收：每一条已勾选 task 都带 sha 或显式偏离说明，且 `git branch -r --contains <sha>` 能命中远端默认分支
    - **部分完成**：回写本身已完成（本轮五份能力增量的边缘半边逐条带 sha 或偏离说明，云端半边逐条标未做 / 阻塞）；**差验收的后半条**——`9176dcb` 目前只在集成分支 `origin/native-migration-repair` 上，`git branch -r --contains` **命中不到远端默认分支 `origin/master`**。解锁条件＝该分支 land 到 master 后回来复核一次 sha 归属（land 前还须先补 §4B，见 4.1 的集成闸）
- [ ] 8.2 把 §9 的真机验收项（9.4、9.4b、9.5–9.10）逐条登记进 `docs/real-machine-acceptance-backlog.md` 的对应簇，并在条目里写清判据与所需账号分组。验收：backlog 里能按本 change 名 grep 到全部 8 条
    - **未做**：本轮为避免与并行流同时写同一份 backlog 文档而未动它（控制仓工作区当前有其他并行流的未提交改动）。无技术阻塞，属 land 前的收尾动作，与 8.4 一并做
- [x] 8.3 运行 `openspec validate restore-native-facebook-residual-parity --strict` <!-- aidcp 2026-07-29 五样本时序与 180s 预算回写后重新实跑通过：Change 'restore-native-facebook-residual-parity' is valid -->
- [ ] 8.4 **（覆盖漏洞收口）** 把本次收口新增的真机项（9.11、9.12）与 §10 引用的真机判据一并登记进 `docs/real-machine-acceptance-backlog.md` 的同一簇，并在条目里注明 §待裁定 1 未裁定时被阻塞的是哪几条任务（10.7）。验收：backlog 里能按本 change 名 grep 到 9.4–9.12 全部 10 条。**另注**：8.1 的措辞写于四份能力增量时期，本次收口后共**五份**（新增 `facebook-consent-overlay`），回写范围按五份对账
    - **未做**：同 8.2，与它一并做

## 9. 验证与验收

- [x] 9.1 运行 Edge 侧：`cd ../aidcp-edge && npm run test:acceptance` → `npm test` → `npm run typecheck`，并跑 Native Rust 全量与 `cargo fmt --check` <!-- aidcp-edge 9176dcb 验收 30/30 全过；全量 2621 例 / 2594 绿 / 26 红 / 1 跳过；typecheck 通过；gate:native（fmt + clippy -D warnings + test，工具链 1.97.1）通过。26 条红**全部**是同集成分支上另一个 change 的失败优先用例（动作侧 15 条 / 通知侧 11 条，等 restore-native-xiaohongshu-action-honesty 的 slice 2.3–2.15），本 change 零新增失败 -->
- [ ] 9.2 重建本机 Native 引擎产物并记录其 SHA-256；确认生产剪枝与打包输入检查仍拒绝任何页面规则分片出现在二进制之外
    - **未做**：本轮未重建产物、未记录 SHA-256。**注**：同集成分支上的 `enforce-native-engine-artifact-gates`（`aidcp-edge be0a8be`）刚把泄漏闸与陈旧闸做成真闸，本条应在它之后跑一次、以那两道闸的实跑结果为准，避免两个流各记一份不一致的产物指纹
- [x] 9.3 显式记录**未执行**的闸：不出安装包、不签名、不部署 dev / ol、不做真机写动作（评论 / 发帖 / 加群）验收 <!-- aidcp-edge 9176dcb 本轮未执行：Electron 打包 / 签名 / 公证、dev 与 ol 部署、任何真机写动作（评论 / 发帖 / 加群）验收、Native 产物重建与指纹记录（见 9.2）；已执行的只有代码级门禁，见 9.1 -->

### 需真机才能定论的项目（MUST NOT 写成已确认事实）

- [ ] 9.4 **真机验收项**：采样 Facebook 中文 / 英文 / 越南语 / 西语四种界面语言下，首页卡与详情页的反应汇总控件是否存在、其 accessible label 与渲染文本的确切形态。判据：能否稳定抽到与页面显示一致的数字。**未核验前不得断言「所有版式都不存在带数字的中性按钮」**——若某些版式的中性控件文本含数字，读数会从恒零变成随机偏差，1.1 的判据须相应收紧（旧代码已记两种真实并存版式：汇总按钮自己显示数字，或动作按钮同按钮内显示数字——「数字只能描述呈现，不能单独决定动作/汇总」 — 见 oracle.md ①）
- [ ] 9.4b **真机验收项（反向，本次复核新增）**：同一批采样里还须记录 `reactionButton()` 在各语言下**实际选中了哪个控件**。该锚点是 `/^(赞|讚|like|me gusta|thích)(\b|\s|$)/i`（`08-reaction-semantics.js:30`）并取 DOM 序第一个命中项：中文汇总标签「赞：N位用户」因全角冒号被排除，但英文形态 `Like: 1.2K` 在 `\b` 下**会**命中——若它先于中性控件出现，点赞执行器就会去按一个非切换控件，正是 `facebook-note-scoped-targeting` 明令禁止的那件事。判据：逐语言记录选中控件是可切换的中性控件还是汇总控件。**这是既有状态、非本 change 引入，本 change 也不改该锚点**；若采样证实命中，另起 change 修点赞定位（本 change 已把读数从该函数摘走，届时收紧它不会再打坏读数）（旧实现的数字守卫正是这条的反向用法：有数字即排除，防把「任何已有反应的帖子」误判为已赞，src/facebook/cta-labels.ts:100-139 — 见 oracle.md ①）
- [ ] 9.5 **真机验收项**：确认运营机上实际运行的桌面客户端构建是否声明就地定位能力（本机源码 `aidcp-edge/src/facebook/driver.ts:46` 声明了它，但运行中的那个包声明什么是运行期事实）。这决定「切到详情面」的开帖指令在生产上是每次都发、还是结构不可达
- [ ] 9.6 **真机验收项**：在 dev 上核对 Facebook 自动评论链在修好读数之前的实际跳过原因分布，确认「整平台被判为不值得评」这一后果链在日志里真的成立（当前结论由代码路径推出，未在生产日志里实证）
- [ ] 9.7 **真机验收项**：观察折叠态评论入口在真实版式下点击一次后编辑框的出现时延，据此确认 2.1 的重探轮次预算足够，且一次点击不会把已展开的编辑框收起（旧预算基线：6 轮 × 700px、每轮 500ms，且这类循环内预算放宽会撞开帖步超时 — 见 oracle.md ②）
- [ ] 9.8 **真机验收项**：采样编辑器在提交前实际会补入的不可见字符量（零宽字符、自动链接化、提及控件化），据此确认 2.4 的额外字数容差取值（旧值 4 的立论是「零宽/不间断空格无害、超出即 @提及污染」，采样应能判 4 与 10 哪个成立 — 见 oracle.md ⑤）
- [ ] 9.9 **真机验收项**：观察小组页 / 搜索结果页「本批看完」在生产上的实际发生频率与恢复效果，据此再定非首页面到底的恢复动作（回首页 / 换关键词 / 停）；本 change 只保证语义不再被标成「找不到目标」（同批须坐实：`explicit_end` 是迁移新加能力、旧实现只有 explicitEmpty，群/搜索面是否有对应「没有更多帖子」文案未知 — 见 oracle.md ④）
- [ ] 9.10 **既有缺口（低优先级，非本次回归）**：反应与动作标签的 Unicode 兼容形 / 分解形不被识别。经复核这是**两代共有的盲区**，不是 Native 迁移引入的回归，本 change 不修、只登记；真机判据是采样各语言下标签的实际 Unicode 形态并确认是否需要归一化（旧词表靠**手工并列** Thích / Bay to cam xuc Thich 穷举而非归一，新引擎逐字继承；两代唯一做 NFD 的只有空态文案 — 见 oracle.md ⑥ 与覆盖漏洞 C）
- [ ] 9.11 **真机验收项（覆盖漏洞收口，服务 §10）**：采样 Facebook 同意条在各界面语言下的真实形态——它是不是 `[role=dialog]` / `[aria-modal]`（还是非对话框的底部横幅）、接受按钮的可见文案与 aria-label、同文案接受按钮是否会并存多个、以及首页在同意条在场时是否同时挂着与同意无关的可见对话框。判据：按 10.1 的作用域口径能否稳定采到策略所需按钮。同批还须核验一处**方向相反**的疑点：`05-session.js:11` 的正文取样是 `text(document.body,5000)`（截断到 5000 字符），退役实现读的是完整 innerText（src/facebook/consent.ts:95），长页面上 cookie 文案若落在截断之外会判成「无同意条」并放行——这条**未经真机确认，MUST NOT 写成既成事实**
- [ ] 9.12 **真机验收项（覆盖漏洞收口，服务 4.6）**：采样 Facebook 三个列表面在「没有新内容」时 `scrollHeight` 的实际抖动幅度与懒加载单批的真实增量，确认 100px 抗噪阈值在 Native 版式上仍是合适取值（旧值 100px 的立论建立在 2026-06 的页面结构上，Native 版式是否同量级未复核）。判据：抖动幅度稳定低于阈值、懒加载单批增量稳定高于阈值；若两者重叠，须改用「连续 N 轮无增长」而非单纯抬阈值，并回写 4.6
- [x] 9.13 验证五样本到底确认与滚动超时链：Edge 运行三份聚焦 TS 契约、`npm run typecheck`、完整 `npm run gate:native`，控制仓运行 OpenSpec strict validate。 <!-- aidcp-edge 9a21df6：TS 48/48、typecheck 通过、Native fmt + clippy -D warnings + 全量 230/230 通过；aidcp 2026-07-29 strict validate 通过 -->

## 10. aidcp-edge — Facebook 同意闸的作用域与失败分档（覆盖漏洞收口）

> **为什么在本 change 里做**：这是 Facebook 侧的残留 parity，不需要任何新能力，改的是既有同意闸的作用域与失败分档；已合并规格 `facebook-consent-overlay` 已经写明了「present 需同时满足 cookie 文案 + 至少一个接受按钮」「策略所需按钮缺失 → 诚实 no_target」这两条，Native 迁移后的实现与它不符——**这是对已上线规格的回归，不是新提案**。
> **影响面（已逐行核对）**：同意闸是 `ensure_facebook_action_gate` 的统一前置，调用点覆盖评论（comment.rs:58、:221）、首帖开帖与加群（runtime.rs:122、shared.rs:559）、feed 滚动 / 刷新 / 开帖（feed.rs:82、:131、:179、:246、:276）、feed 点赞（feed_like.rs:28）、Reels（reels.rs:28）、发布五处（publish.rs:120、:166、:229、:472、:754）。**一旦作用域落错，这些动作会被同一条 `blocked_by_consent` 全部判成阻断。**
> **串行要求**：`facebook/shared.rs` 的点击原语归 `restore-native-actuation-humanization-and-locating`（本节只调用、不改原语）；`repair-native-facebook-group-join-decoding` 的 operationStage 白名单含 `action_gate_consent_probe`，本节 MUST 保留该 stage 名。

- [x] 10.1 采集作用域改由同意语义自身界定：把 `facebook-router/05-session.js:18` 的 `first(['[role="dialog"]','[aria-modal="true"]'])||document` 改成「候选容器自身文本命中 cookie 政策文案时才收窄到它，否则在整个 document 上采集」。MUST NOT 让一个不含 cookie 文案的可见对话框成为采集框。验收：路由用例——页面同时存在良性对话框（聊天弹窗 / 加载浮层）与**非对话框的底部同意横幅**时，两个策略点位仍被采到；良性对话框单独在场且无 cookie 文案时判「不存在同意条」（参照 src/facebook/consent.ts:114-124 —— 退役实现在整个 document 上采集、取首个命中，**没有**这个失效模式；首页常年挂良性对话框这一现象另见 src/facebook/feed-reader.ts:349-354 — 见 oracle.md ③） <!-- aidcp-edge 9176dcb 只有自身文本命中 cookie 文案的可见容器才收窄，否则整 document 采集；新增 facebook-consent-scope.test.ts -->
- [x] 10.2 给存在性判定补「至少一个可点接受按钮」这个合取项：`05-session.js:22` 今天是 `cookieCopy&&!captcha&&!loginPath`。**两处后果都要在验收里锁住**：① cookie 文案在页但按钮词表全不命中时，MUST 判「不存在同意条」让受闸动作照常继续，MUST NOT 把评论 / 点赞 / 发帖 / 加群 / 滚动 / 刷新一律判成 `blocked_by_consent`；② 同一分片的阻断分类里，登录分支以 `!consent.present` 为条件（`:46`），present 假真会让「带 cookie 文案的登录墙」被误判成同意条阻断、拿不到 `login_required`——验收须含这条回归（参照 src/facebook/consent.ts:67-80 的纯判定四条合取 — 见 oracle.md ③） <!-- aidcp-edge 9176dcb present 门补「至少一个可点接受按钮」合取项；带 cookie 文案的登录墙仍拿得到 login_required（回归用例已锁） -->
- [x] 10.3 探测失败降级：`facebook/shared.rs:419-422` 与 `:455-458` 今天把 `probe_facebook_consent` 的错误经 `?` 直接上抛，整条命令变成引擎错误。改为按退役实现处置——探测失败既不假设有同意条、也不假成功，记日志后当作「无同意条」让既有闸继续。验收：Rust 用例断言同意探针返回错误时动作照常继续、命令不因此失败（参照 src/facebook/consent.ts:188-195 的注释与分支 — 见 oracle.md ③） <!-- aidcp-edge 9176dcb 探测失败降级为「当作无同意条」继续，不再炸成引擎错误 -->
- [x] 10.4 失败分档：把「策略所需按钮定位不到」（文案 / 布局漂移，可诊断）与「点满三次仍未清掉」（升级停手）分成两个可区分终态——今天 `shared.rs:445-452` 与 `:455-462` 把两者折叠成同一个 `blocked_by_consent`。MUST NOT 引入云端没有归宿的新原因码：复用退役实现的 `no_target` 前须确认它在同意闸语境下的云端归宿与既有语义不冲突（口径同 4B.4 的覆盖式断言）；若确认不成立，则保留 `blocked_by_consent` 并把分档落到回执的诊断 / 观测字段里，同样要求两档可分。验收：用例断言两种失败给出可区分结论，且所选表达方式在云端有归宿（参照 src/facebook/consent.ts:200-206 与 :223-224 — 见 oracle.md ③）。**（实装实测得出，免得下一个人重复 grep）云端归宿的实测结论**：`blocked_by_consent` 在 `aidcp-cloud/src` 上 grep **零命中**——它今天在云端没有任何专属归宿；而 `no_target` 在评论链路上有具体语义，把同意闸的失败改报 `no_target` 会与那套语义串味。所以本条按「保留 `blocked_by_consent` + 分档落回执诊断 / 观测字段」这一支落地，**不**新增原因码 <!-- aidcp-edge 9176dcb 两档可分：按钮定位不到=未点击过；点满三次仍清不掉=点过但升级停手；原因码仍 blocked_by_consent -->
- [ ] 10.5 回执可观测性：让同意闸的处理结果带上「探到没探到 / 清没清掉 / 点了几次」三项（退役实现是 handled / cleared / attempts / reason 四元组），落在既有诊断或观测通道里；MUST NOT 新增协议消息类型、MUST NOT 改 `action_gate_consent_probe` 这个 operationStage 名。验收：用例断言「探到了但没清掉」与「压根没探到」在回执上可分（见 oracle.md ③）
    - **部分完成** <!-- aidcp-edge 9176dcb 三项可分 -->：三项都落到既有诊断 / 观测通道且**可分**（探到没探到 / 清没清掉 / 点没点过），本条验收要求的「探到了但没清掉 vs 压根没探到」已锁住；**差的是「点了几次」的精确次数**——现只做到布尔（点过 / 没点过），要精确计数得给动作回执加字段，落点在 `native/page-engine/src/model.rs`（本轮白名单外，与 1.3 / 1.4 同一批协议窗口）。未新增协议消息类型，`action_gate_consent_probe` 这个 operationStage 名未动
- [x] 10.6 用例（旧 `test/facebook/consent.test.ts` 一整组可 port）：策略所需按钮缺失 → 诚实不点、按 10.4 的分档收敛；探测失败 → 视为无同意条继续；横幅清不掉 → 有界重试后升级；`necessary_only` / `accept_all` 各点各自的按钮并点后复探确认清除；登录门 / 验证码优先三态（含「同意条正文含『登录 Facebook』字样仍判同意条」）；良性对话框 + 底部横幅共存 → 仍采到按钮。MUST NOT 放宽「策略所需按钮缺失时绝不改点另一个按钮」这条已上线红线 <!-- aidcp-edge 9176dcb 新增 tests/facebook_consent_gate.rs + facebook-consent-scope.test.ts：按钮缺失诚实停手零点击 / 探测失败继续 / 清不掉有界升级 / 良性对话框 + 底部横幅共存仍采到 / 登录门 · 验证码优先三态 -->
- [ ] 10.7 **阻塞标记（见 design.md §待裁定 1）**：在「多个同文案接受按钮时取首个 vs 保持不唯一即停手」裁定之前，MUST NOT 落地任何放宽歧义处置的改动（今天 `05-session.js:25-26` 要求命中数恰好 1、`shared.rs:435-443` 据此放弃点击）。本节其余各条（10.1–10.6）不受该裁定阻塞，可先行落地
    - **阻塞（裁定未下）**：阻塞于 design.md §待裁定 1，需**用户裁定**解锁。本轮按现状「不唯一即停手」落地，并**加用例把现状锁住**——这样将来无论裁定走哪一支，改动都会撞到一条明写的断言，不会被人默默放宽。真机项 9.11 会采样「同文案接受按钮是否会并存多个」作为裁定输入，但采样结论不等于裁定
