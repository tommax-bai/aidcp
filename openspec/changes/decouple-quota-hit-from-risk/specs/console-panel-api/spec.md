## ADDED Requirements

### Requirement: 看板按账号活动暴露配额用量与上限

`GET /api/dashboard/summary` 的按账号今日切片（`totalsByAccount`）SHALL 对每个账号附上当前 **day 窗口生效配额上限**（每动作，取自该账号 `RiskController.effectiveQuotas()` 的现读值，随风控态 / 档位变化）与**每动作是否已在任一滑动窗饱和**的标记，使管理后台能就地把「用了多少 / 上限多少」呈现、到顶标红。

该组合 MUST 为**只读**：MUST NOT 经 `RiskController` 写、MUST NOT 触发任何风控状态迁移，且沿用面板「只用点查 / 内存态、不跑阻塞全表扫描」红线。缺 controller / 缺账号态时 MUST 诚实回落（不编造上限），归因待补的全局切片语义不变。此「配额用量」呈现 MUST 与风控状态徽标在语义上区分——它是**我方节流用量**，不是平台威胁态。

#### Scenario: 按账号今日活动带当前生效上限

- **WHEN** 请求 `GET /api/dashboard/summary`
- **THEN** 每个账号的今日各动作计数旁附当前 day 窗口生效上限（如 `restricted` 账号的互动上限如实为 0、`warned` 账号为缩放值）

#### Scenario: 已饱和动作被标记供前端标红

- **WHEN** 某账号某动作已撞到当日或突发窗上限
- **THEN** 该动作在响应中带「已饱和」标记，管理后台据此把该格标红

#### Scenario: 用量组合只读、不写风控态

- **WHEN** 面板层为总览接口计算按账号用量 / 上限
- **THEN** 该计算不触发任何风控状态写 / 迁移（`applySignal` / `setQuotaLevel` 不被调用），风控终态单写不变量不受影响
