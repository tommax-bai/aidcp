## Why

用户在代理失败后明确点击单环境“启动”是在请求立即重试，但当前启动链会复用两分钟内的新鲜失败缓存，导致按钮看似重新启动、实际没有再次探测代理。手动重试必须以本次点击后的新证据裁决，不能被上一次失败结论挡住。

## What Changes

- 单环境显式“启动”在进入启动或待机唤醒流程前，立即作废该环境已经完成的代理预检缓存；若真实检测恰好在途则继续复用该单飞请求。
- 本次手动启动随后重新读取当前 Cloud 代理权威，并实际执行或等待一轮当前代理连通与受控出口检测；同一次启动内部仍可复用刚取得的结果。
- 自动唤醒、环境选择预热、批量启动和代理预检的既有 TTL/单飞行为保持不变。
- 显式 `no_proxy`、未知检测设施和既有 fail-closed 代理原因语义保持不变。
- 增加 Electron 主进程与代理预检回归测试；不改变 Cloud、协议或数据库，不构建 Edge 安装包。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `facebook-proxy-preflight`: 单环境手动启动必须绕过此前缓存的确定成功或失败结果，以本次点击触发或当时已经在途的真实探测证据决定启动；自动路径继续复用短时缓存。

## Impact

- `aidcp-edge/src/electron/main.cjs`：单环境 `edge:start` 入口的预检缓存失效时点。
- `aidcp-edge/test/electron/`：手动启动重新探测与自动路径不受影响的聚焦覆盖。
- `aidcp`：`facebook-proxy-preflight` OpenSpec delta 与交付证据。
- 无 Cloud、数据库或协议改动；源代码更新不会自动更新已安装客户端。
