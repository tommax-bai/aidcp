## ADDED Requirements

### Requirement: 安全限额数字可在管理后台按档位配置且 canDo 每次读最新

云端的安全限额**数字**（每账号每动作的滑动窗配额）SHALL 为可配置、可在管理后台按风控档位（conservative / normal / aggressive）编辑，且**每日上限与分钟 / 小时突发上限都 SHALL 独立可编辑**（突发上限 MUST NOT 仅由每日值派生）。云端 SHALL 把这些数字落库（新增 `quota_config` 表，迁移 `0010`，主键 `(tier, action)`，含 `daily` / `per_minute` / `per_hour` 三列）并维护内存镜像；`RiskController.canDo(action)` 经 `effectiveQuotas()` MUST **每次现读**当前生效数字（经注入的配额提供者读内存镜像），使管理后台改完即热加载生效、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当配额提供者缺失、某 `(tier, action)` 缺行、或字段非有限非负整数时，`effectiveQuotas()` MUST 回落到代码写死默认（`quotas.ts` 的 `DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP`），MUST NOT 抛错、MUST NOT 让风控闸失效。配额表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（零回归）。`warned` / `restricted` / `frozen` 状态对基准三档的缩放 / 清零语义 MUST 保持不变，只是基准三档数字来源改为提供者（缺值回落写死默认）。

#### Scenario: 后台改某档某动作每日上限，下一次 canDo 即按新值

- **WHEN** 管理后台把 `normal` 档 `comment_like` 的每日上限从 6 改为 4 并保存成功
- **THEN** 无需重启，该账号下一次 `canDo('comment_like')` 的每日窗判定按 4 生效（命中即热加载）

#### Scenario: 分钟 / 小时突发上限独立可改、不由每日派生

- **WHEN** 管理后台单独调高某档某动作的分钟突发上限、不改其每日上限
- **THEN** `effectiveQuotas()` 的分钟窗数字按所配值生效，且每日窗数字不被该改动连带改变

#### Scenario: 缺行 / 非法值回落写死默认、绝不 brick

- **WHEN** 某 `(tier, action)` 在 `quota_config` 缺行，或其某窗口字段为非有限非负整数
- **THEN** `effectiveQuotas()` 对该动作回落 `quotas.ts` 写死默认、不抛错，风控闸照常工作

#### Scenario: 配额表为空时与现状逐位一致

- **WHEN** `quota_config` 表无任何行（如迁移刚跑完）
- **THEN** `effectiveQuotas()` 在每个状态 / 档位下产出的三窗口数字与改造前（`deriveWindowQuotas` 写死默认）逐位相同

### Requirement: 限额数字编辑绝不触碰风控状态单写路径

安全限额**数字**的编辑 MUST 只写 `quota_config` 表，MUST NOT 经由风控状态单写路径（`RiskController.setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表）。配额提供者注入 `effectiveQuotas()` 后 MUST 仅作只读读取，MUST NOT 写入或改变账号风控终态（`normal` / `warned` / `restricted` / `frozen`）或档位 `quotaLevel`。账号风控终态 MUST 仍仅由云端 `RiskController` 单写（既有不变量不被本配置通道动摇）。

#### Scenario: 改限额数字不改风控状态

- **WHEN** 管理后台保存新的限额数字
- **THEN** 写操作只落 `quota_config` 表，归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`setQuotaLevel` / `applySignal` 不被调用

#### Scenario: 提供者只读、不写状态

- **WHEN** `effectiveQuotas()` 经配额提供者读取当前数字
- **THEN** 该读取不触发任何状态迁移 / 持久化写，风控终态单写路径不受影响

### Requirement: 管理后台限额页与 JWT 守卫的非乐观写

管理后台 SHALL 提供安全限额配置页（`/quotas` 路由 + 导航项），展示三档 × 全动作 × 三窗口（每日 / 分钟 / 小时）的当前生效值并可编辑。云端面板 API SHALL 提供 `GET /api/quotas`（回显当前生效值 + 审计字段，库缺行处以写死默认合成）与 `PUT /api/quotas`，二者 MUST 经 JWT 守卫。写为**非乐观**：服务端 MUST 先校验（有限非负整数 + 合理上限 + 合法 tier / action），任一字段非法时整块拒（4xx）、MUST NOT 部分落库、MUST NOT 假成功；写库成功后 MUST 回显服务端真态，管理后台以回显刷新（不本地假设成功）。

#### Scenario: 合法编辑写库并回显真态

- **WHEN** 携带有效 JWT 的 `PUT /api/quotas` 提交合法的非负整数限额
- **THEN** 服务端校验通过、写 `quota_config` 成功、刷新内存镜像并回显含 `updatedAt` / `updatedBy` 的真态，前端据此刷新

#### Scenario: 非法值整块拒、绝不落库

- **WHEN** `PUT /api/quotas` 提交了负数 / 非整数 / 超上限的限额
- **THEN** 服务端返回 4xx 校验错、不写任何行、不假成功（保持配额配置一致、绝不部分落库）

#### Scenario: 未授权写被拒

- **WHEN** 无有效 JWT 调用 `GET /api/quotas` 或 `PUT /api/quotas`
- **THEN** 返回 401，不读 / 不写配额配置
