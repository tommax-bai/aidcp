# Design — 词汇批 6b：发布段化 + back/close 合并 + `task.*` + kernel v0.1.4

## Context

批 6 收尾半边，四件事共用一次协议热区改动与一次 manifest digest 重钉：① 发布是全协议唯一「平台维进载荷」处；② `{p}.note.close` 云端零发送点、与 back 语义重叠（分工裁决是蓝图挂了两批的待决项）；③ `navigation.back` 是浏览词汇里最后一条无平台段的页面手势；④ `edge.task.*` 前缀冗余。kernel 裸字符串豁免表命中其中四个改名面，强制出 v0.1.4。

## Goals / Non-Goals

**Goals**：① 平台维从载荷字段迁进消息名，出入闸按名校验；② automation 侧发布平台静默缺省清零；③ back/close 合并、close 退役回引擎内部；④ `task.*` 收口非平台域命名；⑤ kernel v0.1.4 一次收编全部豁免表改动。

**Non-Goals**：不改发布 kind 的执行语义与后置校验、不改租约状态机行为、不动 api/content 仓源码与 pin（既有线头）、不动 kernel 发布契约（`PublishLogDispatchDraft.platform` 保持 optional，收口点在 automation）、不改 `EdgeTask*`/`PublishCommand*` TS 类型标识符、视频号不获得发布名（kernel fail-closed 现状即正确行为）。

## 1. 名表（唯一权威）

| 旧名 | 新名 | 方向 | 说明 |
| --- | --- | --- | --- |
| `publish.command` | `xiaohongshu.publish.command` / `facebook.publish.command` | cloud → edge | kind 表分平台（§2） |
| `publish.command.result` | `xiaohongshu.publish.command.result` / `facebook.publish.command.result` | edge → cloud | `.result` 尾段沿批 6a 定案的第三族约定 |
| `xiaohongshu.note.close` / `facebook.note.close` | **删除** | — | 零发送点；close＝back 的引擎内部子步骤 |
| `navigation.back` | `xiaohongshu.navigation.back` / `facebook.navigation.back` | cloud → edge | XHS 形 `targetPage` 必填；FB 形无该字段 |
| `edge.task.acquire` / `edge.task.acquired` / `edge.task.release` / `edge.task.released` | `task.acquire` / `task.acquired` / `task.released` 前二者同形去前缀 → `task.acquire` / `task.acquired` / `task.release` / `task.released` | 双向 | 非平台域、无平台段；`acquired/released` 过去分词形本就合规 |

协议消息 107 → **108**；登记表 56 不变。`publish.approval_request` / `publish.approval_action`(.result) / `publish.draft_image_remove`(.result) / `publish.result` 六条不改名（proposal 已述）。

## 2. 发布分平台 kind 表（决策）

**vocabulary 不拆、合法集拆**：`PublishCommandKind` 12 词全量保留为共享词表；新增 FB 合法子集（6 词：`navigate_entry` / `select_mode` / `upload_image` / `fill_field` / `submit_publish` / `capture_postId`，探查自计划构造器 `platform-profile.ts:56-67` 与 FB profile）。落法：

- **云端类型面**：两条消息各绑各的载荷型——XHS 形 `kind` 取 12 全集，FB 形 `kind` 取 6 子集联合（非法组合如 `facebook + set_schedule` 编译期不可表示）。载荷 `platform?` 字段删除（该字段本是手抄 `'xiaohongshu' | 'facebook'` 二元联合、连 `wechat_channels` 都没有，删除后协议与 kernel `PlatformId` 的不一致一并消失）。
- **发送点**：`command-sequencer.ts:595` 按计划平台选消息名；`:556` `reconcile_scheduled` 硬编码处直接写 `xiaohongshu.publish.command`（XHS-only kind，诚实）。
- **边缘路由**：`main.ts:1259` 的 `env.payload.platform ?? 'xiaohongshu'` 删除，平台从消息名前缀解析（批 5 mapper 同模式）；`platformDriver.platform` 不符走既有 `platform_publish_executor_unavailable` 诚实失败。`native-page-engine/publish.ts:44` 超时预算按名前缀取。
- **manifest**：12 条 publish 条目 `edgeTypes` 分平台（共享 6 kind 挂双名、XHS-only 6 kind 挂单名），`receipts` 同步平台形。
- **静默缺省清零（automation）**：`BuildPublishCommandPlanInput.platform` 转必填（`platform-profile.ts:27`）；`command-sequencer.ts:281/:296`、`publish-dispatcher.ts:895`、`publish-scheduler.ts:336`、`automation-main.ts:1454` 的 `?? 'xiaohongshu'` 全删——draft 无 platform 即 fail-closed 带独立原因（不发命令、不猜平台；错猜的失败模式是「XHS 命令发给 FB 边缘」，虽会被平台段闸拦下，但决策已在静默中做错）。api `publish-log-store.ts:379` 的 DB 读取层缺省保留并就地注释（历史行真为 XHS，事实非猜测）。

## 3. back/close 合并（决策，蓝图挂账两批的裁决）

**裁定：删 `{p}.note.close`，「离开内容单元回列表」唯一形态＝`{p}.navigation.back`。**

依据（探查坐实）：FB 侧两名是同一函数（`feed.rs:173` 一个 `||` 分支）、注入路由一条 `if`（`90-dispatch.js:120`）、能力清单逐字段相同、`note_close` 回执报的就是 `back`；XHS 侧 close（关弹层原地不动、无列表验证）是 back（关弹层＋前向导航重建来源列表＋`page.cards` 重报）的严格子步骤；云端零发送点，连策展 LLM 的 `close_note` 判决都经 `quality.reject` → BackToFeed 角色 → `navigation.back` 落地。规则三反向适用：**没有一条云端决策需要「只关弹层、不确认列表」**——该差异是引擎执行细节，不冒泡。

**连带清退**：`EdgeCommand` 动作 `close_note`（零构造点）、bridge `close_note` 映射行、三张关联键表 `close` 键行（值 `close` 随键消失；零发送点＝零回执，无消费面）、引擎 `note_close` kind、manifest/timing 条目、诊断与标签表。**保留**：XHS 引擎关弹层内部函数（back 的子步骤）；策展 LLM 判决词汇 `close_note` 与 `ManagerActionName`（另一命名空间，红线）。

**back 平台段化**：`xiaohongshu.navigation.back{ targetPage: 'feed'|'search'（必填）, reason?, dwellMs? }`——targetPage 转必填是规则二的兑现（探查坐实唯一发送点 `role-dispatcher.ts:4424` 在 `pageType` 缺席时不填该字段，边缘一直在替云端决定回哪——改为云端显式补 `'feed'`）；缺字段按格式错误 fail-closed 拒收。`facebook.navigation.back{ reason?, dwellMs? }`——FB 的来源列表（home/search/group）是引擎记录的会话事实、非云端选择项，不设伪选择字段。bridge：`back` 进平台组合表双平台映射（`wechat_channels` 缺席即响亮 throw，现状语义）。

## 4. `edge.task.*` → `task.*`

纯前缀去冗余，4 条同批换。载荷/类型标识符（`EdgeTaskKind`/`EdgeTaskPriority`/`EdgeTask*Payload`）不动；`EdgeTaskKind` 的值 `'publish'` 等是值命名空间（红线）。改动面（探查全单）：协议两份 union+map、edge `main.ts` 收发 7 处、`edge-client.ts:891` 路由分支、两份登记表、`command-diagnostics.ts:68-69/:252/:261`、`identity-command-gate.ts` ackGap 串与注释、manifest 4 处 edgeType/receipt、`renderer.js:2584-2585` 标签、automation `edge-task-lease-client`/`handler.ts:723,726`/`ws-server.ts:392-393`/`preemption.ts:13`/`automation-edge-access.ts:325`、双仓测试约 12 文件。

## 5. kernel v0.1.4（一次收编）

`transport-gate-exemptions.ts` 豁免表新内容（7 → 6 条）：

```
task.acquire · task.release · captcha.assist.capture · captcha.assist.click
· xiaohongshu.navigation.back · facebook.navigation.back
```

（note.close 两条随协议删除退出豁免表——它们不再存在，谈不上豁免。）配套：`test/transport-gate-exemptions.test.ts` 逐条按序断言同步；`:35` 的 stale `interaction.like`（批 5 遗留、裸 string 假绿）换现役真名；package.json `version` 同步抬 0.1.4（v0.1.1 漏抬的教训）；annotated tag `v0.1.4` 推远端；automation pin `#v0.1.3`→`#v0.1.4`（npm 改写 `github:` 形后手工恢复 `git+ssh://`，lock 内层镜像同查——批 5+7 交接 §2 第 5 条）。api/content pin 不动（既有线头，其经旧 kernel 解析的 aidcp-cloud 旧名断言测试因此保持绿、不改）。

## 6. 静默失效点清单（typecheck 无感，逐处点名）

| # | 位置 | 改法 |
| --- | --- | --- |
| 1 | edge `edge-client.ts:880`（publish 独立分支）/ `:891`（task 分支）/ 白名单里 `navigation.back`(:843) 与两条 note.close(:809,810) | publish/back 换双名、task 换新名、note.close 删条 |
| 2 | edge `command-diagnostics.ts`：`ACTIVE_COMMAND_TYPES`（:35,36 删、:58,:67,:68,:69 换）、`FIXED_SUMMARIES` 键、`PUBLISH_KINDS`（:123-126 裸 12 串——kind 不改、集合保留，逐条核对不动）、`:244` publish 摘要分支 | 逐张结构 |
| 3 | edge manifest JSON：publish 12 条 edgeTypes/receipts、note_close 条目删除、edge.task 4 处（:585-594）——JSON，typecheck 全盲 | 重建 + digest 五位点重钉 |
| 4 | edge `command-manifest.test.ts:64-84` kind 冻结表按平台重构、**`:139` `includes('publish.command')` 跳过谓词**（改名后静默失配、闸误报） | 同批改 |
| 5 | edge `renderer.js:2561,2562（删）/2583/2584/2585` 标签表 | 键换名/删除 |
| 6 | automation `command-sequencer.ts:556` 硬编码消息名、`ws-server.ts:392-393` | 手工点名 |
| 7 | 三张关联键表 `close` 键行删除 + `back` 键随双名换（值 `back` 不动）；`action-key-parity` 重跑 | 三表同步 |
| 8 | kernel 豁免表 + 逐条按序断言测试（§5） | 同 commit |
| 9 | aidcp-cloud `publish-dispatcher.test.ts:982,1019` 消息名 | 与 automation 同步 |
| 10 | `xhs-command-router.js:635-663`（note_close 规则删除、navigation_back 保留）、`facebook-router/90-dispatch.js:120-123`（`||` 分支收敛为单 kind） | 引擎 JS，无类型 |

## 7. 同形异义不改（sed 红线）

- **值命名空间**：`EdgeTaskKind` 的 `'publish'`、`RISK_ACTIONS` 的 `'publish'`、`UI_DAILY_USAGE_ACTIONS` / `STATE_SURFACE_KINDS` 裸词、关联键值 `back`、`publish_*` nativeKind 12 条、身份闸 ack 种类 `publish_command_result`（snake_case 另一词表）。
- **另一命名空间**：策展 LLM 判决 `close_note`（`content-curator-role.ts`，落地为 `quality.reject` 事件）、`ManagerActionName` 的 `close_note`、kernel `DelegatedAction`（`publish_post` 等）、`PublishStatus`、调度目录 `'post'`、`schedule_platform_unsupported` 等原因码、`publish.approval.decision`（edge CLIENT 注册表键，非 MessageType——顺手核真伪、疑似死键单独登记不混入本批）。
- **禁用正则形**：`s/publish\./` 安全、`s/publish/` 不安全；`edge.task` 裸词 grep 会命中 `EdgeTaskKind` 类型名（保留）。

## 8. 验证与变异纪律

- 四道集成复验：protocol-parity + operation-registry-parity + action-key-parity（三表 close 行删除后重跑）+ 双仓 typecheck；kernel 仓自测。
- 发布红线：`AC-PUB-*` 全过（未授权绝不静默发布）+ publish-approval-contract 测试确认审批族未被误动。
- **变异纪律（先 commit 再变异）**：① manifest 删一条 publish edgeType→manifest 测试必红；② 豁免表删 `task.release`→kernel 测试必红；③ bridge 删 back 一个平台映射→bridge 测试必红；④ 边缘 FB 载荷塞 XHS-only kind→拒收断言必红。复原回绿。
- aidcp-cloud 集成仓 publish/role-dispatcher 桶跑绿。

## Risks / Trade-offs

- [manifest digest 与 6a 并行撞车] → 6a 不碰 manifest（IM 无 nativeKind），本批独占 digest；与其他在飞 native change（`restore-native-facebook-residual-parity` 等）以集成串行 + rebase 后重算重钉兜底（批 5+7 实测流程）。
- [删 note.close 后某隐藏消费面残留] → 探查已穷尽 grep 两仓 src；集成期以 typecheck（MessageType 穷举）+ 全量测试 + `openspec validate` 三层兜底；引擎内部关弹层函数保留，行为面零缩水。
- [targetPage 转必填漏改发送点] → 唯一发送点探查坐实（`role-dispatcher.ts:4425`）；边缘格式 fail-closed 拒收 + 回归断言「缺 targetPage 拒收」。
- [kernel 豁免表漏改＝槽位死锁（静默）] → kernel 测试逐条按序断言 + 变异②；automation pin 同批抬升，集成期跑 automation 全量测试（豁免表消费点 `automation-edge-access.ts:65,331` 走新版）。
- [发布链改动误伤审批族] → 审批族六条名不动、publish-approval-contract 回归；「不进白名单」写进 tasks 防误加。

## Migration Plan

kernel 先行（worktree 开发 → 测试 → tag v0.1.4 推远端）→ edge / automation worktree 并行开发（automation 先抬 pin 再改名，typecheck 立即接住豁免表消费面）→ 双仓测试 + typecheck → 与 6a 串行集成（6a 先落，本批 rebase 后 manifest 重建重钉 digest）→ 四道 parity + 变异 → automation dev 部署（安全序列）→ tasks.md 回写 → 真机项登记 backlog → archive。回滚＝revert 两仓提交 + automation pin 回 v0.1.3 + dev 重部署（kernel tag 无需回收，无消费者即无效）。

## Open Questions

（无——back/close 分工与 kind 表拆法均已在 §2/§3 定案；`publish.approval.decision` 疑似死键不阻塞本批，单独登记。）
