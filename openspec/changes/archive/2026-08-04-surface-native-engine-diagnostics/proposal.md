## Why

Rust 引擎**已经在写诊断行**：`native/page-engine/src/` 下 15 处 `eprintln!`、11 类具名标签（`main.rs:381/521/533`、`engine.rs:1271/1559/1829/1915/2352/2432/2440/2456`、`facebook/group_join.rs:35`、`facebook/runtime.rs:179/452`、`facebook/shared.rs:634`）。**没有任何一条能被人读到。** 宿主把引擎子进程的错误输出收进一个 2048 字符的滚动尾缓冲（`src/native-page-engine/client.ts:42`、`:626-628`），而这份缓冲**只在构造进程级失败对象时**才挂出去（`:483/526/544/558/633/643/824/830`）。命令正常返回、进程正常退出的那些行，随进程一起丢弃。

这不是「少了一行记账」，是**一整类记账没有收件人**。三种后果各自独立成立：

- **成功路径上的降级永不可见。** 逐字输入的降级记账已经写好了（`input.rs:499-506` 生成 note，`engine.rs:1559/1915` 打出来），命令仍返回 `ok=true`、进程不退出 ⇒ 那两行必然丢弃。**「已经记账了」在生产上等价于「没记账」。**
- **连失败诊断也大半看不见。** `native_page_engine_session_open_failed`（`main.rs:381`）与 `native_page_engine_request_rejected`（`main.rs:521`）走的是「回一个错误响应、进程继续活着」，同样够不到进程级失败那一刻。只有紧邻进程退出、且落在最后 2048 字符里的才有机会。
- **指针拟人轨迹的降级（E12）连标记都没有**，而且**修它绕不开这条通路** —— 这正是它在拟人化线收口时被具名交接出来的原因（`docs/edge-honesty-gap-inventory.md` E12）。

**通路的末端其实已经存在，缺的只有一跳。** Electron 外壳逐行读核心子进程的 stdout/stderr，一路进 UI 活动流、一路 append 到 `userData/logs/edge.log`（`src/electron/main.cjs:187-190`，~5MB 轮转）；另有一条结构化诊断通路 `[command-diagnostic]`（核心 stdout → `src/electron/command-diagnostics.cjs` → 50 条 / 30 分钟环 → 渲染层，`main.cjs:5860-5874`）。**断点只在「引擎子进程 → 核心进程」这一跳**：`src/native-page-engine/` 整个模块对 console 零输出，`client.ts` 只 import Node 内置（`:1-6`），是刻意保持的纯协议客户端。

## What Changes

- **引擎子进程的错误输出改为逐行转发到核心进程的诊断出口**，不再只当作进程级失败的附属证据。转发是 tee：现有的滚动尾缓冲**保留**（进程级失败仍需要它做归因），新增的是一条并行的、不依赖进程死亡的出口。
- **纯协议客户端保持纯协议**：`client.ts` 新增一个可选的诊断回调选项，不引入 `node:fs` / `console` 依赖；具体写到哪里由 `runtime.ts` 这一层决定并注入。缺席该选项时行为与今天逐字相同。
- **转发按行切分，而不是按 chunk 拼接。** 今天的尾缓冲允许一行被截断成两半、也允许前半行被挤掉；诊断行必须整行到达，半行必须被识别为半行。
- **每条转发行带上归因**：当时在飞的那条命令（`runtime.ts:214-220` 的 `serial()` 保证同一运行时同一时刻只有一条命令在飞）。在飞命令为零或多于一条时，**如实标注归因不确定，MUST NOT 猜一条挂上去**。
- **转发有量的上限，且上限是响亮的**：超过上限时报出「本次丢弃 N 行」，MUST NOT 静默截断（静默截断读起来和「引擎没说话」一模一样）。
- **指针拟人轨迹的降级变成两态可分 + 留痕（E12）**。今天 `generate_pointer_path`（`input.rs:1215-1233`）把两件完全不同的事压成同一个返回形状：「目标就在指针脚下（`distance <= 2.0`，合理，不是降级）」与「帧预算只剩 1 帧（`budget == 1`，降级）」。改为在返回值上把这两者分开，并在预算导致帧数掉出拟人下限（`POINTER_FRAME_COUNT_MIN = 15`，即剩余预算低于约 480ms）与塌成单帧（剩余约 63ms 以内）时各自留痕。**MUST NOT 因此改变点击的成败判定** —— 降级下的点击业务结果是真的，回执仍应如实为成功。
- **内容安全边界随通路一起前移**：转发出去的行只能是引擎自己生成的、有界的、无页面内容的诊断，MUST NOT 挟带选择器、URL、DOM 文本、凭据或页面派生字符串。这条今天由 `native-page-engine` 的解码诊断要求覆盖（其场景明写「serialized stdout、bounded stderr … 只含字段路径与 JSON 类别」），通路打开后它从「反正没人看」变成真正承重。

## Capabilities

### New Capabilities

- `native-engine-diagnostic-channel`: 引擎子进程诊断行到达运营可见位置的通路本身 —— 逐行转发、归因、有界与响亮丢弃、内容安全边界，以及「成功路径上的记账也必须到得了人眼前」这条不变量。

### Modified Capabilities

- `native-actuation-primitives`: 指针拟人轨迹在预算收紧时的降级须与「目标已在脚下」两态可分，并且必须留痕；现有要求只规定了轨迹形态，对降级一字未提。

## Impact

- **aidcp-edge（唯一受影响仓）**
  - `src/native-page-engine/client.ts`：stderr 处理由「拼尾缓冲」改为「切行 → tee（尾缓冲 + 诊断回调）」；新增可选回调选项。
  - `src/native-page-engine/runtime.ts`：注入诊断出口，附加在飞命令归因。
  - `native/page-engine/src/input.rs`：指针路径返回形状区分降级来源；新增降级 note（形态对齐已有的 `typing_degradation_note`）。
  - `native/page-engine/src/engine.rs`：指针降级 note 的打点（可达面＝小红书评论提交 `:1510` / 详情浮层关闭 `:2112` 等传真实死线的路径）。
  - 测试：`test/native-page-engine/client.test.ts` 增转发与切行断言；`native/page-engine` 增降级两态可分的单测。
- **不涉及**：Edge-Cloud WebSocket 协议（`PROTOCOL_VERSION` 不动）、云端、console。诊断只进本机，**不回传云端**（与 `src/client/command-diagnostics.ts:5` 已声明的边界一致）。
- **不涉及**：Native IPC 协议版本（`NATIVE_PAGE_ENGINE_PROTOCOL_VERSION = 2`）。本方案走「宿主转发子进程错误输出」，不走「协议加一条诊断记录」——后者要动就绪握手（未就绪时任何非就绪记录都会被判协议非法并终止引擎，`client.ts:657-662`），代价与风险都显著更高。
