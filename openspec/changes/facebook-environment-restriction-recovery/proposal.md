## Why

Facebook 的通用 `/checkpoint` 页面当前仅凭 URL 就被归为验证码，导致没有验证码控件或人机验证证据的安全检查也会立即把账号置为 `restricted`。同时，桌面客户端把真实受限状态弱化为“节奏已调整”，客户既看不清当前环境为何停工，也没有环境级的安全恢复入口。

## What Changes

- 收窄 Facebook 验证码分类：只有明确验证码 iframe 或人机验证语义证据才判为 `captcha`；仅命中 `/checkpoint` 的页面进入有持续性确认的未知阻断路径，仍 fail-closed 停手但不冒充已看到验证码。
- 在客户鉴权域新增环境级风险状态读取与受限恢复接口；Cloud 逐请求校验客户归属并解析环境绑定账号，客户端不提交或获知 `accountId`、风险信号种类或审计理由。
- 恢复操作只允许 Facebook 环境从 `restricted` 回到 `normal`，经既有 `RiskController` 的 `operator_override_recover` 单写并解除该账号名下的 Cloud 下发暂停；其它状态、平台、未绑定或归属冲突均 fail-closed。
- Electron 客户端对当前 Facebook 环境显示明确的“账号受限”状态，并在“今日进展”底部提供一个紧凑的“解除受限”按钮和 `?` 说明浮层；点击后先二次确认，再展示 Cloud 写后真态或真实失败。
- 若 Facebook 页面仍有 checkpoint/验证码/限流阻断，Edge 继续本地停手；新的有效阻断证据仍可再次把账号升级为受限，恢复按钮不得伪造平台已解除限制。

## Capabilities

### New Capabilities

<!-- None. This change extends existing captcha, customer-auth, and companion-UI contracts. -->

### Modified Capabilities

- `captcha-incident-handling`: Generic Facebook checkpoint URLs no longer count as captcha evidence by themselves while true captcha evidence remains immediate fail-closed.
- `client-customer-auth`: Adds ownership-scoped Facebook environment risk-state read and restricted recovery without exposing account selectors.
- `edge-companion-ui`: Shows explicit per-environment restricted state and a compact recovery action with contextual help.

## Impact

- `aidcp-edge`: Facebook overlay classifier/tests; Electron preload/main IPC; companion renderer markup, state fetch/recovery flow, labels, styles, and smoke/logic tests.
- `aidcp-cloud`: Customer-auth routes/dependencies, `RiskController` restricted-only recovery helper, runtime injection, and route/controller tests.
- OpenSpec contracts: captcha incident handling, customer auth, and edge companion UI.
- No protocol message type or payload changes, no database migration, and no desktop installer build in this change.
