## Why

环境删除完成后，Cloud 会保留注册表与生命周期历史供环境资产审计，但端用户「环境归属」候选接口当前复用了这份全量历史，导致 `deleted` 环境重新出现在「待分配」池。运营不应看到或重新选择已经删除的环境。

## What Changes

- 管理侧 `GET /api/client-environments` 只返回生命周期不是 `deleted` 的环境，已删除环境不再进入端用户归属的待分配候选池。
- 独立环境资产接口 `GET /api/environments` 继续返回完整生命周期历史，默认筛选和「全部生命周期」能力不变。
- 保留删除中、删除失败及撤权清理中的真实状态；本次只过滤已经完成删除的终态。
- 增加面板接口回归测试，锁定两个接口对同一环境全集的不同展示边界。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `client-customer-auth`: 端用户归属候选池排除 `deleted` 环境，同时保留环境资产历史读口的完整生命周期。

## Impact

- **aidcp-cloud**：收窄内部面板端点 `/api/client-environments` 的响应；`ClientUserStore.listAllEnvironments()`、客户侧 `/my-environments`、数据库与协议不变。
- **aidcp-console**：无需源代码改动；现有归属抽屉会直接消费收窄后的 Cloud 权威结果。
- **API**：响应结构不变，仅删除不再可分配的终态行；`/api/environments` 仍是完整历史数据源。
