## 1. aidcp-edge — 泄漏闸门从事实源派生

- [ ] 1.1 在 `scripts/` 下新增一个共享模块，运行时读取 `native/page-engine/src/facebook-router/manifest.txt`，导出「已登记分片名列表」，供剪枝脚本、打包后置扫描与测试共用
- [ ] 1.2 把 `scripts/prune-production-dist.mjs:47-57` 的 10 条 `facebook-router/*.js` 字面量删掉，改为按 1.1 的列表生成禁止路径，并把检查根重新锚定到该脚本实际能产出的语料（当前 `dist/facebook-router` 与 `src/facebook-router` 均不存在，须先确认剪枝脚本应该守的是哪个目录，若确认无对应产物则改为「守 dist 全树的分片文件名」并记录判断依据）
- [ ] 1.3 把 `scripts/after-pack.cjs:177-187` 的 10 条 `/native/page-engine/src/facebook-router/*.js` 字面量删掉，改为按 1.1 的列表生成条目；同时对 electron-builder 的 `files` 允许清单加一条断言：允许清单一旦被放宽到覆盖 `native/page-engine/src/**`，打包失败
- [ ] 1.4 加一条对账断言：清单里的每个条目都必须被上述两处闸门覆盖，缺一即失败；`08-reaction-semantics.js` 当前缺席这两处，接入后应立即被这条断言接住

## 2. aidcp-edge — 否定式闸门的可证伪自测

- [ ] 2.1 为剪枝脚本的禁止路径闸加一条自测：在临时目录里造出一个被禁文件、跑闸门、断言抛错
- [ ] 2.2 为剪枝脚本与打包扫描的明文标记闸各加一条自测：在临时语料里植入一条标记、断言闸门拒绝
- [ ] 2.3 为打包后置扫描的禁止条目闸加一条自测：用一个植入了被禁条目的临时 asar（或等价条目清单桩）断言拒绝
- [ ] 2.4 把 `test/native-page-engine/build-contract.test.ts:38,43` 那类「断言脚本文本里出现某标识符」的用例标注为「存在性断言、不构成判定证据」，并在同文件补上指向 2.1–2.3 的判定型断言
- [ ] 2.5 接上跨语言契约夹具的 TypeScript 侧：`native/page-engine/tests/contract_fixtures.rs:29-53` 回放 `tests/fixtures/page-probe-contracts.json` 并断言其 `sourceContract` 为 `src/native-page-engine/client.ts#NativePageProbeResult`，而实测 `test/` / `src/` / `scripts/` 对该夹具与 `contract_fixtures` 引用为零。新增一条 TypeScript 用例加载同一份夹具，按 `NativePageProbeResult` 消费每条 `expected`（类型级 + 运行时校验二者其一即可，但必须在改类型名 / 改字段时变红），并断言该类型标识符仍存在；验收标准：临时把 `client.ts` 里该类型改名后这条 TS 用例失败（Rust 侧的字符串比对此时仍绿，须在本清单记录这一对照）

## 3. aidcp-edge — 明文哨兵双向校验

- [ ] 3.1 给 `scripts/build-native-page-engine.mjs:41-51` 的 9 条 `forbiddenCleartextMarkers` 加一条存活校验：每条必须在会进入 release 编译的页面规则/引擎源码里定位到，定位不到即失败
- [ ] 3.2 处置两条已失效哨兵 `Input.dispatch` 与 `Page.navigate`（实测只出现在 `native/page-engine/src/facebook/publish_tests.rs`，该文件经 `src/facebook/publish.rs:892` 的 `#[path]` 挂在 `#[cfg(test)]` 下、不进 release）：要么改指一个活特征，要么显式记录这条覆盖被放弃及理由，MUST NOT 静默删除
- [ ] 3.3 补一条自测：临时把某条哨兵改成不存在的串，断言存活校验失败

## 4. aidcp-edge — 分片登记完整性与拼接不变量

- [ ] 4.1 在 `native/page-engine/build.rs` 的 `read_ordered_sources`（131-161 行）里加反向对账：列出分片目录内的文件，凡未登记在清单里即 `panic!` 并指名该文件
- [ ] 4.2 在同一函数里落定拼接不变量：片间插入显式分隔字节，或断言每片以 `\n` 结尾（二选一并在注释里写清选了哪条及理由）；实测当前 11 片末字节均为 `0a`，接入后不应产生行为变化
- [ ] 4.3 让 `test/native-page-engine/facebook-router-source.ts:22-24` 的 TypeScript 复刻实现采用与 4.2 完全相同的规则，并加一条断言：两种拼接结果逐字节相等
- [ ] 4.4 补两条失败优先用例：① 目录里放一个未登记文件 → 构建期对账失败；② 造一份缺尾随换行的分片 → 拼接不变量失败

## 5. aidcp-edge — 产物校验绑定源码

- [ ] 5.1 在 `scripts/build-native-page-engine.mjs` 的 `build()` 里计算「引擎源码输入摘要」（Rust 源码树 + `src/facebook-router/` 全部分片与清单 + `build.rs` + `command-manifest.json`），写入 staged `manifest.json` 的新字段
- [ ] 5.2 在同文件 `verify()`（72-113 行）里重算该摘要并比对，不一致即抛「产物相对源码已过期」；保留既有的哈希/清单/协议版本/能力摘要检查
- [ ] 5.3 确认 `scripts/ensure-native-page-engine-dev.mjs:19-28` 的「verify 成功即 return verified、不重建」在 5.2 之后自动变成「源码变了就重建」，不再需要额外分支；如需改动则一并落地
- [ ] 5.4 复现并消灭已知实证：`touch native/page-engine/src/facebook-router/00-shared.js` 后跑 `node scripts/ensure-native-page-engine-dev.mjs`，改造前输出 `OK: unsigned target artifact verified ...` 且不重建；改造后必须触发重建。把改造前后的实测输出记进本清单
- [ ] 5.5 在 `src/electron/native-page-engine-artifact.cjs` 的打包态校验里同步接受并校验新字段（缺字段视为不兼容清单）

## 6. aidcp-edge — Rust 门禁进标准环境与集成闸

- [ ] 6.1 新增 npm 脚本（如 `gate:native:fmt` / `gate:native:clippy` / `gate:native:test`），内部复用 `build-native-page-engine.mjs` 里 `resolveCargoBinary()` 的 rustup 解析思路（`rustup which ...`，`cwd: crateDir`），保证从仓根调用也解析到 `native/page-engine/rust-toolchain.toml` 钉死的工具链
- [ ] 6.2 工具链或组件缺失时脚本 MUST 非零退出并写明「解析到哪个工具链、缺哪个组件」，MUST NOT 记为跳过或非阻断
- [ ] 6.3 新增一条聚合脚本 `gate:native`，串起 6.1 三项，供集成闸单点调用
- [ ] 6.4 在 `.github/workflows/` 新增一个按 push / PR 触发的检查流水线，跑 `npm test`、`npm run typecheck`、`npm run gate:native`；现有 `build-desktop.yml` 保持手动触发的出包职责不变
- [ ] 6.5 在控制仓 `scripts/land-change`（当前第 38-42 行只跑 `test:acceptance` / `npm test` / `typecheck`）补上：当被集成的仓存在 `gate:native` 脚本时一并运行
- [ ] 6.6 记录一次性安装步骤（`rustup toolchain install` 需带 `components`），并检查 `scripts/build-desktop-macos-ol-arm64-common.sh` 里 `--profile minimal` + `export RUSTUP_TOOLCHAIN` 的组合是否会绕开 `rust-toolchain.toml` 的组件声明；若会，一并修正

## 7. aidcp-edge — 混淆边界诚实化与密钥单一来源

- [ ] 7.1 把编码密钥收敛到单一定义，`native/page-engine/build.rs:7-9` 与三处运行时副本（`src/xhs.rs:23`、`src/facebook.rs:39`、`src/probe.rs:8`）共用同一来源；纯常量重定向，MUST NOT 改动任何解码语义
- [ ] 7.2 补一条会真正执行的解码内容断言：对嵌入资产解码后校验其明文特征，密钥不一致时失败（该断言随 6.1 的 Rust 门禁进入自动流程）
- [ ] 7.3 在 `aidcp-edge/CLAUDE.md` 新增「Native 页面引擎」一节，写明：这层编码只挡扫读级别、不构成保密，拿到安装包即可还原；MUST NOT 基于「规则已加密」把凭据 / 令牌 / 可访问远端系统的密钥塞进同一通道
- [ ] 7.4 同节写入本轮四类「本地全绿、只有真跑页面命令才现形」的失效模式法条：① 新增嵌入资产必须同时改构建脚本的读取与 `rerun-if-changed` 声明；② 新增分片必须同时登记进清单；③ 分片命名的词典序即执行结构序，新分片命名须排在依赖它的分片之前；④ 改页面规则后开发态必须由源码摘要强制重编

## 8. aidcp-edge — 测试信号分离与假失败消除

- [ ] 8.1 给退役路径用例（当前抽样 6 个文件 4717 行：`test/flows/publish-command-handlers.test.ts`、`test/browse/browse-session.test.ts`、`test/locating/engine.test.ts`、`test/browse/note-extractor.test.ts`、`test/flows/like-runner.test.ts`、`test/integration/publish-e2e.test.ts`）加统一标记，标记依据为「其被测模块出现在生产剪枝黑名单里」，MUST NOT 用 skip
- [ ] 8.2 让套件收尾分别报出「生产路径覆盖 / 退役路径覆盖」两个计数
- [ ] 8.3 加一条对账断言：生产剪枝黑名单新增条目时，指向该模块的测试文件必须已被标记为退役覆盖，否则失败
- [ ] 8.4 修 `native/page-engine/src/facebook/publish_tests.rs:1006-1035` 的截止期用例（:1022 的 `unix_time_ms() + 50`）：改用可注入 / 测试可控时钟表达「已过期」，或显式串行化；被测判定点在 `src/facebook/publish.rs` 点击前的过期检查，行为不改
- [ ] 8.5 按同一模式清理 `native/page-engine/tests/fake_cdp.rs` 里的 `unix_time_ms() + N` 绝对墙钟截止期
- [ ] 8.6 修 `test/native-page-engine/client.test.ts:13-27` 的子进程握手预算（当前逐条 500 毫秒 / 进程 3 秒）：或抬到能容纳默认并行度下的进程启动，或把该文件显式串行化；两者择一并写清理由

## 9. aidcp-edge — 跨平台打包资源按目标平台解析

- [ ] 9.1 把 `package.json` 的 `build.extraResources` 里 `build/native-page-engine/${platform}-${arch}` 与 `build/gost/${platform}-${arch}` 的平台来源改为目标平台（electron-builder 的 `${platform}` 宏在 `node_modules/app-builder-lib/out/util/macroExpander.js:34-35` 返回 `process.platform`，即构建主机平台）
- [ ] 9.2 在拷贝/解析阶段即校验目标平台资源存在，失败时报错写明「目标平台/架构、主机平台/架构、实际解析到的目录」；保留 `scripts/after-pack.cjs:235-238` 现有的目标平台后置校验作为第二道
- [ ] 9.3 加一条不出包的用例：以目标平台 `win32` 求解资源路径，断言解析结果与主机平台无关

## 10. aidcp（控制仓）— 护栏与在途工作收口

- [ ] 10.1 更新 `docs/architecture.md`：组件图（72-85 行）、边缘模块表（125-138 行）、`DomProvider` / `ActionExecutor` 接口说明（141-144 行）与单步定位 / 锚点晋升两节（172-201 行）当前仍把已从生产剪除的 JS 页面智能当现役；改为如实描述 Native 引擎为现役、并标注这些 TypeScript 模块为退役保留
- [ ] 10.2 复核根 `CLAUDE.md` §2 的「DOM-first 定位三道闸」铁律表述：三道闸的语义仍然有效，但其权威落点已不是 `aidcp-edge/src/locating/engine.ts`；据实修订指针，不改变红线本身
- [ ] 10.3 在活跃 change `facebook-consent-structural-detect` 与 `facebook-join-actuation-decouple` 的 `tasks.md` 顶部登记「实装落点 `src/facebook/consent.ts` / TypeScript 加群执行器已在 `scripts/prune-production-dist.mjs` 的生产剪枝黑名单里，按现落点实装不会改变生产行为」，并交由其属主决定改写落点或废弃；MUST NOT 代其改写立论
- [ ] 10.4 在 `native-page-engine-production-cutover/tasks.md` 里标注：其未勾的 4.6 / 6.5 / 9.1 / 9.3 所需的机械位置由本 change 提供，本 change 不代替其覆盖率承诺；并明确该 change 归档前必须先收口 9 条未勾任务（3.2 / 3.3 / 4.6 / 6.5 / 8.5 / 9.1 / 9.3 / 9.4 / 9.5），否则归档会把缺口随 delta 并进主规格变成已上线保证
- [ ] 10.5 在 `docs/real-machine-acceptance-backlog.md` 新增或并入「小红书 Native 切换真机验收」簇，承接 9.4 / 9.5 两项（当前全文无 XHS native 簇）

## 11. 验证与验收

- [ ] 11.1 在 aidcp-edge worktree 内跑 `npm run test:acceptance`、`npm test`、`npm run typecheck`，记录通过数与本次新增用例的定位
- [ ] 11.2 跑新增的 `npm run gate:native`（fmt / clippy / test），记录解析到的工具链版本与实际执行的组件
- [ ] 11.3 记录 5.4 的改造前后实测对照（touch 分片后 verify 的输出）
- [ ] 11.4 记录 1.4 对账断言在接入 `08-reaction-semantics.js` 前后的实际报错文本
- [ ] 11.5 在本清单按 `<!-- <repo> <commit-sha> 备注 -->` 格式回写 aidcp-edge 与控制仓的提交 sha（sha 必须取自已推送的提交）
- [ ] 11.6 **【真机验收项，不得当成已确认事实】** 打一次 macOS 安装包并在真机启动，确认改造后的产物校验、打包资源解析与冒烟全过；本 change 的代码级验证 MUST NOT 声称覆盖这一项（按 §6 纪律，打安装包只在用户明确要求时执行）
- [ ] 11.7 **【真机验收项】** 在 macOS 主机上执行一次 Windows 打包，确认 9.1/9.2 的报错确实指向真因；CI 上两个作业各自宿主等于目标、不触发此路径，故只能靠人工跨平台跑一次
- [ ] 11.8 **【真机验收项】** 确认本机之外的 CI 运行器上实际生效的 Rust 编译器版本与 `rust-toolchain.toml` 钉死的版本一致；当前无 CI 运行日志、产物里也不记录编译器版本，事后无法对账，需拿到 6.4 新流水线的首次运行日志才能定论
- [ ] 11.9 **【真机验收项】** 小红书 Native 切换的只读真机矩阵与写动作验收（承接 10.5 的 backlog 簇），本 change 不做、不声称
- [ ] 11.10 运行 `openspec validate enforce-native-engine-artifact-gates --strict`
