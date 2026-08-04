## Context

`ClientUserStore.listAllEnvironments()` 是 Cloud 对环境注册表、归属、账号、安装与生命周期的完整聚合。面板目前让 `GET /api/client-environments`（端用户归属候选池）和 `GET /api/environments`（环境资产页）共同消费同一个 `listPanelEnvironments()` 结果。删除终态会被持久保留用于历史审计，因此复用全量结果会让 `deleted` 环境进入归属候选池。

当前端用户的已分配读已经只返回 `active` 环境；问题仅在管理侧候选接口未按用途收窄。环境资产页则明确支持查看全部生命周期，不能在 store 层丢弃删除历史。

## Goals / Non-Goals

**Goals:**

- 让 `/api/client-environments` 不返回生命周期为 `deleted` 的环境。
- 保持 `/api/environments` 返回完整生命周期历史。
- 保留 `waiting_edge`、`deleting`、`delete_failed` 与撤权清理状态的真实展示。
- 用同一份 store 假数据验证两个端点的不同边界。

**Non-Goals:**

- 不删除或迁移环境注册表历史数据。
- 不改变客户侧 `/my-environments`、归属写入或环境删除生命周期。
- 不修改 Console 页面结构、交互或 API 响应字段。

## Decisions

### D1. 在内部面板路由边界过滤，而不是修改 store 聚合

`listAllEnvironments()` 同时承担环境资产历史读。若在 store SQL 或映射阶段排除 `deleted`，环境资产页的「全部生命周期」会失去权威历史。因此只在 `/api/client-environments` 响应前按 `environment.lifecycle.state !== 'deleted'` 收窄；`/api/environments` 继续直接返回完整结果。

备选方案是在 Console 本地过滤。该方案会让已删除环境继续经网络进入候选数据源，并使行为依赖前端版本，不符合 Cloud 权威数据边界，故不采用。

### D2. 只排除已完成删除的终态

删除中、删除失败与撤权清理中的环境仍需向运营展示真实状态，现有 UI 也会禁止清理未完成的候选被勾选。本次不扩大状态过滤，只排除 `deleted`。

### D3. 接口级回归测试锁定用途差异

面板测试使用同一个 `listAllEnvironments()` 桩同时返回 `active` 与 `deleted` 两行，断言 `/api/client-environments` 只返回 active 行，而 `/api/environments` 两行都返回。这样未来若两个路由再次无差别复用全量结果，测试会直接失败。

## Risks / Trade-offs

- [未来新增删除终态但未同步过滤] → 生命周期联合类型与接口测试共同约束；本次严格按现有 `deleted` 终态处理。
- [误伤环境资产历史] → 测试同时断言 `/api/environments` 仍返回 deleted 行。
- [Console 与 Cloud 滚动发布] → 响应结构不变，只减少不可分配行；Console 无需兼容分支。

## Migration Plan

- 无数据库、协议或 Console 迁移。
- Cloud 验证后按默认流程部署到 `dev`；接口生效后归属抽屉下次查询即不再收到删除终态。
- 回滚只需恢复 `/api/client-environments` 的原始全量响应，不影响历史数据。

## Open Questions

无。
