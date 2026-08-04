# Tasks

> 三段互相独立，可并行开发；集成串行。
> A 段最紧急（生产停摆），但 **MUST NOT 只做 A**：让 A 藏了六天的是 B 与 C。

## 1. aidcp-edge — A. 引擎准入上限按平台道对齐

- [x] 1.1 引擎侧非 Facebook 会话准入上限抬到与宿主下发的非 Facebook 会话超时一致。
      改 `native/page-engine/src/protocol.rs` 的 `MAX_TIMEOUT_MS`，并就地写明它必须 ≥ 宿主
      `src/native-page-engine/runtime.ts` 的 `DEFAULT_NATIVE_SESSION_TIMEOUT_MS`（与 Facebook 那条
      已有的同型注释对称）。
      <!-- aidcp-edge 3b789d8 MAX_TIMEOUT_MS 30_000→45_000，注释写明来龙去脉 -->
- [x] 1.2 守卫 `test/native-page-engine/timeout-chain-contract.test.ts` 从「Facebook 一条道」改成
      **逐平台道对账**：每条道验四件事——请求 ≤ 边缘准入 / 请求 ≤ 引擎天花板 /
      会话超时 ≤ 两道准入 / 会话超时 ≥ 会被它夹回的天花板。
      <!-- aidcp-edge 3b789d8 SESSION_LANES 逐道对账 -->
- [x] 1.3 **加元断言：引擎准入里被特判的平台集合 == 守卫覆盖的平台道集合。**
      从 `protocol.rs` 的准入分支里解析出被特判的平台名，与守卫的道表按集合比对，
      不一致即失败并点名。**这条才是本段的真修复**——只抬 1.1 那个常量，等于把同一枚地雷
      挪到下一个平台。参考 memory `hand-copied-name-lists`：手抄名单在漏项时恰好是绿的。
      <!-- aidcp-edge 3b789d8 元断言：平台全集与准入 match 臂都从 Rust 源码读出对账；准入同时改为穷举 match（新增平台不选道即编译失败） -->
- [x] 1.4 变异验证：把 1.1 改回旧值，确认 1.2 失败；把一个假平台特判塞进 `protocol.rs` 准入分支，
      确认 1.3 失败并点名该平台。**记录是哪条用例抓住的**（memory `mutation-attribution-not-just-redness`）。
      验完还原，注意 `mv` 还原会保留旧 mtime、导致 cargo 跳过重编（memory `mutation-check-mv-restore-mtime-trap`）。
      <!-- aidcp-edge 3b789d8 四条变异逐条施加并记归因：①常量回退→逐道用例；②新增平台无道→元断言点名 Douyin；③换错准入常量→元断言「验的不是同一个数」；④改回兜底 else→元断言响亮失败 -->
- [x] 1.5 `cargo test`（引擎）+ `npm run typecheck` + `npm run test:acceptance` + `npm test` 全绿。
      cargo 不在 PATH，须指 rustup toolchain bin（memory `native-engine-cargo-path`）。
      <!-- aidcp-edge 3b789d8 cargo 24 组全绿零失败；typecheck / acceptance 39 / 全量 3116 均通过 -->
- [x] 1.6 用**编译后的引擎二进制**实跑一次会话开启，确认非 Facebook 平台不再被 `invalid_request` 拒。
      喂一条 `session_open`（平台非 Facebook、超时取宿主实际下发值）即可，不需要真浏览器：
      通过准入后会走到端点连接（无浏览器时 `endpoint_unreachable`），**这就是通过准入的证据**。
      <!-- aidcp-edge 3b789d8 重编译引擎实跑：xiaohongshu@45000 与 wechat_channels@45000 穿过准入，xiaohongshu@45001 仍被拒——闸未被拆除 -->

## 2. aidcp-edge — B. 会话启动失败必须离开本进程

- [x] 2.1 四个启动点（首次 / 身份重立后 / 恢复自动化 / 冷待机唤醒，`src/main.ts` 1344 / 1431 / 1478 / 1702）
      不再各自 `catch(console.error)`，改为经一个具名失败上报口。
      <!-- aidcp-edge 9a4093d 四点统一走 startBrowseSession(site) -->
- [x] 2.2 该口按**结构性**分档并在回执上标出：门口拒收类（准入不通过 / 能力不支持）判结构性 ⇒
      可落终态，回执写清「为什么重来也不会变」；端点不可达 / 浏览器未就绪类判非结构性 ⇒
      **MUST NOT 落终态**，保留带上限的自愈通道。判据见 `docs/stop-or-continue.md`。
      <!-- aidcp-edge 9a4093d BROWSE_START_FAILURE_CLASS 互斥+穷尽映射；默认偏非结构性 -->
- [x] 2.3 **上报云端**：失败必须离开本进程。当下连不上云端不解除该义务，只是延后。
      <!-- aidcp-edge 9a4093d 经 error 信封上报；断连攒下、cloud.reconnected 补发 -->
- [x] 2.4 **让外壳运行态离开「正常」**：外壳判核心停摆走一张具名白名单，当前这条错误不在其中，
      于是 `edge` 轴停在 running、`automationState` 落在 ready。补进白名单或走既有的运行姿态通道，
      二选一，但 MUST 有一条真的会翻。
      <!-- aidcp-edge 9a4093d 走既有运行姿态通道 automation_stalled（edge 轴翻 warning + 持久失败卡片）；IPC 送不到时的兜底日志行本就在白名单，故未动 fleet.cjs -->
- [x] 2.5 **周期巡视的武装 MUST NOT 依赖首扫成功**：把 `scheduleProbe()` 移出「首扫成功之后」这一位置
      （`src/native-page-engine/browse-session.ts:339`）。首扫失败恰恰是最需要它的时刻，
      而四个入口没有一个会再次触发它。
      <!-- aidcp-edge 9a4093d scheduleProbe() 移入 finally -->
- [x] 2.6 用例：① 首扫抛结构性失败 ⇒ 上报云端 + 外壳姿态翻转 + 回执标结构性 + 巡视仍武装；
      ② 首扫抛非结构性失败 ⇒ 不落终态 + 自愈通道有上限。
      **闸类断言要喂违规输入**，别只验恒真路径（memory `gate-always-true-equals-gate-gone`）。
      <!-- aidcp-edge 9a4093d browse-start-failure-honesty.test.ts 9 条；变异三条均单点归因 -->

## 3. aidcp-edge — C. 界面 MUST NOT 把「读不到」画成「没有」或「在跑」

- [x] 3.1 首页标题空态判定区分 `null`（未知）与 `0`（确认为空）：
      `src/electron/renderer/content-workspace.js:1160` 的 `(inspiration || 0) === 0 && (drafts || 0) === 0`
      以及 1168 / 1175 的 `${inspiration || 0}`。任一计数未知时 MUST NOT 宣布「暂无待处理内容」，
      改为说明有分区暂时读不到。**同屏格子已经是诚实的（null → `—`），标题必须与它一致。**
      <!-- aidcp-edge 78b49fe 先判 === null，点名读不到的分区并报出已确认的一半 -->
- [x] 3.2 「最值得看的灵感」失败分支按**自己那个来源**判：
      `content-workspace.js:884` 的 `sourceState.kind === 'error' && draftState.kind === 'error'`
      改为精选来源失败即显示可重试失败，MUST NOT 落进讲准入条件的空态文案
      （「只有赞藏表现和内容证据完整…才会进入这个位置」——那是把故障讲成产品判断）。
      <!-- aidcp-edge 78b49fe && 改 ||，并点名失败侧 -->
- [x] 3.3 「正在浏览 / 正在继续寻找」这类**声称执行层在动作**的文案改为需要执行层证据：
      现状唯一判据是 `automationActive = automationState !== 'stopped'`
      （`content-workspace.js:2155`），9 档里 8 档为真、含 `paused` 与 `error`。
      无证据时退到不声称动作的措辞，并去掉暗示活动的动效（`content-workspace.js:899` 的 live 圆点）。
      口径要与诊断面板一致——同一个 `ready`，那边标「待任务」，内容页不能讲「正在浏览」。
      <!-- aidcp-edge 78b49fe 证据信号取 automationState === 'running'（唯一要求本代内上报过 loopStage 且浏览器就绪的档，与诊断面板同档）；关掉脉动圆点；automationActive 保持为意图信号不动 -->
- [x] 3.4 账号身份行标明来源：`content-workspace.js:827` 的 `` `小萝北 · ${environment?.label}` ``。
      后半段实际是**客户端环境名**（本例即 AdsPower 环境名「工程师大白」），而标题栏对平台昵称
      有 `@` 来源标记、这一行没有。与标题栏口径对齐，并确保这行不读起来像人设名
      ——人设在系统里不承载名称字段，客户端也不接收人设名。
      <!-- aidcp-edge 78b49fe 改为「小萝北（AI 助手） ｜ 账号 <name>（<来源>）」，仅平台昵称加 @；renderer.js 多传一个 labelSource -->
- [x] 3.5 用例覆盖 3.1 / 3.2 的**违规输入**：精选 null + 草稿 0 ⇒ 标题不得宣布空；
      精选 error + 草稿 ready ⇒ 最值得看的灵感必须是失败态而非空态。
      <!-- aidcp-edge 78b49fe content-workspace.test.ts 新增 4 条 + 修正 1 条既有断言；变异四条均单点归因 -->

## 4. 收尾

- [x] 4.1 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（回归纪律，CLAUDE.md §4）。
      <!-- aidcp-edge e6ea316 acceptance 39/39、全量 3116 条 3115 通过 0 失败 1 跳过（gated 真机）、typecheck 通过、cargo 24 组全绿 -->
- [x] 4.2 提交推送到 edge `master`（集成前 rebase 到最新 master；push 遇 non-ff 一律 rebase 重来、绝不 force）。
      <!-- aidcp-edge e6ea316 rebase→origin/master 后 ff 推送；rebase 引入一处语义冲突（主干新用例引用被改名的符号，文本无冲突、仅 typecheck 抓到）已修并单独成一提交 -->
- [x] 4.3 tasks.md 回写 sha，格式 `<!-- aidcp-edge <sha> 备注 -->`；**sha 必须取自已推送的提交**
      （memory `tasks-md-sha-must-be-pushed`）。
      <!-- aidcp-edge e6ea316 本表 sha 均取自已推送提交 -->
- [x] 4.4 **真机验收项登记 backlog**：本 change 的效果只有在**重新打包的桌面客户端**上才看得到
      （引擎是随包分发的 Rust 二进制）。打包属用户显式触发（CLAUDE.md §6），不进本 change 的自动收尾。
      登记：小红书会话真机开起来、首扫失败真的翻红、首页文案三态。
      <!-- aidcp docs/real-machine-acceptance-backlog.md 簇 129（15 条：A 段 3 / B 段 4 / C 段 4 / 已知未闭合 4）。
           **出包之前本簇物理上一条都验不了**——装机版 0.3.25 里的引擎二进制仍带旧准入。 -->
- [ ] 4.5 `openspec validate restore-xiaohongshu-native-session-honesty --strict` 通过后归档。

## 5. 明确不做（登记，不修）

- [ ] 5.1 `aidcp-api` 的 9 项客户端依赖未接线（今日进展 / 进行中 / 委托任务 / 草稿精修 / 草稿操作 /
      互动接口 / 人设自动填充 / 运营别名 / 入离职）——属活跃 change `deploy-derived-services-to-dev`，
      2026-08-04 16:17 仍在提交、16:19 刚部署 dev，并发改同一组装根必撞。
      **本 change 只保证读取失败被如实呈现，不负责让它读得到。**
- [ ] 5.2 握手 `tempo=1.3` 二义：`status=warned` 与 `quota_level=conservative` 同值 1.3，
      日志只打 tempo、不打来源，排障分辨不了。
- [ ] 5.3 `warned` 无自动回落：恢复逻辑与 7 天常量都在，但全仓无人调用、也无人发恢复信号；
      而 `warned` 会**永久禁掉发布**。「配额超限钉成 warned」那条边已于 2026-07-01 拆除，
      但**没有迁移回滚存量状态**，旧库里被钉上去的仍在原地。唯一出口是运营手动下恢复指令。
- [ ] 5.4 边缘与云端**各有一套显示名优先级**，且边缘没有「运营别名」字段
      （该字段也在 5.1 那批未接线里）：后台配的别名客户端看不到，同一账号两端显示名可不同。
- [ ] 5.5 **云端没有 `error` 这条边的消费者**（B 段实装时发现并如实报出）：edge→cloud 的 `error`
      落进云端 `handler.ts` 的 `default:`、被回一条 `unsupported_type`。所以本 change 达成的是
      「失败离开了本进程、到达了云端传输层」，**不是**「云端会据此动作」。要让云端真正升级，
      需要一条新的 edge→cloud 消息类型——那要协议四处同步、且会撞协议热点文件的单写者约束
      （CLAUDE.md §7），故另立 change。已登记 backlog 簇 129.12。
- [ ] 5.6 `automationState` 仍会落在 `ready`（外壳 `deriveStates()` 按「子进程在 + 云端已连」推导，
      运行姿态不参与）。本 change 按 2.4 的「二选一」走了姿态通道；改 `deriveStates` 与 C 段 3.3
      是同一条链，同时改必撞。已登记 backlog 簇 129.13。
- [ ] 5.7 `automation_stalled` 在「重试中」窗口措辞略强于事实；暂停不归还已消费的自愈预算。
      两条均为保守方向，已登记 backlog 簇 129.14 / 129.15。
