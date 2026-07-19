## Why

客户端当前只接受 `email----password----2FA----cookie` 的 Facebook 账号资料，运营侧已有的 `uid|password|cookie|access_token|email|timestamp` 导出记录无法直接用于“创建环境”和“批量创建环境”，需要人工重排且容易把账号、Cookie 与邮箱配错。

## What Changes

- Facebook 单个新建与批量新建的共用账号解析入口同时接受既有四字段格式和新的六字段竖线格式。
- 六字段格式使用邮箱作为 AdsPower 登录用户名、沿用密码与 Cookie，并以 UID 对 Cookie 中可读取的 `c_user` 做一致性校验。
- Access Token 与采集时间只作为输入格式边界被识别，不写入 AdsPower、不进入创建计划、设置、日志或回执。
- 竖线解析允许 Cookie 值自身包含 `|`，错误仅报告安全行号与字段原因；批量任一行非法时仍在第一条 `user/create` 前整批拒绝。
- 客户端输入框说明同时展示两种受支持格式。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `adspower-environment-provisioning`: 扩展 Facebook 单建/批量建环境账号资料的受支持行格式与敏感字段处置契约。

## Impact

- `aidcp-edge/src/electron/facebook-account-import.cjs` 的共用 Facebook 账号导入解析器。
- `aidcp-edge/src/electron/renderer/index.html` 的账号格式提示。
- Facebook 账号导入与 Electron renderer 回归测试；不新增依赖、云端 API 或持久化字段。
