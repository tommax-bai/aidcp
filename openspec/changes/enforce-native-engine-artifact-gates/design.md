## Context

2026-07 的 Native 迁移把浏览器页面智能从 TypeScript 搬到 Rust 引擎（07-22 小红书切生产、07-23 Facebook 与微信跟进），实质结构是：页面规则仍然是 JavaScript，构建期按清单拼接、逐字节异或后编进二进制，运行时注入页面执行。迁移公开的动机是防反编译，明确决定不双跑、不比对、不回退，回滚手段只有装包回滚。

在这个结构下，"构建期的那几道闸"就是这条链路唯一的机械保护。本 change 处理的是这几道闸当前的实际判定能力，全部在代码里坐实过：

- **两份防泄漏清单与事实源漂开，且各自都指不到能出问题的位置。** 事实源是 `aidcp-edge/native/page-engine/src/facebook-router/manifest.txt`（11 条）。生产剪枝脚本的禁止路径前 10 条是 `facebook-router/*.js`，拼在 `dist` 根下（`scripts/prune-production-dist.mjs:47-57、94-98`），而仓内既没有 `dist/facebook-router` 也没有 `src/facebook-router`——这 10 条断言恒不触发。打包后置扫描的禁止条目是 `/native/page-engine/src/facebook-router/*.js`（`scripts/after-pack.cjs:177-187`），同样只有 10 条、缺 `08-reaction-semantics.js`；而 electron-builder 的 `files` 允许清单只含 `dist/**/*`、`src/electron/**/*.cjs`、`src/electron/renderer/**/*`、`package.json`，`native/page-engine/src/**` 根本进不了归档——所以这 10 条同样恒不触发。**当前真正在挡明文的是 `files` 允许清单和 TypeScript 源码树的布局，不是这两份清单。** 清单本身只提供了"有人在守"的错觉，且新增分片会自动逃出去（`08-reaction-semantics.js` 于 `0439ecf` 加入清单，两份禁止列表建于 `a6623a4`，此后再无对账）。
- **清单只做正向断言，不做反向对账。** `build.rs:131-161` 逐条断言条目唯一、不含路径分隔符、按词典序递增、集合非空，但从不列目录看有没有未登记的文件。新增一个分片却忘记登记，构建照过、二进制里没有它、运行时静默走缺失逻辑。
- **拼接不插分隔符。** `build.rs:155` 直接 `source.extend(...)`，TypeScript 侧复刻实现 `test/native-page-engine/facebook-router-source.ts:22-24` 同样 `join('')`。当前 11 个分片末字节实测都是 `0a`，所以没翻车；但一旦某片尾随换行被去掉、且该片最后一行以行注释结尾，下一片首行就会被吞掉——结果仍是合法脚本，只是某个常量或函数凭空消失，跑到那条路径才报未定义。构建期四条断言与 TypeScript 复刻都不覆盖这一层。（说明：本 change 不主张"分片里现在已经存在行注释"——实测 11 个分片里 `^\s*//` 命中为 0，这是一条潜在缺口而非已发生故障。）
- **开发态"校验通过"与源码无关。** `scripts/ensure-native-page-engine-dev.mjs:19-28` 的逻辑是"`--verify` 成功即返回 verified、不重建"；而 `scripts/build-native-page-engine.mjs:72-113` 的 `verify()` 只读 staged 二进制、它自己写的 `.sha256`、它自己写的 `manifest.json`、`Cargo.toml` 的 version、`command-manifest.json` 的摘要——没有任何一项来自 Rust 源码或页面规则源码。二进制哈希与 `.sha256` 是同一次构建同时写的、必然自洽；能力摘要只反映命令清单，改实现不动它；`Cargo.toml` 的 version 自迁移起未变。三条逃生口同时失效，闸门报"已校验"、事实是"与源码无关"——这是"静默假成功"红线在构建闸上的形态。
- **明文哨兵是单向判定。** `build-native-page-engine.mjs:41-51` 列 9 条特征串，只在二进制里"找到"时报警，从不校验这些串当前是否还存在于会进生产编译的源码里。实测 `Input.dispatch` 与 `Page.navigate` 只出现在 `native/page-engine/src/facebook/publish_tests.rs`，而该文件由 `native/page-engine/src/facebook/publish.rs:892` 经 `#[path]` 挂在 `#[cfg(test)]` 下——release 构建里不存在，这两条哨兵已经是空哨。失活的表现形式是"扫描通过"，与真的没泄漏无法区分。
- **Rust 侧完全不在自动流程里。** `package.json` 全表 cargo 零命中；`.github/workflows/` 只有一个手动触发的出包流水线 `build-desktop.yml`，全文无 `npm test` / `cargo test` / clippy / typecheck；控制仓集成闸 `scripts/land-change:38-42` 只跑 `test:acceptance` + `npm test` + `typecheck`。工具链版本钉死只写在 `native/page-engine/rust-toolchain.toml`，rustup 只有在当前目录位于 crate 内才解析得到它——于是"装的工具链没有 cargo-clippy"这类偏差反复出现在各条 change 的验收记录里。
- **跨语言契约夹具只有单侧回放。** `native/page-engine/tests/contract_fixtures.rs:29-53` 回放 `tests/fixtures/page-probe-contracts.json`，并断言夹具头部的 `sourceContract` 恰为 `src/native-page-engine/client.ts#NativePageProbeResult`——也就是说这份夹具自称"以 TypeScript 那个类型为准"。实测 `test/` / `src/` / `scripts/` 里对该夹具文件与 `contract_fixtures` 的引用为零：TypeScript 侧既不加载它、也没有任何断言保证那个类型仍存在或仍与夹具期望一致。于是改 TypeScript 类型不会让任何东西变红（Rust 只比字符串路径，不比字段），而 Rust 侧的这条断言还会一直绿着，制造"两端已对齐"的错觉。这与本项目已经吃过两次的"手工双份契约 + 零路径级测试"是同一形态。
- **混淆强度需要如实记账。** 密钥是编译期写死的 11 字节（`build.rs:7-9`），另有三份运行时副本（`src/xhs.rs:23`、`src/facebook.rs:39`、`src/probe.rs:8`），四处无单一来源。本机在两个已构建产物里各命中一处该字面量（`build/native-page-engine/darwin-arm64/aidcp-page-engine` 偏移 1837753、`darwin-x64` 偏移 1908273）。也就是说拿到一份安装包、定位这 11 个字节并对二进制按 11 个相位逐段异或，即可还原全部页面规则明文，不需要访问仓库、也不需要已知明文攻击。
- **跨平台打包取的是构建主机平台。** `package.json` 的 `build.extraResources` 用 `build/native-page-engine/${platform}-${arch}`，而 electron-builder 的宏展开对 `platform` 返回 `process.platform`（`node_modules/app-builder-lib/out/util/macroExpander.js:34-35`）。在 macOS 上跑 `electron:build:win` 会把宿主平台的引擎目录当成 Windows 包的资源拷进去。它是失败关闭的——`scripts/after-pack.cjs:235-238` 用 `context.electronPlatformName` 作为目标平台去校验，会因平台字段与可执行文件名不符当场抛错，不会静默发出坏包——但失败点在整条构建之后，且报错不指向真因。CI 上两个作业各自宿主等于目标，不触发。
- **测试信号错位。** 退役 TypeScript 路径的用例仍在 `npm test` 里全绿：抽样 6 个文件即 4717 行（`test/flows/publish-command-handlers.test.ts` 1285、`test/browse/browse-session.test.ts` 2470、`test/locating/engine.test.ts` 334、`test/browse/note-extractor.test.ts` 222、`test/flows/like-runner.test.ts` 112、`test/integration/publish-e2e.test.ts` 294），无一条 skip，而对应模块已在生产剪枝黑名单里。同时新路径的对等覆盖尚未建立（迁移主 change 的 4.6 / 6.5 仍未勾）。另有两类结构性假失败：Rust 侧用例在构造时用绝对墙钟加极小余量当截止期（`native/page-engine/src/facebook/publish_tests.rs:1022` 余量 50 毫秒，被测路径 `src/facebook/publish.rs` 在点击前先查是否已过期），并行跑会在截止期之后才启动；TypeScript 侧 Native 用例每条都要真起一个子进程再走标准输入输出握手（`test/native-page-engine/client.test.ts:13-27`），命令预算却只有 500 毫秒。

## Goals / Non-Goals

**Goals**

- 让防泄漏闸门的枚举**从事实源派生**，新增分片自动进闸，登记与闸门不一致时构建失败。
- 让每道否定式闸门**能被证明会失败**：有一条植入违规内容并断言拒绝的自测。
- 让明文哨兵**先证明自己还在守着东西**，失活即判失败而不是判通过。
- 让开发态与打包态的"校验通过"**由源码输入决定**，源码变了必须重建。
- 把 Rust 格式化 / 静态检查 / 测试放进与 TypeScript 门禁同一个机械位置，且与调用目录无关。
- 把混淆层的真实边界写进护栏文档，阻止后续基于错误前提扩大这条通道的用途。
- 让打包资源按目标平台解析，报错指向真因。
- 把退役路径覆盖与生产覆盖分开计数；消除两类结构性假失败。
- 让自称跨语言的契约夹具在**两侧都有会执行的断言**，单侧回放不再冒充"两端已对齐"。

**Non-Goals**

- 不替换混淆方案、不引入"真加密"（对本地可执行文件不存在真正的保密），不新增密钥分发或远程取密。
- 不改任何页面规则分片的行为、不改 Rust 引擎的命令与结果语义、不改边云协议、不改云端与控制台。
- 不删除退役 TypeScript 模块或其测试（删除是另一条独立决策）。
- 不做部署、不出安装包、不做真机写动作、不声称任何真机验收结论。

### 明确不承接的分派条目（具名，不静默漏）

分派简报里以下条目**不进本 change**，逐条写明去处，避免"混进产物门禁 change 让它无法收敛"：

| 条目 | 为什么不做 / 由谁承接 |
| --- | --- |
| 小红书开帖是否真的落 404（要看地址是否带令牌、详情正文是否为空） | 运行时行为缺口，与构建期门禁无关。落点是小红书开帖链路，需真机判定；由 `docs/real-machine-acceptance-backlog.md` 的 XHS Native 簇（本 change task 10.5 建立）承接判定，判定后另起 change 修行为。 |
| 看图命令导致的深读永久挂起（推自代码路径、无真机实例） | 同上，运行时行为缺口；归属深读/看图命令的行为 change，本 change 不改任何命令语义。 |
| Facebook 热度恒 0 在全部布局下的正则判定（"所有布局的中性按钮都不含数字"未核验） | 页面规则内容问题。本 change 明确不改任何分片内容（见"与其他并行 change 的边界"），归属 Facebook 页面规则 change。 |
| 跨环境错投（重连复用旧端点）的真实概率 | 运行时端口/连接行为，与引擎产物门禁无关；归属边缘环境-端点绑定相关 change。 |
| 小红书提交窗口缺失是否会撕裂写入（依赖"写命令不做飞行中取消"这一当前实现） | 运行时并发语义，需真机复现；归属小红书提交窗口 change。 |
| 四处"找不到就退回文档主体"的空根塌陷 | 页面规则/定位行为，需导航瞬时窗口触发；归属对应平台的页面规则 change。 |
| 小红书通知去重键折叠、行选择器退化的后果规模 | 需线上数据支撑，无代码级判据；归属通知巡视相关 change。 |
| 七个簇里"维持原判"的编号条目（`F-IPC-*` / `INJ-*` / `TXT-*` / `PACE-*` / `GEST-*` / `TIME-*` / `RETRY-*` / `PLAT-OBS-*` / `BUILD-*` / `DRIFT-*`） | 简报只给了编号、无正文与原始状态，无法在代码里坐实，因此**不据编号写任何 Requirement**。处置口径：补齐正文后重做一次并案；本 change 不代其立论。 |

上表中唯一被本 change 吸收的 C 段条目是"CI 上实际生效的 Rust 编译器版本无法对账"——它直接依附于本 change 新建的流水线，写成 task 11.8 的流水线验收项，且**不写进任何 Requirement**。

## 关键决策

### D1. 闸门枚举一律从页面规则清单派生，禁止手写字面量数组

生产剪枝与打包后置扫描都在运行时读 `manifest.txt`，据此生成禁止集合；清单里存在但任何闸门未覆盖的条目，构建失败。

**被否决的替代：把 `08-reaction-semantics.js` 补进两份清单。** 这只修一次实例、不修机制——它正是 `a6623a4` 建清单、1 小时 51 分后 `0439ecf` 加分片这条时序的第二次重演。手写清单与事实源之间没有任何机械对账，下一个分片会以完全相同的方式漏出去。

**被否决的替代：只留 electron-builder 的 `files` 允许清单当唯一保护。** 允许清单确实是现在真正在挡的那道，但它是"默认拒绝"的宽口径规则，任何一次为了别的原因放宽 `files` 都会静默打开这条缝，而没有任何东西会提醒。派生式禁止清单是针对这一类具体资产的第二道，且能在允许清单被放宽时立刻报警。

### D2. 否定式闸门必须自带可证伪自测

每道"不许出现"的闸门配一条测试：在一份临时语料里植入被禁内容、跑该闸门、断言它拒绝。没有这条自测的闸门不计入覆盖。

**被否决的替代：只用断言脚本文本包含某些字符串来证明闸门存在**（现状 `test/native-page-engine/build-contract.test.ts:38,43` 就是这种，只断言脚本源码里出现 `manifest.json` 与 `forbiddenCleartextMarkers`）。这类断言在闸门指向不存在的位置时同样全绿——它证明的是"代码里写了这段话"，不是"这段话会判定"。本 change 的两条空转闸门在这类断言下已经绿了很久。

### D3. 明文哨兵改成双向：既查产物里没有，也查源码里还有

哨兵集合每条都必须能在"会进入 release 编译的页面规则源码"里定位到；只落在 `#[cfg(test)]` 编译单元或已删除标识符上的哨兵，判为失效并使构建失败。

**被否决的替代：把失效哨兵直接删掉。** 那会把覆盖归零这件事变成一次静默的减法。要求"失效即失败"逼着改动者当场选：要么把哨兵重新指到一个活的特征，要么显式记录这条覆盖被放弃。

### D4. 校验面加入源码摘要，且开发态"verified"必须由它决定

构建时把引擎源码输入（Rust 源码树、页面规则分片与其清单、命令清单、`build.rs`）算一个摘要写进 staged 清单；`--verify` 重算并比对，不一致即判过期。开发态入口据此重建。

**被否决的替代：靠 `Cargo.toml` 版本号 bump 来表达"源码变了"。** 那是人工纪律，迁移至今跨约 30 次提交一直停在同一版本号，已经被实践证伪；而且它无法表达"只改了页面规则分片"这类不涉及 crate 版本的改动。

**被否决的替代：每次 `electron:dev` 无条件重建。** 全量 release 构建代价过大，会把开发循环拖垮；摘要比对能在源码没变时保留跳过。

### D5. 分片拼接的正确性用显式断言承担，而不是靠排版习惯

构建期与 TypeScript 复刻实现二选一并保持一致：要么在片间插入一个显式分隔字节，要么断言每片以换行结尾。同时构建期列目录反向对账未登记文件。

**被否决的替代：靠代码评审保证每片末尾留换行。** 这条不变量没有任何机械表达，且违反它的后果不是报错而是内容被吞——拼接结果仍是合法脚本，只在跑到那条路径时才报未定义，是最难归因的一类。

### D6. Rust 门禁做成仓内脚本并进集成闸，工具链解析与调用目录无关

新增 npm 脚本封装 `cargo fmt --check` / `clippy` / `test`，脚本内部按 crate 目录解析钉死的工具链（复用现有 `resolveCargoBinary` 那条 rustup 解析路径的思路）；工具链或组件缺失时失败退出，MUST NOT 记为"跳过"。控制仓集成闸补上调用。

**被否决的替代：只在 CI 出包流水线里加 Rust 步骤。** 那条流水线是手动触发的发版动作，跑不到日常改动上；而 Rust 改动恰恰是日常的。

**被否决的替代：要求开发者手工在 crate 目录里敲 cargo。** 这就是现状，各条 change 的验收记录已经显示覆盖随手工调用方式漂移。

### D7. 混淆层写成"扫读阻力"，并封住这条通道承载敏感值的可能

护栏文档明确：嵌入的页面规则只做扫读级别的阻隔，任何拿到安装包的人都能还原；MUST NOT 把凭据、令牌、可访问远端系统的密钥经这条通道分发。同时密钥收敛到单一定义，使轮换不可能只改一半，并给解码后内容加一条会真正执行的断言。

**被否决的替代：换更强的加密或做运行时取密。** 用户口径明确：对本地可执行文件不存在真正的保密，换算法只是把成本从"搜 11 个字节"抬到"读一段反汇编"，不改变结论，却会让人误以为这条通道可以承载敏感值——那才是真正的风险。

### D8. 打包资源目录由后置校验的同一套目标平台事实解析

资源分阶段落点由目标平台与目标架构决定，与构建主机无关；不匹配时的报错必须写明"目标平台 X / 主机平台 Y / 解析到的目录 Z"。

**被否决的替代：维持现状不动，理由是"反正失败关闭"。** 失败关闭确实成立，但失败点在整条构建之后、报错不指向真因，等于把一次跨平台出包的全部时间浪费掉再让人猜。

### D9. 测试信号分离，而不是删测试

退役路径的用例保留但打上明确标记，套件分别报"生产路径覆盖 / 退役路径覆盖"两个计数；时间敏感的引擎用例改用可注入时钟（或按相对预算 + 串行化），使并行调度抖动不再产生失败。

**被否决的替代：直接删掉退役路径的 4700 余行测试。** 在新路径对等覆盖尚未建立之前删除，会把仅存的行为口径也一起丢掉——迁移主 change 的 4.6 / 6.5 正是"用退役实现当行为口径去补 Native 覆盖"这件事，删了就没有 oracle 了。

**被否决的替代：把假失败的用例标 skip。** 那是把信号换成沉默，仍然违反"不静默假成功"的同一条红线。

### D10. 自称跨语言的契约夹具必须两侧都回放

夹具头部写了 `sourceContract` 指向另一门语言的类型，就必须在那门语言侧也有一条会执行的断言：TypeScript 侧加载同一份夹具、按该类型消费每条 `expected`，并断言那个类型标识符仍然存在。任一侧缺席即由门禁判失败。

**被否决的替代：删掉 `sourceContract` 字段，让夹具只对 Rust 负责。** 那会把"两端对齐"这条已经写下的承诺静默撤回，而夹具的期望值本身就是照着 TypeScript 类型写的——撤回字段不会让它变正确，只会让漂移变得不可发现。

**被否决的替代：靠 `typecheck` 兜底。** TypeScript 的类型检查看不见一份 JSON 夹具，改类型名也不会让它变红；这正是现状。

## 风险与回滚

- **派生式禁止清单可能把当前"恒不触发"变成"当场报错"。** 这正是目的，但首次接入时要接受一次性修整：闸门被重新指到真实语料后，可能立刻暴露出别的未登记资产。缓解办法是先加对账断言并跑一次，把结果如实登记，再打开失败开关。
- **源码摘要口径过宽会让开发态频繁重建。** 摘要输入只取真正影响二进制的文件集合（分片、清单、Rust 源码、`build.rs`、命令清单），不纳入测试文件与文档；上线后观察一次开发循环的重建频率。
- **Rust 门禁进集成闸会拉长每次合并时间，也可能在没装工具链的机器上直接拦停。** 按"缺失即失败、不跳过"的口径这是刻意的；但需要在护栏文档里写清一次性安装步骤，否则会变成合并阻塞。
- **哨兵双向校验可能与后续页面规则重构频繁冲突。** 失效时的正确动作是重新指向一个活特征，不是放宽规则；这条要写进护栏。
- **回滚**：本 change 全部落在构建与测试链路，回滚即回退相应提交；不涉及数据、协议、运行时行为，无迁移。

## 与其他并行 change 的边界

本 change **只碰构建、门禁、测试基础设施与文档**，不碰任何运行时行为文件。明确不改：

- `aidcp-edge/native/page-engine/src/facebook-router/*.js` 的内容（只把它们的**清单**当事实源读取）
- `aidcp-edge/native/page-engine/src/engine.rs` 与 `src/facebook/**`、`src/xhs.rs`、`src/probe.rs` 的行为逻辑（唯一例外是密钥定义的单一来源收敛，属纯常量重定向、不改语义）
- 两份 `protocol.ts`、`aidcp-cloud/src/comm/command-bridge.ts`、角色注册表、`src/risk/risk-state-machine.ts`（§7 热点文件，本 change 完全不涉及）
- 任何云端或控制台文件

与迁移主 change `native-page-engine-production-cutover` 的关系：那条 change 仍活跃（账面 42/51），其未勾的 9 条里，4.6（逐命令 Native 契约测试）、6.5（发布安全夹具移植）、9.1（全部本地目标的 Rust 格式化/测试/静态检查/release 构建）、9.3（打包输入图检查、打包冒烟、签名核验、泄漏扫描）与本 change 高度重叠。**本 change 提供的是这些任务所需的机械位置**（派生式闸门、可证伪自测、源码绑定校验、Rust 门禁入口、退役/生产覆盖分离），**不替代那条 change 对具体命令覆盖率的承诺**。两者的收口顺序：本 change 先落基础设施，主 change 再据此逐条补覆盖并在归档前收口——否则归档会把这 9 条随 delta 并进主规格，从此变成"已上线保证"。

与 `openspec/specs/native-page-engine/` 的关系：那是可行性验证阶段的只读探针规格（写着 opt-in、read-only、"现有 JavaScript 执行器仍是唯一生产写入方"），已被生产切换实际取代但尚未重写。本 change **不往那份规格里塞生产行为要求**，新增独立能力 `native-engine-artifact-gates` 承载。

与两条仍活跃、但实装落点已从生产剪除的 change（`facebook-consent-structural-detect` 指向 `src/facebook/consent.ts`、`facebook-join-actuation-decouple` 指向 TypeScript 加群执行器的词表定位）的关系：本 change **不改它们的内容**，只在自己的任务清单里要求把"落点已失效"这件事当场登记到那两条 change，由它们的属主决定是重写落点还是废弃。
