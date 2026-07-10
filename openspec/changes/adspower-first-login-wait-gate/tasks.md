# Tasks — adspower 首次登录等待门 + 诚实停手真退出

> 全部落 `aidcp-edge`（edge-only，无 cloud/console 改动、无 ECS 部署）。实装后按 `<repo> <sha> 备注` 回写。

## 1. aidcp-edge — 启动期「等登录」门（account-identity-resolution）

- [ ] 1.1 `src/cdp/self-identity.ts`：加「有界等待登录」helper——保持传入 CDP 附着，每 `intervalMs`（~5s）做**一次**就地重读（复用 `readSelfIdentity({ allowNavigate: false })`），读出形态合规稳定 id 即返回成功、否则轮询到超时返回失败。判定纯函数化 + **按迭代次数上界**循环（不依赖 `now()` 前进，与既有 hydrate 循环同款，防测试恒定时钟死循环）。**内层就地重读须用极小 hydrate 预算**（单次 `IN_PLACE_SCAN` / `hydrateTimeoutMs≈0`），MUST NOT 把 `readSelfIdentity` 默认 ~6s hydrate 轮询嵌进 ~5s 外层循环（否则中断响应延迟退化到 ~6s、每 tick 多花无谓等待）。中断检查落在每 tick 之间。
- [ ] 1.2 env 读取超时上限与开关（如 `AIDCP_ADSPOWER_LOGIN_WAIT_MS`，默认 ~5min；设 0/关闭值即回到「不等待、即刻停手」——但该即刻停手仍 MUST 走 3.1 真退出端点，见 3.3）。
- [ ] 1.3 `src/main.ts` 身份块：门控用**可判定条件**——`provider===adspower`（无壳侧登录门）+ 启动期首次身份读取 + `decision.kind==='halt'`——命中即进入 1.1 helper；读出真 id → 用该 id 继续既有握手路径。MUST NOT 引入「读不出是否属登录尚未建立」的首读分类器（无结构化判据）；确凿登出由超时兜底。`self` / `override` 路径逐字不动。
- [ ] 1.4 等待期**不 `session.close`**、保持浏览器与 CDP 附着；输出可被外壳识别的「请扫码登录 / 等待登录中」状态行（便于 UI 与运维）。
- [ ] 1.5 adspower 首读改 `allowNavigate=false`（登录页无「我」锚点，去掉 ~13s 无效 navigate 合成点击与半渲染登录页误导航风险）；`self` 首读维持原行为。**真机须验**：历史仅靠 navigate 兜底才读出 id 的已登录老号布局，改 `allowNavigate=false` 后就地仍能读出（否则老号会空等到超时=回归，见 5.2）。

## 2. aidcp-edge — 等待可即时中断（account-identity-resolution）

- [ ] 2.1 等待循环中**主动排空 / 拦截 IPC 生命周期命令队列**（`pendingLifecycleCommands`，`main.ts:101-107`）：收到暂停 / 关闭 → 即时中断循环、以**干净停止**语义收口退出（走 3.1 端点，不触发自动重起；早窗无账号会话可暂停、adspower 浏览器外部托管不受进程退出影响）。**不**临时接管 SIGINT/SIGTERM（早窗内信号走进程默认处置即立即终止、本就即时，多余接管是易错的装卸）。等待结束（成功/超时/中断）后交回正常派发，等待期排队命令**恰好派发一次**。

## 3. aidcp-edge — 诚实停手真终止、绝不留僵尸（edge-node-supervised-recycle）

- [ ] 3.1 抽一个「收口真退出」端点：置退出码 → 关闭 stdin 控制读取器 + 断开 / 移除 IPC（`process.disconnect` / 卸 `message` 监听）→ 必要时 `process.exit`；替换 `main.ts:194-206` 的 `exitCode=1` + bare return。退出码按语义分叉：**登录超时 / 早窗中断 = 干净停止码（不触发自动重起）**；其它既有可重起终态维持可重起码。
- [ ] 3.2 审计同源停手 / 退出端点，**仅订正范围、勿盲目纳入**：`main.ts:194-206` 是已坐实的「置 exitCode 却不退」僵尸，本 change 修它。`main.ts:605-609`（身份重检停手）是**刻意的 stay-alive 降级**（不置 exitCode、有意不关浏览器、留在无身份态不重连），转成真退出 + recycle 可能触发身份误翻转重起回归（见 identity-watcher-brick 教训）——**默认保持原样、不并入 3.1**，仅在 proposal/design 订正其「非 exitCode 僵尸」的描述。`main.ts:313`（recycle `EXIT_RECYCLE`）实为死路径（`requestShutdown` 在其可触发前已赋值），低风险不动。
- [ ] 3.3 回归测试：① 断言带 IPC + stdin 常驻句柄的核心在停手 / 终态路径上**进程确实终止**（非存活僵尸）；② 断言等待超时路径走真退出、退出码为**干净停止**（不触发自动重起）；③ 断言 `AIDCP_ADSPOWER_LOGIN_WAIT_MS=0`（关等待）时的即刻停手**仍走 3.1 真退出端点**（关等待 MUST NOT 复活 bare-return 僵尸）；④ 注入 IPC close/pause 到等待循环 → 断言循环即时中断且进程真终止（退出码语义正确）；⑤ 模拟等待中登录成功 → 断言等待期拦截被交回、后续正式 lifecycle **单派发**、不悬挂。
- [ ] 3.4 回归测试：断言等待门**严格限** `adspower + 启动期首读 + halt`——`self`、`override`、**已登录读出成功**三条路径均**不**进入等待、行为逐字不变（防误触）。
- [ ] 3.5 回归测试（守迭代上界陷阱）：给等待 helper 注入**恒定假时钟 + 桩 sleep**，断言其返回有界的超时失败（无 `RangeError`、无死循环、无 hang）——锁死 memory `edge-poll-helpers-iteration-bounded` 的已知坑。

## 4. aidcp-edge —（可选）外壳等待态文案

- [ ] 4.1 `src/electron/main.cjs`：识别「等待登录」状态行 → UI 显示「请在浏览器里扫码登录」；**不加**任何 respawn 抑制（核心不退出则 respawn 本就不触发；超时走干净停止码亦不重起）。

## 5. 验证与交付

- [ ] 5.1 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全绿。
- [ ] 5.2 真机验收（登记 `docs/real-machine-acceptance-backlog.md` 新簇）：
  - ① 新建环境首登不卡死；
  - ② 慢速扫码（>20s）可续上握手；
  - ③ 始终不登录 → 到超时**诚实干净停止**（非僵尸）+ 看护 / 外壳「启动」可用、**不无限重起**；
  - ④ 等待期点「暂停 / 关闭」即时响应（干净停止、不被重起后再进等待）；
  - ⑤ **已登录老号零回归**：`allowNavigate=false` 就地即能读出 id（历史仅靠 navigate 兜底的布局须重点验，否则空等到超时=回归）；
  - ⑥ **登录落点 tab 一致性**（头号风险）：扫码登录完成后，对 `attachToPage` 选中的那个 CDP tab 的就地重读**确实能在数个 tick 内读出稳定 id**——覆盖「同 tab 内重定向」与「登录落到新 tab」两种；若登录落到非附着 tab，就地重读永远读不到、白等到超时且 UI 仍显示「在等」＝静默假成功，须据实处置（换附着目标 / 诚实提示）。
- [ ] 5.3 edge-only：land 到 `aidcp-edge` master + 重建安装包；**不部署 cloud**（无协议 / 云端改动）。
