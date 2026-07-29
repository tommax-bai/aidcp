## Why

AdsPower 对外提供的是依赖本机 runtime 的 Local API，当前 Cloud 运行环境没有该 runtime，也不再计划为管理后台托管 AdsPower CLI/runtime。继续保留云端删除入口和 API Key 配置只会产生不可用能力与误导性失败，因此管理后台应回到环境资产只读管理。

## What Changes

- **BREAKING**：移除管理后台环境页的删除入口、影响确认弹窗和删除进度/重试操作；管理后台不再触发 AdsPower 或 AIDCP 环境删除。
- **BREAKING**：移除内部 Panel 环境删除端点以及 Cloud AdsPower 删除/存在性查询客户端，不再接受任何云端环境删除请求。
- 从 Cloud 平台凭据目录和 Console 设置页移除 AdsPower API Key；不再把云端保存 AdsPower Key 描述为可启用环境删除。
- 不恢复旧的 Edge maintenance poll/claim/result 或 outbox 远程删除链，避免换一种异步方式继续执行管理后台删除。
- 保留既有环境清单、账号反向环境摘要和历史 lifecycle/删除审计的只读兼容；已有 deleted 行不复活，历史表/列不做破坏性迁移。
- 桌面客户端本地的逐环境二次确认 AdsPower 删除保持不变。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `admin-environment-direct-deletion`: 移除 Cloud 直调 AdsPower 与管理后台删除能力，历史状态只读保留。
- `adspower-environment-provisioning`: 删除环境的允许来源重新收紧为桌面客户端本地逐环境二次确认，管理后台不再是允许来源。
- `console-panel-api`: 移除内部环境删除写端点与 AdsPower API Key 凭据目录项。
- `model-provider-config`: 平台配置页不再展示或保存 AdsPower API Key。

## Impact

- `aidcp-cloud`: 删除 AdsPower 直调客户端、Panel 删除编排/路由与 AdsPower 凭据注册；保留非破坏性的历史 schema 和环境只读投影。
- `aidcp-console`: 删除环境页删除交互和相关请求类型/文案；设置页删除 AdsPower 凭据展示，环境与账号资产查询继续可用。
- `aidcp-edge`: 不恢复已退休的远程 maintenance 执行链；本地桌面删除不变，无需构建安装包。
- `dev`: 部署 Cloud/Console 后验证删除路由不可用、页面无删除入口、设置页无 AdsPower Key，同时不触碰已有环境或历史审计数据。
