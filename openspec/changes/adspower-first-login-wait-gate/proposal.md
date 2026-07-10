## Why

运营反馈：桌面客户端**新建环境、扫码登录后会卡住，有时要重启整个 edge 客户端才生效**。多 agent 对抗验证 workflow + 逐行代码核实定位到根因（两个缺陷叠加，均在 `aidcp-edge`）：

1. **adspower 启动路径缺一道「等登录」门。** `self` 模式壳侧有 cookie 轮询登录门（登录前不起核心、每 5s 查一次、**登录后才起、无限等待不放弃**，`main.cjs:1268-1319`）；`adspower` 的 `startAdsPowerFlow`（`main.cjs:1398-1427`）备好运行时后**直接起核心，无任何等价物**（`pluggable-browser-provider` spec 亦明确「adspower 不做本机端口 cookie 轮询、登录门是 self 专属」）。新建环境=**全新未登录**的分身，核心 attach 浏览器后**只读一次**身份（`main.ts:192`），未登录必判 `halt`。给操作者扫码的宽限仅这一次读取内部的 ~6s hydrate 轮询 + ~13s navigate 兜底 ≈ **6–19s，且没有第二次尝试**。

2. **这与既有 spec 直接冲突。** `account-identity-resolution` 已要求「无身份态…**应继续等待登录**；登录并读出身份后才握手」——实装却选了「即刻停手」，违背 spec 本意。

3. **更糟：诚实停手没真退出，挂成僵尸。** `halt` 分支（`main.ts:194-206`）用 `process.exitCode=1` + **bare return**，不调 `process.exit`（真退出路径在 `main.ts:860/906`）。核心是带 **IPC 通道**（`spawn` stdio 第 4 路 `ipc`，`main.cjs:1116` + `process.on('message')` `main.ts:103`）与 **stdin 控制读取器**（`AIDCP_BROWSER_CONTROL_STDIN=1`，`main.ts:185`）的子进程，两个常驻句柄把事件循环钉住 → **进程不退、挂成存活僵尸**（`session.close()` 已把 CDP 关掉，故「显示浏览器」报 `CDP未连接`）。于是 `child.on('exit')` **永不触发** → `edge-node-supervised-recycle` 规定的有界重起根本不 engage；外壳手动「启动」因僵尸 `handle.child` 仍在而 `early-return` 空操作（`main.cjs:1578`）；操作者唯一恢复手段退化为「重新登录」（SIGTERM 强杀）或重启整个外壳——正对上症状原话。

**「有时候」不是重启预算决定的**（该预算永不 engage），而是**扫码快慢 vs 单次 ~6–19s 识别窗口**：预先扫过/极快登录 → 窗口内命中 → 成功；正常/慢速扫码（找手机、开 App、扫、确认、跳转，常 15–45s）→ 错过窗口 → 僵尸 → **永久卡死**，只能重启。

本 change 是**让实装回到既有 spec 本意 + 补一处诚实性红线**，不重写身份/启动栈。

## What Changes

- **给无壳侧登录门的 provider（当前即 `adspower`）在核心内补一道有界「等登录」门**：门控用**可判定条件**（`provider=adspower` + 启动期首读 + `halt`，**不**试图在首读时区分「登录尚未建立」vs「已登录但读不出」——无此判据、由超时兜底），命中即**不即刻停手**——保持浏览器与 CDP 附着（操作者看得见、扫得了码），周期性**就地重读**（`allowNavigate=false`，不骚扰二维码页），**有界等待**至读出真 id（无缝续握手）或达到宽松的人类登录超时（env 可调/可缩短/可关闭）后**诚实干净停止**（退出码不触发自动重起，避免永不登录节点无限重起环）。`self` 壳侧门无限等待、`adspower` 核心内门有界，差异刻意保留。
- **等待窗可即时中断（收窄到 IPC 生命周期命令路径）**：等待落在生命周期信号尚未接线的启动早窗，唯一会被搁置的是经 IPC 堆进待派发队列的暂停/关闭（信号走进程默认处置本就即时、无需接管）；等待期收到暂停/关闭 MUST 即时收口、干净停止，MUST NOT 被搁置到握手之后。
- **修「诚实停手不真退出」的僵尸**：任何诚实停手/终态退出路径 MUST **真正终止进程**——释放会钉住事件循环的常驻句柄（IPC 通道、stdin 控制读取器）后再退（必要时显式 `process.exit`/断开 IPC），绝不仅置退出码后 `return`；补回归断言。这样看护层的有界重起语义与外壳「启动」都恢复正常。
- **红线全保留**：只在读出真实稳定 id 时握手，超时诚实停手、**零回落 `default`**；`AIDCP_ACCOUNT_ID` 覆盖逃生阀不受门影响；等待期 `allowNavigate=false`。

## Capabilities

### Modified Capabilities

- **`account-identity-resolution`**：新增两条 requirement——① 启动期首次登录 MUST 有界等待（无壳侧登录门的 provider 在核心内提供等价门）；② 启动期「等待登录」MUST 可即时中断。落实既有「应继续等待登录」的未竟实装。
- **`edge-node-supervised-recycle`**：新增一条 requirement——诚实下线/停手 MUST 真正终止进程（释放 IPC/stdin 常驻句柄），绝不留存活僵尸钉死事件循环、致有界重起不触发与外壳「启动」空操作。
- **`pluggable-browser-provider`**（MODIFIED）：把「provider 失败诚实停手」里「profile 未登录致身份读不出」这一即时停手触发项，收窄为「经核心内有界登录等待门后仍未登录/读不出」——使归档后 spec 集不自相矛盾（否则同一 adspower-启动-未登录条件会有「即时停手」与「等待后停手」两条对立条款）。红线「绝不回落 self/绝不猜」不变。

（前两条以 **ADDED Requirements**、第三条以 **MODIFIED Requirements** 落进既有 capability，保持 validate/archive-clean。）

## Impact

- **Affected repos：仅 `aidcp-edge`。** cloud **零改**（不新增/改任何边-云协议消息、不动 `command-bridge` / `RoleName` / `risk-state-machine`）；console 零改。
- **主要文件**：`src/main.ts`（身份块 188-220 + 收口端点）、`src/cdp/self-identity.ts`（薄封装等待/就地重读，复用 `readSelfIdentity` `allowNavigate=false`）、可选 `src/electron/main.cjs`（等待态状态文案映射，**不加** respawn 抑制）。**均非序列化热点文件**（`protocol.ts` / `command-bridge` / `RoleName` / `risk-state-machine` 全不碰）。
- **与 `pluggable-browser-provider` 协调**：其「profile 未登录时诚实失败而非默认起跑」红线（未登录绝不以本机指纹/IP 起跑、绝不回落 `self`）**不变**；本 change 经一条 **MODIFIED delta** 把该「未登录触发即时停手」收窄为「经核心内有界登录等待门后仍未登录才停手」，使两 spec 对同一条件的处置在归档后一致（非靠 proposal 口头协调）。
- **并行协调**：活跃 change `self-contained-ads-runtime` 也动 adspower 运行时与 `main.ts` 启动早段（`ensureAdsRuntime`）；若并行开发须对 `main.ts` 启动段视为单写、rebase 后集成。
- **行为影响**：新建环境首登不再卡死；对**已登录老号零回归**（读出即走、等待门不触发）；看护/headless/无人值守场景须以 env 给短超时或关闭，避免核心空等占用。

## Open Risks / Follow-ups

- **同源停手端点（仅订正、不盲目纳入）**：唯一坐实的「置 exitCode 却不退」僵尸是 `main.ts:194-206`，本 change 修它。`main.ts:605-609`（身份重检停手）是**刻意的 stay-alive 降级**（不置 exitCode、有意不关浏览器、留在无身份态不重连）——转真退出可能触发身份误翻转重起回归（identity-watcher-brick 教训），**默认保持原样**；`main.ts:313` 实为死路径。实装只审计订正、不强改（tasks 3.2）。
- **登录落点 tab 一致性（头号真机风险，已升为验收项 5.2⑥）**：整个修复靠对**已附着**的那个 CDP tab 就地重读；若扫码登录落到非附着 tab，就地读永远读不到、白等到超时且 UI 仍显示「在等」＝静默假成功。真机须验「同 tab 重定向」与「登录落新 tab」两种。
- **navigate 兜底移除的老号回归（已升为验收项 5.2⑤）**：adspower 首读改 `allowNavigate=false` 去掉 ~13s 无效合成点击与误导航风险，但历史仅靠 navigate 兜底才读出 id 的已登录老号布局须真机验证就地仍能读出，否则空等到超时=回归。
