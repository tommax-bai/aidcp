# requeue-proxy-authority-fetch-failure

## Why

`bound-proxy-preflight-retry`（2026-08-07 归档）给代理预检的可恢复失败建了有界重排通道，但 2026-08-09 dev 断网实测暴露一个盲区：**整网断掉时，启动准备根本走不到「探测代理」那一步**——它先死在更前面的「向云端读环境代理权威记录」（一次 HTTP 请求），而这次失败被折进 `proxy_authority_unavailable`（「云端答复了但给不出记录」的名字），该名字在不可恢复清单里 ⇒ 当场终结成异常，重排通道零参与。

这是两条既有铁律的复合违背：

- **「跨进程 / 兄弟服务暂时读不到，恒非结构性失败」**（`docs/stop-or-continue.md`）——请求没送达云端正是这一类，却被判成了配置错误终局。
- **「跨层翻译 MUST NOT 有兜底桶」**——HTTP 传输失败（status 0）与「云端答复了但给不出记录」两个不同结论共用一个原因值（`main.cjs` 里 `|| 'proxy_authority_unavailable'` 的兜底写法），下游按后者的语义判死了前者。

另有一处接线缺口同因不同址：`startEdge` 起核心前的网络准备晚验对 `unavailable` 直接调终结函数、绕过分流——排队通过后网络才断掉的窗口正好落在这里，即便原因可恢复也不重排（既有契约测试只盖了主启动流一条道，见 memory「守卫只盖一条道」）。

## What Changes

- **原因拆名**：云端代理权威读取的 HTTP 请求未送达（断网 / DNS / 超时；`clientAuthFetch` catch 出口的 status 0 + error）返回独立原因 `proxy_authority_unreachable`，**MUST NOT** 折进 `proxy_authority_unavailable`。「未配置 base」的早退（status 0 无 error）仍按配置类处理。
- **归类可恢复**：新原因**刻意不进**不可恢复清单（该清单是不可恢复白名单、未列入即可恢复），从而自然进入既有有界重排通道（预算与间隔沿用：默认 2 次重排、20s/60s）。
- **晚验接分流**：`startEdge` 起核心前的网络准备晚验改走 `handleProxyPreflightFailure` 分流，与主启动流同一处置；不再无条件终结。
- **文案**：新原因有明确中文文案（「暂时联系不上云端，代理配置读取不到」），不落「代理当前不可用」默认桶。

不在本次范围（如实登记，不静默）：

- **视频号临时浏览器通道**（`main.cjs` transientBrowserQueue 内）对 `unavailable` 仍直接终结——该通道有独立租约结算语义，重排需单独设计；断网时它会显示新原因的诚实文案但不重排。
- **核心子进程退出路径**的 `proxy_authority_unavailable` 终局（核心侧代理权威管道缺失）——那是 spawn 后的结构性条件，不属预检。
- **网络恢复自动重启**（无网络恢复监听，预算耗尽后仍需人工重启）与**运行中环境断网的处置**——均为独立功能，另行立项。

## Capabilities

### Modified Capabilities

- `facebook-proxy-preflight`: 「可恢复的预检失败 SHALL 走有界重排重试通道」的两类划分修正——云端权威读取的传输失败归可恢复类；不可恢复类中「环境代理权威读不到」收窄为「云端答复了但给不出记录」。新增两个 Scenario：断网时权威读取失败进重排；启动前晚验走同一分流。

## Impact

- **aidcp-edge**（Electron 主进程，唯一落点）
  - `src/electron/main.cjs`：`readAuthoritativeProfileProxy` 拆名、`proxyPreflightFailureText` 加文案、`startEdge` 晚验接分流。
  - `src/electron/proxy-preflight.cjs`：不可恢复清单加「刻意不列 unreachable」注释（清单本身不改）。
  - 测试：`proxy-preflight.test.ts` 可恢复清单补新原因；`proxy-preflight-requeue-contract.test.ts` 补两条接线断言（拆名 + 晚验分流）。
- **不涉及**：云端任何服务、边云协议、重排预算与间隔参数。
- **生效条件**：需重打桌面安装包并装机（本 change 落地时本机源码已含，运营机以装机版本为准）。
