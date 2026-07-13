## Why

Facebook 浏览闭环已经具备，但桌面端未向分身核心传入浏览模式，导致所有 Facebook 分身在开发云端也停在默认 `off`，只能连接云端而不会主动浏览。开发环境需要能一次启动全部 Facebook 分身进行真实闭环测试，同时不能把该行为带入线上环境。

## What Changes

- 当桌面端解析出的实际云端为 `dev` 时，为每个 Facebook AdsPower 分身注入 `AIDCP_FB_BROWSE_AUTO=on`。
- 仅对 Facebook 分身生效；小红书及其他平台不受影响。
- 当实际云端为 `ol` 或自定义地址时，桌面端显式注入 `off`，不允许继承外壳中的误开值。
- 保留既有浏览节奏、风险配额、延迟、失败熔断和单分身独立监督逻辑；本变更不修改这些控制。

## Capabilities

### New Capabilities

- `facebook-dev-autobrowse-policy`: Desktop edge derives and injects an explicit Facebook automatic-browse mode from the resolved cloud environment.

### Modified Capabilities

- `edge-cloud-env-selection`: The selected or resolved cloud environment also governs the Facebook automatic-browse mode passed to each spawned core.

## Impact

- Edge desktop spawn environment: `aidcp-edge/src/electron/main.cjs` and its tests.
- Edge fleet spawn environment tests: `aidcp-edge/test/electron/fleet.test.ts`.
- No cloud service, protocol, console, database, or `ol` deployment changes.
