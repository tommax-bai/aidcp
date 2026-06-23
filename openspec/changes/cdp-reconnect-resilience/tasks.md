> 仅改 aidcp-edge；不碰协议 v2、不碰云端代码。缺省关闭（不传 `reconnect` 配置即零行为变化），装配处显式开启。

## 1. aidcp-edge — CdpClient 内化有界重连（client.ts）

- [ ] 1.1 `wsUrl` 由 `readonly`（client.ts:80）改为可更新私有字段；新增 `setTargetUrl(url)` 或重连内部直接赋值
- [ ] 1.2 新增私有态 `intentionalClose=false` / `reconnecting=false`；`close()`（client.ts:146）置 `intentionalClose=true` 以区分主动 vs 意外 close
- [ ] 1.3 改造 `'close'` 回调（client.ts:105-108）为有界退避重连状态机：意外 close → `failAllPending('CDP WS lost, reconnecting')` → 退避循环（成功 emit `reconnected` / 耗尽 emit `unrecoverable`）
- [ ] 1.4 退避器：`base=500 / max=8000 / maxAttempts=5` + 极薄 jitter；并加**运行时硬上限计时器**（≤90s，到点强制 `unrecoverable`），不靠纸面相加（D2）
- [ ] 1.5 重连退避循环每次 `sleep` 后、`connect` 前检查 `intentionalClose`，命中即终止重连不再建新 WS（D7）；`connect()` 复用前安全弃用旧 ws，避免双 socket
- [ ] 1.6 新增带标记错误类型 `CdpDisconnectedError`；重连态/未连接时 `send`（client.ts:115-117）抛该类型而非泛化 Error（D6，供上层精确区分 WS-lost vs 业务失败）
- [ ] 1.7 `CdpClientOptions.reconnect` 配置（maxAttempts/baseDelayMs/maxDelayMs/hardCapMs/discover.urlIncludes/onReconnected）+ 轻量事件（`reconnecting`/`reconnected`/`unrecoverable`，复用 client.ts:135 `on()` 机制或极薄 emitter）；缺省不传即关闭

## 2. aidcp-edge — target 重发现 + 域/反检测重注入（targets.ts / session.ts / stealth-injector.ts）

- [ ] 2.1 重连用 `firstPageTarget`（targets.ts:41-53）**硬保底** `urlIncludes`（默认 `xiaohongshu.com`，用 `/json` 的 target `url` 字段 targets.ts:13），MUST NOT 落 `pages[0]`
- [ ] 2.2 抽出单一函数 `reEnableAndInject(cdp)`：`Runtime.enable`/`Page.enable`/`Input.enable`（main.ts:98 重连后须补）+ `injectStealth`（stealth-injector.ts:269）；首次 attach（session.ts:48-56）与重连 `onReconnected` 共用，避免口径漂移
- [ ] 2.3 确认重注入幂等无叠加（旧 WS 死亡其 addScriptToEvaluateOnNewDocument 注册随之消失，新 WS 全新单次注册）

## 3. aidcp-edge — BrowseSession 续跑接线（browse-session.ts）

- [ ] 3.1 订阅 CdpClient `reconnected` 事件：清 `noteOpenedAt=null`（browse-session.ts:185,698），避免残留旧时刻误判 dwell 达标
- [ ] 3.2 `executeCommand` 外层薄包裹：仅捕获 `CdpDisconnectedError`（browse-session.ts:406-411）→ 等 `reconnected`（有界）→ 丢弃该 in-flight 命令；其他业务异常仍按现有失败语义走（D6）
- [ ] 3.3 续跑点：重连成功后先判当前真实 URL → **先过 `waitWhileBlocked()`**（browse-session.ts:401，浮层闸门，B2）→ 按当前页 `ensureExplore`→`reportVisibleCards`（:331-349,:618-653）或重报 `note.detail`，让云端重判
- [ ] 3.4 订阅 `unrecoverable` 事件 → loop 走本地终止（复用 browse-session.ts:293 合成 `session.end`，`reason='cdp_unrecoverable'`）；`finally` 照常 `running=false` + 日志（:280-283）
- [ ] 3.5 不可恢复时**停止一切上报 + 退 loop**，由云端 240s idle 看门狗兜底终止（D4：edge→cloud 无终止消息类型，**不**主动发终止信号、不碰协议）

## 4. aidcp-edge — 装配（main.ts / session.ts）

- [ ] 4.1 `attachToPage`（session.ts:44）注入 `reconnect` 配置：`discover.urlIncludes='xiaohongshu.com'` + `onReconnected=reEnableAndInject`
- [ ] 4.2 main.ts 装配段把 BrowseSession 接到 CdpClient 重连事件（reconnected/unrecoverable）

## 5. 测试与红线（aidcp-edge）

- [ ] 5.1 CdpClient 重连单测：注入 `wsFactory` 模拟意外 close → 重连成功 / 耗尽两条路径；断言重连成功后续跑、耗尽后 `unrecoverable` 且 `send` 继续诚实 reject
- [ ] 5.2 主动 close 不触发重连的单测；**重连退避进行中调 `close()` → 不再产生新 WS**（D7）
- [ ] 5.3 `CdpDisconnectedError` 区分单测：薄包裹只对该类型走等重连，其他异常不被吞进重连等待（D6）
- [ ] 5.4 BrowseSession 续跑单测：重连后清 `noteOpenedAt`、先过 `waitWhileBlocked()`、重报 `page.cards`、不重放旧命令
- [ ] 5.5 `npm run typecheck`（本变更不动协议，但必跑守穷举不漂移）
- [ ] 5.6 `npm run test:acceptance`（AC-PROTO-*/AC-PUB-*/AC-RISK-* 全过）+ 全量 `npm test`
- [ ] 5.7（gated 真机）浏览中模拟 DevTools WS 关闭：观察有界重连续跑 / 耗尽诚实终止 / 不被云端看门狗误杀 / 重连落浮层先过闸门
