## Context

客户端人工改名以 `envKey` 解析绑定账号后写入 `accounts.operator_alias`，Cloud 的账号显示名解析器再按运营别名、平台昵称、运营标签、账号 ID 生成 `displayName`。`GET /api/client-environments` 已为每个已绑定环境返回 `account.displayName`，但 Console 的 `ClientEnvironmentView` 仍停留在旧子集类型，“环境归属”抽屉也继续渲染环境 `label`，因此丢失人工别名。

“环境归属”同时包含已挂载账号和未挂载环境。前者的人类可见账号名必须使用 Cloud 统一解析结果；后者没有账号名可解析，只能展示环境自身的系统名或既有备注。

## Goals / Non-Goals

**Goals:**

- 让环境归属的待分配、已分配两张表都显示绑定账号的 `account.displayName`。
- 保持 Console 不复制 `operatorAlias → nickname → label → accountId` 的账号优先级。
- 为未挂载或滚动发布期间缺少账号投影的环境提供稳定、诚实的环境级回落。
- 用纯辅助函数和 focused tests 锁定人工别名优先与回落边界。

**Non-Goals:**

- 不修改客户端改名交互、Cloud 别名写接口、账号解析器或数据库。
- 不把显示名用于客户归属保存、路由、账号绑定或环境身份。
- 不承诺本次改动发布新的桌面安装包。

## Decisions

### 1. 已绑定环境只消费 Cloud `account.displayName`

Console 不读取 `account.operatorAlias`、`account.nickname` 或 `account.label` 来重算名称。客户端人工改名成功后，Cloud 已确认的 `account.displayName` 即为后台应展示的昵称；这也保持统一账号显示名的单一决策点。

备选方案是在前端复刻客户端四档优先级。该方案会让账号别名优先级再次分叉，而且无法从当前 DTO 可靠区分所有来源，因此拒绝。

### 2. 通过全局环境注册表按 `envKey` 丰富已分配草稿行

待分配行本身来自 `/api/client-environments`，可直接读取账号投影。已分配行来自客户 scope，只含 `envKey/label/platform`；页面继续使用现有 `envMeta` 映射按稳定 `envKey` join 注册表，再读取同一个 `account.displayName`。保存请求仍原样提交 scope 字段，显示 join 不参与写入。

### 3. 未绑定环境使用环境级回落

当注册表没有可用的绑定账号显示名时，展示顺序为 `environmentName → scope/registry label → envKey`。这些值只描述环境本身，不构成另一个账号昵称解析器。完整 `envKey` 仍在独立 ID 列展示并可复制。

### 4. 对齐 Console DTO 的已有 additive 字段

Console 为 `ClientEnvironmentView` 补充 Cloud 已返回的 `environmentName` 与最小账号显示投影。页面不新增请求，不改变查询缓存或 Cloud 合约版本。

## Risks / Trade-offs

- [旧 Cloud 在滚动发布窗口尚未返回新增投影] → 类型允许缺省，辅助函数回落到 scope/registry 的环境字段，不白屏也不伪造人工昵称。
- [已分配 scope 行与注册表短暂不同步] → join 缺失时保留该 scope 行自己的备注和 `envKey`，下一次查询刷新后自然收敛。
- [账号显示名与环境系统名同名或重名] → 仅影响人类展示；选择、保存和归属始终使用 `envKey`，不按名称猜测。

## Migration Plan

1. 在 Console worktree 更新类型、展示辅助函数与测试。
2. 运行 focused tests、全量测试、typecheck 和 build，再通过 OpenSpec strict validation。
3. fast-forward 集成并从干净 `aidcp-console/master` 发布到 `dev`。
4. 验证 Console 资产可访问；若页面回归，回滚 Console 静态构建即可，Cloud 与 Edge 无需回滚。

## Open Questions

无。
