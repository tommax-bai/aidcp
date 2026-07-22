## Context

管理后台账号页通过通用 `AccountsTable` 渲染账号事实列。当前 `platformAddon` 把 Facebook 配置入口附着到平台标签，`runtimeControl` 则为视频号追加独立“运行控制”列，造成账号级配置入口位置不一致。`AccountsTable` 同时被只读仪表盘复用，因此账号页专属能力必须继续通过可选 render prop 注入，不能影响只读调用方。

## Goals / Non-Goals

**Goals:**

- 让账号页只出现一个语义明确的“配置”列。
- 按账号平台在该列渲染视频号运行控制或 Facebook 配置入口。
- 保持平台列只表达平台事实，并保持仪表盘等只读表格不新增配置列。
- 用渲染测试锁定表头、入口位置和现有弹窗行为。

**Non-Goals:**

- 不合并视频号与 Facebook 的弹窗、状态或后端配置接口。
- 不改变任何配置保存、权限、CAS、风险或发布语义。
- 不为小红书新增账号级配置能力。

## Decisions

1. `AccountsTable` 使用单一可选 `configurationControl(account)` render prop，并由它决定是否增加“配置”列。相比保留平台 addon 加另一列，该设计让列语义与内容一一对应，也保留表格组件对平台具体业务的无知。
2. `AccountsPage` 负责平台分派：视频号返回现有运行控制按钮，Facebook 返回现有 `FacebookSearchConfig` 紧凑入口，其他平台返回 `null`。相比在 `AccountsTable` 内判断平台，这能把页面业务组合留在页面层。
3. 平台列移除账号页专属 addon，仅渲染平台标签。Facebook 配置组件本身及其 API 路径不变，避免把视觉归并扩大成配置领域重构。
4. 无可用账号级配置的平台在该列使用通用空态破折号，由表格层在 render prop 返回空值时补齐，避免出现含义不明的空白单元格。

## Risks / Trade-offs

- [Risk] render prop 返回 `null` 时表格可能显示空白，降低可读性 → 在统一配置列集中补齐空态并用测试覆盖。
- [Risk] Facebook 入口移动后测试仍只验证“存在”，无法证明位置 → 新增表头与单元格范围断言，确认入口不再位于平台单元格。
- [Trade-off] 两个平台仍打开不同形态的 UI → 这是领域行为差异；本次只统一入口位置，不伪造统一配置模型。

## Migration Plan

1. 在 `aidcp-console` 隔离 worktree 实现并运行聚焦测试、全量测试与 typecheck/build。
2. fast-forward 集成到 `master` 并推送。
3. 该变更仅更新管理后台静态资源，按 dev 部署规范备份并发布 Console；验证页面资源、HTTP 与关键 UI。
4. 回滚时恢复部署前静态目录备份或回退 Console 提交，不涉及数据迁移。

## Open Questions

无。
