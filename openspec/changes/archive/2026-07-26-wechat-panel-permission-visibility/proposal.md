## Why

视频号互动配置权限目前只存在于 Cloud 环境变量中。运营人员在管理后台无法确认六项权限分别控制什么，也无法看出哪些后台账号已经被授权，排障只能登录服务器检查配置。

## What Changes

- 在管理后台设置页增加只读“视频号权限设置”卡片。
- 展示固定六项互动权限的权限名、中文说明和当前获授权的后台用户名。
- Cloud 增加 JWT 保护的只读权限概览接口，只返回有效后台用户名与权限映射，不返回密码、环境变量原文或未知/失效账号。
- 本阶段不提供任何权限新增、删除或编辑入口，不改变现有授权判定。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `console-panel-api`: 增加视频号互动权限的只读管理后台可见性。

## Impact

- Cloud: 权限概览构造、只读 panel API、API 版本与测试。
- Console: 设置页权限卡片、类型、查询与测试。
- Control: `console-panel-api` 契约增量。
- 不修改权限规则、数据库、协议、Edge 或客户鉴权 API。
