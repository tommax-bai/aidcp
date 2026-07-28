## 1. aidcp-edge — 命令清单对账（声明变成断言）

- [ ] 1.1 建立「声明回执 ↔ 成功路径可达发出点」对账检查：从命令清单读每条命令的 `receipts`，与宿主 `src/native-page-engine/browse-session.ts` 的 `report()` 输出分派表逐条比对，两个方向都查（声明有而不可达 / 可达而未声明），不一致即失败并打印命令名与不匹配的回执名。判据必须**跨平台取并集**（单次执行只产出一个输出，`note_browse_images` 这类是小红书回详情、Facebook 回动作回执）且**排除失败路径**（`browse-session.ts:436` 的 `reportFailure` 对任何命令都发一条 `ok:false` 动作完成，算进来则对账恒真）
- [ ] 1.2 跑一次 1.1 的检查，把当前全部不一致逐条记入本文件，每条标注结论为「补发出」或「改声明」。声明了两条回执的共 12 条：`page_scroll` / `feed_refresh` / `search_execute` / `note_open` / `note_close` / `navigation_back` / `note_browse_images` / `profile_open` / `notification_open` / `notification_browse_comments` / `notification_back_home` / `captcha_click`。其中**起草期已实读坐实**的只有三条结论，其余 9 条不预判、以检查输出为准：
  - `note_open`：声明的 `action.completed` 在成功路径上不可达（两平台成功恒回 `note_detail`，`report()` 的 `note_detail` 分支直接 return）
  - `note_close` / `navigation_back`：声明的 `page.cards` 反向不可达（两平台成功恒回 `action_receipt`）
  - `search_execute`：两条回执**都发**（`page_cards` 分支在信封为 `search.execute` 时同时报动作完成，`browse-session.ts:283-308`）——不得把它当成缺口
- [ ] 1.2.1 复核结论登记：简报称「身份读取命令声明会发身份观测回执、而整条命令在边缘入口就被吞掉」，实读**未能复现**——`identity.read_current` / `identity.read_self_profile` 在 `src/native-page-engine/command-mapper.ts:10-11,35-36,60-61,87` 有完整映射，`report()` 的 `identity_observation` 分支照发 `identity.observed`（`browse-session.ts:334-335`）。故身份类命令不预标为缺口，一律交 1.1 的对账检查判定
- [ ] 1.3 按 1.2 的结论逐条落实；无法在本 change 内落实的，写进一张显式冻结清单，每条含命令名、声明值、实际行为、消除动作，并在检查里断言冻结清单只许缩短
- [ ] 1.4 把 `requestContract` 的断言从「字符串非空」升级为「必须解析到一个真实存在的具名请求契约」，不存在即失败
- [ ] 1.5 把 `effect` 与 `cancellation` 的断言从「字符串非空」升级为「必须属于一个封闭取值集，且与引擎侧对该命令的写判定 / 取消安全点一致」

## 2. aidcp-edge — 命令词表从枚举导出

- [ ] 2.1 把 `native/page-engine/src/command.rs` 的词表一致性检查改为从 `NativeCommand` 穷举导出（用 serde 往返或穷举 match 生成 kind 列表），不再以 `PRODUCTION_COMMAND_KINDS` 手写数组作为比较的一方
- [ ] 2.2 为「可执行但不进清单」的变体建立显式排除表并断言其内容（当前应恰为 `page_probe` 一条），排除理由随表记录
- [ ] 2.3 加一条失败优先的回归：在枚举里新增一个变体而不动清单与排除表时，该检查必须失败
- [ ] 2.4 修正该检查的名称，使其名副其实（现名 `production_enum_matches_the_frozen_manifest_exactly` 与其实际比较对象不符）

## 3. aidcp-edge — 提交窗口预算单一事实源

- [ ] 3.1 确定提交窗口标签与预算的单一事实源（宿主侧常量或命令清单产物二选一），删除另一侧的独立数字声明
- [ ] 3.2 改造引擎侧：按标签请求窗口，不再随请求发出自写的预算数字（`native/page-engine/src/facebook/capability.rs` 的 `JOIN_WINDOW` / `COMMENT_WINDOW` / `PUBLISH_WINDOW`）
- [ ] 3.3 改造宿主侧 `src/native-page-engine/client.ts`：以事实源为准给出预算并保留上限约束，取消对引擎自报预算的相等断言
- [ ] 3.4 把「标签未知 / 预算不符事实源」的运行期处理从 `failProtocol` + `terminate()` 改为可归因的、绑定当前命令的契约违规结论，引擎进程不再被整体终止
- [ ] 3.5 加回归：单侧修改一个窗口预算时，仓库检查失败；且不存在任何运行期路径能让该修改表现为「按下按钮前终止引擎」
- [ ] 3.6 加回归：引擎请求一个大于事实源上限的预算时，宿主只授予事实源上限

## 4. 产物新鲜度 — 本 change 不做，交叉核对

产物摘要输入范围、开发态重编判据、打包态产物校验与 Electron 侧期望摘要，整片归并行 change `enforce-native-engine-artifact-gates`。本节只做核对，**不修改** `native/page-engine/build.rs`、`scripts/build-native-page-engine.mjs`、`scripts/ensure-native-page-engine-dev.mjs`、`src/electron/native-page-engine-artifact.cjs`。

- [ ] 4.1 记录起草期坐实的现状供交叉核对：能力摘要仅哈希 `command-manifest.json`（`native/page-engine/build.rs:19-21`）；引擎版本恒 `0.1.0`（`Cargo.toml:3`）；`verify()` 只做产物自洽（`scripts/build-native-page-engine.mjs:72-113`）；开发引导为「校验通过就不重编」（`scripts/ensure-native-page-engine-dev.mjs:19-27`）；实测自 2026-07-22 起规则目录 10 次提交 vs 命令清单 4 次提交
- [ ] 4.2 待 `enforce-native-engine-artifact-gates` 落地后核对：源码导出的摘要是否已进入宿主↔引擎的启动握手比对（`src/native-page-engine/client.ts:481-489` 现比引擎版本 / 平台适配器版本 / 适配器表 / 能力摘要四项）。若未进入，单开后续 change 承接「运行期握手也要能证明规则新鲜度」并在此登记
- [ ] 4.3 待该 change 落地后核对：Electron 侧硬编码期望摘要（`src/electron/native-page-engine-artifact.cjs:19`）是否已可派生或已有机械同步闸；若仍是裸常量，在此登记为未消除缺口

## 5. aidcp-edge — 引擎故障后的自愈

- [ ] 5.1 把 `src/native-page-engine/browse-session.ts:141-142` 的会话结束收尾从成功路径移到 `finally`，使结束会话命令失败时收尾仍执行
- [ ] 5.2 给 `src/native-page-engine/runtime.ts:128-131` 的会话缓存加存活判据（现为命中即返回、零判据）：返回缓存句柄前必须**取到存活的肯定证据**（如子进程未退出且通道可写），取不到即按已死处理、丢弃并重开——「没记到死讯」不算存活证据
- [ ] 5.3 加回归：引擎进程已退出时下发结束会话 → 该命令失败，但 owner 被释放；随后一条命令能重建引擎并正常执行
- [ ] 5.4 加回归：缓存会话的传输已死时，下一条命令走重建而不是立刻抛「引擎已退出」

## 6. aidcp-edge — 重连绑定与预算

- [ ] 6.1 让引擎重连时重新向宿主/提供方解析端点，不再复用 `native/page-engine/src/engine.rs` 会话结构里存的 `host` / `port`；宿主侧 `runtime.ts` 相应提供会话期内可重复取值的端点解析入口（当前 `getEndpoint()` 只在建会话时调用一次）
- [ ] 6.2 给 `native/page-engine/src/endpoint.rs:214-226` 的 `select_target`（现判据仅「目标类型 page + 平台 URL 允许集 + 调试地址端口」）增加分身身份证据判据；身份证据的具体载体在实装期与浏览器提供方一侧确定后记录在此。现成候选：provider 认领失联浏览器用的「`<profileId>_` 前缀缓存目录 + `DevToolsActivePort` 标记」（`src/cdp/browser-provider.ts:728-745`）
- [ ] 6.3 无法取得身份证据、或无候选目标可证明属于被准入实例时，返回诚实的执行器健康类失败，不附着任何目标
- [ ] 6.4 把 `engine.rs:509-528` 重连后的重试纳入与首跑相同的绝对截止线包裹，超时即释放单命令槽位并回超时
- [ ] 6.5 加回归：重连 + 重试的总耗时不超过原命令预算；预算耗尽后槽位被释放，下一条命令不再被 `CommandInProgress` 顶回
- [ ] 6.6 加回归：候选目标的端口对上但身份证据不匹配时，引擎拒绝附着且不执行任何命令

## 7. aidcp-edge — 取根、诊断与焦点守卫的诚实归因

- [ ] 7.1 在 `native/page-engine/src/facebook-router/00-shared.js:13-19` 的共享取用函数（`all` / `first`）里加空 root 防护，使传入空 root 时返回可归因于「无有效根」的空结果而非抛 `TypeError`（当前直接对传入 root 调 `querySelectorAll`，零防护）
- [ ] 7.2 修 `20-feed.js:253` 的 `currentDetail()`：`… || document.querySelector('main') || document.body` 之后无空判、直接进 `noteDetail(root, permalinkOf(root)…)`，是**当前唯一实读坐实会把空根交给遍历**的取根点（行号按 `aidcp-edge@9cd7691`；简报给的 `87,147,233` 已被 07-28 改动顶偏）。改为取不到有效根时返回诚实的未开始理由
- [ ] 7.2.1 交叉核对另 4 处 `|| document.body` 取根点（`20-feed.js:87,154,166` 与 `40-group-join.js:103`）：起草期实读结论是它们下游均空安全（`:87` 紧跟 `if(!scope)return`；`:154` 只进 `node&&…` 循环；`:166` 只以 `scope&&…` / `all(…,scope||document)` 使用；`40-group-join.js:103` 进 `targetGroupScope`，其 `:50-51` 首行即 `if(!groupId||!main)return`）。若实装期复读推翻某一处，按 7.2 同样处理并在此记录；结论不变则不改这 4 处，**不做空转补丁**
- [ ] 7.3 给 `native/page-engine/src/xhs.rs:66-72` 与 `native/page-engine/src/probe.rs:89-98` 的结果解码入口补上与 `facebook.rs:607-620` 同级的有界解码诊断（阶段 / 字段路径 / 异常位置），且诊断保持有界、不含页面正文与凭据。**先核对**并行 change `restore-native-xiaohongshu-session-guards` 是否已把解码入口一并覆盖；已覆盖则划掉本条、不重复实现
- [ ] 7.4 在 `native/page-engine/src/input.rs:108-128` 区分「焦点守卫求值失败或输出缺失」与「焦点确实丢了」两类结论（通道失败已单列为 `Engine`，保持不变）
- [ ] 7.5 加回归：① 取用函数收到空 root → 回可归因的空结果、不抛（写命令路径因此不会被判 `Ambiguous`，对照 `engine.rs:532-543` 的「写 + 任何规则错误 → Ambiguous」）；② 导航瞬间无有效根 → `note_open` 回未开始而非抛；③ 非 Facebook 平台解码失败 → 携带同级诊断；④ 守卫求值失败 → 与目标丢失是两个不同结论

## 8. aidcp-cloud — 评论预算传输而非重算

- [ ] 8.1 确定评论提交预算的计算方（云端下发或边缘回报）并在该侧按「实际会被打进编辑器的完整串」计算，另一侧改为据传输值派生
- [ ] 8.2 删除非计算方的常量副本（`aidcp-cloud/src/comment-agent/facebook-edge-steps.ts:46-57` 与 `aidcp-edge/src/native-page-engine/browse-session.ts:65-71` 其中一份）
- [ ] 8.3 加回归：带群聊码后缀的评论上，判定方的等待窗口不短于执行方的命令预算；慢但成功的提交不会被判超时
- [ ] 8.4 加回归：改动预算常量时只有一处声明变化，不存在第二份公式可以保留旧值

## 9. 验证 / 验收

- [ ] 9.1 `cd ../aidcp-edge && npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）
- [ ] 9.2 `cd ../aidcp-edge && npm test` 与 `npm run typecheck`
- [ ] 9.3 `cd ../aidcp-edge/native/page-engine && cargo fmt --check && cargo clippy -- -D warnings && cargo test --locked`
- [ ] 9.4 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`
- [ ] 9.5 在本文件记录 1.2 对账检查的完整输出（命令名 + 不匹配回执名 + 结论），以及冻结清单的初始条目数；后续 change 只许该条目数下降
- [ ] 9.6 运行 `openspec validate harden-native-engine-runtime-contracts --strict`

### 9.7 真机验收项（本 change 不执行，登记进 `docs/real-machine-acceptance-backlog.md`）

以下均为**推断，未在真机坐实**，不得当成既成事实：

- [ ] 9.7.1 跨环境错投的真实发生概率：同机多环境并行时，指纹浏览器释放的调试端口被另一环境复用的频率与分配策略，未实测；需在真机上观察端口回收行为后再评估 6.2 身份证据判据是否足够
- [ ] 9.7.2 空根塌陷需要导航瞬时窗口（`document.body` 为 `null`）才触发，**未复现**；已发生过的那一次是同构但不同调用点。复核实读后进一步收窄：5 处兜底取根里只有 `20-feed.js:253` 无空判，且它在**读命令**（`note_open`）路径上——「写命令因空根被记成可能已做」当前**没有已坐实的路径**，只是取用层零防护带来的结构风险。需真机验证 7.2 改动后该窗口内 `note_open` 的实际结论是「未开始」而非在页面内抛异常
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

- [ ] 9.8.1 不部署（dev / ol 均不做）；不出安装包、不做签名公证
- [ ] 9.8.2 不做任何真机写动作（点赞 / 评论 / 加群 / 发帖）
- [ ] 9.8.3 不改 Cloud↔Edge 协议 v2 消息集合、动作名口径与命令映射；不改风控状态机与配额档位
- [ ] 9.8.4 不改 `openspec/specs/` 下任何文件
