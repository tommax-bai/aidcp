## Why

客户端编辑已有环境代理时会丢弃 AdsPower `user/list` 返回的 `proxy_password`，并把密码输入框强制置空；保存又会整体替换 `user_proxy_config`。运营只修 host、port 或用户名时如果没有重新输入密码，提交载荷便不再包含旧密码，带鉴权代理可能因此失效。

## What Changes

- 允许环境代理详情把 AdsPower 返回的 `proxy_password` 以内存态传到本地编辑浮层并回显。
- 保存已有环境代理时默认提交回显的现有密码；用户仍可直接修改或清空密码后提交。
- 保持代理凭据不写入设置、台账或日志，并继续对请求/错误日志脱敏。
- 增加回归测试，证明读取、回填和受限 `user/update` 提交链不会静默丢失密码。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `adspower-environment-provisioning`: 修改代理凭据在本地编辑界面的内存态可见性与已有环境代理更新语义，使现有密码可回显并随修改请求保留提交。

## Impact

- `aidcp-edge/src/electron/ads-local-api.cjs` 的环境代理结构化结果。
- `aidcp-edge/src/electron/renderer/renderer.js` 与代理编辑表单提示。
- Edge Electron 代理读取/写入回归测试。
- 不改变 Cloud、Console、协议 v2、持久化格式或 AdsPower API 端点。
