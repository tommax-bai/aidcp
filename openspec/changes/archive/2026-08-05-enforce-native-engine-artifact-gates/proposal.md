## Why

2026-07 把页面智能迁到 Native 引擎后，围绕它建起来的一整套构建期安全网现在**看着在跑、实际不判定**：生产剪枝脚本对 10 个 Facebook 页面规则分片逐条断言"不许出现在产物里"，但它检查的位置在任何分支上都不存在（`aidcp-edge/scripts/prune-production-dist.mjs:47-57` 指向 `dist/facebook-router/*`，而仓内既无 `dist/facebook-router` 也无 `src/facebook-router`）——10 条全部空转；安装包内的那份禁止条目清单同样只有 10 条（`aidcp-edge/scripts/after-pack.cjs:177-187`），漏掉的正是承载点赞状态识别与反应控件定位的 `08-reaction-semantics.js`，而真正的事实源是 11 条的 `native/page-engine/src/facebook-router/manifest.txt`。这份安装包内清单同样**当前恒不触发**——electron-builder 的 `files` 允许清单只含 `dist/**/*`、`src/electron/**/*.cjs`、`src/electron/renderer/**/*`、`package.json`，`native/page-engine/src/**` 根本进不了归档；**今天真正在挡明文的是那份允许清单和 TypeScript 源码树的布局，不是这两份禁止清单**。

**【实装实测订正 · 两份清单不是同一份的两个副本】** 上面"两份禁止清单当前恒不触发"两条都成立，但读起来像同一份清单被抄了两遍，实际内容并不相同：剪枝那份是**产物相对路径**，除 10 条分片外还含一批已迁移到 Native 的退役 TypeScript 模块产物；打包那份是**归档条目名**，只含 10 条分片。实装期的处置也因此分两半：**分片部分**两处统一收口到同一事实源（页面规则清单）并按运行时派生；**退役模块部分**无法由该清单派生，保留显式枚举，但收敛到同一个共享模块里、不再各自手抄。

同一层还有三处机械缺口：构建期只断言清单条目唯一、无路径分隔符、按词典序递增（`native/page-engine/build.rs:131-161`），**从不检查分片目录里有没有未登记的文件**；分片按顺序直接拼接、中间不插任何分隔字节（`build.rs:155`），"每片以换行结尾"于是从排版习惯变成了正确性前提；开发态那道"校验通过"读的是产物自己写的哈希与清单、`Cargo.toml` 版本号和能力摘要（`scripts/build-native-page-engine.mjs:72-113`），**没有一项来自 Rust 源码或页面规则源码**，改了源码不重建照样打印 OK。

与此同时，近两万行 Rust 与全部构建脚本在任何自动流程里都不执行：`package.json` 全表 cargo 零命中，唯一的 CI 工作流是手动触发的出包流水线、既不跑单测也不跑 Rust 测试，控制仓集成闸 `scripts/land-change:38-42` 也只跑 TypeScript 三件套。此外那份自称"以 TypeScript 类型为准"的跨语言契约夹具只有 Rust 侧回放（`native/page-engine/tests/contract_fixtures.rs:29-53`），TypeScript 侧对它零引用——改类型不会让任何东西变红。混淆这一层的实际强度同样需要如实写清：密钥是编译期写死的 11 字节（`build.rs:7-9`，另有三份运行时副本 `xhs.rs:23` / `facebook.rs:39` / `probe.rs:8`），本机在两个已构建产物里各命中一处（darwin-arm64 偏移 1837753、darwin-x64 偏移 1908273）。

## What Changes

- 把两处防泄漏清单改成**从页面规则清单运行时派生**，并让"清单里有、闸里没有"当场使构建失败。
- 给每道否定式闸门补一条**可证伪自测**：在被检查的语料里植入违规内容、断言闸门确实拒绝；没有这条自测的闸门不计入覆盖。
- 让明文哨兵串**先证明自己还活着**：每个哨兵必须在当前进入生产编译的页面规则源码里存在，只落在仅测试编译单元里的哨兵一律判为失效。
- 构建期增加两条完整性断言：分片目录里的每个文件都必须登记在清单里；分片拼接必须插入显式分隔符或断言每片以换行结尾，TypeScript 侧的复刻实现同规则。
- 把开发态与打包态的产物校验**绑定到源码**：staged 清单记录由引擎源码输入算出的摘要，对不上即判过期并重建，MUST NOT 打印通过。
- 把 Rust 格式化 / 静态检查 / 测试做成仓内 npm 脚本（解析钉死的工具链、与调用目录无关、工具缺失即失败不跳过），并纳入集成闸。
- 把混淆边界写进护栏文档：这层只挡扫读级别、不构成保密；MUST NOT 基于"规则已加密"这个前提把凭据类敏感值塞进同一通道。密钥定义收敛到单一来源，使轮换无法只改一半。
- 打包资源目录按**目标平台**解析，不再取构建主机平台；平台不匹配时的报错必须指向真因。
- 分离测试信号：退役 TypeScript 路径的用例明确标注为退役覆盖、不再冒充生产覆盖；时间敏感的引擎用例改用可注入时钟或串行化，消除并行调度抖动造成的假失败。
- 自称跨语言的契约夹具**两侧都要有会执行的断言**：声明的那个 TypeScript 类型侧也必须消费同一份夹具，单侧回放不再算"两端已对齐"。

## Capabilities

### New Capabilities

- `native-engine-artifact-gates`: 定义 Native 引擎嵌入资产的登记完整性、防泄漏闸门的可证伪性、产物与源码的绑定校验、Rust 门禁的机械执行位置、跨语言契约夹具的双侧回放，以及混淆层的诚实边界。

### Modified Capabilities

- `edge-desktop-packaging`: 把"不得带着过期或缺失的编译产物出包"从 TypeScript 编译扩展到 Native 引擎产物；把打包资源的平台解析从构建主机平台改为目标平台。

## Impact

- `aidcp-edge/scripts/prune-production-dist.mjs`
- `aidcp-edge/scripts/after-pack.cjs`
- `aidcp-edge/scripts/build-native-page-engine.mjs`
- `aidcp-edge/scripts/ensure-native-page-engine-dev.mjs`
- `aidcp-edge/native/page-engine/build.rs`
- `aidcp-edge/native/page-engine/src/facebook-router/manifest.txt`（作为事实源被读取，内容不改）
- `aidcp-edge/package.json`（新增 Rust 门禁脚本与打包资源解析）
- `aidcp-edge/.github/workflows/`
- `aidcp-edge/test/native-page-engine/`、`aidcp-edge/native/page-engine/tests/`
- `aidcp-edge/CLAUDE.md`（新增 Native 引擎护栏法条）
- `aidcp/docs/architecture.md`、`aidcp/CLAUDE.md`（§2 指针订正）、`aidcp/scripts/land-change`
- `aidcp/docs/real-machine-acceptance-backlog.md`（新增 XHS Native 簇）、`aidcp/openspec/changes/{native-page-engine-production-cutover,facebook-consent-structural-detect,facebook-join-actuation-decouple}/tasks.md`（只登记事实，MUST NOT 代其改写立论）
- 本 change **不含**：不改任何页面规则分片的行为、不改 Rust 引擎的命令语义、不改边云协议、不改云端；不做部署、不出安装包、不做真机写动作；不替换混淆方案（不引入"真加密"）。
