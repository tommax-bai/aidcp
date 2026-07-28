## Why

小红书在 2026-07-22（aidcp-edge `317cd47`）整体切到 Native Page Engine 后，浏览 / 搜索 / 开笔记 / 点赞收藏关注 / 评论 / 通知巡视 / 发布原子全部由一份 290 行的页内路由脚本一次性求值完成（`aidcp-edge/native/page-engine/src/xhs-command-router.js`）。Rust 侧的小红书分发只对验证码抓取 / 点击、带 URL 的开帖、读自身主页、搜索、上传图片、进入发布入口、定时稿抓取与对账这几支写了平台语义，其余一律落到 `native/page-engine/src/engine.rs:708` 的通配求值分支。Facebook 侧同形态的能力压平已由一批 restore / repair change 逐条修回（`restore-native-facebook-*` 六个中五个 tasks 全勾，另有归档的 `archive/2026-07-26-restore-native-facebook-behavior-parity`），小红书侧此前没有任何**页面动作**平价 change，也没有与 `native-facebook-behavior-parity` 对等的平价规格（同批另有 `restore-native-xiaohongshu-session-guards` 处理宿主侧监测体与提交窗口，不碰页面规则，边界见 design D6）。

两条已在代码里坐实的红线击穿最紧急：① 评论只提交正文一个字段（`xhs-command-router.js:236`），云端随评论下发、并已进人审终稿的联系方式串码（`aidcp-cloud/src/comment-agent/edge-steps.ts:341-352`、Rust 侧 `command.rs:296` 已声明并校验）在最后一步静默消失，直接违反「审=发」，而 Facebook 侧同一字段是正确拼接的（`native/page-engine/src/facebook/comment.rs:72-79`）；② 开帖成功判据是「地址里还能解析出笔记 id」（`xhs-command-router.js:194`；同一分支的入口 `:188` 更进一步——地址里有目标 id 即判「已在详情页」，连点击都不发就直接回一份详情），本仓真机文档记录的裸链导航错误页恰恰仍带这个 id（`aidcp-edge/docs/xhs-layout-states.md:59-60`），一次失败开帖会带着空壳详情被上报，云端在 `aidcp-cloud/src/comm/handler.ts:667-690` 不判空壳、照常记一次浏览并扣配额。

另有五类同源退化：看图命令不产动作回执（`xhs-command-router.js:206-209`）使云端深读等待表永久挂起（`aidcp-cloud/src/agents/deep-reader.ts:64-73,122-124` 无超时）；返回列表回执恒 `ok:true`（`:203-204`）；滚动评论区回执同样恒 `ok:true`、真实位移只塞进一个观测字段、评论条数直接回报请求值（`:211-213`），云端据此把「已读评论数」记成 1（`aidcp-cloud/src/agents/comment-reviewer.ts:106-110` 读 `ok` 后按 reason 缺省取 1）；点赞/收藏/关注的控件定位退成「文本含该词的第一个元素」+ 固定 450ms 单次采样 + 「已」字兜底（`:145`、`:232-233`）；通知巡视的去重键、正文与行选择器三处一起退回真机校准之前（`:125-134`，旧实现与其原因注释见 `317cd47^:src/browse/notification-monitor.ts:126-170`）。

## What Changes

- 为小红书建立与 Facebook 对等的 Native 行为平价规格，明确「命令→定位→提交→同目标后验→终局分类」在小红书侧的可验证契约。
- **BREAKING** 评论提交文本改为「正文 + 联系方式串码」的完整合成文本，回读校验覆盖合成后的完整文本；合成失败或回读不含串码时在提交前诚实失败（当前行为是静默丢弃串码后照常发出）。
- 开帖成功改为必须有正面详情证据（详情容器 + 非空正文/图片证据），错误页与空壳详情一律不上报详情、不产生浏览计数；开帖执行方式按真机结论选定，不以「地址里有笔记 id」作为唯一判据。
- 看图命令改为返回可度量的动作回执（实际前进张数或 `no_target`），每一步重新解析翻页控件并校验图序真前进；不再以「详情刷新」输出充当回执，同时保证翻页过程中看到的图片证据仍能到达云端（当前那条「详情刷新」是精选库参考图刷新与灵感池图片更新的唯一来源，改回执时不得把它一并弄丢）。
- 返回列表与滚动评论区的回执 `ok` 改为反映真实的页面结果，不再硬编码为真；评论区滚动按实测位移与实测候选条数回报，不得把请求值当实测值。
- 点赞 / 收藏 / 关注改为结构化定位（互动条内具名控件、排除反向与汇总控件）+ 有界轮询等待状态翻转，未翻转诚实回不确定；不再以控件文本含「已」作为成功兜底。
- 通知巡视的行选择器、正文抽取、去重键回到真机校准契约：行按已标定容器结构选取、正文只取正文容器且缺失即空串、去重键必须逐条稳定且不得使用按用户折叠的主页链。
- v1 兼容分支（`plan_execute` 的滚动步骤）不得再无测量就写「已确认」：先判定是否仍有活跃产出方，无则连同分支一并删除，判不清或仍有产出方则改为按实测位移回报（判据与依据见 design D5 与 tasks 2.8）。
- 补齐小红书 Native 的行为级回归测试，并修掉「测试里把元素几何全局钉死、可见性判断恒真」这类使保护失效的夹具写法。
- 不改协议 v2、不改云端概率 / 配额 / 风控记账、不改命令信封与结果形状。

## Capabilities

### New Capabilities

- `native-xiaohongshu-behavior-parity`: 定义 Native-only 小红书的命令边界、目标绑定、提交与后验证据、终局语义与回归门，与 `native-facebook-behavior-parity` 对等。

### Modified Capabilities

- `notification-monitoring`: 收紧「稳定 itemKey」的定义——去重键必须逐条稳定、不得是按发送者折叠的主页链，缺失时留空交由云端回退键，且回退键所依赖的正文不得含时间等每次巡视都会变的串。

## Impact

- `aidcp-edge/native/page-engine/src/xhs-command-router.js`（本 change 的单写区）
- `aidcp-edge/native/page-engine/src/engine.rs`（小红书分发分支——**与 `restore-native-xiaohongshu-session-guards` 共写该文件的小红书执行入口，集成需串行**）
- `aidcp-edge/test/native-page-engine/`（新增小红书行为平价测试，修 `router-contract.test.ts:37-39` 的几何钉死夹具；该目录同批另有 change 增删文件，按文件名分区）
- 云端 `aidcp-cloud/src/agents/deep-reader.ts` 的等待表超时兜底（仅在真机确认深读挂起后作为独立跟进项，本 change 不含实装）
- 覆盖漏洞收口（2026-07-28）新增的可能落点，按 tasks 2.9 / 2.11 的机制二选一确定，均需与 `restore-native-xiaohongshu-session-guards` 对账（tasks 6.5）：`aidcp-edge/native/page-engine/src/xhs-page-probe.js` 与 `probe.rs`（未读角标读数若挂在页面探针上，`StructuralSignals` 带 `deny_unknown_fields`，字段须两处同步）、`native/page-engine/src/model.rs` 与 `xhs.rs`（回执若要携带通知项）、`aidcp-edge/src/native-page-engine/browse-session.ts` 的输出路由（回执若由宿主补发）
- 未读检出的**宿主侧**周期装配与未读信号发送方不在本 change：已具名交接给 `restore-native-xiaohongshu-session-guards`（见 design.md 交接表与 tasks 4.5 / 4.6），承接方未落地前本 change 的通知类修复在生产上不通电
- 本 change **只产出规格**，不含代码实装、不含部署、不含 Edge 安装包打包 / 签名 / 发版、不含任何真机写动作，也不改 `openspec/specs/` 下任何已合并 spec 文件。
