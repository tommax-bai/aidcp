## 1. aidcp-edge — 命令清单对账（声明变成断言）

- [x] 1.1 建立「声明回执 ↔ 成功路径可达发出点」对账检查：从命令清单读每条命令的 `receipts`，与宿主 `src/native-page-engine/browse-session.ts` 的 `report()` 输出分派表逐条比对，两个方向都查（声明有而不可达 / 可达而未声明），不一致即失败并打印命令名与不匹配的回执名。判据必须**跨平台取并集**（单次执行只产出一个输出，`note_browse_images` 这类是小红书回详情、Facebook 回动作回执）且**排除失败路径**（`browse-session.ts:436` 的 `reportFailure` 对任何命令都发一条 `ok:false` 动作完成，算进来则对账恒真） <!-- aidcp-edge 74eaf41 新建常驻检查 test/native-page-engine/runtime-contracts-command-receipts.test.ts：从 browse-session.ts 源码机械导出 report() 输出分派表（含 search.execute 补发与随行载荷两类条件分支），双向对账、跨平台并集、排除 reportFailure；未登记的 client.<method>( 出口当场断言失败。6 tests / 6 pass -->
- [x] 1.2 跑一次 1.1 的检查，把当前全部不一致逐条记入本文件，每条标注结论为「补发出」或「改声明」。声明了两条回执的共 12 条：`page_scroll` / `feed_refresh` / `search_execute` / `note_open` / `note_close` / `navigation_back` / `note_browse_images` / `profile_open` / `notification_open` / `notification_browse_comments` / `notification_back_home` / `captcha_click`。其中**起草期已实读坐实**的只有三条结论，其余 9 条不预判、以检查输出为准： <!-- aidcp-edge 74eaf41 对账跑通，14 条不一致逐条登记；起草期三条结论有一条被实读推翻并就地订正 -->
  - `note_open`：声明的 `action.completed` 在成功路径上不可达（两平台成功恒回 `note_detail`，`report()` 的 `note_detail` 分支直接 return）——**实测维持原判**
  - ~~`note_close` / `navigation_back`：声明的 `page.cards` 反向不可达（两平台成功恒回 `action_receipt`）~~ ——**该结论已被实读推翻（2026-07-29）**。Facebook 侧这两条命令不走页面规则：`facebook/feed.rs` 的 dispatch 把 `NoteClose|NavigationBack` 交给 `execute_facebook_back_to_list`，成功路径恒回 `CommandOutput::PageCards`（`feed.rs:315-339`）。按 design 定的「跨平台并集」判据，两条命令的可达集恰为 `{action.completed(小红书), page.cards(Facebook)}` = 声明集，**不是缺口**。若照预写结论去「修实现或删声明」，会把一条真实存在的回执从契约里删掉、让云端按声明配置的角色等一条再也不写在契约里的回执。
  - `search_execute`：两条回执**都发**（`page_cards` 分支在信封为 `search.execute` 时同时报动作完成，`browse-session.ts:283-308`）——不得把它当成缺口。**实测维持原判**
- [x] 1.2.1 复核结论登记：简报称「身份读取命令声明会发身份观测回执、而整条命令在边缘入口就被吞掉」，实读**未能复现**——`identity.read_current` / `identity.read_self_profile` 在 `src/native-page-engine/command-mapper.ts:10-11,35-36,60-61,87` 有完整映射，`report()` 的 `identity_observation` 分支照发 `identity.observed`（`browse-session.ts:334-335`）。故身份类命令不预标为缺口，一律交 1.1 的对账检查判定 <!-- aidcp-edge 74eaf41 对账实测判定为一致，未预标缺口，起草期复核结论确认成立 -->
- [x] 1.3 按 1.2 的结论逐条落实；无法在本 change 内落实的，写进一张显式冻结清单，每条含命令名、声明值、实际行为、消除动作，并在检查里断言冻结清单只许缩短 <!-- aidcp-edge 74eaf41 14 条全部进 FROZEN_RECEIPT_GAPS（命令名/方向/回执名/消除动作），三条断言：非冻结不一致一律失败、清单不许留已消除条目、条目数 ≤ FROZEN_GAP_BUDGET=14 -->
  - 跨 change 依赖登记（2026-07-29）：**14 条声明修正本轮不可落实**。`native/page-engine/command-manifest.json` 的 sha256 被 `test/native-page-engine/build-contract.test.ts:79-88` 反向绑定到 `src/electron/native-page-engine-artifact.cjs:19` 的 `EXPECTED_CAPABILITY_DIGEST`（实测现值 `89c8488c…4b1c71`），而那个常量归并行 change `enforce-native-engine-artifact-gates`。清单改动必须与该常量**同一提交内**改，否则 build-contract 当场红、且打包校验带着对不上的摘要出门。消除动作已逐条写在冻结清单里，改起来是机械动作。这也是 3.1 选择宿主常量而非清单产物作为提交窗口事实源的直接原因。
- [x] 1.4 把 `requestContract` 的断言从「字符串非空」升级为「必须解析到一个真实存在的具名请求契约」，不存在即失败 <!-- aidcp-edge 74eaf41 32 条全覆盖：29 条解析到 src/comm/protocol.ts 导出类型，3 条非云端信封名走显式解析表且必须点名真实存在的基契约 / 引擎侧结构 -->
- [x] 1.5 把 `effect` 与 `cancellation` 的断言从「字符串非空」升级为「必须属于一个封闭取值集，且与引擎侧对该命令的写判定 / 取消安全点一致」 <!-- aidcp-edge 74eaf41 effect 6 值 / cancellation 4 值封闭集，并与引擎写判定交叉断言（platform_write|draft_write ⇒ may_write()==true 等），18 条写/读命令都造了能过 validate() 的样本、非空转 -->

## 2. aidcp-edge — 命令词表从枚举导出

- [x] 2.1 把 `native/page-engine/src/command.rs` 的词表一致性检查改为从 `NativeCommand` 穷举导出（用 serde 往返或穷举 match 生成 kind 列表），不再以 `PRODUCTION_COMMAND_KINDS` 手写数组作为比较的一方 <!-- aidcp-edge 74eaf41 NativeCommand 改由 native_commands! 宏定义，导出 NATIVE_COMMAND_KINDS 与 kind()；手写数组 PRODUCTION_COMMAND_KINDS 已删（全仓无其他引用） -->
- [x] 2.2 为「可执行但不进清单」的变体建立显式排除表并断言其内容（当前应恰为 `page_probe` 一条），排除理由随表记录 <!-- aidcp-edge 74eaf41 新增 MANIFEST_EXCLUDED_COMMAND_KINDS（kind+理由），当前恰 page_probe 一条；断言排除项必须可执行、必须不在清单、理由非空 -->
- [x] 2.3 加一条失败优先的回归：在枚举里新增一个变体而不动清单与排除表时，该检查必须失败 <!-- aidcp-edge 74eaf41 判据抽成 vocabulary_drift(枚举,清单,排除表)：假想新变体必报 unaccounted:*、清单遗留必报 orphan:* -->
- [x] 2.4 修正该检查的名称，使其名副其实（现名 `production_enum_matches_the_frozen_manifest_exactly` 与其实际比较对象不符） <!-- aidcp-edge 74eaf41 改名为 every_enum_kind_is_either_in_the_manifest_or_in_the_declared_exclusion_table -->

## 3. aidcp-edge — 提交窗口预算单一事实源

- [x] 3.1 确定提交窗口标签与预算的单一事实源（宿主侧常量或命令清单产物二选一），删除另一侧的独立数字声明 <!-- aidcp-edge 74eaf41 事实源定为宿主 client.ts 的 NATIVE_COMMIT_WINDOW_BUDGETS；引擎侧降为「标签+镜像数字、运行期不作数」，新增机械对账用例：单边改一个数字仓库检查当场失败 -->
  - 决策记录（2026-07-29）：事实源选宿主常量而非清单产物，直接原因见 1.3 的跨 change 依赖——清单产物的摘要被 Electron 侧常量反向绑定，本 change 动不了。
  - 该表同时是**准入名单**：标签不在表内即拒发窗口。并行流在 b57d619 接上的五条小红书窗口请求，其标签在本提交内一并加入（`xhs_comment_submit`=4000 / `xhs_notification_comments`=20000 / `xhs_notification_likes`=20000 / `xhs_notification_follows`=20000 / `xhs_publish_submit`=15000）；对账用例同批扩到**同时读两份引擎源**（`facebook/capability.rs` + `commit_window.rs`），只读一份会让另一份完全没有闸。
- [ ] 3.2 改造引擎侧：按标签请求窗口，不再随请求发出自写的预算数字（`native/page-engine/src/facebook/capability.rs` 的 `JOIN_WINDOW` / `COMMENT_WINDOW` / `PUBLISH_WINDOW`）
  - 偏离说明（2026-07-29）：**本轮只做到「宿主权威 + 引擎数字不作数 + 机械对账防漂」，线路上的 `budget_ms` 字段仍在**（现语义已从「声明」降为「请求值」，宿主按 `min(请求, 事实源)` 授予）。物理删除该字段要同时改 `commit_window.rs` 的请求结构、`protocol.rs` 的 `CommitWindowRequestRecord`、`main.rs` 的记录构造、`facebook/shared.rs` 的取用点——四个文件本轮均在其他并行流的单写区，未触碰。
- [x] 3.3 改造宿主侧 `src/native-page-engine/client.ts`：以事实源为准给出预算并保留上限约束，取消对引擎自报预算的相等断言 <!-- aidcp-edge 74eaf41 parseCommitWindowRequest 只做结构校验；新增 grantCommitWindowBudget(label, requested)：标签不认识回 undefined，认识则授 min(requested, 事实源)，缺失/非法按事实源授；下发给窗口守卫的是授予值 -->
- [x] 3.4 把「标签未知 / 预算不符事实源」的运行期处理从 `failProtocol` + `terminate()` 改为可归因的、绑定当前命令的契约违规结论，引擎进程不再被整体终止 <!-- aidcp-edge 74eaf41 新增 rejectCommitWindowContract：先发 accepted:false 否决这一次窗口（不可逆动作不会被按下），再把 commit_window_unavailable / effectPhase=not_started / reasonCode=commit_window_label_unknown 绑到当前命令；结构性坏记录仍走 failProtocol（那时连是哪条命令都读不出来） -->
- [x] 3.5 加回归：单侧修改一个窗口预算时，仓库检查失败；且不存在任何运行期路径能让该修改表现为「按下按钮前终止引擎」 <!-- aidcp-edge 74eaf41 runtime-contracts-commit-window.test.ts 两条：镜像对账（从两份引擎源正则提取 label/budget 与宿主表 deepEqual）+ 标签不认识时同一会话随后一条命令仍正常执行并回 page_cards（旧口径下会因 terminate() 直接失败） -->
- [x] 3.6 加回归：引擎请求一个大于事实源上限的预算时，宿主只授予事实源上限 <!-- aidcp-edge 74eaf41 引擎报 90_000 → 守卫收到 18_500（=NATIVE_COMMIT_WINDOW_BUDGETS.fb_join_click） -->

## 4. 产物新鲜度 — 本 change 不做，交叉核对

产物摘要输入范围、开发态重编判据、打包态产物校验与 Electron 侧期望摘要，整片归并行 change `enforce-native-engine-artifact-gates`。本节只做核对，**不修改** `native/page-engine/build.rs`、`scripts/build-native-page-engine.mjs`、`scripts/ensure-native-page-engine-dev.mjs`、`src/electron/native-page-engine-artifact.cjs`。

- [x] 4.1 记录起草期坐实的现状供交叉核对：能力摘要仅哈希 `command-manifest.json`（`native/page-engine/build.rs:19-21`）；引擎版本恒 `0.1.0`（`Cargo.toml:3`）；`verify()` 只做产物自洽（`scripts/build-native-page-engine.mjs:72-113`）；开发引导为「校验通过就不重编」（`scripts/ensure-native-page-engine-dev.mjs:19-27`）；实测自 2026-07-22 起规则目录 10 次提交 vs 命令清单 4 次提交 <!-- aidcp-edge 74eaf41 交叉核对完成，未改任何产物闸文件；其中两条起草期事实已过期，就地订正 -->
  - **订正（2026-07-29）——后两条已过期，照原文当现状引用会低估现有闸门**：并行 change `enforce-native-engine-artifact-gates` 已落地（`aidcp-edge be0a8be`）。① `scripts/build-native-page-engine.mjs` 现在算 `computeEngineSourceDigest(引擎源码输入)`（:174）并与产物清单的 `sourceDigest` 比对（:248-257），构建后重算写入清单（:312-323）——`verify()` 已不只是产物自洽；② `scripts/ensure-native-page-engine-dev.mjs` 的「校验通过就不重编」现在**同时覆盖「源码改了没重建」**（:30-40 注释与实现，重建理由原样带出）。
  - 仍然成立的两条：`build.rs` 的 `capabilityDigest` **只哈希 `command-manifest.json`**；`Cargo.toml` 引擎版本恒 `0.1.0`。
- [x] 4.2 待 `enforce-native-engine-artifact-gates` 落地后核对：源码导出的摘要是否已进入宿主↔引擎的启动握手比对（`src/native-page-engine/client.ts:481-489` 现比引擎版本 / 平台适配器版本 / 适配器表 / 能力摘要四项）。若未进入，单开后续 change 承接「运行期握手也要能证明规则新鲜度」并在此登记 <!-- aidcp-edge 74eaf41 核对完成：源码摘要未进入握手，缺口仍在，按本条要求登记 -->
  - 登记（2026-07-29）：**缺口仍在，需单开后续 change 承接**。实读 `src/native-page-engine/client.ts:505-515`，启动握手仍只比引擎版本 / 平台适配器版本 / 适配器表 / 能力摘要四项；引擎 ready 记录里根本没有 `sourceDigest`（`build.rs` 不导出），`runtime.ts` 读包内 `manifest.json` 时也不校验它。后果：「新二进制 + 旧规则」能在构建 / 打包期被抓，**运行期握手仍证明不了规则新鲜度**。
- [x] 4.3 待该 change 落地后核对：Electron 侧硬编码期望摘要（`src/electron/native-page-engine-artifact.cjs:19`）是否已可派生或已有机械同步闸；若仍是裸常量，在此登记为未消除缺口 <!-- aidcp-edge 74eaf41 核对完成：仍是裸常量，但已有机械同步闸，缺口按实测收窄 -->
  - 订正（2026-07-29）：**起草期描述比现状悲观**。`:19` 的 `EXPECTED_CAPABILITY_DIGEST` 确实仍是裸常量（实测值 `89c8488c…4b1c71`），但已有机械同步闸——`test/native-page-engine/build-contract.test.ts:79-88` 断言它等于清单实际 sha256。缺口从「无人对账」收窄为「**需人工改两处、漏改会被测试当场拦下**」。同一绑定即 1.3 的跨 change 依赖来源。

## 5. aidcp-edge — 引擎故障后的自愈

- [ ] 5.1 把 `src/native-page-engine/browse-session.ts:141-142` 的会话结束收尾从成功路径移到 `finally`，使结束会话命令失败时收尾仍执行
  - 本轮未做（2026-07-29）：落点 `src/native-page-engine/browse-session.ts` 归并行流（该文件本轮被 b57d619 大改）。实读 HEAD 仍是 `await active;` 之后紧跟 `if (env.type === 'session.end') this.stop('cloud_session_end');`（:245-246），`finally` 块只复位 `active` / `activeAbort`——**命令失败时收尾仍不执行，缺口原样保留**。需在 browse-session.ts 的单写者手里落。
- [x] 5.2 给 `src/native-page-engine/runtime.ts:128-131` 的会话缓存加存活判据（现为命中即返回、零判据）：返回缓存句柄前必须**取到存活的肯定证据**（如子进程未退出且通道可写），取不到即按已死处理、丢弃并重开——「没记到死讯」不算存活证据 <!-- aidcp-edge 74eaf41 client.ts 新增 NativeProcessTransport.isLive()（握手完成 + 未退出 + 未被 kill + exitCode/signalCode 均为 null + stdin.writable）与会话级 isLive()；runtime.ts 的 sessionFor 取不到证据即丢弃重开，新增 discardSession() 让收尾失败不堵住重建入口 -->
  - 非空转验证：把 `cached.session.isLive()` 临时短路成 `true` 后，会话自愈 3 条里有 2 条失败（随即还原并以 `git diff` 确认）。
- [ ] 5.3 加回归：引擎进程已退出时下发结束会话 → 该命令失败，但 owner 被释放；随后一条命令能重建引擎并正常执行
  - 偏离说明（2026-07-29）：**只落了 runtime 层那一半**。已有用例「引擎已退出时释放 owner：收尾失败不堵住重建入口」（校验新旧引擎 pid 不同），`closeOwner` 打在已死句柄上不再把异常抛给调用方（调用点是 `void closeOwner(...)`，抛出去即未处理拒绝）。缺的是「**下发结束会话命令**」这条入口——它依赖 5.1，同属 browse-session.ts 单写区。
- [x] 5.4 加回归：缓存会话的传输已死时，下一条命令走重建而不是立刻抛「引擎已退出」 <!-- aidcp-edge 74eaf41 runtime-contracts-session-recovery.test.ts 3 tests / 3 pass：传输已死走重建 + 外部 SIGKILL（宿主完全没机会记到死讯）后仍能重建 + 健康会话必须被复用（判据不许严到每条命令重开引擎） -->

## 6. aidcp-edge — 重连绑定与预算

- [ ] 6.1 让引擎重连时重新向宿主/提供方解析端点，不再复用 `native/page-engine/src/engine.rs` 会话结构里存的 `host` / `port`；宿主侧 `runtime.ts` 相应提供会话期内可重复取值的端点解析入口（当前 `getEndpoint()` 只在建会话时调用一次）
  - 本轮未做（2026-07-29）：引擎侧复用 `self.host`/`self.port` 的逻辑在 `native/page-engine/src/engine.rs:203-217`，该文件本轮归并行流且已被大改；宿主侧 `getEndpoint` 改成会话期可重复调用**必须与它同批**，单改一侧没有意义。归 engine.rs 单写者。
- [ ] 6.2 给 `native/page-engine/src/endpoint.rs:214-226` 的 `select_target`（现判据仅「目标类型 page + 平台 URL 允许集 + 调试地址端口」）增加分身身份证据判据；身份证据的具体载体在实装期与浏览器提供方一侧确定后记录在此。现成候选：provider 认领失联浏览器用的「`<profileId>_` 前缀缓存目录 + `DevToolsActivePort` 标记」（`src/cdp/browser-provider.ts:728-745`）
  - 偏离说明（2026-07-29）：**判据与失败语义已在 `endpoint.rs` 内落成并单测覆盖，但尚未接线到真实附着路径 —— MUST NOT 当成已生效的防护**。已落：`BrowserInstanceIdentity`（:233）+ `read_browser_identity()`（:259，经 CDP `GET /json/version` 读取）+ `select_target_for_instance()`（:281）；`cargo test --lib endpoint::` 10/10 通过，含 `refuses_to_attach_without_proven_instance_identity` 与 `browser_instance_identity_comes_only_from_a_browser_debugger_url`。
  - **身份证据载体已确定并记录**：浏览器级调试地址 `/devtools/browser/<uuid>`（换浏览器进程必换值，**端口回收复用带不过去**），非起草期候选的缓存目录 / `DevToolsActivePort`。
  - 接线缺口：`select_target` 的调用点在 `engine.rs` / `lib.rs`，且「准入时记下的实例身份」要从宿主经 `session_open` 参数传进来（`src/protocol.rs` 的 `SessionOpenParams` 加分身身份字段 + `client.ts` + `runtime.ts` + `src/cdp/browser-provider.ts` 准入时记录浏览器实例 id）。这些文件本轮均在其他单写区。
- [ ] 6.3 无法取得身份证据、或无候选目标可证明属于被准入实例时，返回诚实的执行器健康类失败，不附着任何目标
  - 偏离说明（2026-07-29）：语义已落成（`EndpointUnreachable`，消息点名「无法自证是被准入的浏览器实例」，**不附着任何目标**，绝不退化成端口对上就接管），单测覆盖「端口 / 平台全对但实例 id 不同 → 报错」「任一侧证据缺失 → 报错」「证据一致才走既有平台 / 端口判据」。同 6.2：**未接线，不算已生效的防护**。
- [ ] 6.4 把 `engine.rs:509-528` 重连后的重试纳入与首跑相同的绝对截止线包裹，超时即释放单命令槽位并回超时
  - 本轮未做（2026-07-29）：整段在 `native/page-engine/src/engine.rs:474-528`，归并行流单写区。
- [ ] 6.5 加回归：重连 + 重试的总耗时不超过原命令预算；预算耗尽后槽位被释放，下一条命令不再被 `CommandInProgress` 顶回
  - 本轮未做（2026-07-29）：依赖 6.4。
- [ ] 6.6 加回归：候选目标的端口对上但身份证据不匹配时，引擎拒绝附着且不执行任何命令
  - 偏离说明（2026-07-29）：**端点选择层那一半已有断言**（端口 / 平台全对、实例 id 不同 → 拒绝并报错）；「**且不执行任何命令**」这一半要等 6.2 接线后才能端到端断言。

## 7. aidcp-edge — 取根、诊断与焦点守卫的诚实归因

- [x] 7.1 在 `native/page-engine/src/facebook-router/00-shared.js:13-19` 的共享取用函数（`all` / `first`）里加空 root 防护，使传入空 root 时返回可归因于「无有效根」的空结果而非抛 `TypeError`（当前直接对传入 root 调 `querySelectorAll`，零防护） <!-- aidcp-edge 74eaf41 新增 rooted() 判据（必须是带 querySelectorAll 的对象），空根回空结果不抛；缺省参数语义不变 -->
- [x] 7.2 修 `20-feed.js:253` 的 `currentDetail()`：`… || document.querySelector('main') || document.body` 之后无空判、直接进 `noteDetail(root, permalinkOf(root)…)`，是**当前唯一实读坐实会把空根交给遍历**的取根点（行号按 `aidcp-edge@9cd7691`；简报给的 `87,147,233` 已被 07-28 改动顶偏）。改为取不到有效根时返回诚实的未开始理由 <!-- aidcp-edge 74eaf41 currentDetail() 兜底链落空时回 action('open',false,'target_not_found')（现址 :254），不再把空根交给详情遍历；jsdom 摘掉 body 后先断言 document.body===null 再跑 note_open -->
- [x] 7.2.1 交叉核对另 4 处 `|| document.body` 取根点（`20-feed.js:87,154,166` 与 `40-group-join.js:103`）：起草期实读结论是它们下游均空安全（`:87` 紧跟 `if(!scope)return`；`:154` 只进 `node&&…` 循环；`:166` 只以 `scope&&…` / `all(…,scope||document)` 使用；`40-group-join.js:103` 进 `targetGroupScope`，其 `:50-51` 首行即 `if(!groupId||!main)return`）。若实装期复读推翻某一处，按 7.2 同样处理并在此记录；结论不变则不改这 4 处，**不做空转补丁** <!-- aidcp-edge 74eaf41 逐处复读，起草期结论不变（现址 :86/:153/:165 与 40-group-join.js:103），按要求未做空转补丁 -->
- [x] 7.3 给 `native/page-engine/src/xhs.rs:66-72` 与 `native/page-engine/src/probe.rs:89-98` 的结果解码入口补上与 `facebook.rs:607-620` 同级的有界解码诊断（阶段 / 字段路径 / 异常位置），且诊断保持有界、不含页面正文与凭据。**先核对**并行 change `restore-native-xiaohongshu-session-guards` 是否已把解码入口一并覆盖；已覆盖则划掉本条、不重复实现 <!-- aidcp-edge 74eaf41 先核对：并行 change 未覆盖（xhs.rs/probe.rs 仍是裸错误），故补上同级诊断（阶段/字段路径/异常类别与原因/标识符/行列）；构造函数只写一份放在 probe.rs 由 xhs.rs 共用 -->
  - 残留（2026-07-29）：诊断实现现为 **2 份覆盖 3 个入口**（原为 1 份覆盖 1 个）。`facebook.rs:911-1080` 里那份等价实现是私有函数，本轮不可编辑该文件；收口到 `error.rs` 留给后续。
- [ ] 7.4 在 `native/page-engine/src/input.rs:108-128` 区分「焦点守卫求值失败或输出缺失」与「焦点确实丢了」两类结论（通道失败已单列为 `Engine`，保持不变）
  - 偏离说明（2026-07-29）：**三态判定已落成，但外显原因码尚未三分**。已落 `FocusGuardVerdict{Focused, Lost, Unreadable}`（`input.rs:139`）：页面抛异常 / 输出缺失 / kind 不对 / 布尔字段不是布尔 = `Unreadable`，只有守卫确实回「目标不在或没聚焦」才是 `Lost`；`cargo test --lib input::` 13/13 通过，含 `focus_guard_separates_unreadable_from_a_real_focus_loss`（1 正 3 反 5 未知）。**但 `Unreadable` 当前映射到 `TextInputFailure::Engine`**，与本条括注「通道失败已单列为 Engine，保持不变」的三分要求不符。
  - **可观察副作用（云端口径会变）**：Facebook 发帖填写这一支的失败原因码由 `composer_focus_lost` 变为 `engine_error`（**仅限守卫求值失败 / 输出缺失这一支**；守卫真回「没聚焦」仍是 `composer_focus_lost`）。这是有意为之——宁可粒度降级，也不把「不知道」说成「知道是坏的」。云端若曾按 `composer_focus_lost` 做过统计，口径会变。
  - 专用变体 `TextInputFailure::GuardUnreadable` 本轮 defer：新增枚举变体会打断三处穷举 match 的编译（`engine.rs:782-791/1348-1351`、`facebook/comment.rs:221-232`、`facebook/publish.rs:612-619`），四个文件均在其他单写区。
- [x] 7.5 加回归：① 取用函数收到空 root → 回可归因的空结果、不抛（写命令路径因此不会被判 `Ambiguous`，对照 `engine.rs:532-543` 的「写 + 任何规则错误 → Ambiguous」）；② 导航瞬间无有效根 → `note_open` 回未开始而非抛；③ 非 Facebook 平台解码失败 → 携带同级诊断；④ 守卫求值失败 → 与目标丢失是两个不同结论 <!-- aidcp-edge 74eaf41 四条全落地：runtime-contracts-page-rules.test.ts 3 tests（null/{}/字符串/0 全回空、有效根照旧、jsdom 摘 body 后 note_open 回 target_not_found）+ runtime_contracts_decode_diagnostics.rs 3 tests（含「诊断绝不能带页面正文或凭据」：cookie 值 / 中文正文 / 带空格的伪标识符都不落盘，整串 ≤512 字节）+ input:: 焦点守卫 1 test -->

## 8. aidcp-cloud — 评论预算传输而非重算

- [ ] 8.1 确定评论提交预算的计算方（云端下发或边缘回报）并在该侧按「实际会被打进编辑器的完整串」计算，另一侧改为据传输值派生
- [ ] 8.2 删除非计算方的常量副本（`aidcp-cloud/src/comment-agent/facebook-edge-steps.ts:46-57` 与 `aidcp-edge/src/native-page-engine/browse-session.ts:65-71` 其中一份）
- [ ] 8.3 加回归：带群聊码后缀的评论上，判定方的等待窗口不短于执行方的命令预算；慢但成功的提交不会被判超时
- [ ] 8.4 加回归：改动预算常量时只有一处声明变化，不存在第二份公式可以保留旧值
  - 本轮未做（2026-07-29）：整节落 `aidcp-cloud`，本轮不碰该仓（三个提交全部落在 `aidcp-edge`）。需边缘侧 `browse-session.ts:65-71` 与云端 `facebook-edge-steps.ts:46-57` **同批**处置，归后续波次。

## 9. 验证 / 验收

- [ ] 9.1 `cd ../aidcp-edge && npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）
  - 阶段性记录（2026-07-29，`aidcp-edge` worktree `native-migration-repair` @ `74eaf41`）：**30/30 全过**（1 条 gated 跳过 = 需真机的 E2E）。change 未收口，本条不勾。
- [ ] 9.2 `cd ../aidcp-edge && npm test` 与 `npm run typecheck`
  - 阶段性记录（2026-07-29）：`npm test` **2676 例 / 2675 绿 / 0 红 / 1 跳过**；`npm run typecheck` **通过**。另实测 `npm run build:dist` **通过**（`reachable=77 removed=68 legacy_page_rules=absent page_rule_fragments_guarded=11 source_maps=absent`）。change 未收口，本条不勾。
- [ ] 9.3 `cd ../aidcp-edge/native/page-engine && cargo fmt --check && cargo clippy -- -D warnings && cargo test --locked`
  - 阶段性记录（2026-07-29）：`npm run gate:native` **通过**（fmt + clippy `-D warnings` + test），toolchain `1.97.1-aarch64-apple-darwin`。change 未收口，本条不勾。
- [ ] 9.4 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`
  - 本轮不适用（2026-07-29）：第 8 节整节未做、`aidcp-cloud` 零改动，故未跑云端闸。第 8 节落地时补跑。
- [x] 9.5 在本文件记录 1.2 对账检查的完整输出（命令名 + 不匹配回执名 + 结论），以及冻结清单的初始条目数；后续 change 只许该条目数下降 <!-- aidcp-edge 74eaf41 完整输出与冻结清单条目数如下 -->

  **对账口径**：声明集 vs 成功路径可达发出点的**跨平台并集**；排除 `reportFailure` 失败路径；随行观测按该命令实际可能携带的载荷分支计算（看图翻页只可能带 `noteDetail`，分类通知只可能带 `notificationItems`）。26 条经浏览会话下发的命令全覆盖；12 条发布命令与 4 条带外命令（`captcha_capture` / `captcha_click` / `wechat_capture_session` / `identity_bootstrap`）另行登记出口、不进本对账。

  **不一致共 14 条，逐条结论**：

  1. `plan_execute` 声明 `["action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」
     - reachable_but_undeclared: `action.result` → 结论「改声明」（成功恒回 `plan_results`，宿主发 `action.result`）
  2. `session_stop` 声明 `[]`
     - reachable_but_undeclared: `action.completed` → 结论「改声明」（两平台成功都回动作回执）
  3. `page_scroll` 声明 `["page.cards","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」（成功恒回卡片；`action.completed` 只在信封为 `search.execute` 时补发）
  4. `feed_refresh` 声明 `["page.cards","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」
  5. `note_open` 声明 `["note.detail","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」（与起草期结论一致）
  6. `profile_open` 声明 `["profile.detail","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」
  7. `notification_open` 声明 `["notification.home","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」
  8. `notification_browse_comments` 声明 `["notification.items","action.completed"]`
     - declared_but_unreachable: `action.completed` → 结论「改声明」
  9. `notification_browse_likes` 声明 `["action.completed"]`
     - reachable_but_undeclared: `notification.items` → 结论「改声明」（随行观测带条目）
  10. `notification_browse_follows` 声明 `["action.completed"]`
      - reachable_but_undeclared: `notification.items` → 结论「改声明」
  11–13. `notification_back_home` 声明 `["notification.home","action.completed"]`
      - declared_but_unreachable: `notification.home` → 结论「改声明」
      - declared_but_unreachable: `action.completed` → 结论「改声明」
      - reachable_but_undeclared: `page.cards` → 结论「改声明」（成功回的是首页卡片）

  （以上 14 条**全部为「改声明」，无一条判「补发出」**——没有任何一条云端角色期望的回执是实现该发而没发的。）

  **对账判定为一致、不得当成缺口的**：
  - `search_execute`：两条回执确实都发（`page_cards` 分支在信封为 `search.execute` 时同时报动作完成）——与起草期结论一致。
  - `note_close` / `navigation_back`：声明 `["action.completed","page.cards"]` 两条**都可达**（小红书回动作回执、Facebook 的 `execute_facebook_back_to_list` 回卡片）——**起草期结论在此被推翻**，详见 1.2。
  - `note_browse_images`：声明 `["note.detail","action.completed"]` 两条都可达（随行观测带 `noteDetail` 快照时发详情）。
  - 其余（`browse_next` / `browse_scroll` / `interaction_*` / `group_join` / `note_scroll_comments` / `identity_read_current` / `identity_read_self_profile` / `notification_browse_comments` 的 `notification.items` 一侧）声明与可达完全一致。

  **冻结清单初始条目数：14**（`FROZEN_GAP_BUDGET = 14`，检查断言只许下降；同时断言清单里不许留已消除条目）。

  - 对账检查自身的已知盲区（2026-07-29 登记）：「每条命令的成功输出 kind」那一侧（`BROWSE_SUCCESS_OUTPUTS`，26 条，每条注明来自哪个 Rust 分支或页面规则分支）是**带出处引用的人工登记表**，键集被强制等于命令映射表；`report()` 那一侧与随行载荷分支是从源码机械导出的。后果：新增命令必须登记（漏登即失败），但**既有条目若被实现悄悄改掉输出 kind，检查抓不到**。要机械化这一侧需从两份页面规则与 Rust 分支导出「命令→输出 kind」表，属独立工作量，建议随后续 change 评估。
  - **既有 flaky 登记（非本 change 引入、非本 change 职责，2026-07-29）**：`facebook::publish::tests` 的三条截止线用例（`select_mode_reports_ambiguous_after_one_unconfirmed_click` / `select_mode_is_ambiguous_when_post_click_confirmation_crosses_the_deadline` / `submit_does_not_confirm_when_the_submitted_probe_crosses_the_deadline`）给的是 `unix_time_ms()+150` 这类**绝对墙钟预算**，机器高负载时会退化成 `NotStarted`；同一二进制连跑三次实测为 失败 / 通过 / 失败，机器空闲时全绿。后果是 CI 或多 agent 并行跑测试时会随机变红、**掩盖真实回归**。另有 `test/native-page-engine/client.test.ts` 的「rejects a ready engine whose capability manifest differs from the packaged contract」（`processTimeoutMs=500`）同属负载敏感 flaky。`publish.rs` / `publish_tests.rs` 本轮不在改动面，此处仅登记。

- [ ] 9.6 运行 `openspec validate harden-native-engine-runtime-contracts --strict`
  - 阶段性记录（2026-07-29）：已运行，输出 `Change 'harden-native-engine-runtime-contracts' is valid`。change 未收口（第 3.2、5.1、5.3、6.x、7.4、8.x 未完成），本条留到收口时勾。

### 9.7 真机验收项（本 change 不执行，登记进 `docs/real-machine-acceptance-backlog.md`）

以下均为**推断，未在真机坐实**，不得当成既成事实：

> 本轮（2026-07-29）**零真机动作**：未打安装包、未部署、未在真机上做任何读写。9.7.1–9.7.11 全部原样保留。

- [ ] 9.7.1 跨环境错投的真实发生概率：同机多环境并行时，指纹浏览器释放的调试端口被另一环境复用的频率与分配策略，未实测；需在真机上观察端口回收行为后再评估 6.2 身份证据判据是否足够
- [ ] 9.7.2 空根塌陷需要导航瞬时窗口（`document.body` 为 `null`）才触发，**未复现**；已发生过的那一次是同构但不同调用点。复核实读后进一步收窄：5 处兜底取根里只有 `20-feed.js:253` 无空判，且它在**读命令**（`note_open`）路径上——「写命令因空根被记成可能已做」当前**没有已坐实的路径**，只是取用层零防护带来的结构风险。需真机验证 7.2 改动后该窗口内 `note_open` 的实际结论是「未开始」而非在页面内抛异常
  - 补充（2026-07-29）：该窗口现已可在 jsdom 里复现（摘掉 `document.body` 后 `note_open` 走到 `currentDetail()`），并已有回归断言回 `target_not_found`；**真机仍需验证导航瞬间的实际结论**。
- [ ] 9.7.3 「引擎死 → 结束会话失败 → 下次开始还是同一个死会话」这条链路是从代码路径推出的，未在真机日志里确认过实例；需真机杀一次引擎子进程验证 5.3 的恢复行为
- [ ] 9.7.4 重连后重试占死唯一命令槽位、宿主预算过后放弃等待且不发取消，导致后续命令被顶回——未在真机日志确认过实例；需真机制造一次 CDP 断连后观察
- [ ] 9.7.5 小红书开帖是否真的落到 404，需真机判定（开帖后看地址是否带令牌、返回的详情正文是否为空）；若单页应用拦截了程序化点击而导航仍走内部路由，该条应降级为纯指纹问题而非假成功
- [ ] 9.7.6 看图命令导致的深读永久挂起直到会话看门狗杀场，是从代码路径推出的，未在真机日志里确认过实例
- [ ] 9.7.7 「所有 Facebook 布局下都不存在带数字的中性按钮」未在真机核验；若某些布局的中性按钮文本含数字，热度读数会变成随机偏差而非恒零
- [ ] 9.7.8 小红书提交窗口缺失目前「只表现为接管失败、不撕裂写入」这一结论，依赖「写命令不做飞行中取消」的当前实现，未真机复现
- [ ] 9.7.9 CI 上实际生效的 Rust 编译器版本（工作流选的稳定版 vs 目录里钉的 1.97.1）是按行为推断判定的，没有拿到 CI 运行日志；产物里不记录编译器版本，事后无法对账。此项归 `enforce-native-engine-artifact-gates` 的产物清单字段范围，本 change 只登记
- [ ] 9.7.10 「小红书通知去重键折叠」「行选择器退化」的后果规模没有线上数据支撑，只有代码与旧注释的对照
- [ ] 9.7.11 简报 C 段提到的七个簇里「维持原判」条目（F-IPC / INJ / TXT / PACE / GEST / TIME / RETRY / PLAT-OBS / BUILD / DRIFT 系列编号）只给了编号、没有正文与原始状态；本 change 未据其编号做任何断言，需补齐正文后再并案

### 9.8 明确不做

- [x] 9.8.1 不部署（dev / ol 均不做）；不出安装包、不做签名公证 <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：未部署 dev/ol、未跑 electron:build、未做签名公证 -->
- [x] 9.8.2 不做任何真机写动作（点赞 / 评论 / 加群 / 发帖） <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：零真机动作，全部验证为本地代码级 -->
- [x] 9.8.3 不改 Cloud↔Edge 协议 v2 消息集合、动作名口径与命令映射；不改风控状态机与配额档位 <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：两份 protocol.ts 与 command-bridge 动作映射零改动，AC-PROTO-* 全过、消息总数不变；风控状态机与配额档位未触碰 -->
- [x] 9.8.4 不改 `openspec/specs/` 下任何文件 <!-- aidcp 2026-07-29 本轮实测成立：控制仓只写本 change 与 restore-native-xiaohongshu-session-guards 两份 tasks.md -->
