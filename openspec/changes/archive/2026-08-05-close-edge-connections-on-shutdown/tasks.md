# Tasks

## 0. 事实源纪律（先读，别跳）

- `src/comm/ws-server.ts` 的**事实源在 `aidcp-cloud`**。`aidcp-automation` 的同名文件是
  `scripts/sync-split-repos` 的派生物：只改 automation 那一份，下一次同步会把它原样覆盖回去，
  而且不报错、不留痕。改动 MUST 先落 cloud，再 `scripts/sync-split-repos --apply --repo aidcp-automation`。
- `src/server.ts` 与 `src/automation-service-entry.ts` 是**派生仓私有的组装根**，
  `sync-split-repos` 对它们「只报不改」。入口那几条修复直接在 `aidcp-automation` 改，
  MUST NOT 指望同步带过去。
- 单体 `aidcp-cloud` **不因本 change 被部署**（CLAUDE.md §8.0）。它在这里只是事实源与整图验证仓。

## 1. aidcp-cloud — 关闭时主动断开在线边缘连接（事实源）

- [x] 1.1 `src/comm/ws-server.ts` 的 `close()`：在等服务端回调之外，遍历当前在线连接逐条发起关闭，
      带「服务端下线」语义的关闭码（1001）与原因串。
      <!-- aidcp-cloud 1edfb90 遍历 wss.clients 而非 this.edges——后者只收录完成 hello 之后的连接，
           一条 pre-hello 的 socket 同样会把 close() 拖住却不在那张表里 -->
- [x] 1.2 有界兜底：起一个定时器，到点仍未关掉的连接直接掐断（terminate）。兜底时限取值写进注释，
      说明为什么是这个量级（下界＝一个正常关闭来回，上界＝必须显著小于进程管理器的停止超时）。
      **这张表故意不 `unref()`**：它只活到兜底时限、且 close 回调一到就被清掉；unref 掉的话，
      当它是事件循环最后一个句柄时进程会直接退出——兜底没跑、close 没 resolve、
      「关停完成」与显式退出码都不出现，等于把这次要修的可观测性又还回去。
      <!-- aidcp-cloud 1edfb90 EDGE_CLOSE_GRACE_MS=5s；新增 closeGraceMs 选项仅供测试缩短 -->
- [x] 1.3 `close()` MUST 保持幂等。补断连之后**再核一遍**幂等性——第二次调用不得对已经关掉的连接
      再操作、不得重复起兜底定时器。
      <!-- aidcp-cloud 1edfb90 进入时先摘 this.wss 引用，重复调用走 Promise.resolve() 早退 -->
- [x] 1.4 回归用例：起一个真实服务端 + 一个真实客户端连上，调 `close()`，断言
      **在客户端没有任何主动动作的前提下** close 在有界时间内 resolve。
      <!-- aidcp-cloud 1edfb90 test/ws-server-shutdown.test.ts；另补一条 pre-hello 连接的同形用例 -->
- [x] 1.5 回归用例：客户端不回关闭握手（把底层 socket pause 掉），断言兜底把它掐断且 close 仍然 resolve。
      <!-- aidcp-cloud 1edfb90 同文件；断言 elapsed >= graceMs，确认走的确实是兜底路径而非提前返回 -->
- [x] 1.6 变异归因：两半修复各自有专属用例抓住。
      <!-- 摘掉主动断连 ⇒ 4 条里红 3 条（装死那条仍绿，它验的是兜底）；
           摘掉兜底 ⇒ 只有装死那条红。两半都不是恒真的闸 -->
- [x] 1.7 `npm run test:acceptance`（189 pass）→ `npm test`（4222 pass / 0 fail）→ `npm run typecheck` 全绿。
      <!-- aidcp-cloud 1edfb90 -->

## 2. aidcp-automation — 同步派生物 + 修入口

- [x] 2.1 `scripts/sync-split-repos --repo aidcp-automation` 对账，差异**只有** `src/comm/ws-server.ts` 一条。
- [x] 2.2 `scripts/sync-split-repos --apply --repo aidcp-automation` 落盘（写入 1 个文件）。
- [x] 2.3 `src/server.ts`：把 `installShutdown` 整个删掉——包括那个重复且从不摘除的信号处理器。
      启动外壳已经挂了自己的处理器并会在首个信号时摘除自己；入口再挂一个常驻的，
      等于把「第二个信号立刻结束」这条逃生口堵死。
      <!-- aidcp-automation a1252a6 那三个 JSON 事件（shutdown_begin/complete/signal_repeat）
           全仓无消费方，故直接由外壳的「收到终止信号…」/「已关停」两行取代 -->
- [x] 2.4 关停干净后显式 `exit(0)`、失败 `exit(1)`。退出注入在**启动外壳**（automation 的信号属主是外壳，
      不同于 api / content 由入口持有），形态与 `aidcp-api/src/api-service-entry.ts` 那一段一致。
      <!-- aidcp-automation a1252a6 AutomationServiceOptions.exit，缺省 process.exit -->
- [x] 2.5 回归用例：关停干净退 0 / 关停失败退 1 / 处理器摘掉自己（原有那条保留）。
      <!-- aidcp-automation a1252a6 test/acceptance/automation-service-entry.test.ts -->
- [x] 2.6 **源码闸**：断言 `src/server.ts` 不再提及 SIGTERM / SIGINT。
      <!-- aidcp-automation a1252a6 这条只能是源码闸：行为用例驱动的是注入的假信号源，
           原理上看不见挂在真 process 上的那一个——而那正是本 bug 藏身之处。
           已变异验证：往 server.ts 加回一行 process.on('SIGTERM') 即当场红 -->
- [x] 2.7 **顺带修**：关停各步改成「一步失败也把后面几步跑完，第一个错误仍然往外抛」。
      原先是一串裸 await，`stop()` / `dispose()` 一抛，后面的归还整段被跳过：
      根从来没关过、内部监听还在，而回执只说「关停失败」、看不出还漏了哪几样没还。
      <!-- aidcp-automation a1252a6 这条是被 2.5 的失败用例逼出来的——那条用例最初直接挂死，
           因为 dispose 抛错之后 root.close() 永远不会跑，内部 HTTP 服务端一直监听着 -->
- [x] 2.8 `npm run test:acceptance`（293 pass）→ `npm test`（2273 pass / 0 fail）→ `npm run typecheck` 全绿。
      <!-- aidcp-automation a1252a6 -->

## 3. 部署与验收（dev）

- [x] 3.1 `scripts/deploy-target dev --check` → 备份（`automation.bak.20260805-165229.tar.gz` + `.env.bak`）
      → git archive 快照 rsync（不从工作区推）→ ECS 上 typecheck CLEAN → restart。
      <!-- 2026-08-05 deployed -->
- [x] 3.2 **验收就是重启本身**：`Stopping…` 与 `Stopped` 落在同一秒，出现 `[aidcp-automation] 已关停`，
      没有 `State 'stop-sigterm' timed out`、没有 SIGKILL。
      <!-- 2026-08-05 16:54:04 实测 RESTART_WALL_MS=83（此前每次 90 000ms 且被强杀） -->
- [x] 3.3 验收时机器上**真有连接挂在 8787**——本 bug 的触发条件就是「有连接在线」，
      空载重启在修复前也是秒停的，那样的验收什么都不证明。
      <!-- 2026-08-05 部署后 dev 上恰好 0 条边缘在线，故从本机主动挂一条 WS 连接到 8787 再重启；
           ss 确认 established=1。该连接收到 code=1001 于 08:54:04.004Z 正常关闭 -->
- [x] 3.4 对端侧核对：断连码是 1001 going away，客户端据此走正常重连路径，不记成异常掉线。
      <!-- 2026-08-05 held client 实测 CLOSED code=1001 -->
- [x] 3.5 部署后健康：三服务 active、NRestarts=0、8787 与 8094 监听在。

## 4. 收口

- [x] 4.1 `openspec validate close-edge-connections-on-shutdown --strict` 通过。
- [ ] 4.2 archive。

## 5. 本 change 明确不做的

- **不改 systemd 的 `TimeoutStopSec`**。把 90 秒调短只会让强杀来得更早，根因原样留着；
  调长则让每次部署更难受。超时上限是**兜底**，不是关停时长的调节旋钮。
- **不动 `aidcp-cloud` 的部署状态**。§8.0 明写它 MUST NOT 被部署到任何环境。
- **不顺手改内部 HTTP 服务端的关闭**。它在本次链条里排在边缘连接入口之后、从未被走到，
  且 api / content 用同一份实现、两个都秒停——**当前没有证据说它有问题**，
  在没有证据的地方加闸属于 CLAUDE.md §2 的「加闸准入」禁止项。若将来实测它也挂住，另行开单。
- **不修「启动失败只设 exitCode、不 exit」**（`aidcp-automation/src/server.ts` 的 catch 分支）。
  它是本次这个缺陷的**启动侧孪生**：装配已经建了池、起了定时器，事件循环上还挂着引用，
  于是进程留在那里不动、systemd 看到 `active (running)`，既不服务也不重启。
  api 侧那份注释明写他们已经踩过并修掉（`api-service-entry.ts` 头部「失败时**真的退出**」一段）。
  **automation 这一侧至今没有实测发生过**，且它与「关停」是两条独立路径，
  改它要单独想清楚「半装配状态下该按什么顺序拆」——不塞进本 change 顺手改。
  **它不进真机 backlog**（那份文档收的是「需要真人在真机上验」的项，这一条是待修代码缺陷，
  不是待验行为）。归档后它只活在本文件里，所以在这里写全：
  文件 `aidcp-automation/src/server.ts` 的 catch 分支，把 `process.exitCode = 1` 改成真退出即可，
  对照实现见 `aidcp-api/src/api-service-entry.ts`。要开单时直接引本段。
