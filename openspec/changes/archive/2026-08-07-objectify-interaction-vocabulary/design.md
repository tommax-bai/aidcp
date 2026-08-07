# Design — 词汇批 5：互动平台化 + 按对象改名

## 1. 名表（5 旧 → 9 新，唯一权威）

平台段取值＝代码平台枚举 `PlatformId`（`xiaohongshu` / `facebook`），与批 2/4 两道平台段闸同源同值。对象段＝该动作真正作用的对象类型（note＝内容单元 / video＝视频对象 / user＝用户 / comment＝评论）。

| 旧名 | xiaohongshu | facebook | 关联键值（不变） | 依据 |
| --- | --- | --- | --- | --- |
| `interaction.like` | `xiaohongshu.note.like` | `facebook.note.like`<br>`facebook.video.like` | `like` | 按对象拆不按位置拆；FB 视频（Reels）已有独立概率策略与独立执行器（reels-reader vs like-executor），xhs 视频笔记仍是 note 对象 |
| `interaction.collect` | `xiaohongshu.note.collect` | — | `collect` | FB 无收藏（原手抄拒集成员） |
| `interaction.follow` | `xiaohongshu.user.follow` | `facebook.user.follow` | `follow` | 对象＝用户；FB 执行语义不变（Reels 绑定：`noteId`＝当前活动 Reel，Feed/主页关注仍 `capability_unsupported`） |
| `interaction.comment` | `xiaohongshu.note.comment` | `facebook.note.comment` | `comment` | 对象＝内容单元；载荷不变（`text`/`groupChatCode`/`fastReturnToFeed`） |
| `interaction.like_comment` | `xiaohongshu.comment.like` | — | `comment_like` | FB 无评论点赞（原手抄拒集成员）；名序反转（`like_comment`→`comment.like`）随对象编址消失，关联键值保留历史形 `comment_like` |

协议消息 103 → **107**；两份操作登记表 52 → **56**（描述符逐条继承旧值，均 `pageAutomation()` 留痕档）。载荷接口共享保留（`InteractionLikePayload` 等接口名不动、多名共用，同批 4 处理 `PageScrollPayload` 的方式）。

## 2. 关联键值不动（本批最重要决策，推翻交接预判）

`action.completed.action` 的**值命名空间本批零改动**。证据链（2026-08-07 全量探查）：

- 值与风控动作名 `RISK_ACTIONS`（kernel `risk-contract`）逐字同名**是设计**：automation `protocol.ts:617` 明写「键名与风控动作名逐字同名，故可直读、零映射」；`handler.ts:1086` `enqueueRiskFact(..., result.action as RiskAction)` 直接强转。
- 值被钉死在：kernel 两个跨仓枚举（`RISK_ACTIONS` / `NoteScopedAction`）、9 张 DB CHECK 约束（migrations 0002/0003/0019/0039/0055/0061 + pg-risk-store DDL 四处 + interaction-feed-store）、`interaction-guard` 去重键内插、`daily-usage` 面板八键、约 120 个消费点。
- 改值＝独立 change 体量（kernel 出版 + DB 迁移回填历史行），对「CLI 层清晰」零收益。语法管协议词汇；关联键是云端内部记账词汇，CLAUDE.md §2 本就写明「该字段是角色关联键，不是协议消息名」——两个命名空间**本该脱钩**，本批把脱钩坐实而非拉平。

**落法**：三张表只换键（5 旧信封名 → 9 新信封名）、值原样：

- edge `command-mapper.ts` `actionNames`：9 新键 → `like`×3 / `collect` / `follow`×2 / `comment`×2 / `comment_like`。
- edge `facebook-session.ts` `FB_COMMAND_ACTION_NAMES`（退役但仍测试）：FB 4 新键同法。
- cloud `handler.ts` `LEGACY_ACTION_COMPLETION_ALIASES`：键 22 → 26 条（删 5 加 9），值不动。

`EdgeCommand.action` 联合类型（`role-dispatcher.ts:724`）与全部发送/回执消费点（`sendNoteScopedCommand('like',…)`、`consumeBudget`、`markCooldown`、`noRecoverScroll`、`interactionRetry`、comment-agent `d.action==='comment'` 谓词、`interaction-guard`）**零改动**。

## 3. like 的对象维：名字声明、执行点核对（决策）

批 4 scroll 拆面的同一模式，对象维只在 like 一条上存在：

- **云端**：`EdgeCommand` 增可选 `likeObject?: 'note' | 'video'`（仅 `action:'like'` 有意义；命名避开批 4 的 `surface`——对象≠位置）。Reels 随机点赞两路径（`role-dispatcher.ts:3914/4034`）显式标 `video`；FB 消费/规则模式 feed 点赞与 xhs 点赞不标（缺省 note）。bridge 组合表：`('like', facebook, video) → facebook.video.like`、`('like', facebook, note|缺省) → facebook.note.like`、`('like', xiaohongshu, note|缺省) → xiaohongshu.note.like`；`('like', xiaohongshu, video)`、`('collect'|'comment_like', facebook, …)` 等不存在组合响亮 throw（结构性不可达的后备，非第二道支持闸）。
- **边缘**：TS mapper 从信封名解析 (platform, object)，object 以参数下传引擎；Rust kind 仍单条 `interaction_like`（timing / postconditions / manifest 算术三张 kind 表全不动）。FB 引擎路由：`facebook.video.like` → Reels 执行路径（现场核对确在视频/Reels 上，不符→诚实失败，MUST NOT 静默转帖级执行器）；`facebook.note.like` 对称。原「按 `listMode` 运行期自判」的分流退役——名字声明取代现场猜测，执行点保留核对权（语法第 1、5 条）。
- xhs 路由：单执行器不变，拆名零行为改动。

## 4. FACEBOOK_UNSUPPORTED_COMMANDS 归零删除（兑现批 4 注记）

- `native-page-engine/browse-session.ts:342-345` 的 Set（恰剩 `interaction.collect` / `interaction.like_comment`）与其唯一生产消费点（`:831`）删除——collect / comment-like 改名后只有 `xiaohongshu.` 前缀形，FB 会话在入口平台段闸即拒（`platform_mismatch`），语义等价且由名表推导。
- 退役 FB 会话平行清单（`facebook-session.ts:617-618` 两个 `case` → `reportUnsupportedCommand`）：旧名死、新名是 `xiaohongshu.*` 结构性到不了 FB 会话——case 臂随改名删除，防两份清单分叉。
- 测试消费点 `pacing-consumption.test.ts:15,191`（用该 Set 推导测试平台）改为按名表前缀推导。

## 5. 关联键对账闸与变异验证（交接前置第 2 件事）

**跨仓半边＝控制仓新脚本 `scripts/action-key-parity`**（形态同 `operation-registry-parity`：语义解析、解析不了判失败、至少两份才算对账成立）：

- 解析三张表：edge `actionNames`、edge `FB_COMMAND_ACTION_NAMES`、automation `LEGACY_ACTION_COMPLETION_ALIASES`（派生仓存在几份查几份）。
- 断言：edge `actionNames` 与 cloud 别名表**键集相同、同键同值**；`FB_COMMAND_ACTION_NAMES` ⊆ `actionNames` 且同键同值。谁多谁少谁不同，逐条打印。

**仓内半边**：

- edge：互动族 9 条逐一断言 `nativeActionNameForCommand` 有显式表项且值正确（杀 `?? type` 静默回落——回落发生时新命令名会被当关联键发出，云端不认）；FB 表既有 21 条 parity 断言随键更新。
- automation：bridge 互动组合逐条断言（探查坐实的零回归网缺口：四个 `edgeCommandToEnvelope` 测试文件无一覆盖互动）——9 个合法组合出正确信封名、代表性非法组合 throw；别名表 26 键穷举断言。
- **变异纪律（先 commit 再变异）**：全绿 → commit → 逐项变异（删 `actionNames` 一条 / 改 `LEGACY_ACTION_COMPLETION_ALIASES` 一个值 / 删 bridge 一个组合 / 删白名单一条）→ 必须红 → `git checkout --` 复原 → 复跑回绿。批 4 教训：白名单删条首轮未被抓住才补的逐条断言，本批开工即有。

## 6. 静默失效点清单（typecheck 全程无感，逐处点名改）

| # | 位置 | 改法 |
| --- | --- | --- |
| 1 | edge `edge-client.ts:825-835` 白名单 if-链 | 5 → 9 条，逐条对名表核；路由回归断言随改 |
| 2 | comment-agent `edge-steps.ts:352` / `facebook-edge-steps.ts:419` 绕 bridge 直发 | 就地改 `xiaohongshu.note.comment` / `facebook.note.comment` |
| 3 | edge `command-diagnostics.ts` `ACTIVE_COMMAND_TYPES`（5→9）/ `FIXED_SUMMARIES`（4 条换键）/ `interaction.comment` 动态摘要分支（换双平台新名） | 三张结构逐条 |
| 4 | edge `renderer.js:2573-2577` 中文标签表 | 5 → 9 键 |
| 5 | edge `ui-events.cjs:180` `/命令: interaction\.comment/` 正则 | 换新名；**顺手修批 4 遗留 4 条失效正则**（`:136/:140/:225/:229` 的 `page.scroll`/`note.open`/`note.scroll_comments`/`profile.open` 旧形），ui-events 测试随改 |
| 6 | 引擎 JS 路由（`xhs-command-router.js:817-905`、`facebook-router/90-dispatch.js:145-197`） | kind 不改则分派臂不动；其中裸串动作名（`'like'`/`'comment'`/`'comment_like'`）是**值**、不动；`kind.replace('interaction_','')` 字符串手术因 kind 不改而无恙——但 FB like 臂要接对象参数分派（§3） |
| 7 | manifest `edgeTypes[]` 5 条目换 9 名 → digest 五位点重钉（生产常量 `native-page-engine-artifact.cjs:19` + 4 测试位点） | `node scripts/build-native-page-engine.mjs` 重建后一次换齐 |

## 7. 同形异义不改（sed 红线）

- **EventBus 事件名**：`interaction.completed` / `interaction.skipped` / `interaction.occurred`（云端内部事件，改了断浏览闭环）。
- **IM 族（批 6 的活）**：`interaction.sync.*` / `interaction.reply.*` / `interaction.offboard.*` / `interaction.auth.*` / `interaction.browser.control` / `interaction.runtime.controls` 及其全部 `Interaction*` 类型。
- **关联键值**：`like` / `collect` / `follow` / `comment` / `comment_like` 在 `action.completed`、风控、冷却、预算、去重、DB、prompt 等一切上下文（§2）。
- **能力串**：edge `driver.ts` 的 `interaction.comment.read` / `.reply` / `interaction.dm.*`（PlatformCapability，另一命名空间）。
- **nativeKind**：`interaction_like` 等 5 条（引擎内部表示，不受语法第 4 条约束）。
- **渠道名 / 任务族 / LLM 词表**：`InteractionChannel='comment'|'dm'`、`comment_batch` 委派族、appraiser prompt 的 `{"action":"like"}` 等（探查 C 类全单）。

## 8. 切换窗口与部署形态

直接切换：automation 部署 dev 后旧客户端对 9 新名 fail-closed 拒收在执行前，无重复对外写入。**dev 车队已因批 1–4 停摆待出包**，本批不新增停摆面、并入同一个包（真机簇 148/149/152 + 本批 153 同验）。部署完成即把批 5 加入出包提请；打包动作仍由用户显式触发。

## 9. 风险登记

| 风险 | 处置 |
| --- | --- |
| 机械替换撞同形异义 | §7 清单逐文件改，不做仓级 sed；`like_comment`↔`comment_like` 名序反转旧例已随对象编址消失，但历史值 `comment_like` 保留——任何「从新名推值」的脚本思路都会在 like×3→一值上翻车，表就是表、不做推导 |
| 关联键回落静默失效 | §5 仓内断言杀 `?? type` 回落；跨仓 `action-key-parity` 收口 |
| bridge 迁组合表漏直发点 | §6-2 两个直发点点名改 + 各自测试断言新名 |
| digest 五位点漏改 | 生产常量优先核（启动硬失败）；重建后五处一次换齐 |
| 并行 change 撞热区 | 本批独占两份 protocol.ts / 登记表 / bridge / 白名单 / 三张关联键表；与批 7 并行开发、集成串行且本批先落；`restore-native-facebook-residual-parity`、`blocking-overlay-dom-capture` 在飞，集成后到者 rebase |
| 计数断言散点 | 两份 protocol-contract 103→107；登记表头注计数同步 56 |
