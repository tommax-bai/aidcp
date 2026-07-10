# Tasks — adspower 首次登录等待门 + 诚实停手真退出

> 全部落 `aidcp-edge`（edge-only，无 cloud/console 改动、无 ECS 部署）。实装后按 `<repo> <sha> 备注` 回写。
> **实装完成**：edge master `a758fc7`（typecheck + acceptance + 952 tests 全绿）。真机验收 → backlog 簇 45。

## 1. aidcp-edge — 启动期「等登录」门（account-identity-resolution）

- [x] 1.1 `src/cdp/self-identity.ts`：加「有界等待登录」helper——保持传入 CDP 附着，每 `intervalMs`（~5s）做**一次**就地重读（复用 `readSelfIdentity({ allowNavigate: false })`），读出形态合规稳定 id 即返回成功、否则轮询到超时返回失败。判定纯函数化 + **按迭代次数上界**循环（不依赖 `now()` 前进，与既有 hydrate 循环同款，防测试恒定时钟死循环）。**内层就地重读须用极小 hydrate 预算**（单次 `IN_PLACE_SCAN` / `hydrateTimeoutMs≈0`）。 <!-- aidcp-edge a758fc7 waitForLoginIdentity：读按 intervalMs 稀疏、中断按 interruptPollMs 亚秒级密；catch 兜异常 -->
- [x] 1.2 env 读取超时上限与开关（如 `AIDCP_ADSPOWER_LOGIN_WAIT_MS`，默认 ~5min；设 0/关闭值即回到「不等待、即刻停手」——但该即刻停手仍 MUST 走 3.1 真退出端点，见 3.3）。 <!-- aidcp-edge a758fc7 AIDCP_ADSPOWER_LOGIN_WAIT_MS 默认 300000；0/非法/负=关等待门 -->
- [x] 1.3 `src/main.ts` 身份块：门控用**可判定条件**——`provider===adspower` + 启动期首次身份读取 + `decision.kind==='halt'`——命中即进入 1.1 helper；读出真 id → 继续既有握手路径。MUST NOT 引入「读不出是否属登录尚未建立」的首读分类器（无结构化判据）；确凿登出由超时兜底。`self` / `override` 路径逐字不动。 <!-- aidcp-edge a758fc7 resolveStartupIdentity 纯编排；门控 adspower+halt+loginWaitMs>0 -->
- [x] 1.4 等待期**不 `session.close`**、保持浏览器与 CDP 附着；输出可被外壳识别的「请扫码登录 / 等待登录中」状态行。 <!-- aidcp-edge a758fc7 等待路径不 session.close；发 [browser-parking] awaiting-login + 中文提示行 -->
- [x] 1.5 adspower 首读改 `allowNavigate=false`（登录页无「我」锚点，去掉 ~13s 无效 navigate 合成点击与半渲染登录页误导航风险）；`self` 首读维持原行为。**真机须验**：历史仅靠 navigate 兜底才读出 id 的已登录老号布局，改后就地仍能读出（见 5.2）。 <!-- aidcp-edge a758fc7 firstReadOpts.allowNavigate=false 仅 adspower；真机核老号→簇45 -->

## 2. aidcp-edge — 等待可即时中断（account-identity-resolution）

- [x] 2.1 等待循环中**主动排空 / 拦截 IPC 生命周期命令队列**（`pendingLifecycleCommands`）：收到暂停 / 关闭 → 即时中断循环、以**干净停止**语义收口退出（走 3.1 端点，不触发自动重起）。**不**临时接管 SIGINT/SIGTERM（早窗内信号走进程默认处置即立即终止、本就即时）。等待结束（成功/超时/中断）后交回正常派发，等待期排队命令**恰好派发一次**。 <!-- aidcp-edge a758fc7 pollInterrupt 非破坏性 find(pause/close)；成功续跑后既有 dispatchLifecycleCommand splice 一次性派发；未接管信号 -->

## 3. aidcp-edge — 诚实停手真终止、绝不留僵尸（edge-node-supervised-recycle）

- [x] 3.1 抽一个「收口真退出」端点：`main.ts:194-206` 的 `exitCode=1` + bare return → `terminateNow`（session.close + process.exit）。退出码按语义分叉：**登录超时 / 早窗中断 = 干净停止码 0（不触发自动重起）**；常规 halt 维持可重起码 1。 <!-- aidcp-edge a758fc7 terminateNow=session.close+process.exit(code)；process.exit 硬终止无视 IPC/stdin 常驻句柄=真退出保证；超时/中断 code=0、常规 halt code=1 -->
- [x] 3.2 审计同源停手 / 退出端点，**仅订正范围、勿盲目纳入**：`main.ts:194-206` 是坐实的「置 exitCode 却不退」僵尸，本 change 修它。`main.ts:605-609`（身份重检停手）是**刻意 stay-alive**（`return` 不置 exitCode、有意不关浏览器、留无身份态不重连），转真退出可能触发身份误翻转重起回归——**保留原样**。`main.ts:313` 实为死路径，不动。 <!-- aidcp-edge a758fc7 已审计：605-609 确认 return 不置 exitCode（刻意 stay-alive）保留；313 死路径不动 -->
- [x] 3.3 回归测试：② 等待超时路径走真退出、退出码为**干净停止**（不自动重起）；③ `AIDCP_ADSPOWER_LOGIN_WAIT_MS=0`（关等待）时即刻停手**仍走真退出端点**（关等待不复活僵尸）；④ IPC close/pause 注入等待循环 → 即时中断且真终止；⑤ 等待中登录成功 → proceed 续跑；① 「进程确实终止」由 terminate action 断言 + 反僵尸不变量覆盖逻辑层。 <!-- aidcp-edge a758fc7 test/cdp/login-wait-gate.test.ts 14 条；①「进程确实终止」由「任何 halt 必 terminate 非 proceed」不变量+process.exit 结构保证覆盖逻辑层，真机复核不留僵尸见簇45 -->
- [x] 3.4 回归测试：等待门**严格限** `adspower + 启动期首读 + halt`——`self`、`override`、**已登录读出成功**三路径均**不**进入等待（防误触）。 <!-- aidcp-edge a758fc7 login-wait-gate.test.ts：self+halt/override/use 三路径 waited==0 -->
- [x] 3.5 回归测试（守迭代上界陷阱）：注入**恒定假时钟 + 桩 sleep**，断言返回有界超时失败（无 `RangeError`/死循环/hang）。 <!-- aidcp-edge a758fc7 login-wait-gate.test.ts：now()恒定+immediateSleep→timeout 有界 -->

## 4. aidcp-edge —（可选）外壳等待态文案

- [x] 4.1 `src/electron/main.cjs`：识别「等待登录」状态行 → UI 显示「请在浏览器里扫码登录」；**不加**任何 respawn 抑制。 <!-- aidcp-edge a758fc7 识别 [browser-parking] awaiting-login → auth:'login required'+presence，无 respawn 抑制 -->

## 5. 验证与交付

- [x] 5.1 `cd ../aidcp-edge && npm run test:acceptance && npm test && npm run typecheck` 全绿。 <!-- aidcp-edge a758fc7 acceptance 16/16(AC-PROTO/AC-PUB 红线绿) + test 952/952 + typecheck 0 err -->
- [ ] 5.2 真机验收 → 已登记 `docs/real-machine-acceptance-backlog.md` **簇 45**（新建环境首登不卡死 / 慢速扫码可续 / 始终不登录诚实干净停止不无限重起 / 等待期暂停关闭即时响应 / 已登录老号零回归 / 登录落点 tab 一致性）。edge 需运营机 pull master `a758fc7` 后生效。
- [~] 5.3 edge-only：已 land `aidcp-edge` master `a758fc7`（主 checkout 已 ff 同步）；**不部署 cloud**（无协议 / 云端改动）。**待做**：重建安装包分发运营机。
