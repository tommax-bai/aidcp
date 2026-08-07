## Why

词汇蓝图批 5（`docs/edge-command-grammar.md` §6.2「互动平台化 + 按对象改名」、§6.3 批次表）：5 条互动命令加平台段并按**对象**改名（对象＝note / video / user / comment）。这是 CLAUDE.md §2 点名的**协议第 5 处同步点**（动作关联键）所在的一批。

前置核实（2026-08-07，两仓全量消费面探查，修正交接文档一处关键预判）：

- **关联键值不动（推翻「批 5 必须动值」的预判）**。全量探查坐实：关联键值（`like`/`collect`/`follow`/`comment`/`comment_like`）与风控动作名 `RISK_ACTIONS` **逐字同名是设计而非巧合**（automation `protocol.ts:617` 明写「可直读、零映射」），耦合链＝`handler.ts:1086` 直接强转入风控 outbox → kernel 跨仓枚举（`RISK_ACTIONS` / `NoteScopedAction`）→ 9 张 DB CHECK 约束 + 历史行。改值＝kernel 出版本 + DB 迁移回填 + ~120 消费点，是独立 change 的体量，且对「CLI 层清晰」目标零收益——语法管协议词汇，不管云端内部记账词汇。**多个新名映回同一个值完全成立**（`facebook.video.like → 'like'`），角色关联、风控记账、冷却、预算、去重、面板日用量全部零改动。
- **FB 视频点赞的对象事实**：0.25 伯并利概率是云端决策（Reels 随机点赞三道闸，`role-dispatcher.ts:3914/4034` 两路径）；边缘现按运行期 `listMode` 内部分流（Reels 执行器 vs 帖级执行器）。拆 `facebook.video.like` 后改为**名字声明对象、执行点核对现场**（批 4 scroll 拆面的同一模式）。
- **FB follow 是 Reels 绑定执行器**（`noteId`＝当前活动 Reel，Feed/主页关注 `capability_unsupported`），对象仍是**用户**（作者），改名 `facebook.user.follow` 不改执行语义。
- **FB 无收藏、无评论点赞**：`FACEBOOK_UNSUPPORTED_COMMANDS` 现役恰剩这两条共享名（批 4 已留「批 5 归零删除」注记）；改名后 `xiaohongshu.note.collect` / `xiaohongshu.comment.like` 由平台段闸结构性拒收，手抄拒集删除。退役 FB 会话里平行的两个 `case` 臂（`facebook-session.ts:617-618`）一并处理，防两份清单分叉。
- **两个绕过 bridge 的直发点**：comment-agent `edge-steps.ts:352`（xhs）与 `facebook-edge-steps.ts:419`（FB）直接 `makeEnvelope('interaction.comment', …)`——bridge 改完这两处不会报错，会静默发旧名，必须逐处改。
- **bridge 互动零回归网**：四个直测 `edgeCommandToEnvelope` 的测试文件没有一个覆盖互动 5 条，本批补齐。

## What Changes

- **5 条旧名 → 9 条平台段对象名**（xiaohongshu 5 + facebook 4，名表见 design §1）；协议消息 103 → 107，两份登记表 52 → 56。直接切换：旧名从两份协议穷举表直接删，无别名、无墓碑（语法规格第 6 要求）。
- **`interaction.like` 按对象拆**：`{p}.note.like` + `facebook.video.like`（不按位置拆）。云端 `EdgeCommand` 增可选对象维（like 专用，`'note'|'video'`，缺省 note）；Reels 随机点赞两路径显式标 video；边缘 mapper 从信封名解析对象下传，引擎按名声明分派执行器、现场不符诚实失败（MUST NOT 静默改执行另一对象的执行器）。
- **动作关联键：只换键、值不动**（本批最重要决策，见 Why）。三张表（edge `actionNames` + 退役 `FB_COMMAND_ACTION_NAMES` + cloud `LEGACY_ACTION_COMPLETION_ALIASES`）键 5 旧名 → 9 新名，值原样映回既有五词。所有按值判定的逻辑（风控记账、冷却、预算、`noRecoverScroll`、去重坑、comment-agent 等待谓词）零改动。
- **云端 bridge：互动 5 条从硬编码直返迁入 (action, platform[, object]) 穷举组合表**（批 4 组合表的扩展），不存在组合（如 xiaohongshu+video、facebook+collect）响亮 throw。
- **`FACEBOOK_UNSUPPORTED_COMMANDS` 归零删除**（兑现批 4 注记）+ 退役 FB 会话平行 case 臂同步处理。
- **新增控制仓对账闸 `scripts/action-key-parity`**（交接文档要求的关联键变异验证的跨仓半边）：语义解析三张关联键表，键集与取值逐条对账，形态同 `operation-registry-parity`。仓内半边＝穷举断言 + bridge 互动用例补齐 + 互动族禁用 `?? type` 静默回落。
- 引擎侧单 kind 不拆（`interaction_like` 等 5 个 nativeKind 与 timing/postconditions 表不动）；manifest 5 条 `edgeTypes[]` 换 9 新名 → 重建重钉 capabilityDigest 五位点（含生产常量）。
- 顺手清账：`ui-events.cjs` 批 4 遗留的 4 条失效命令名正则（`page.scroll` / `note.open` / `note.scroll_comments` / `profile.open` 旧形）与本批 `interaction.comment` 正则一并按新名修复。
- `docs/protocol.md` §2 表与载荷节、bridge 映射段、`docs/edge-command-grammar.md` 批 5 行随改同步。
- **BREAKING（内部协议，预期内）**：与批 1–4 同一个未出包切换窗口（dev 车队已停摆待装机，批 5 不新增停摆面）；部署后旧客户端对 9 新名 fail-closed 拒收在执行前，无重复对外写入风险。出包仍待用户显式触发，本批完成后并入同一个包提请。

## Capabilities

### New Capabilities
（无）

### Modified Capabilities

手写 delta（语义真变）：
- `native-facebook-behavior-parity`: FB 对 collect / comment-like 的拒收机制从「共享名返回 `capability_unsupported`」换为「平台段闸结构性拒收 `xiaohongshu.*` 名」——批 4 已为深读/巡视/主页做过的翻转补上最后两条；`interaction.collect` / `interaction.like_comment` 字面从规格消失。
- `facebook-reels-browse`: Reels 点赞命令名化为 `facebook.video.like`；对象路由从「边缘按运行期 listMode 自判」变为「名字声明对象 + 执行点核对现场」，对象不符诚实拒绝。

机械改名 delta（纯名字提及，语义零变）：其余引用旧名的 capability（grep 实测 12 个：author-profile-visit、command-pacing、comment-interaction、facebook-note-scoped-targeting、facebook-reels-inline-follow、facebook-scheduled-comment、interaction-cooldown、interaction-risk-gating、read-to-write-note-lane 等）在集成期脚本化生成、归档前对当时最新 spec 文本重生成一遍。**delta 生成的同形异义红线**：`interaction.completed` / `interaction.skipped` / `interaction.occurred` 是 EventBus 事件名不改；`interaction.sync.*` / `interaction.reply.*` / `interaction.offboard.*` / `interaction.auth.*` / `interaction.browser.control` / `interaction.runtime.controls` 是 IM 族（批 6）不改；`action∈{like,collect,follow,comment,comment_like}` 等关联键**值**不改。

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`、`src/client/{operation-registry,edge-client,command-diagnostics}.ts`、`src/native-page-engine/{command-mapper,browse-session}.ts`、退役但仍编译的 `src/browse/browse-session.ts` 与 `src/facebook/{facebook-session,comment-handler}.ts`（含 `FB_COMMAND_ACTION_NAMES`）、`src/electron/renderer/renderer.js`、`src/electron/ui-events.cjs`、`src/electron/native-page-engine-artifact.cjs`（digest 常量）、`native/page-engine/command-manifest.json` + fb/xhs 路由 JS 的对象分派、`test/acceptance/protocol-contract.test.ts`（计数 103→107）+ 约 17 个测试文件。
- `aidcp-automation`：`src/comm/{protocol,command-bridge,operation-registry,handler}.ts`、`src/orchestrator/role-dispatcher.ts`（发送点标对象）、`src/comment-agent/{edge-steps,facebook-edge-steps}.ts` 两个直发点 + 测试（protocol-contract 计数同步、bridge 互动用例新增、comment-scheduler 系列约 40 处 `interaction.comment` 字面）。
- 控制仓：`docs/protocol.md`、`docs/edge-command-grammar.md`、新脚本 `scripts/action-key-parity`、spec delta 两批。
- **并行注意**：`restore-native-facebook-residual-parity` 与 `blocking-overlay-dom-capture` 在飞（动 edge native 文件）；批 7（`normalize-nonplatform-vocabulary`）与本批并行开发、**集成串行且本批先落**（两批都动两份 protocol.ts 热区，后到者 rebase）。热点单写：两份 protocol.ts、登记表、bridge、白名单、三张关联键表本批独占。
- **不出包不算完**：并入批 1–4 既有的未出包窗口（真机簇 148/149/152 同包），真机验收项登记 backlog 簇 153。
