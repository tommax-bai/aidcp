> 仅改 aidcp-edge；不碰协议 v2、不碰云端代码。缺省关闭（不传 `reconnect` 配置即零行为变化），装配处显式开启。
> 实装落 <!-- aidcp-edge 157e63e -->：typecheck ✓ / acceptance 11/11 / 全量 300/300（含 6 CdpClient 重连例 + 2 BrowseSession 续跑例）。

## 1. aidcp-edge — CdpClient 内化有界重连（client.ts）

- [x] 1.1 `wsUrl` 由 `readonly`（client.ts:80）改为可更新私有字段（重连内部直接赋值）
- [x] 1.2 新增私有态 `intentionalClose=false` / `reconnecting=false`；`close()` 置 `intentionalClose=true` 以区分主动 vs 意外 close
- [x] 1.3 改造 `'close'` 回调为有界退避重连状态机：意外 close → `failAllPending(CdpDisconnectedError)` → `runReconnect()`（成功 emit `cdp.reconnected` / 耗尽 emit `cdp.unrecoverable`）；旧/被弃用 ws 的 close 用「this.ws !== ws」代守忽略
- [x] 1.4 退避器：`base=500 / max=8000 / maxAttempts=5` + **运行时硬上限 `hardCapMs=90_000`**（到点强制 `unrecoverable`），不靠纸面相加
- [x] 1.5 重连退避循环每次 `sleep` 后、`connect` 前检查 `intentionalClose`（主动 close 抢占）；`connect()` 复用前弃用旧 ws（避免双 socket / 迟到事件）
- [x] 1.6 新增带标记错误类型 `CdpDisconnectedError`；未连接/断线时 `send` 抛该类型（供上层精确区分 WS-lost vs 业务失败）
- [x] 1.7 `CdpClientOptions.reconnect` 配置（maxAttempts/baseDelayMs/maxDelayMs/hardCapMs/rediscoverTarget/onReconnected/sleepImpl/nowImpl）+ 生命周期事件复用现有 `on()` 机制（`cdp.reconnecting/reconnected/unrecoverable`）；缺省不传即关闭

## 2. aidcp-edge — target 重发现 + 域/反检测重注入（session.ts / targets.ts / stealth-injector.ts）

- [x] 2.1 重连用 `firstPageTarget` **硬保底** `urlIncludes`（默认 `xiaohongshu.com`，用 `/json` 的 target `url` 字段），MUST NOT 落 `pages[0]`（rediscoverTarget 闭包，targets.ts 既有 urlIncludes 过滤无需改）
- [x] 2.2 抽出单一函数 `reEnableAndInject(cdp)`：`Runtime.enable`/`Page.enable`/`Input.enable` + `injectStealth`；首次 attach（session.ts）与重连 `onReconnected` 共用，避免口径漂移
- [x] 2.3 重注入幂等无叠加（旧 WS 死亡其 addScriptToEvaluateOnNewDocument 注册随之消失，新 WS 全新单次注册）—— 设计/实现已据此

## 3. aidcp-edge — BrowseSession 续跑接线（browse-session.ts）

- [x] 3.1 订阅 CdpClient `cdp.reconnected` 事件：清 `noteOpenedAt=null`，避免残留旧时刻误判 dwell 达标（`BrowseCdp` 加可选 `on?`）
- [x] 3.2 loop 薄包裹：仅捕获 `CdpDisconnectedError` → 等 `cdp.reconnected`（有界）→ 丢弃该 in-flight 命令；其他业务异常仍按现有失败语义冒泡
- [x] 3.3 续跑点：重连成功后**先过 `waitWhileBlocked()`**（浮层闸门，防把「连上」当「可用」）→ `ensureExplore`→`reportVisibleCards` 重报让云端重判
- [x] 3.4 订阅 `cdp.unrecoverable` → loop 走本地终止（`stopForReason('cdp_unrecoverable')`，复用合成 `session.end`）
- [x] 3.5 不可恢复时**停止一切上报 + 退 loop**，由云端 240s idle 看门狗兜底终止（edge→cloud 无终止消息类型，**不**主动发终止信号、不碰协议）

## 4. aidcp-edge — 装配（session.ts / main.ts）

- [x] 4.1 `attachToPage` 注入 `reconnect` 配置：`rediscoverTarget`（域名硬过滤）+ `onReconnected=reEnableAndInject`（缺省启用，传 `reconnect:false` 关闭）
- [x] 4.2 main.ts 经 `session.cdp`（真实 CdpClient 暴露 `on()`）自动接线 BrowseSession 重连事件；移除冗余的 `main.ts` `Input.enable`（已并入 reEnableAndInject）

## 5. 测试与红线（aidcp-edge）

- [x] 5.1 CdpClient 重连单测：意外 close → 重连成功 / 耗尽 `unrecoverable` 两条路径；耗尽后 `send` 继续诚实 reject
- [x] 5.2 主动 close 不触发重连 + **重连退避进行中 close() → 抢占、不再建新 ws**
- [x] 5.3 `CdpDisconnectedError` 类型区分单测（未连接 send / 断线在途命令均为该类型）
- [x] 5.4 BrowseSession 续跑单测：断线命令 → 等重连 → 续跑重报 + 不退会话；`cdp.unrecoverable` → 干净停循环
- [x] 5.5 `npm run typecheck` ✓
- [x] 5.6 `npm run test:acceptance` 11/11 + 全量 `npm test` 300/300（含 8 新例）
- [ ] 5.7（gated 真机，部分验证）浏览中遇到 DevTools WS 关闭。<!-- 2026-06-23 真机：诚实失败路径已实地验证——断连→有界重连真的跑→连不上→明确「不可恢复」干净停循环、停上报（不再静默僵尸）。happy-path 自动恢复由 8 单测覆盖、但真机干净镜头未拍到（该次断连目标页已随环境 kill 消失，落不可恢复属正确行为）。剩：一次「页面存活、仅 WS 抖断」的受控真机复测确认 happy-path 恢复。归档时此项显式留待（归档≠完全验证）。-->
