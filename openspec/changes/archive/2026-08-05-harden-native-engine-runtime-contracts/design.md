## Context

2026-07 边缘把浏览器页面智能从 TypeScript 迁到 Rust「Native Page Engine」，动机是防反编译；07-22 小红书切生产、07-23 Facebook 与微信跟进，之后二十余个修复提交。实质架构是：页面规则仍是 JS，构建期按清单拼接、异或混淆后编进二进制，运行时注入页面执行。迁移明确不双跑、不比对、不回退，回滚手段只有装包回滚——也就是说，运行期出的每一个契约漂移都没有对照组可比，只能靠构建期/测试期抓。

本 change 面对的是「拆进程 + 拆语言」带来的一类共同形态：**同一件事实在两侧各写一份，而没有任何机械手段让两份对上**。已在代码里坐实的现状：

- **声明零消费**。命令清单每条命令都有 `receipts` / `requestContract` / `effect` / `cancellation` 四列。全仓对 `receipts` 的引用只有 `aidcp-edge/test/native-page-engine/command-manifest.test.ts:14` 一处 TypeScript 接口字段声明，没有任何断言；`native/page-engine/src/` 下 grep `receipts` 零命中。另外三列的唯一断言是「字符串长度大于 0」（同文件 :122-124）。
- **声明与行为已经对不上（逐条实读，不一概而论）**。清单 42 条命令里有 12 条声明了两条回执：`page_scroll` / `feed_refresh` / `search_execute` / `note_open` / `note_close` / `navigation_back` / `note_browse_images` / `profile_open` / `notification_open` / `notification_browse_comments` / `notification_back_home` / `captcha_click`。边缘一次命令执行只有一个 `execution.output`，`report()` 按输出种类分派（`aidcp-edge/src/native-page-engine/browse-session.ts:278-400`）。已在代码里坐实的两个方向的缺口：
  - `note_open` 声明 `['note.detail','action.completed']`，但两个平台的成功路径都恒产出 `note_detail`（`native/page-engine/src/facebook-router/90-dispatch.js:75-82`、`src/xhs-command-router.js:187-196`），而 `report()` 的 `note_detail` 分支直接 `return`（`browse-session.ts:310-329`）——**声明的动作完成在成功路径上没有任何可达发出点**。
  - `note_close` / `navigation_back` 声明 `['action.completed','page.cards']`，但两个平台的成功路径恒产出 `action_receipt`（`90-dispatch.js:83-86`、`xhs-command-router.js:197-205`）——**声明的 `page.cards` 反向不可达**。
  - 反例同样坐实，所以不能按「声明两条就一定对不上」推广：`search_execute` 的两条回执**确实都发**——`page_cards` 分支在信封为 `search.execute` 时先报 `page.cards` 再报 `action.completed`（`browse-session.ts:283-308`）；`note_browse_images` 是**跨平台并集**（小红书回详情、Facebook 回动作回执），单次执行只发一条、并集与声明相符。
  - 因此对账的判据必须是「声明集合 = 成功路径上可达发出点的并集」，而不是「= 单次执行发出的集合」；且必须排除失败路径——`reportFailure`（`browse-session.ts:436`）对任何命令都会发一条 `ok:false` 的动作完成，若把失败路径算进来，`action.completed` 对每条命令都会被算成「已落地」，对账将退化成恒真。其余 8 条多回执命令的落地情况由 1.1 的对账检查产出，本 change 不预判。
- **词表已经漂了一条**。`NativeCommand` 枚举 43 个变体（`native/page-engine/src/command.rs:449-493`），`PRODUCTION_COMMAND_KINDS`（同文件 :11-52）与清单各 42 条，差集是 `PageProbe`。名为 `production_enum_matches_the_frozen_manifest_exactly` 的测试（同文件 :1035-1049）比的是 `PRODUCTION_COMMAND_KINDS` 与清单，从未触及枚举。
- **跨语言常量双写并做相等断言**。`native/page-engine/src/facebook/capability.rs:36-47` 写死三个提交窗口标签与预算（18_500 / 20_000 / 20_000），`src/native-page-engine/client.ts:854-857` 再写一份并在 `parseCommitWindowRequest` 里做严格相等比对；不等即返回 undefined，调用点走 `failProtocol` + `terminate()`（`client.ts:500-508`）。两端都是裸数字，typecheck 抓不到。
- **能力握手不覆盖页面规则**。`native/page-engine/build.rs:19-21` 的能力摘要只对 `command-manifest.json` 求 SHA-256；页面规则源（Facebook 规则分片、小红书三份 JS、两份选择器表）只进 `rerun-if-changed`、不进摘要。引擎版本取 `CARGO_PKG_VERSION`，`Cargo.toml:3` 自建仓至今恒为 `0.1.0`。平台适配器版本是写死字符串，出现在 `protocol.rs`、`scripts/build-native-page-engine.mjs`、`src/electron/native-page-engine-artifact.cjs` 三处。开发态的 `scripts/build-native-page-engine.mjs` 的 `verify()` 只做产物自洽（二进制哈希对自己的校验文件、清单字段对 Cargo 版本与命令清单摘要），没有任何一项与页面规则源码新鲜度相关；`scripts/ensure-native-page-engine-dev.mjs:19-27` 是「校验通过就不重编」。实测自 2026-07-22 起 `native/page-engine/src/facebook-router/` 有 10 次提交、`command-manifest.json` 有 4 次。
- **自愈入口被故障堵死**。`src/native-page-engine/runtime.ts:129-131` 的会话缓存命中即返回，不查传输存活；进程退出没有任何监听会清掉 `owner`（`closeOwner` 的调用点只有 `browse-session.ts:164/182/193`，全在 `stop()` / `close()` / `closeAndWait` 路径上）。而 `browse-session.ts:141-142` 把 `if (env.type === 'session.end') this.stop()` 写在 `await active` 之后、`catch` 之前——引擎已死时 `await active` 必抛，收尾被跳过。
- **重连不带身份**。`engine.rs:206-207` 用会话结构里存的 `self.host` / `self.port` 重新列目标；`endpoint.rs:214-226` 的筛选条件是「目标类型是 page + URL 命中平台允许集 + 调试地址端口等于端点端口」，无分身身份证据。边缘只在建会话那一次调 `getEndpoint()`（`runtime.ts:136`）。
- **重连重试无超时包裹**。`engine.rs:474-494` 只对首跑套 `tokio::time::timeout`；`engine.rs:509-528` 的重连分支直接再调 `execute_platform_command_once`，不再套超时。重连本身有 `remaining` 包裹（`engine.rs:203-217`），但重试没有。引擎同时只接一条命令，其余一律以 `CommandInProgress` 顶回（`main.rs:251-263`）。
- **取根空值兜底与诊断不对称（复核后按实读收窄）**。`00-shared.js:13-19` 的取用函数（`all` / `first`）直接对传入 root 调 `querySelectorAll`，root 为 `null` 即抛 `TypeError` —— **这条结构缺口成立且无任何防护**。以 `|| document.body` 兜底取根的调用点实测为 5 处（`20-feed.js:87,154,166,253` 与 `40-group-join.js:103`，行号已按 `aidcp-edge@9cd7691` 校正；简报给的 `87,147,233` 已被 07-28 的改动顶偏），但逐处读下来只有 **1 处**真会把空根交给遍历：
  - `20-feed.js:253` 的 `currentDetail()`：`... || document.querySelector('main') || document.body` 之后**无空判**，直接 `noteDetail(root, permalinkOf(root)...)`，其内 `articleAuthor` / `articleBody` / `all('img',root)` 会对 `null` 调 `querySelectorAll` 当场抛。它挂在 `note_open` 非 feed 面（`90-dispatch.js:75-82`）——**是读命令路径，不是写命令路径**。
  - 另 4 处下游都是空安全的：`20-feed.js:87` 紧跟 `if(!scope)return {card:null}`；`:154` 的 `anchor` 只进 `for(let node=anchor;node&&…)`；`:166` 的 `scope` 只以 `scope&&scope.querySelector(…)` 与 `all(…,scope||document)` 使用；`40-group-join.js:103` 的 `main` 进 `targetGroupScope`，其首行即 `if(!groupId||!main)return {region:null,…}`（`40-group-join.js:50-51`），随后的 `all('button,…')` 用的是默认 root `document`。
  - 「空根塌陷会把写命令记成可能已做」这条**机制**在代码里成立：写命令的任何规则错误都被判 `EffectPhase::Ambiguous`（`native/page-engine/src/engine.rs:532-543`）。但**当前没有一处已坐实的写命令路径会经由上述兜底拿到空根**——写路径的塌陷是「取用层零防护 + 未来新写的规则」这一结构风险，不是既成事实。故本 change 的闸落在取用层（防未来），并把「导航窗口内 `document.body` 为空 → 遍历当场抛」列为真机验收项（9.7.2），不在 spec 里断言它已发生在写命令上。
  - 诊断侧：`facebook.rs:607-620` 的解码带有界诊断（阶段/字段路径/异常位置），`xhs.rs:66-72` 与 `probe.rs:89-98` 是裸错误。`input.rs:108-128` 的逐字焦点守卫里，通道失败已被单独归为 `Engine`（`.map_err(|_| TextInputFailure::Engine)`），但「守卫求值抛异常导致 `/result/value/output` 缺失」与「焦点确实丢了」都塌成 `TargetLost`。
- **评论预算双写**。云端 `aidcp-cloud/src/comment-agent/facebook-edge-steps.ts:46-58` 与边缘 `browse-session.ts:65-71,244-261` 各写同一组常量（18_000 / 220 / 90_000）。边缘那份已在 `aidcp-edge 745b754` 修成按实际待输入串（正文 + 换行 + 群聊码）算并减 1_000ms slack，云端仍只把正文传给预算函数（同文件 :367-370）。于是两侧现在朝相反方向漂：**当派生值已超出 28s 下限（即长评论）且后缀长度 ≥ 4 个字符时**（`220 × (后缀长度 + 1) > 1_000`），边缘的命令预算大于云端的等待窗口，云端会先判超时——短评论两侧都夹在下限上、边缘因减 slack 仍先返回，不受影响。

## Goals / Non-Goals

**Goals**

- 让命令清单成为被机械检查的契约：声明的回执、请求契约、效果与取消语义都能在测试期与实现对上，声明层已有的缺口因此当场暴露。
- 让命令词表的一致性检查从引擎自己的类型穷举导出，而不是从一份手写数组导出。
- 消除跨语言双写常量的自杀式失败模式：提交窗口预算单一事实源，不一致在构建/测试期失败而非运行期终止引擎。
- 让能力握手覆盖真正被执行的页面规则，使「新二进制 + 旧规则」「旧二进制 + 新规则源」都不可能悄悄通过。
- 让引擎进程死亡后仍能被结束会话这一动作真正清掉，下一次开始重建引擎。
- 让重连绑定回被准入的那一个分身，并让重连后的重试留在同一条绝对截止线内。
- 让导航瞬间的空根、各平台的解码失败、以及焦点守卫的两类不同原因都有可归因的诚实结论。
- 让 Facebook 评论提交预算只算一次并传输。

**Non-Goals**

- 不改 Cloud↔Edge 协议 v2 的消息类型集合、动作名口径与命令映射。
- 不改风控状态机、配额档位、节奏系数中心值。
- 不改任何 Facebook / 小红书 / 微信的平台行为语义（点赞、加群、发帖、评论的选目标与提交编排一律不动）。
- 不引入双跑、影子执行或 JavaScript 回退路径——迁移已明确否掉。
- 不做部署、不出安装包、不做真机写动作验收。
- 不改 `openspec/specs/native-page-engine/`（只读探针期规格）。

## Decisions

### 1. 回执列变成对账断言，而不是先去逐条修实现

先建立「声明 ↔ 实际可发回执」的机械对账，让所有缺口一次性列出来；再按对账结果逐条裁决是补发出还是改声明。

被否决的替代：直接去改 `note_open` 让它多发一条动作完成回执。否决理由是——这只修了被点名的那一条，其余同构条目（`page_scroll` / `feed_refresh` / `search_execute` / `note_close` / `navigation_back` / `profile_open` / 各 `notification_*` 都声明了两条回执）继续留在原地，而且下一条新命令照样能写一个发不出的声明。对账断言是唯一一条能机械抓住其余多条的守卫。

被否决的替代二：删掉 `receipts` 列，承认它只是文档。否决理由是——这一列是能力摘要的输入（`build.rs:19-21` 哈希整份清单），删掉等于把握手的语义面又缩小一圈；而且它已经正确记录了云端角色期望的回执，是现成的事实源。

### 2. 词表一致性检查从枚举导出

把 `PRODUCTION_COMMAND_KINDS` 从「与清单比对的一方」降为「由枚举穷举生成/校验的派生物」，并要求枚举里不进清单的变体必须进一张有断言的显式排除表（当前只有页面探测一条）。

被否决的替代：把页面探测补进清单了事。否决理由是——它不解决「测试名声称比枚举、实际比数组」这个结构问题，下一个新增变体照样可以只加枚举不加数组、测试照样绿。

### 3. 提交窗口预算改为宿主权威 + 单一事实源

引擎按标签请求窗口，预算由宿主给出或由两侧共同读取的构建期产物（命令清单）给出；引擎侧不再独立写死一份数字并让宿主做相等断言。运行期若仍出现标签未知或预算与事实源不符，宿主 MUST 以可归因的契约违规结论处理，MUST NOT 以匿名「协议非法」把整个引擎终止。

被否决的替代一：保留双写 + 相等断言，只补一个 Rust 单测。否决理由是——Rust 测试与 TypeScript 常量之间仍无联系，且危害不在「没测到」而在「失败姿势」：一个纯节奏调优的改动会在按下按钮前杀掉引擎，随后被上报成一条普通失败并让整个环境砖化。

被否决的替代二：干脆去掉相等断言，宿主无条件接受引擎报来的预算。否决理由是——那会让引擎侧一个笔误直接放大成不受控的写保护窗口，宿主对不可逆写的保护时长就失去了上限。保留上限、去掉双写，才两头都成立。

### 4. 产物新鲜度整片让给 `enforce-native-engine-artifact-gates`，本 change 不做

起草期确实在代码里坐实了这条缺口：能力摘要只对命令清单一个 JSON 求哈希（`native/page-engine/build.rs:19-21`），页面规则源只进 `rerun-if-changed`、不进摘要；引擎版本取 `CARGO_PKG_VERSION`，`Cargo.toml:3` 恒为 `0.1.0`；开发态 `scripts/build-native-page-engine.mjs` 的 `verify()` 只做产物自洽（二进制对自己的校验文件、清单字段对 Cargo 版本与命令清单摘要），没有一项与规则源码新鲜度相关，而 `scripts/ensure-native-page-engine-dev.mjs:19-27` 是「校验通过就不重编」；实测自 2026-07-22 起规则目录 10 次提交、命令清单 4 次提交。命令清单摘要还被硬编码进 Electron 侧产物校验器（`src/electron/native-page-engine-artifact.cjs:19`，当前值与实测 `shasum` 一致）。

但并行 change `enforce-native-engine-artifact-gates` 已经拥有这整片，且给出的方案更完整：它在暂存清单里另记一份**由引擎源码输入导出**的摘要（Rust 源、规则分片、有序清单、构建脚本、命令清单），验证时从工作区重算比对，并明确写了「MUST NOT 仅依赖产物自身校验和 / 产物自身清单 / crate 版本号 / 不随实现改动变化的能力摘要」，同时覆盖开发态重编判据与 Electron 侧字段校验。两者要改的是同一批文件（`build.rs`、两个构建脚本、Electron 校验器），并行必撞。

因此本 change **不写**这条要求、不动这四个文件。留一条集成后的交叉核对：若该 change 落地后，源码摘要仍未进入宿主与引擎之间的启动握手比对（`src/native-page-engine/client.ts:481-489` 现比四项：引擎版本、平台适配器版本、适配器表、能力摘要），则单开后续 change 承接「运行期握手也要能证明规则新鲜度」。

被否决的替代：本 change 也写一份、集成期再合。否决理由是——两份 delta 会在同一批构建期文件上产生真冲突，而这类冲突的解决只能靠人逐行判断，收益为零。

### 5. 结束会话的收尾放进 `finally`，并给会话句柄加存活判据

结束会话的本地收尾必须无论该命令成功失败都执行；会话缓存在返回句柄前必须确认底层传输仍活着，已死则丢弃并重建。

被否决的替代：只在云端加「结束会话失败就重发一次」。否决理由是——重发打的是同一个已死的会话句柄，第二次同样失败；自愈入口被堵死这一点没有变。

被否决的替代二：让引擎退出事件直接触发整个核心进程重启。否决理由是——同机多环境并行时一个环境的引擎死会牵连其余环境，且与既有的浏览器槽位/租约语义冲突。收敛到会话粒度即可。

### 6. 重连重新取端点并要求身份证据

重连时向浏览器提供方重新解析端点，而不是复用建会话那一次的快照；目标选择的判据除平台与端口外，必须包含能证明这是被准入的那个分身的证据。拿不到身份证据时诚实失败并交回宿主处理，MUST NOT 退化成「端口对上就接管」。

被否决的替代：把端点缓存加个 TTL。否决理由是——TTL 不解决身份问题，只是把错投的窗口改窄；而错投的后果是在真实账号上留下平台可见行为，窄窗口不是可接受的残余风险等级。

关于身份证据的具体载体（分身标识、用户目录、浏览器实例标识或提供方回传的 profile 标识）留待实装期在浏览器提供方一侧确定；本规格只约束「必须有可验证的身份证据，且无证据时不接管」。现成的候选载体已在代码里存在：AdsPower provider 认领失联浏览器时用的判据是「缓存目录名以 `<profileId>_` 打头 + 该目录下的 `DevToolsActivePort` 标记」（`aidcp-edge/src/cdp/browser-provider.ts:728-745`），即「端口 ↔ 分身」的绑定证据本机已可取；调试端口本身由 AdsPower 按 profile 动态返回（同文件 :426-468）。跨环境错投的真实发生概率取决于指纹浏览器的端口分配策略与浏览器重启频率，**未实测**，已列入真机验收项。

### 7. 重连后的重试留在同一条绝对截止线内

重连后的重试与首跑共用同一条绝对截止线；超过即释放唯一命令槽位并回超时。

被否决的替代：给重试单独一份超时预算。否决理由是——那会让总耗时变成「首跑预算 + 重试预算」，宿主早已在预算过后放弃等待且不发取消，期间新命令一律被顶回，等于把槽位占死的时间加倍。

### 8. 取根、解码诊断、焦点守卫按「诚实归因」统一

取根拿不到有效根时返回诚实的未开始理由，不把空根交给遍历；解码诊断从 Facebook 扩到小红书与页面探测；焦点守卫区分「守卫求值本身失败/输出缺失」与「焦点确实丢了」两类结论（通道失败当前已单独归类，保持不变）。

被否决的替代：给 5 处 `|| document.body` 各打一个空判补丁。否决理由是——上面的实读已经说明其中 4 处的下游本来就是空安全的，逐处补丁既是空转、又漏掉真正的结构缺口：取用函数（`00-shared.js:13-19`）对空 root 零防护，下一处新写的根解析照样能塌。闸要落在取用层；真正无空判的那一处（`20-feed.js:253` 的 `currentDetail`）另行按「取不到有效根即诚实未开始」改。

### 9. 评论预算传输而非重算

由一侧按「实际会被打进编辑器的完整串」算出预算并随命令传输，另一侧据传输值派生自己的等待窗口。

被否决的替代：两侧都改成算完整串。否决理由是——公式仍是两份，下一次改常量还是要记得改两处；而这一次的实证正是「边缘改了、云端没改」，双写的代价已经付过一次。

## 风险与回滚

- **[回执对账暴露的缺口比预期多]** 对账断言一开就红，可能牵出多条实现修改。缓解：允许以显式、有理由、逐条登记的方式先冻结少量已知缺口，但冻结清单只许下降、且必须在本 change 的 tasks 里逐条写明消除动作。
- **[身份证据在某些提供方模式下取不到]** 自建（self）模式与托管指纹浏览器模式的可用证据不同。缓解：规格只要求「无证据不接管」，不规定证据载体；取不到证据时诚实失败优于错投。
- **[重连重试纳入截止线后，慢网下观察态加群成功率下降]** 原先超预算仍在跑的那部分现在会被截断。缓解：截断结论是诚实超时而非假成功；若真机显示成功率明显下降，正确的动作是调该命令的预算中心值，而不是放开截止线。
- **回滚**：本 change 全部改动落在边缘构建期/测试期与两个进程的本地协议层，加上云端一处预算传输，可按提交粒度独立回滚；无数据迁移、无协议消息增删、无部署动作。

## 与其他并行 change 的边界

- **不碰** `openspec/specs/` 下任何文件（本 change 只在自己的 `changes/` 目录内产出 delta）。
- **不碰** `openspec/specs/native-page-engine/`——那是可行性验证期的只读探针规格（opt-in / read-only），生产运行时行为不进那里。
- **不 MODIFIED 尚未归档的能力**：`native-page-engine-production`（属 `native-page-engine-production-cutover`）、`native-page-engine-platform-coverage`（属 `native-page-engine-platform-cutover`）、`native-facebook-capability-runtime`（属 `preserve-native-facebook-capability-boundaries`）均只活在活跃 change 里，本 change 一律不引用为 MODIFIED，相关约束改由新增能力 `native-engine-runtime-contracts` 承接。
  - 特别地，`native-page-engine-production-cutover` 已 ADDED 一条「Browser and Native recovery ownership MUST remain distinct」，规定 Native 可在提供方端点健康时自行刷新目标重连。本 change 的重连要求是它的**细化**（重连时重新解析端点、并要求身份证据），不与之矛盾，也不去编辑它；两者合并顺序由集成期决定，若该 change 先归档，本 change 的对应要求可在实装期再评估是否改写为对它的 MODIFIED。
- **只 MODIFIED 一条真实存在的要求**：`pluggable-browser-provider` 的「CDP 接入层在 provider 之下保持不变」。`native-page-engine-production-cutover` 对同一能力只做 ADDED（两条新要求），标题不重叠，delta 可并存。
- **不改 `edge-task-execution-coordination`**：本 change 涉及的是 Native 引擎进程内的单命令槽位，不是任务级租约；`native-page-engine-platform-cutover` 已在该能力上有 ADDED delta，避免撞车。
- **热点文件避让**：不动两份 `protocol.ts`、不动 `aidcp-cloud/src/comm/command-bridge.ts` 的动作映射、不动角色注册（`event-bus/types.ts` 的 `RoleName`、`src/config/role-catalog.ts`）、不动 `src/risk/risk-state-machine.ts`。
- **与 Facebook 行为类 change 的边界**：`restore-native-facebook-*`、`preserve-native-facebook-capability-boundaries`、`facebook-*` 系列拥有平台行为语义；本 change 只动 `facebook-router` 的取根兜底与共享取用函数的空防护，不改任何选目标、提交、后验编排。若集成时与它们在 `20-feed.js` / `40-group-join.js` 冲突，以行为类 change 的编排为准，本 change 只保留空防护。
- **与 `enforce-native-engine-artifact-gates` 的边界**：产物新鲜度、明文防泄漏清单、分片拼接完整性、Rust 工具链闸、打包平台解析、Electron 侧产物校验，全部归它；本 change 不动 `native/page-engine/build.rs`、`scripts/build-native-page-engine.mjs`、`scripts/ensure-native-page-engine-dev.mjs`、`scripts/after-pack.cjs`、`scripts/prune-production-dist.mjs`、`src/electron/native-page-engine-artifact.cjs`、`package.json` 的打包配置。本 change 唯一与它相邻的动作是往命令清单里加/改声明与排除表，那属于清单内容而非闸门。
- **与 `restore-native-xiaohongshu-session-guards` 的边界**：该 change 拥有小红书侧的阻断观测装配、提交窗口下沉、验证码取证透传、以及**逐命令回执诊断与会话生命周期诊断**的平台中立化。本 change 只碰**结果解码入口**的有界诊断（`native/page-engine/src/xhs.rs`、`src/probe.rs` 的 `result_from_cdp`），不碰回执级与会话级诊断。若该 change 先落地并已把解码入口一并覆盖，本 change 的对应要求即被吸收，实装期核对后从 tasks 里划掉而非重复实现。
- **与 `restore-native-xiaohongshu-action-honesty` 的边界**：该 change 拥有小红书评论「正文 + 串码」的合成文本与回读校验；本 change 只碰 Facebook 评论提交**预算**的计算与传输，不碰任何平台的文本合成与回读语义。
- **与 `restore-native-actuation-humanization-and-locating` 的边界**：该 change 拥有指针 / 滚轮 / 节奏原语与定位三道闸；本 change 只碰逐字输入焦点守卫的**失败归因分类**，不改其时序、不改任何拟人参数、不动指针原语。
- **与 `add-managed-automation-runtime` 的关系**：该 change 在运行模型层取代/收编约 60 份已上线 spec，其处置映射表见其 `design.md` §24。本 change 处理的是边缘引擎进程的本地契约与故障韧性，不属于发布/评论/浏览/排期/风控配额/仲裁/客户投影这几类被点名的能力面；实装前仍应复核一次该映射表。

## Open Questions

- 身份证据的载体在托管指纹浏览器模式下具体取哪一项，需要在浏览器提供方一侧确认可稳定获取；未确认前不得把某一项写死进规格。
- 评论预算的传输方向（云端算好下发，还是边缘算好回报）取决于云端是否需要在下发前就知道自己的等待窗口；两者都能消除双写，需在实装期择一并只保留一处公式。
