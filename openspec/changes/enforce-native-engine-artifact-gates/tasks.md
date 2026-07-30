## 1. aidcp-edge — 泄漏闸门从事实源派生

- [x] 1.1 在 `scripts/` 下新增一个共享模块，运行时读取 `native/page-engine/src/facebook-router/manifest.txt`，导出「已登记分片名列表」，供剪枝脚本、打包后置扫描与测试共用 <!-- aidcp-edge be0a8be 新增 scripts/native-engine-inventory.cjs 为唯一派生点；写成 CommonJS 以同时供 ESM 脚本与 electron-builder 的 after-pack 钩子同步调用 -->
- [x] 1.2 把 `scripts/prune-production-dist.mjs:47-57` 的 10 条 `facebook-router/*.js` 字面量删掉，改为按 1.1 的列表生成禁止路径，并把检查根重新锚定到该脚本实际能产出的语料（当前 `dist/facebook-router` 与 `src/facebook-router` 均不存在，须先确认剪枝脚本应该守的是哪个目录，若确认无对应产物则改为「守 dist 全树的分片文件名」并记录判断依据）<!-- aidcp-edge be0a8be 判断依据：任何分支下都不产出 dist/facebook-router，原 10 条恒不触发；改为按清单派生分片文件名、检查根重锚到整棵 dist 树按文件名判 -->
  - 【实装实测订正 · 次序必须写死】原任务只规定了闸门的锚定位置、没规定它与剪枝步骤的**先后**。实测把分片闸放在剪枝之后：植入的分片会先被剪枝当孤儿删掉，闸门随后报通过——泄漏路径原样留着、痕迹被同一次构建擦掉，正是「静默假成功」在构建闸上的形态。已改为**剪枝之前**判并补回归用例。次序要求同步写进 `specs/native-engine-artifact-gates/spec.md`（新增「闸门 MUST 在任何会改写被检语料的步骤之前执行」一句与对应 Scenario）
- [x] 1.3 把 `scripts/after-pack.cjs:177-187` 的 10 条 `/native/page-engine/src/facebook-router/*.js` 字面量删掉，改为按 1.1 的列表生成条目；同时对 electron-builder 的 `files` 允许清单加一条断言：允许清单一旦被放宽到覆盖 `native/page-engine/src/**`，打包失败 <!-- aidcp-edge be0a8be 原先漏掉的 08-reaction-semantics.js 随派生自动进闸 -->
  - 【范围说明】允许清单断言当前只覆盖 `build.files`，未纳入 `build.extraResources`。判断依据：`extraResources` 是归档外资源，不构成「明文分片进 asar 归档」的路径；如后续要把 `extraResources` 也纳入，须另立判据
- [x] 1.4 加一条对账断言：清单里的每个条目都必须被上述两处闸门覆盖，缺一即失败；`08-reaction-semantics.js` 当前缺席这两处，接入后应立即被这条断言接住 <!-- aidcp-edge be0a8be 对账断言同时要求两个脚本里不得再出现手抄字面量 -->
  - 【实装实测】接入后两处闸门均由清单派生，`08-reaction-semantics.js` 不再缺席，对账断言在当前树上直接通过；11.4 要求的「接入前的实际报错文本」未单独取样（派生与对账在同一次改造里落地，无中间态可复现）

## 2. aidcp-edge — 否定式闸门的可证伪自测

- [x] 2.1 为剪枝脚本的禁止路径闸加一条自测：在临时目录里造出一个被禁文件、跑闸门、断言抛错 <!-- aidcp-edge be0a8be test/native-page-engine/artifact-gates.test.ts，植入违规→断言拒绝，另配无植入的对照断言放行 -->
- [x] 2.2 为剪枝脚本与打包扫描的明文标记闸各加一条自测：在临时语料里植入一条标记、断言闸门拒绝 <!-- aidcp-edge be0a8be 同上文件，两道标记闸各一对（植入 / 对照） -->
- [x] 2.3 为打包后置扫描的禁止条目闸加一条自测：用一个植入了被禁条目的临时 asar（或等价条目清单桩）断言拒绝 <!-- aidcp-edge be0a8be 用等价条目清单桩，避免自测依赖真出包 -->
- [x] 2.4 把 `test/native-page-engine/build-contract.test.ts:38,43` 那类「断言脚本文本里出现某标识符」的用例标注为「存在性断言、不构成判定证据」，并在同文件补上指向 2.1–2.3 的判定型断言 <!-- aidcp-edge be0a8be -->
- [ ] 2.5 接上跨语言契约夹具的 TypeScript 侧：`native/page-engine/tests/contract_fixtures.rs:29-53` 回放 `tests/fixtures/page-probe-contracts.json` 并断言其 `sourceContract` 为 `src/native-page-engine/client.ts#NativePageProbeResult`，而实测 `test/` / `src/` / `scripts/` 对该夹具与 `contract_fixtures` 引用为零。新增一条 TypeScript 用例加载同一份夹具，按 `NativePageProbeResult` 消费每条 `expected`（类型级 + 运行时校验二者其一即可，但必须在改类型名 / 改字段时变红），并断言该类型标识符仍存在；验收标准：临时把 `client.ts` 里该类型改名后这条 TS 用例失败（Rust 侧的字符串比对此时仍绿，须在本清单记录这一对照）

## 3. aidcp-edge — 明文哨兵双向校验

- [x] 3.1 给 `scripts/build-native-page-engine.mjs:41-51` 的 9 条 `forbiddenCleartextMarkers` 加一条存活校验：每条必须在会进入 release 编译的页面规则/引擎源码里定位到，定位不到即失败 <!-- aidcp-edge be0a8be 哨兵分 live / 结构类两档，live 类必须在 release 编译语料里定位到，定位不到即失败 -->
- [x] 3.2 处置两条已失效哨兵 `Input.dispatch` 与 `Page.navigate`（实测只出现在 `native/page-engine/src/facebook/publish_tests.rs`，该文件经 `src/facebook/publish.rs:892` 的 `#[path]` 挂在 `#[cfg(test)]` 下、不进 release）：要么改指一个活特征，要么显式记录这条覆盖被放弃及理由，MUST NOT 静默删除 <!-- aidcp-edge be0a8be 处置为「显式记录的结构类哨兵」，不参与 live 存活校验、也不删除 -->
  - 【实装实测订正 · 原判据不成立】原任务与 design.md 把这两条 CDP 方法名断为「空哨兵」，只给了「改指活特征 / 显式放弃」两条出路。实测引擎的 CDP 层是**刻意分域存放方法名**的（域名与方法名不以整串形式出现在 release 语料里），因此这两条哨兵本就不该按整串匹配去判存活——它们不是失效，而是**形态不同**。据此第三条出路成立并已采用：标为结构类、显式记录、排除在整串存活校验之外
- [x] 3.3 补一条自测：临时把某条哨兵改成不存在的串，断言存活校验失败 <!-- aidcp-edge be0a8be 自测覆盖三种失活形态 -->

## 4. aidcp-edge — 分片登记完整性与拼接不变量

- [x] 4.1 在 `native/page-engine/build.rs` 的 `read_ordered_sources`（131-161 行）里加反向对账：列出分片目录内的文件，凡未登记在清单里即 `panic!` 并指名该文件 <!-- aidcp-edge be0a8be 同时对分片目录本身声明 rerun-if-changed；不声明的话新增文件根本不触发这次对账 -->
- [x] 4.2 在同一函数里落定拼接不变量：片间插入显式分隔字节，或断言每片以 `\n` 结尾（二选一并在注释里写清选了哪条及理由）；实测当前 11 片末字节均为 `0a`，接入后不应产生行为变化 <!-- aidcp-edge be0a8be 选「断言每片以换行结尾」：不插分隔字节即不改变已编入二进制的字节，接入零行为差 -->
- [ ] 4.3 让 `test/native-page-engine/facebook-router-source.ts:22-24` 的 TypeScript 复刻实现采用与 4.2 完全相同的规则，并加一条断言：两种拼接结果逐字节相等
  - 【阻塞】需改 `test/native-page-engine/facebook-router-source.ts`——该文件在本轨可改文件白名单外，且被路由契约测试消费。解锁条件：由白名单属主放行或该文件的属主接手。Node 侧的等价枚举实现已在 be0a8be 新增的 `scripts/native-engine-inventory.cjs` 里备好，可直接复用；**与本轮改动直接咬合，越早接越好**
- [x] 4.4 补两条失败优先用例：① 目录里放一个未登记文件 → 构建期对账失败；② 造一份缺尾随换行的分片 → 拼接不变量失败 <!-- aidcp-edge be0a8be 两条在隔离的 crate 拷贝里实测通过（不污染真分片目录） -->

## 5. aidcp-edge — 产物校验绑定源码

- [x] 5.1 在 `scripts/build-native-page-engine.mjs` 的 `build()` 里计算「引擎源码输入摘要」（Rust 源码树 + `src/facebook-router/` 全部分片与清单 + `build.rs` + `command-manifest.json`），写入 staged `manifest.json` 的新字段 <!-- aidcp-edge be0a8be 新字段 sourceDigest；输入集排除测试专用文件；只加字段、不抬清单版本号（理由见 5.5） -->
- [x] 5.2 在同文件 `verify()`（72-113 行）里重算该摘要并比对，不一致即抛「产物相对源码已过期」；保留既有的哈希/清单/协议版本/能力摘要检查 <!-- aidcp-edge be0a8be 既有检查全部保留，摘要比对为新增的第五道 -->
- [x] 5.3 确认 `scripts/ensure-native-page-engine-dev.mjs:19-28` 的「verify 成功即 return verified、不重建」在 5.2 之后自动变成「源码变了就重建」，不再需要额外分支；如需改动则一并落地 <!-- aidcp-edge be0a8be 开发态「已校验」分支改由源码摘要决定；校验失败理由原样带进重建日志、不吞 -->
- [ ] 5.4 复现并消灭已知实证：`touch native/page-engine/src/facebook-router/00-shared.js` 后跑 `node scripts/ensure-native-page-engine-dev.mjs`，改造前输出 `OK: unsigned target artifact verified ...` 且不重建；改造后必须触发重建。把改造前后的实测输出记进本清单
  - 【部分完成】判定逻辑已由用例证明（摘要随分片内容变化、同输入稳定），但**改造前后的实测对照未取到**：本工作区产物目录为空，需先做一次完整 release 构建才能跑这条对照。按「不当既成事实」口径保持未勾。解锁条件：在有已构建产物的工作区跑一次 touch 分片 → `ensure-native-page-engine-dev.mjs` 的前后对照并把输出记进本条
- [ ] 5.5 在 `src/electron/native-page-engine-artifact.cjs` 的打包态校验里同步接受并校验新字段（缺字段视为不兼容清单）
  - 【阻塞】需改 `src/electron/native-page-engine-artifact.cjs`，该文件在本轨可改文件白名单外。解锁条件：由白名单属主放行或该文件属主接手
  - 【实装实测注记 · 落地时必看】该打包态校验**硬校验清单版本号恒等于 1**。因此 5.1 只新增了 `sourceDigest` 字段、**没有抬版本号**——先抬版本会让打包在 5.5 落地之前就炸。落地 5.5 时必须「先接受新字段、再考虑是否抬版本」，两步不可颠倒

## 6. aidcp-edge — Rust 门禁进标准环境与集成闸

- [x] 6.1 新增 npm 脚本（如 `gate:native:fmt` / `gate:native:clippy` / `gate:native:test`），内部复用 `build-native-page-engine.mjs` 里 `resolveCargoBinary()` 的 rustup 解析思路（`rustup which ...`，`cwd: crateDir`），保证从仓根调用也解析到 `native/page-engine/rust-toolchain.toml` 钉死的工具链 <!-- aidcp-edge be0a8be scripts/gate-native.mjs + package.json 四条脚本；另断言解析到的工具链与钉死声明一致 -->
- [x] 6.2 工具链或组件缺失时脚本 MUST 非零退出并写明「解析到哪个工具链、缺哪个组件」，MUST NOT 记为跳过或非阻断 <!-- aidcp-edge be0a8be 失败文案同时写明安装命令 -->
- [x] 6.3 新增一条聚合脚本 `gate:native`，串起 6.1 三项，供集成闸单点调用 <!-- aidcp-edge be0a8be gate:native = fmt + clippy -D warnings + test -->
- [x] 6.4 在 `.github/workflows/` 新增一个按 push / PR 触发的检查流水线，跑 `npm test`、`npm run typecheck`、`npm run gate:native`；现有 `build-desktop.yml` 保持手动触发的出包职责不变 <!-- aidcp-edge be0a8be 新增 checks.yml（typecheck / 验收 / 全量 / gate:native）；build-desktop.yml 职责不变，仅修其工具链安装方式（见 6.6 订正） -->
- [ ] 6.5 在控制仓 `scripts/land-change`（当前第 38-42 行只跑 `test:acceptance` / `npm test` / `typecheck`）补上：当被集成的仓存在 `gate:native` 脚本时一并运行
  - 【阻塞】改动影响全车队的集成闸（控制仓 `scripts/land-change`），本轨未做。解锁条件：由主 session / fleet 层统一改并周知。**这是让整套门禁真正生效的最后一步**——在它落地前，6.1–6.4 只在 CI 与人工调用时生效，合并路径上仍不强制
- [ ] 6.6 记录一次性安装步骤（`rustup toolchain install` 需带 `components`），并检查 `scripts/build-desktop-macos-ol-arm64-common.sh` 里 `--profile minimal` + `export RUSTUP_TOOLCHAIN` 的组合是否会绕开 `rust-toolchain.toml` 的组件声明；若会，一并修正
  - 【部分完成】核查已完成并坐实：该组合确实会绕开钉死声明。安装命令已写进 gate 脚本的失败文案（6.2）。差两件：① 修 `scripts/build-desktop-macos-ol-arm64-common.sh`（补两个组件 + 停止覆盖钉死版本）——该文件在本轨可改文件白名单外；② 把一次性安装步骤写进护栏文档（`aidcp-edge/CLAUDE.md`，同 7.3 的白名单阻塞）
  - 【实装实测订正 · 原任务漏了同形态第二处且后果更重】原任务只点名了出包 shell 脚本。实测 **CI 出包工作流（`build-desktop.yml`）的两个作业用的工具链 action 会导出环境变量、盖掉钉死版本**——比 shell 脚本那处更重，因为它决定运营真出包用的编译器。已在 be0a8be 一并修正：改为按 `rust-toolchain.toml` 的声明显式安装该 channel，并带上静态检查与格式化组件

## 7. aidcp-edge — 混淆边界诚实化与密钥单一来源

- [ ] 7.1 把编码密钥收敛到单一定义，`native/page-engine/build.rs:7-9` 与三处运行时副本（`src/xhs.rs:23`、`src/facebook.rs:39`、`src/probe.rs:8`）共用同一来源；纯常量重定向，MUST NOT 改动任何解码语义
  - 【阻塞】需同时改三份运行时副本（`native/page-engine/src/xhs.rs`、`src/facebook.rs`、`src/probe.rs`），均在本轨可改文件白名单外，且其中一份归轨 A 占用。解锁条件：轨 A 收工后由白名单属主放行统一收敛（纯常量重定向，不改解码语义）
- [ ] 7.2 补一条会真正执行的解码内容断言：对嵌入资产解码后校验其明文特征，密钥不一致时失败（该断言随 6.1 的 Rust 门禁进入自动流程）
  - 【阻塞】依赖 7.1 的单一来源收敛先落地（否则断言只能证明某一份副本自洽）；同样受上述白名单阻塞。6.1 的 Rust 门禁入口已就位，断言一旦落地即自动进流程
- [ ] 7.3 在 `aidcp-edge/CLAUDE.md` 新增「Native 页面引擎」一节，写明：这层编码只挡扫读级别、不构成保密，拿到安装包即可还原；MUST NOT 基于「规则已加密」把凭据 / 令牌 / 可访问远端系统的密钥塞进同一通道
  - 【阻塞】需改 `aidcp-edge/CLAUDE.md`，该文件在本轨可改文件白名单外。解锁条件：白名单属主放行或由主 session 统一落护栏文档
- [ ] 7.4 同节写入本轮四类「本地全绿、只有真跑页面命令才现形」的失效模式法条：① 新增嵌入资产必须同时改构建脚本的读取与 `rerun-if-changed` 声明；② 新增分片必须同时登记进清单；③ 分片命名的词典序即执行结构序，新分片命名须排在依赖它的分片之前；④ 改页面规则后开发态必须由源码摘要强制重编
  - 【阻塞】同 7.3（`aidcp-edge/CLAUDE.md` 在白名单外）。四条法条的机械对应物已在 be0a8be 落地（① 分片目录 rerun-if-changed、② 未登记文件即构建失败、③ 清单词典序断言、④ 源码摘要驱动重建），只差写进护栏文档

## 8. aidcp-edge — 测试信号分离与假失败消除

- [ ] 8.1 给退役路径用例（当前抽样 6 个文件 4717 行：`test/flows/publish-command-handlers.test.ts`、`test/browse/browse-session.test.ts`、`test/locating/engine.test.ts`、`test/browse/note-extractor.test.ts`、`test/flows/like-runner.test.ts`、`test/integration/publish-e2e.test.ts`）加统一标记，标记依据为「其被测模块出现在生产剪枝黑名单里」，MUST NOT 用 skip
- [ ] 8.2 让套件收尾分别报出「生产路径覆盖 / 退役路径覆盖」两个计数
- [ ] 8.3 加一条对账断言：生产剪枝黑名单新增条目时，指向该模块的测试文件必须已被标记为退役覆盖，否则失败
- [ ] 8.4 修 `native/page-engine/src/facebook/publish_tests.rs:1006-1035` 的截止期用例
  - **频率与范围实测（2026-07-30，由 `restore-native-actuation-humanization-and-locating` 的第五波回写；本条仍归本 change 处置）**：
    ① **范围比本条原文大**：不止 `:1022` 那一条。同族至少三条 —— `select_mode_reports_ambiguous_after_one_unconfirmed_click`（`:659`，`unix_time_ms() + 150`）、
    `select_mode_is_ambiguous_when_post_click_confirmation_crosses_the_deadline`（`:728`）、`submit_does_not_confirm_when_the_submitted_probe_crosses_the_deadline`（`:1007`，`+50`）。
    ② **频率**：当天累计约 34 次全量、红 4 次（≈12%），**全部落在有并发负载的时段**；20 轮低负载测量里 0 次。
    在主干上跑 `npm run gate:native` **首跑即红**（`left: NotStarted, right: Ambiguous`）。
    ③ **订正一条流传的旧结论**：`restore-native-xiaohongshu-session-guards` 7.4 记的「正常负载 39 次全量从未红」**不成立**，
    多半是在空载下取样得出的 —— 与本批反复踩的「单独跑那个文件永远全绿」是同一种自证。
    ④ **修法上的一个反直觉约束（动手前必看）**：`submit_...` 那条给的预算是 50ms，而 `pointer_time_allowance_ms` 会据此把帧预算算成 **1**，
    也就是说**它今天能过，正是因为踩中了「预算不足就静默退化成瞬移」那条降级路径**。
    单纯抬预算会让点击变慢、反而更容易红；「换可测试时钟」与「指针降级」这两件事必须一起想。
    ⑤ 另一族（`fake_cdp.rs` 三条 feed-recovery 用例共用落点）已于 `aidcp-edge 7f9ea7f` 修掉，配对测量修前 7/10 红 → 修后 0/10。
    **P4 修掉之后主干门禁剩下的红全部来自本条这一族。**（:1022 的 `unix_time_ms() + 50`）：改用可注入 / 测试可控时钟表达「已过期」，或显式串行化；被测判定点在 `src/facebook/publish.rs` 点击前的过期检查，行为不改
- [ ] 8.5 按同一模式清理 `native/page-engine/tests/fake_cdp.rs` 里的 `unix_time_ms() + N` 绝对墙钟截止期
- [ ] 8.6 修 `test/native-page-engine/client.test.ts:13-27` 的子进程握手预算（当前逐条 500 毫秒 / 进程 3 秒）：或抬到能容纳默认并行度下的进程启动，或把该文件显式串行化；两者择一并写清理由

## 9. aidcp-edge — 跨平台打包资源按目标平台解析

- [ ] 9.1 把 `package.json` 的 `build.extraResources` 里 `build/native-page-engine/${platform}-${arch}` 与 `build/gost/${platform}-${arch}` 的平台来源改为目标平台（electron-builder 的 `${platform}` 宏在 `node_modules/app-builder-lib/out/util/macroExpander.js:34-35` 返回 `process.platform`，即构建主机平台）
  - 【阻塞】两个待改文件（`package.json` 的 `build.extraResources`、分平台打包配置）虽在白名单内，但改法要动分平台打包配置、**本机无法验证**（需真出包才能确认目标平台解析路径正确）。解锁条件：拿到一次真出包（或跨平台打包）的验证机会，见 11.7
  - ⏸ **【降级为「按 case 处理」，2026-07-30，用户裁定】不做，后面看 case。****已确认这样做是安全的**：即便在 macOS 上打 Windows 包踩中这条，也是**响亮失败、不会静默出错包** —— `scripts/after-pack.cjs` 的打包后置校验按**目标平台**（`context.electronPlatformName`）取值，`src/electron/native-page-engine-artifact.cjs` 直接比对产物清单里的 `platform` / `arch` / 可执行文件名，对不上即抛错（清单实测带 `"platform":"darwin"`、`"arch":"arm64"`）。**触发条件**：第一次真的要在 macOS 上出 Windows 包时回到本条；在那之前它零影响、不可能悄悄发货。
- [ ] 9.2 在拷贝/解析阶段即校验目标平台资源存在，失败时报错写明「目标平台/架构、主机平台/架构、实际解析到的目录」；保留 `scripts/after-pack.cjs:235-238` 现有的目标平台后置校验作为第二道
  - ⏸ **【降级为「按 case 处理」，2026-07-30，用户裁定】不做，后面看 case。****已确认这样做是安全的**：即便在 macOS 上打 Windows 包踩中这条，也是**响亮失败、不会静默出错包** —— `scripts/after-pack.cjs` 的打包后置校验按**目标平台**（`context.electronPlatformName`）取值，`src/electron/native-page-engine-artifact.cjs` 直接比对产物清单里的 `platform` / `arch` / 可执行文件名，对不上即抛错（清单实测带 `"platform":"darwin"`、`"arch":"arm64"`）。**触发条件**：第一次真的要在 macOS 上出 Windows 包时回到本条；在那之前它零影响、不可能悄悄发货。
- [ ] 9.3 加一条不出包的用例：以目标平台 `win32` 求解资源路径，断言解析结果与主机平台无关

## 10. aidcp（控制仓）— 护栏与在途工作收口

  - ⏸ **【降级为「按 case 处理」，2026-07-30，用户裁定】不做，后面看 case。****已确认这样做是安全的**：即便在 macOS 上打 Windows 包踩中这条，也是**响亮失败、不会静默出错包** —— `scripts/after-pack.cjs` 的打包后置校验按**目标平台**（`context.electronPlatformName`）取值，`src/electron/native-page-engine-artifact.cjs` 直接比对产物清单里的 `platform` / `arch` / 可执行文件名，对不上即抛错（清单实测带 `"platform":"darwin"`、`"arch":"arm64"`）。**触发条件**：第一次真的要在 macOS 上出 Windows 包时回到本条；在那之前它零影响、不可能悄悄发货。
- [ ] 10.1 更新 `docs/architecture.md`：组件图（72-85 行）、边缘模块表（125-138 行）、`DomProvider` / `ActionExecutor` 接口说明（141-144 行）与单步定位 / 锚点晋升两节（172-201 行）当前仍把已从生产剪除的 JS 页面智能当现役；改为如实描述 Native 引擎为现役、并标注这些 TypeScript 模块为退役保留
- [ ] 10.2 复核根 `CLAUDE.md` §2 的「DOM-first 定位三道闸」铁律表述：三道闸的语义仍然有效，但其权威落点已不是 `aidcp-edge/src/locating/engine.ts`；据实修订指针，不改变红线本身
- [ ] 10.3 在活跃 change `facebook-consent-structural-detect` 的 `tasks.md` 顶部登记「实装落点 `src/facebook/consent.ts` 已从生产构建剪除，按现落点实装不会改变生产行为」，并交由其属主决定改写落点或废弃；MUST NOT 代其改写立论 <!-- 2026-07-30 本条原同时指向 facebook-join-actuation-decouple，该 change 已由用户裁定按「立论过期」删除（其落点 TypeScript 加群执行器 src/facebook/join-executor.ts 全仓仅剩 import type 引用、运行时不可达，编译后从 dist 剪除），故本条收窄为单条。判据不变：代码是否还算数，看核心入口到不到得了，不看有没有人引用 -->
- [ ] 10.4 在 `native-page-engine-production-cutover/tasks.md` 里标注：其未勾的 4.6 / 6.5 / 9.1 / 9.3 所需的机械位置由本 change 提供，本 change 不代替其覆盖率承诺；并明确该 change 归档前必须先收口 9 条未勾任务（3.2 / 3.3 / 4.6 / 6.5 / 8.5 / 9.1 / 9.3 / 9.4 / 9.5），否则归档会把缺口随 delta 并进主规格变成已上线保证
- [ ] 10.5 在 `docs/real-machine-acceptance-backlog.md` 新增或并入「小红书 Native 切换真机验收」簇，承接 9.4 / 9.5 两项（当前全文无 XHS native 簇）

## 11. 验证与验收

- [x] 11.1 在 aidcp-edge worktree 内跑 `npm run test:acceptance`、`npm test`、`npm run typecheck`，记录通过数与本次新增用例的定位 <!-- aidcp-edge be0a8be 分支 native-migration-repair 实测：验收 30/30 全过；全量 2621 例 / 2594 绿 / 26 红 / 1 跳过；typecheck 通过。26 红全部是同分支他轨的失败优先用例（动作侧 15 条等 slice 2.3–2.7、通知侧 11 条等 2.9–2.15），本 change 零新增失败。本 change 新增用例定位：test/native-page-engine/artifact-gates.test.ts（各闸门的植入 / 对照自测 + 闸门次序回归）、build-contract.test.ts（存在性断言标注 + 判定型断言） -->
- [x] 11.2 跑新增的 `npm run gate:native`（fmt / clippy / test），记录解析到的工具链版本与实际执行的组件 <!-- aidcp-edge be0a8be 从仓根调用即解析到钉死工具链 1.97.1；实际执行 fmt --check、clippy -D warnings、test 三项全过 -->
- [ ] 11.3 记录 5.4 的改造前后实测对照（touch 分片后 verify 的输出）
  - 【阻塞于 5.4】本工作区产物目录为空，取不到改造前后的对照输出。解锁条件同 5.4：先做一次完整 release 构建
- [ ] 11.4 记录 1.4 对账断言在接入 `08-reaction-semantics.js` 前后的实际报错文本
  - 【无法取样】派生化与对账断言在同一次改造里落地，没有「清单已含该分片、闸门尚未派生」的中间态可复现；当前树上对账断言直接通过。若要留证据，只能人为回退派生再跑一次，本轮未做
- [ ] 11.5 在本清单按 `<!-- <repo> <commit-sha> 备注 -->` 格式回写 aidcp-edge 与控制仓的提交 sha（sha 必须取自已推送的提交）
  - 【部分完成】aidcp-edge 侧本轨 sha `be0a8be`（已推 origin/native-migration-repair）已回写。差控制仓侧 sha——本轮按分工不提交控制仓，提交由主 session 统一做，届时补写
- [ ] 11.6 **【真机验收项，不得当成已确认事实】** 打一次 macOS 安装包并在真机启动，确认改造后的产物校验、打包资源解析与冒烟全过；本 change 的代码级验证 MUST NOT 声称覆盖这一项（按 §6 纪律，打安装包只在用户明确要求时执行）
- [ ] 11.7 **【真机验收项】** 在 macOS 主机上执行一次 Windows 打包，确认 9.1/9.2 的报错确实指向真因；CI 上两个作业各自宿主等于目标、不触发此路径，故只能靠人工跨平台跑一次
- [ ] 11.8 **【真机验收项】** 确认本机之外的 CI 运行器上实际生效的 Rust 编译器版本与 `rust-toolchain.toml` 钉死的版本一致；当前无 CI 运行日志、产物里也不记录编译器版本，事后无法对账，需拿到 6.4 新流水线的首次运行日志才能定论
- [ ] 11.9 **【真机验收项】** 小红书 Native 切换的只读真机矩阵与写动作验收（承接 10.5 的 backlog 簇），本 change 不做、不声称
- [ ] 11.10 运行 `openspec validate enforce-native-engine-artifact-gates --strict`

## 12. 跨属主改动待追认（他人 change 已改本 change 的属主文件）

> 登记人：`restore-native-actuation-humanization-and-locating` 的第四波收口（2026-07-30）。
> 该 change 的 9.2 表里已自认越界，但**只登记在越界方自己的台账里，属主这边看不到** —— 本节补上。
> **MUST NOT 当成默认通过**：方向是收紧不等于属主已同意。

- [ ] 12.1 追认或否决 `aidcp-edge f652786` 对本 change 三个属主文件的改动：
  `scripts/native-engine-inventory.cjs`、`scripts/prune-production-dist.mjs`、
  `test/native-page-engine/artifact-gates.test.ts`。
  **改了什么**：分片泄漏守卫的覆盖面从「只数 Facebook 有序清单」改成**按目录派生**，计数 11 → 17；
  有序清单继续管拼接顺序，并与目录派生做交叉对账（对不上即响亮失败）。
  **为什么是越界**：与越界方自身 5.7「不改该文件一行」的纪律直接冲突，且这三个文件是本 change 1.1 / 1.2 / 2.1 的产物。
  **属主要判的**：① 目录派生是否与 1.4「清单每条都必须被两处闸门覆盖」的对账语义相容（会不会出现「目录里有、清单里无」被派生自动放行、反而绕过 1.4）；
  ② 11 → 17 是**覆盖面变了**、不是新增 6 个分片，本 change 台账里若已记过 11 这个数，须一并订正为「计数不是覆盖的证据」。

- [ ] 12.2 若追认，把 12.1 的结论回写进 1.1 / 1.2 / 2.1 的任务行备注（带 `f652786`）；
  若否决，由属主给出替代形态并通知越界方，**MUST NOT 静默保留**。
