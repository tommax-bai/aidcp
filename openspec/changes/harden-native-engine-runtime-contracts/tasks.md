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

> **3.2 本轮延后（2026-07-31，用户裁定；仍是待办，不弃守）。** 事实源已收口到宿主、引擎数字已降为「请求值」、
> 机械对账用例已防漂——**危害已经消除**，剩下的是把线路上那个失效字段物理删掉，属整洁工作。
> 且它要同时动四个文件的结构，收益与代价不成比例。留待下一轮连同 §8 一起做。

- [x] 3.1 确定提交窗口标签与预算的单一事实源（宿主侧常量或命令清单产物二选一），删除另一侧的独立数字声明 <!-- aidcp-edge 74eaf41 事实源定为宿主 client.ts 的 NATIVE_COMMIT_WINDOW_BUDGETS；引擎侧降为「标签+镜像数字、运行期不作数」，新增机械对账用例：单边改一个数字仓库检查当场失败 -->
  - 决策记录（2026-07-29）：事实源选宿主常量而非清单产物，直接原因见 1.3 的跨 change 依赖——清单产物的摘要被 Electron 侧常量反向绑定，本 change 动不了。
  - 该表同时是**准入名单**：标签不在表内即拒发窗口。并行流在 b57d619 接上的五条小红书窗口请求，其标签在本提交内一并加入（`xhs_comment_submit`=4000 / `xhs_notification_comments`=20000 / `xhs_notification_likes`=20000 / `xhs_notification_follows`=20000 / `xhs_publish_submit`=15000）；对账用例同批扩到**同时读两份引擎源**（`facebook/capability.rs` + `commit_window.rs`），只读一份会让另一份完全没有闸。
- [x] 3.2 改造引擎侧：按标签请求窗口，不再随请求发出自写的预算数字
  - <!-- aidcp-edge (见集成后 sha) 引擎侧三个窗口常量的数字已删，线路上只剩标签；宿主 `client.ts` 的请求类型改为不含预算，按标签发放后再组装成带预算的形状——「谁说了算」因此在类型上就看得见。兼容性两个方向都不破（旧宿主收不到字段按自己的表发放，新宿主忽略旧引擎带的字段），故不动协议版本。 -->
  - **具名能力去除（如实登记，非遗漏）**：本条同时去掉了「引擎可以要一个**更短**的写保护窗口」这个能力。
    旧设计是宿主取 `min(引擎请求, 事实源)`，注释明写「引擎可以要更短，不能要更长」。
    3.2 要求线路上不再有引擎自写的数字 —— 两者**物理上不可兼得**。
    - **生产影响为零，且这是可核的而非假设的**：引擎原来发的三个数字（27750 / 30000 / 30000）
      与宿主表里的三个**逐字一致**，所以取 min 与按标签发放对每个已存在的标签都返回同一个数。
      测试夹具里那个 18500 是**刻意造的差异值**，只为让 min 这条路可观测。
    - **是全量 TypeScript 测试抓出来的**：假引擎当时还在发那个字段、用例还在断言旧语义。
      **`gate:native` 与 `test:acceptance` 都覆盖不到这条** —— 记下来，别把全量测试当可跳过的。
（`native/page-engine/src/facebook/capability.rs` 的 `JOIN_WINDOW` / `COMMENT_WINDOW` / `PUBLISH_WINDOW`）
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

> **5.1 / 5.3 本轮延后（2026-07-31，用户裁定；仍是待办，不弃守）。** 自愈的**主干已经在**：5.2 / 5.4 让「缓存句柄必须拿到
> 存活肯定证据、拿不到就丢弃重开」生效，所以「引擎死了下一条命令还打在死句柄上」这条已经堵住。5.1 补的是另一条口子
> （结束会话命令**自己**失败时收尾不执行），只有两行，但落点归 `browse-session.ts` 的单写者。
> **本轮若因 §6 的接线工作打开了该文件，就顺手一并做掉并在此回写 sha**；否则留下一轮。

- [x] 5.1 把 `src/native-page-engine/browse-session.ts:141-142` 的会话结束收尾从成功路径移到 `finally`，使结束会话命令失败时收尾仍执行 <!-- aidcp-edge 0a5167e 收尾移进 finally，位置在 active/activeAbort 复位之后（此刻命令已落定，停机的中止信号不会打到一条还在跑的命令上）。注释写明后果链：收尾不做 = owner 位不释放 + 周期观测不停 ⇒ 下次开始拿到的还是同一场死会话，而云端只看到一条普通失败、没有任何东西指向「这个环境已经变砖」 -->
  - 本轮未做（2026-07-29）：落点 `src/native-page-engine/browse-session.ts` 归并行流（该文件本轮被 b57d619 大改）。实读 HEAD 仍是 `await active;` 之后紧跟 `if (env.type === 'session.end') this.stop('cloud_session_end');`（:245-246），`finally` 块只复位 `active` / `activeAbort`——**命令失败时收尾仍不执行，缺口原样保留**。需在 browse-session.ts 的单写者手里落。
- [x] 5.2 给 `src/native-page-engine/runtime.ts:128-131` 的会话缓存加存活判据（现为命中即返回、零判据）：返回缓存句柄前必须**取到存活的肯定证据**（如子进程未退出且通道可写），取不到即按已死处理、丢弃并重开——「没记到死讯」不算存活证据 <!-- aidcp-edge 74eaf41 client.ts 新增 NativeProcessTransport.isLive()（握手完成 + 未退出 + 未被 kill + exitCode/signalCode 均为 null + stdin.writable）与会话级 isLive()；runtime.ts 的 sessionFor 取不到证据即丢弃重开，新增 discardSession() 让收尾失败不堵住重建入口 -->
  - 非空转验证：把 `cached.session.isLive()` 临时短路成 `true` 后，会话自愈 3 条里有 2 条失败（随即还原并以 `git diff` 确认）。
- [x] 5.3 加回归：引擎进程已退出时下发结束会话 → 该命令失败，但 owner 被释放；随后一条命令能重建引擎并正常执行 <!-- aidcp-edge ef1258f 新增用例「引擎已死时下发结束会话：命令诚实报失败，且收尾照做（owner 释放 + 周期观测停）」，落在 test/native-page-engine/runtime-contracts-session-recovery.test.ts。**做了变异归因、不是只看全绿**：把收尾从 finally 挪回成功路径后，恰好只有这条新用例变红、同文件另三条仍绿。前置里先 start() 一次让周期观测真的武装，否则「观测停了」这条断言在一个从未起拍的观测上恒真（memory gate-always-true-equals-gate-gone） -->
  - **【已完成 2026-08-05】** 上一轮登记的「改对了但没有断言钉着」已消除。真机侧对照项
    （`docs/real-machine-acceptance-backlog.md` 簇 124.2，杀一次引擎子进程验恢复）**仍然保留**——
    它验的是真进程行为，与这条脱机回归互不替代。
  - **⚠ 本条原文的前半句今天已不成立，是实测发现，不是措辞问题。** 原文写「引擎进程已退出 → 该命令失败」，
    而它写于 5.2 / 5.4 之前。用真引擎实跑：结束命令**不会失败**——运行时的存活判据先一步认出缓存句柄是僵尸、
    丢弃重开，于是这条命令落在**新**引擎上正常成功。**「引擎已退出」单独不再构成结束命令的失败原因。**
    5.1 真正护住的是更一般的一类：**结束命令因任何原因失败**（重建也起不来 / 页面规则报错 / 中途被接管）时收尾照做，
    新用例喂的正是这一类。原文后半句「随后一条命令能重建引擎」**未另写用例**：
    它已由同文件既有那条真引擎用例（断言前后 pid 不同）钉住，再写一条只会重复，
    且会把一条必然自愈的路径伪装成失败路径。判断已写进测试文件的注释块里。
  - 偏离说明（2026-07-29）：**只落了 runtime 层那一半**。已有用例「引擎已退出时释放 owner：收尾失败不堵住重建入口」（校验新旧引擎 pid 不同），`closeOwner` 打在已死句柄上不再把异常抛给调用方（调用点是 `void closeOwner(...)`，抛出去即未处理拒绝）。缺的是「**下发结束会话命令**」这条入口——它依赖 5.1，同属 browse-session.ts 单写区。
- [x] 5.4 加回归：缓存会话的传输已死时，下一条命令走重建而不是立刻抛「引擎已退出」 <!-- aidcp-edge 74eaf41 runtime-contracts-session-recovery.test.ts 3 tests / 3 pass：传输已死走重建 + 外部 SIGKILL（宿主完全没机会记到死讯）后仍能重建 + 健康会话必须被复用（判据不许严到每条命令重开引擎） -->

## 6. aidcp-edge — 重连绑定与预算

- [x] 6.1 让引擎重连时重新向宿主/提供方解析端点，不再复用 `native/page-engine/src/engine.rs` 会话结构里存的 `host` / `port`；宿主侧 `runtime.ts` 相应提供会话期内可重复取值的端点解析入口（当前 `getEndpoint()` 只在建会话时调用一次）
  - <!-- aidcp-edge 559d6dc 已落，两半同批。引擎侧新增 `endpoint_resolver.rs`（引擎→宿主的端点请求通道，形状照抄既有的提交窗口请求器），重连改为「重解析端点 → 实读身份 → 比对基线 → 才列目标」；宿主侧 `runtime.ts` 的 `getEndpoint()` 变成会话期可重复取值的解析入口，`client.ts` 应答端点请求时回**当前**端点、解析不出就诚实回空。**宿主说解析不出即报错、绝不静默沿用旧值。** -->
  - **顺带照顾了第二个端点生产者**：`src/wechat-channels/browser-sidecar.ts` 捕获的是冻结端点、永不重解析，它靠每次 open 新建运行时来满足契约——已加注释，防将来改成原位重启时静默失效。
- [x] 6.2 给 `native/page-engine/src/endpoint.rs:214-226` 的 `select_target`（现判据仅「目标类型 page + 平台 URL 允许集 + 调试地址端口」）增加分身身份证据判据；身份证据的具体载体在实装期与浏览器提供方一侧确定后记录在此。现成候选：provider 认领失联浏览器用的「`<profileId>_` 前缀缓存目录 + `DevToolsActivePort` 标记」（`src/cdp/browser-provider.ts:728-745`）
  - 偏离说明（2026-07-29）：**判据与失败语义已在 `endpoint.rs` 内落成并单测覆盖，但尚未接线到真实附着路径 —— MUST NOT 当成已生效的防护**。已落：`BrowserInstanceIdentity`（:233）+ `read_browser_identity()`（:259，经 CDP `GET /json/version` 读取）+ `select_target_for_instance()`（:281）；`cargo test --lib endpoint::` 10/10 通过，含 `refuses_to_attach_without_proven_instance_identity` 与 `browser_instance_identity_comes_only_from_a_browser_debugger_url`。
  - **身份证据载体已确定并记录**：浏览器级调试地址 `/devtools/browser/<uuid>`（换浏览器进程必换值，**端口回收复用带不过去**），非起草期候选的缓存目录 / `DevToolsActivePort`。
  - <!-- aidcp-edge 559d6dc **接线缺口已补齐，防护现在真生效**。会话结构此前只有 host/port、零身份字段，现在带上准入时的浏览器实例身份；身份由宿主随开会话参数传入（`SessionOpenParams` 新增可选字段 + `#[serde(default)]`，旧宿主仍能解析；值畸形当场拒绝、不当作「没给」）。宿主侧证据是**现成的**：指纹浏览器就绪轮询本来就在实读 `/json/version` 却把响应体丢了，现在返回浏览器级调试地址；自带 Chrome 那条走同形状的尽力而为读取（读不到不致命）。`endpoint.rs` 把身份那一半析出成 `ensure_admitted_instance` 供附着路径先行把关，判据逻辑一行没重写 -->
  - **开会话时刻仍走老判据，有意为之**：开会话去自读身份需要多一次网络往返，会把 13 个单次应答、不按路径分发的测试假服务端全部打坏；且那一刻**没有可比对的独立事实**（宿主刚把浏览器交过来）。已在代码里写明理由。防护落在重连——那正是端口被回收复用的时刻。
- [x] 6.3 无法取得身份证据、或无候选目标可证明属于被准入实例时，返回诚实的执行器健康类失败，不附着任何目标
  - 语义已落成（`EndpointUnreachable`，消息点名「无法自证是被准入的浏览器实例」，**不附着任何目标**，绝不退化成端口对上就接管）。<!-- aidcp-edge 559d6dc 已接线并端到端覆盖。无基线时**在碰端点之前就拒绝**——去碰也只能碰出一个无从比对的读数，那不叫证据。 -->
- [x] 6.4 把 `engine.rs:509-528` 重连后的重试纳入与首跑相同的绝对截止线包裹，超时即释放单命令槽位并回超时
  - <!-- aidcp-edge 559d6dc **实测结论：一半本来就满足、另一半是空转，而且两者是耦合的**。截止线确实同时传给了重连与重试、重连内部也按剩余预算包了超时——这半没问题。但**重试那次调用本身没有任何超时包裹**：任何不自行守截止线的内层步骤（CDP 请求被收下却永不应答）会永久挂住。而「超时即释放单命令槽位」结构上存在（出结果后无条件清空活动命令）却**空转**——它只在命令返回时才触发，无界重试永远不返回，于是活动命令槽位永远占着、后续命令全被顶回且无人能恢复。**给重试加上剩余预算包裹，才让槽位释放这件事真正成立。** 注：探针路径本来就安全（自算预算），缺口只在平台命令那条。 -->
- [x] 6.5 加回归：重连 + 重试的总耗时不超过原命令预算；预算耗尽后槽位被释放，下一条命令不再被 `CommandInProgress` 顶回
  - <!-- aidcp-edge 559d6dc 落在 `tests/runtime_contracts_reconnect_binding.rs`。**变异验证**：把重试的超时包裹去掉即转红（外层 6 秒守卫触发＝证明重试真的是无界的），不是空断言。 -->
- [x] 6.6 加回归：候选目标的端口对上但身份证据不匹配时，引擎拒绝附着且不执行任何命令
  - <!-- aidcp-edge 559d6dc 「且不执行任何命令」这一半现在端到端断言得上了：新用例用**按路径分发**的假浏览器，靠访问轨迹证明引擎连入侵者的目标列表都没去要。**归因已由控制仓独立复现**（不是只看「改完全绿」）：把身份闸换回老判据后重编（确认出现 Compiling、未踩「还原不重编」的坑），该用例当场转红，另三条如常绿——因为只变异了身份这一处。 -->

## 7. aidcp-edge — 取根、诊断与焦点守卫的诚实归因

> **7.4 本轮延后（2026-07-31，用户裁定；仍是待办，不弃守）。** 三态判定**已经落成**（求值失败 / 输出缺失 / 真丢焦点已分开、
> 13 条单测覆盖），诚实性缺口已消除；剩下的是把「读不到」这一态的外显原因码单独拉出来，属粒度问题不属真假问题。
> 且新增枚举变体会打断三处穷举匹配的编译、牵动四个文件。留待下一轮。

- [x] 7.1 在 `native/page-engine/src/facebook-router/00-shared.js:13-19` 的共享取用函数（`all` / `first`）里加空 root 防护，使传入空 root 时返回可归因于「无有效根」的空结果而非抛 `TypeError`（当前直接对传入 root 调 `querySelectorAll`，零防护） <!-- aidcp-edge 74eaf41 新增 rooted() 判据（必须是带 querySelectorAll 的对象），空根回空结果不抛；缺省参数语义不变 -->
- [x] 7.2 修 `20-feed.js:253` 的 `currentDetail()`：`… || document.querySelector('main') || document.body` 之后无空判、直接进 `noteDetail(root, permalinkOf(root)…)`，是**当前唯一实读坐实会把空根交给遍历**的取根点（行号按 `aidcp-edge@9cd7691`；简报给的 `87,147,233` 已被 07-28 改动顶偏）。改为取不到有效根时返回诚实的未开始理由 <!-- aidcp-edge 74eaf41 currentDetail() 兜底链落空时回 action('open',false,'target_not_found')（现址 :254），不再把空根交给详情遍历；jsdom 摘掉 body 后先断言 document.body===null 再跑 note_open -->
- [x] 7.2.1 交叉核对另 4 处 `|| document.body` 取根点（`20-feed.js:87,154,166` 与 `40-group-join.js:103`）：起草期实读结论是它们下游均空安全（`:87` 紧跟 `if(!scope)return`；`:154` 只进 `node&&…` 循环；`:166` 只以 `scope&&…` / `all(…,scope||document)` 使用；`40-group-join.js:103` 进 `targetGroupScope`，其 `:50-51` 首行即 `if(!groupId||!main)return`）。若实装期复读推翻某一处，按 7.2 同样处理并在此记录；结论不变则不改这 4 处，**不做空转补丁** <!-- aidcp-edge 74eaf41 逐处复读，起草期结论不变（现址 :86/:153/:165 与 40-group-join.js:103），按要求未做空转补丁 -->
- [x] 7.3 给 `native/page-engine/src/xhs.rs:66-72` 与 `native/page-engine/src/probe.rs:89-98` 的结果解码入口补上与 `facebook.rs:607-620` 同级的有界解码诊断（阶段 / 字段路径 / 异常位置），且诊断保持有界、不含页面正文与凭据。**先核对**并行 change `restore-native-xiaohongshu-session-guards` 是否已把解码入口一并覆盖；已覆盖则划掉本条、不重复实现 <!-- aidcp-edge 74eaf41 先核对：并行 change 未覆盖（xhs.rs/probe.rs 仍是裸错误），故补上同级诊断（阶段/字段路径/异常类别与原因/标识符/行列）；构造函数只写一份放在 probe.rs 由 xhs.rs 共用 -->
  - 残留（2026-07-29）：诊断实现现为 **2 份覆盖 3 个入口**（原为 1 份覆盖 1 个）。`facebook.rs:911-1080` 里那份等价实现是私有函数，本轮不可编辑该文件；收口到 `error.rs` 留给后续。
- [x] 7.4 在 `native/page-engine/src/input.rs:108-128` 区分「焦点守卫求值失败或输出缺失」与「焦点确实丢了」两类结论（通道失败已单列为 `Engine`，保持不变） <!-- aidcp-edge 0a5167e 新增只活在守卫路径上的失败类型，不往共享枚举里加变体。**理由值得留给后人**：那个共享枚举被 7 处穷举匹配消费、其中 5 处根本不带守卫，加变体会逼那 5 处各写一条「此路不可达」分支——每一条都是把「结构上不会发生」变成「发生了我就随便报一个」的机会。用类型把它圈在守卫路径里，不带守卫的调用方连看见它的机会都没有。通道失败仍单列，未动。配套用例断言「读不出焦点」与「读到焦点丢了」在回执上可分，停手行为两者完全一致——所以那条断言就是归因诚实本身 -->
  - 偏离说明（2026-07-29）：**三态判定已落成，但外显原因码尚未三分**。已落 `FocusGuardVerdict{Focused, Lost, Unreadable}`（`input.rs:139`）：页面抛异常 / 输出缺失 / kind 不对 / 布尔字段不是布尔 = `Unreadable`，只有守卫确实回「目标不在或没聚焦」才是 `Lost`；`cargo test --lib input::` 13/13 通过，含 `focus_guard_separates_unreadable_from_a_real_focus_loss`（1 正 3 反 5 未知）。**但 `Unreadable` 当前映射到 `TextInputFailure::Engine`**，与本条括注「通道失败已单列为 Engine，保持不变」的三分要求不符。
  - **可观察副作用（云端口径会变）**：Facebook 发帖填写这一支的失败原因码由 `composer_focus_lost` 变为 `engine_error`（**仅限守卫求值失败 / 输出缺失这一支**；守卫真回「没聚焦」仍是 `composer_focus_lost`）。这是有意为之——宁可粒度降级，也不把「不知道」说成「知道是坏的」。云端若曾按 `composer_focus_lost` 做过统计，口径会变。
  - 专用变体 `TextInputFailure::GuardUnreadable` 本轮 defer：新增枚举变体会打断三处穷举 match 的编译（`engine.rs:782-791/1348-1351`、`facebook/comment.rs:221-232`、`facebook/publish.rs:612-619`），四个文件均在其他单写区。
- [x] 7.5 加回归：① 取用函数收到空 root → 回可归因的空结果、不抛（写命令路径因此不会被判 `Ambiguous`，对照 `engine.rs:532-543` 的「写 + 任何规则错误 → Ambiguous」）；② 导航瞬间无有效根 → `note_open` 回未开始而非抛；③ 非 Facebook 平台解码失败 → 携带同级诊断；④ 守卫求值失败 → 与目标丢失是两个不同结论 <!-- aidcp-edge 74eaf41 四条全落地：runtime-contracts-page-rules.test.ts 3 tests（null/{}/字符串/0 全回空、有效根照旧、jsdom 摘 body 后 note_open 回 target_not_found）+ runtime_contracts_decode_diagnostics.rs 3 tests（含「诊断绝不能带页面正文或凭据」：cookie 值 / 中文正文 / 带空格的伪标识符都不落盘，整串 ≤512 字节）+ input:: 焦点守卫 1 test -->

## 8. aidcp-cloud — 评论预算传输而非重算 —— **已摘出本 change（2026-07-31 用户裁定）**

> 整节四条落到 `docs/cloud-orchestration-residuals-descoped-2026-07-31.md` §B。
>
> **摘出的判据是「Rust 迁移碰过它没有」**：评论提交预算的公式云端与边缘各写了一份，
> 这在 JS 时代就是两份，**迁移一行没碰过**。它的危害方向也是**诚实的**（错报失败：长评论被判超时），
> 不是本批要处置的静默假成功 —— 这也是它此前被反复延后的真实原因。
>
> **摘出 ≠ 弃守**：零开工，缺陷仍在、立论仍成立，只是换了账本归属，待正式立项。
>
> **⚠️ 一个此前被写混的点，摘出时已澄清**：原抬头写「留待下一轮连同 3.2 一起做，两条是同一件事的两半」，
> 这句**不准确**。§3 是**提交窗口**（引擎向宿主请求写窗口时长，纯边缘内部）；
> 本节是**评论提交预算**（云端判定方的等待窗口 vs 边缘执行方的命令预算，跨仓）。
> **不同的常量、不同的文件，只是主题相近。3.2 因此不受本次摘出影响，仍留在本 change。**

## 9. 验证 / 验收

- [x] 9.1 `cd ../aidcp-edge && npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过） <!-- aidcp-edge ef1258f 实测 39/39 全过（AC-PROTO / AC-PUB / AC-RISK 安全红线在内）；rebase 到 origin/master bdc652f 之后复跑一次仍 39/39 -->
  - 阶段性记录（2026-07-29，`aidcp-edge` worktree `native-migration-repair` @ `74eaf41`）：**30/30 全过**（1 条 gated 跳过 = 需真机的 E2E）。change 未收口，本条不勾。
- [x] 9.2 `cd ../aidcp-edge && npm test` 与 `npm run typecheck` <!-- aidcp-edge ef1258f 实测 npm test 3153 例 / 3152 绿 / 0 红 / 1 跳过（跳过的是 gated 的 AC-E2E 真机层）；typecheck 通过，rebase 后复跑仍通过。§12 登记的那条既有 flake 本轮两次全量均未触发 -->
  - 阶段性记录（2026-07-29）：`npm test` **2676 例 / 2675 绿 / 0 红 / 1 跳过**；`npm run typecheck` **通过**。另实测 `npm run build:dist` **通过**（`reachable=77 removed=68 legacy_page_rules=absent page_rule_fragments_guarded=11 source_maps=absent`）。change 未收口，本条不勾。
- [x] 9.3 `cd ../aidcp-edge/native/page-engine && cargo fmt --check && cargo clippy -- -D warnings && cargo test --locked` <!-- aidcp-edge ef1258f 经 npm run gate:native 跑（它按 rust-toolchain.toml 解析钉死工具链，比直接 cargo 更能保证跑的是同一个编译器）：OK toolchain=1.97.1-aarch64-apple-darwin steps=fmt,clippy,test，clippy 带 -D warnings。注：cargo 不在默认 PATH，须先 export PATH="$HOME/.rustup/toolchains/1.97.1-aarch64-apple-darwin/bin:$PATH" -->
  - 阶段性记录（2026-07-29）：`npm run gate:native` **通过**（fmt + clippy `-D warnings` + test），toolchain `1.97.1-aarch64-apple-darwin`。change 未收口，本条不勾。
- [x] 9.4 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck` <!-- 2026-07-31 **不适用**：本条存在的唯一理由是 §8 的云端改动，而 §8 已随本次裁定摘出（见该节抬头）。**本 change 至此零云端改动**，跑云端测试没有对象。若将来重新纳入云端工作，本条须跟着回来。 -->
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

- [x] 9.6 运行 `openspec validate harden-native-engine-runtime-contracts --strict` <!-- aidcp 本次 实测输出：Change 'harden-native-engine-runtime-contracts' is valid -->
  - 阶段性记录（2026-07-29）：已运行，输出 `Change 'harden-native-engine-runtime-contracts' is valid`。change 未收口（第 3.2、5.1、5.3、6.x、7.4、8.x 未完成），本条留到收口时勾。

### 9.7 真机验收项 —— **已移出本清单（2026-07-31 用户裁定）**

> 原 9.7.1–9.7.11 共 11 条已统一收拢到 `docs/real-machine-acceptance-backlog.md`，
> 不再计入本 change 的任务数、不再阻塞归档：
> **簇 124**（重连绑定 / 同机多环境端口回收）承接 9.7.1 / 9.7.3 / 9.7.4；
> **簇 125**（小红书 Native 切换）承接 9.7.2 / 9.7.5 / 9.7.6 / 9.7.8 / 9.7.10；
> **簇 126**（Facebook 残余对齐）承接 9.7.7；
> **簇 127**（产物门禁打包与 CI）承接 9.7.9，并登记 9.7.11 为引用悬空的资料缺口。
>
> **口径不变**：登记 ≠ 已验证。这 11 条**至今无人在真机上确认过**，
> MUST NOT 因本 change 归档而读成「验过了」。

### 9.8 明确不做

- [x] 9.8.1 不部署（dev / ol 均不做）；不出安装包、不做签名公证 <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：未部署 dev/ol、未跑 electron:build、未做签名公证 -->
- [x] 9.8.2 不做任何真机写动作（点赞 / 评论 / 加群 / 发帖） <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：零真机动作，全部验证为本地代码级 -->
- [x] 9.8.3 不改 Cloud↔Edge 协议 v2 消息集合、动作名口径与命令映射；不改风控状态机与配额档位 <!-- aidcp-edge 74eaf41 2026-07-29 本轮实测成立：两份 protocol.ts 与 command-bridge 动作映射零改动，AC-PROTO-* 全过、消息总数不变；风控状态机与配额档位未触碰 -->
- [x] 9.8.4 不改 `openspec/specs/` 下任何文件 <!-- aidcp 2026-07-29 本轮实测成立：控制仓只写本 change 与 restore-native-xiaohongshu-session-guards 两份 tasks.md -->

## 10. 跨属主改动待追认（他人 change 已改本 change 的属主文件）

> 登记人：`restore-native-actuation-humanization-and-locating` 的第四波收口（2026-07-30）。
> 该 change 的 9.2 表里已自认越界，但**只登记在越界方自己的台账里，属主这边看不到** —— 本节补上。
> **MUST NOT 当成默认通过。**

- [x] 10.1 **【追认 2026-08-05】** 追认或否决对 `test/native-page-engine/runtime-contracts-command-receipts.test.ts` 的改动（`aidcp-edge f652786` 一批）：
  **真因是本 change 的一道门禁被改哑了** —— 它用**源码文本切片**取「已路由命令集合」，
  越界方把那张表改名导出后切片切出**空串**，对账退化成「空集 == 空集」**恒真**。
  改法是直接 `import` 那张表、不再切源码文本。另订正 5 处出处串。
  **属主要判的**：这次是运气好才红（切片正好落空）；**换个写法就是静默恒真**。
  本 change 里是否还有同族的「按源码文本切片取集合再对账」的门禁 —— 若有，应一并换成 import 真实产物。
  - **【追认 2026-08-05】结论：追认，且订正台账 sha。**
    - **sha 记错了**：`f652786` **从未碰过**这两个测试文件（`git show --stat` 实核，它只改了产物门禁那三个文件）。
      本条描述的改动实际来自越界方的 `e748a56` / `1b890ea` / `25fa1c3` 三提交。
    - **改法确认为收紧**：原先按 `const nativeKinds = {` 到第一处 `} as const;` 切源码文本再正则捞 kind，
      改名即切出空串 ⇒ 已路由集合变空集 ⇒ 对账退化成「空集 == 空集」**恒真且不报错**。
      现改为 `import { nativeCommandKindByEnvelopeType }` 直接取那张表。**这正是本仓「闸恒真 = 闸不在」的判例形态**，追认。
    - **同批还改了 5 处 `source:` 说明串**（`xhs-command-router.js …` → `engine.rs execute_xhs_*`）：
      实核为**事实订正**——那几个动作在引擎特化后确实不再走注入路由，不是放宽断言。
    - **属主要查的「同族门禁」已逐条查过，结论是不需要一并改**：本文件另有三处仍从源码文本派生
      （`declaredMethod` / `methodBody` / `reportDispatchTable`，以及对 `protocol.ts` / `command.rs` 的 `assert.match`），
      但**它们每一处都带「找到了没有」的响亮断言**（`assert.ok(start >= 0, …)` / `assert.ok(declaration, …)` /
      `assert.ok(cases.length > 0, …)` / `assert.match(...)`），改名会当场红、不会静默变空。
      **失效模式与被修的那条不同族**：区别不在「切不切源码」，而在**切空之后有没有人喊**。


- [x] 10.2 **【追认 2026-08-05】** 追认或否决对 `test/native-page-engine/runtime-contracts-commit-window.test.ts` 的改动（同批）：
  新增「窗口预算 ≥ 命令墙钟上限」断言，并把镜像门禁的正则改成**能解析常量引用并回查引擎侧**，解析不出即响亮失败。
  **属主要判的**：这条与本 change §3「提交窗口预算单一事实源」同向，但断言归属该落在本 change 还是越界方。
  - **【追认 2026-08-05】结论：追认，且归属问题已由本 change 自己的 §3 交付回答。**
    - **sha 同样记错**：改动来自越界方 `92f7882`，不是 `f652786`。
    - **那条「窗口预算 ≥ 命令墙钟上限」断言今天仍在**（本文件第 106 行起），且**已经不靠正则**——
      改为直接比较导入的 `NATIVE_COMMIT_WINDOW_BUDGETS.xhs_comment_submit` 与 `MAX_NATIVE_TIMEOUT_MS`。
    - **「解析常量引用回查引擎侧」那半已被本 change 的 3.2 取代**：3.2 把引擎侧的预算数字整个删掉、
      收成单一事实源，于是镜像对账无物可对（`21e2018` 据此把该用例改去守一条**新**不变量：
      引擎声明的每个提交窗口标签都必须在宿主准入白名单里——白名单同时是准入闸，
      认不出的标签会拒发窗口，等于在不可逆动作上失去写保护），随后 `0a5167e` 删掉那个被改写孤立的常量解析辅助。
    - **归属结论**：断言归本 change，已由 3.2 一线接管，越界方那半自然消解。**无需通知越界方改动作。**


- [x] 10.3 **【已完成 2026-08-05：两条均追认，结论与订正后的 sha 已写在 10.1 / 10.2 条下；无否决项，故无需通知越界方】** 结论回写对应任务行备注（带 sha）；否决则由属主给出替代形态并通知越界方，**MUST NOT 静默保留**。

## 11. §6 交付记录（2026-07-31 · aidcp-edge `559d6dc`）

**修掉的危害**：同机多环境并行时，指纹浏览器释放的调试端口会被另一环境复用。引擎重连只按
「目标类型 + 平台域名 + 端口」挑目标，**可能附着到别的分身的浏览器上，随后一切动作落在别人账号里**。
这是整批唯一一条会造成「张冠李戴」的缺陷。此前判据整套已写成、单测全过，但**零生产调用方**——
本次做的就是把它接到真实附着路径上。

**重连现在的顺序**：重解析端点 → 实读端点自报的实例身份 → **比对准入基线**（排在列目标之前）→ 才列目标并选中。
无基线 → 在碰端点之前就拒绝。身份证据的载体是浏览器级调试地址里的实例标识，**换浏览器进程必换值、
端口回收复用带不过去**。

**测试与归因**：新增 Rust 侧 4 例（自带**按路径分发**的假浏览器，靠访问轨迹证明「拒绝时连目标列表都没去要」）
+ TypeScript 侧 2 例。**每条都做了变异验证**，不是只看「改完全绿」：

| 用例 | 变异 | 结果 |
| --- | --- | --- |
| 端口对上、实例不同 → 拒绝且零命令 | 重连改回老判据 | 红（访问轨迹显示它去要了入侵者的目标列表） |
| 无基线 → 碰端点之前就拒绝 | 伪造一个基线 | 红（轨迹多出一次身份读取） |
| 浏览器换端口后经宿主重解析找回 | 始终用存下来的 host/port | 红（端点不可达） |
| 重试守住预算且释放槽位 | 去掉重试的超时包裹 | 红（外层守卫触发＝证明重试真是无界的） |

**控制仓已独立复现第一条**（本仓不只转述子代理结论）：把身份闸换回老判据后重编——确认输出里出现
`Compiling`、未踩「还原后 cargo 跳过重编、测的是旧二进制」那个坑——该用例当场转红，另三条如常绿
（因为只变异了身份这一处）。

**一条子代理主动交代的未捕获变异**：给端点解析结果加记忆化**没有**被任何用例抓住——
单次重连场景下没有「更早的解析值」可变陈旧。已换成贴近真实回归形状的用例，**而不是把这个变异留在账外**。

**验证实测**：`test:acceptance` 31/31（安全红线全过）· 全量 `npm test` 2870 tests / 2869 pass / 0 fail / 1 skip ·
`typecheck` 通过 · `gate:native` OK（fmt + clippy -D warnings + cargo test --locked）·
`build:dist` 通过（生产剪枝检查未放宽）。

**两个既有测试夹具被迫更新**（因为重连现在要过身份闸）：断连恢复的假 CDP、Facebook 加群异常的假服务端。
后者**当场暴露了夹具缺口**——不改它会把一条诚实的诊断错误静默变成端点不可达。

### 具名偏离与登记

1. **开会话时刻仍走老判据（有意，非遗漏）**：见 6.2 条下说明。防护落在重连，那正是端口被回收复用的时刻。
2. **端点解析器的无宿主变体会回落到开会话时的端点**：这是给测试与库调用方的**具名降级**、不是静默成功——
   **身份闸仍然生效，误附着依然不可能**，丢掉的只是「换端口后重新找回」这一项恢复能力。
   生产入口始终接真实通道。
3. **引擎/宿主版本耦合**：新引擎配旧宿主时会发出端点请求，旧宿主会把它误路由进待决命令表。
   这与既有的提交窗口请求器是**同一个性质**、且两者同包发布，**登记而非当作新问题**。
4. **运行时契约 5.1 未做**：交接文档给的是机会性口径（「落地后若打开了会话文件就顺手做掉」），
   §6 的工作从未打开那个文件，**条件未触发**。不是遗漏，留待其属主。
5. **发现一条既有 flake（非本次引入，已证）**：高负载下跑全量时，会话恢复那条用例偶发管道断裂失败——
   根因是存活性判断的竞态（系统进程已退出但运行时尚未标记流不可写）。
   **已用基线树对照证明不是本次引入**（基线全量 2867 通过 / 0 失败；本次树重跑两遍均 0 失败）。
   本轮不修（超出范围），**登记备查**。

## 12. 待处理：会话恢复的存活性判断竞态（2026-08-01 登记，**非本轮引入**）

> **【已转登记 2026-08-05，归档前的必要动作】本节分析已原样搬到
> `docs/deferred-defect-proposals-2026-08-05.md` §8，处置为「记档、遇到 case 再处理」。**
>
> **为什么必须搬**：本节没有勾选框，因此**任何「任务是否全勾」的检查都拦不住它随归档消失**。
> 一条**尚未修复的生产缺陷**跟着 change 进 `archive/` 目录，等于此后无人再看得见。
>
> **判据（照根 `CLAUDE.md` §2 的加闸准入）**：竞态吃掉的是**一条**命令，
> 下一条命令时进程已被完全回收、存活判断会正常判死并重建 ⇒ 后果可恢复、不对外可见、非不可逆写入。
> **概率低 × 后果可恢复 = 记档即可。** 三条触发条件（含「有人想给这条用例加重试」）写在该文件 §8。
>
> 下方原文保留，仅作追溯。

**症状**：`test/native-page-engine/runtime-contracts-session-recovery.test.ts` 的
「缓存会话的传输已死时，下一条命令走重建而不是立刻抛引擎已退出」在**满负载并行跑全量**时
偶发 `write EPIPE`。单跑必过。

**已出现两次**（2026-08-01 同日）：一次在运行时契约流的全量跑里，一次拦下了产物门禁流的集成。
**两次都不是当批引入的** —— 运行时契约流用基线树对照证明过（基线全量 2867 通过 / 0 失败，
其树重跑两遍均 0 失败）；产物门禁流单跑该文件 3/3 通过。

**根因（由运行时契约流的实装方给出，本轮未复核代码）**：存活性判断的竞态 ——
**操作系统层面的进程已经退出，但运行时尚未把标准输入标记为不可写、也还没填上退出码**。
于是判断认为传输还活着，去写，拿到管道断裂。

### ⚠️ 为什么它不只是「测试偶发」

**同一个竞态在生产上会走错分支。** 那条被测行为本身是：传输已死时**走重建**、而不是抛「引擎已退出」。
存活性判断误判成「还活着」时，代码会去写一个已死的管道 —— 拿到的是一个**异常**，
而不是走进重建路径。也就是说：

- 期望行为：传输死了 → 认出来 → 重建引擎 → 命令正常执行
- 竞态下的实际行为：传输死了但判断没认出来 → 写 → 管道断裂异常

**这正是本仓红线的反面**：一个「资源已经不可用」的结构性事实，被表达成了一个异常，
而不是走进已经写好的恢复路径。

### 建议修法（未实装，留给属主）

不要只放宽存活性判断的等待。**写入侧捕获管道断裂并当作「传输已死」处置、走同一条重建路径** ——
判断是尽力而为的预检，写入失败才是权威事实。这样竞态窗口内的那次写入不再是异常，
而是恢复链的正常入口。

**MUST NOT 的处置**：给测试加重试、或把它标成允许失败。那会让上面那条生产缺陷失去唯一的现场证据。
