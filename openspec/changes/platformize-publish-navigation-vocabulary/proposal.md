## Why

词汇蓝图批 6 的收尾半边（`docs/edge-command-grammar.md` §6.2「IM 族、发布与收尾」行、§6.3 批次表）：发布平台段化、`navigation.back` 与 `note.close` 分工裁决后平台段化、`edge.task.*` 前缀冗余清理。发布是全协议唯一「平台维进载荷」处（`platform?` 缺省静默当小红书），与批 4/5 已立的「平台段进名字、出入闸按名校验」不一致。

前置核实（2026-08-07，四路并行探查，多处修正蓝图预判）：

- **发布链发送点全在 automation**（`publish-agent/command-sequencer.ts:595` 唯一构造点）；content / api 两仓无协议副本、零消息名占用——交接文档「批 6 可能扩到 content」的预判解除，本批不动 content。
- **真正有发布的平台只有 2 个**：XHS 全量 12 kind、FB 子集 6 kind（beta）；视频号发布在 kernel 层结构性拒绝（`publish-platform-profile.ts:55` throw）。只拆 `xiaohongshu` / `facebook` 两个名，不造零生产者的 wechat 名。
- **载荷 `platform?` 上方叠着四层 `?? 'xiaohongshu'`**（api DB 读取层 → kernel 草稿契约 optional → automation dispatcher/scheduler → 计划构造入参）：删线缆字段只治线缆，须同批把 automation 侧全部静默缺省收掉（fail-closed 带原因），否则名字治好了、决策层照旧猜。
- **back/close 分工证据**：FB 侧两名同一条代码路径（引擎一个 `||` 分支、`note_close` 回执报的就是 `back`、能力清单逐字段相同）；XHS 侧 close（纯关弹层）是 back（关弹层＋重建并验证来源列表）的严格子步骤；**云端从未发过 note.close**——策展 LLM 的 `close_note` 判决落到线缆也是 `navigation.back`。裁决＝合并：`{p}.note.close` 从协议删除，关弹层降回引擎内部子步骤（原语不出引擎）。
- **kernel 必出 v0.1.4**：`transport-gate-exemptions.ts:34-43` 裸字符串豁免表命中本批四个改名面（`edge.task.acquire/release`、`xiaohongshu.note.close`、`facebook.note.close`、`navigation.back`），漏改无编译错、后果是槽位死锁。transport 仓零占用、不出版。
- **api pin 不动**（沿既有裁定：v0.1.1 落后为已登记线头、不推浏览命令非阻塞）；aidcp-cloud 经 api 旧 kernel 解析的旧名断言测试因此不受影响。

## What Changes

- **发布平台段化**：`publish.command`(.result) → `xiaohongshu.publish.command`(.result) + `facebook.publish.command`(.result)；**删载荷 `platform?` 字段**（该字段还是手抄二元联合、非 `PlatformId`）；原子 kind 表分平台（XHS 12 / FB 6，FB 非法 kind 云端类型不可表示、边缘 fail-closed）。`publish.approval_*` / `publish.draft_image_remove*` / `publish.result` 六条**不改名**（edge→cloud 请求族或按信封 id 关联的应答，非云端主动命令；MUST NOT 加进 edge-client 主动命令白名单——CLAUDE.md §2 注的既有红线）。
- **automation 侧发布平台静默缺省清零**：计划构造入参 `platform` 转必填；dispatcher / scheduler / delegated-loader 的 `?? 'xiaohongshu'` 删除，缺失即 fail-closed 带独立原因（`draft_platform_missing` 类）。唯一保留的缺省在 api DB 读取层（历史行真为 XHS，事实缺省非猜测，就地注释坐实）。content 仓生成侧 7 处同病缺省登记线头、不在本批。
- **`{p}.note.close` 删除（2 条）**：零发送点、FB 侧与 back 同路径、XHS 侧是 back 子步骤。边缘 `close_note` EdgeCommand 动作、bridge 映射、三张关联键表 `close` 键行、引擎 `note_close` kind 与 manifest 条目一并清退（引擎保留关弹层内部函数供 back 复用）。
- **`navigation.back` → `xiaohongshu.navigation.back` + `facebook.navigation.back`**：XHS 形 `targetPage: 'feed' | 'search'` **转必填**（规则二：补空即决策，决策归上层；唯一发送点在 `pageType` 缺席时由云端显式补 `'feed'`）；FB 形不带 `targetPage`（回引擎记录的来源列表是事实非选择）。
- **`edge.task.*` → `task.*`（4 条）**：`edge.` 前缀冗余（非平台域本就无前缀层级）；载荷类型标识符（`EdgeTask*`）不动。
- **kernel v0.1.4**：豁免表 `edge.task.acquire/release`→`task.*`、删两条 note.close、`navigation.back`→两平台形；配套逐条断言测试同步；顺手修 stale 测试串（批 5 遗留 `interaction.like`）；package.json version 同步抬（v0.1.1 的教训）+ annotated tag。automation pin v0.1.3→v0.1.4（保 `git+ssh://` 形，npm 改写后手工恢复）。
- **manifest digest 重钉一次**：publish 12 条 `edgeTypes` 分平台 + `note_close` 条目删除 + `edge.task` 4 处 edgeType/receipt 换名，`build-native-page-engine.mjs` 重建后五位点（生产常量 + 4 测试位点）一次换齐。
- 协议消息 **107 → 108**（publish +2、note.close −2、back +1、task ±0）；两份登记表 **56 不变**（publish +1、note.close −2、back +1）。`docs/protocol.md` 头部计数、§2 表、载荷节、bridge 映射段随改。
- **BREAKING（内部协议，预期内）**：并入批 1–5+7 未出包切换窗口；新名 fail-closed 拒收在执行前。发布链改动按 AC-PUB-* 红线全过后才集成。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

手写 delta（语义真变）：

- `publish-pipeline`: 发布协议从「一条通用消息 + kind 参数 + 载荷 platform 字段」改为「平台段消息名 + 分平台 kind 表、载荷无平台维」；平台静默缺省清零（fail-closed）
- `browse-loop-resilience`: `navigation.back` 平台段化；XHS 形 `targetPage` 必填，「payload 无 targetPage」情景改为格式 fail-closed 拒收 + 云端总是显式声明目标列表
- `command-pacing`: `dwellMs` 载体清单收敛（`{p}.note.close` 退役，离页停留唯一载体为 `{p}.navigation.back`）

机械改名 delta（纯名字提及，语义零变，集成期脚本化生成、归档前重生成）：

- `edge-task-execution-coordination`（8 处 `edge.task.*`→`task.*`）、`publish-dispatch-resilience`（2 处）、`captcha-incident-handling`、`facebook-identity`、`facebook-post-publish`、`interaction-cooldown`、`interaction-risk-gating`、`platform-page-command-routing`（`navigation.back`→FB 语境平台形）、`read-to-write-note-lane`

## Impact

- `aidcp-edge`：`src/comm/protocol.ts`、`src/client/{edge-client,operation-registry,command-diagnostics,identity-command-gate}.ts`、`src/main.ts`（publish 路由 `:1259` 删静默缺省、task 收发 `:1039-1048`）、`src/flows/publish-command-handlers.ts`、`src/facebook/publish-executor.ts`、`src/native-page-engine/{command-mapper,publish,client}.ts`、`src/browse/browse-session.ts` 与 `src/facebook/facebook-session.ts`（back/close 分派与 `FB_COMMAND_ACTION_NAMES`）、`src/electron/renderer/renderer.js`、native 引擎（`command.rs`、`facebook/{feed,shared,capability}.rs`、`xhs-command-router.js`、`facebook-router/90-dispatch.js`）、`command-manifest.json` + `command-timing.json` + digest 五位点、测试约 20 文件（含 `command-manifest.test.ts` 的 kind 冻结表与 `:139` publish 跳过谓词——裸串，改名后静默失配须同批改）。
- `aidcp-automation`：`src/comm/{protocol,command-bridge,handler,operation-registry,ws-server,preemption,edge-task-lease-client}.ts`、`src/publish-agent/{command-sequencer,platform-profile,publish-dispatcher,publish-scheduler}.ts`（含 `:556` 硬编码平台与全部 `?? 'xiaohongshu'`）、`src/orchestrator/role-dispatcher.ts`（back 发送点补显式 targetPage、`close_note` 动作清退）、`src/automation-main.ts:1454`、`src/automation-edge-access.ts`、kernel pin 抬升、测试约 12 文件。
- `aidcp-kernel`：`transport-gate-exemptions.ts` + 测试、version bump + tag v0.1.4。
- `aidcp-cloud`（集成测试仓）：`publish-dispatcher.test.ts`、`role-dispatcher.test.ts` 相关断言；`mirror-stale-stop-work` / `handler.test` 经 api 旧 kernel 解析、不动。
- 控制仓：`docs/protocol.md`、`docs/edge-command-grammar.md`（批 6 行标 ✅ + back/close 裁决记录）、spec delta 12 份。
- **sed 红线**：`EdgeTaskKind` 值 `'publish'`、`RISK_ACTIONS`/`UI_DAILY_USAGE_ACTIONS`/`STATE_SURFACE_KINDS` 里的裸词 `publish`、策展 LLM 判决词汇与 `ManagerActionName` 的 `close_note`、身份闸 ack 种类 `publish_command_result`（snake_case 另一词表）、`publish_*` nativeKind、kernel `DelegatedAction`/`PublishStatus` 等——全部是值或另一命名空间，MUST NOT 随改。
- **并行注意**：与批 6a（`platformize-inbox-vocabulary`）并行开发、**集成串行、6a 先落**（同碰两份 protocol.ts、登记表、edge-client、command-diagnostics、renderer、protocol-contract 测试热区；manifest digest 只本批碰，无双重重钉）。热点单写：三张关联键表、kernel 豁免表本批独占。
- **不出包不算完**：并入既有未出包窗口，真机验收（XHS/FB 发布链新名端到端、back 新名、task 租约链）登记 backlog。
