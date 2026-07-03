## ADDED Requirements

### Requirement: 节奏兜底配置只读端点

面板 API SHALL 暴露只读端点 `GET /api/pacing`，返回每类操作（`action` / `scroll` / `card_gap` / `detail_dwell`）的兜底 floor 配置目录：每项含**生效值**（`minMs` / `maxMs`，已含读出口夹逼护栏）、`overridden`（库内是否有该 op 行，用于区分「运营已覆盖」与「系统默认」）以及审计字段（`updatedAt` / `updatedBy`）。当 pacing 配置依赖未注入（进程未装配该能力）时该端点 SHALL 返回 `503 pacing_unavailable`，MUST NOT 崩溃或返回半初始化数据。该端点 MUST 只读，MUST NOT 触发任何写库或状态迁移。

#### Scenario: 返回生效值与覆盖标记

- **WHEN** console 请求 `GET /api/pacing`，且 `action` 已被运营覆盖、`scroll` 未覆盖
- **THEN** 返回目录中 `action` 项 `overridden=true` 带审计字段、`scroll` 项 `overridden=false` 取系统默认值

#### Scenario: 依赖未注入返回 503

- **WHEN** 云端进程未装配 pacing 配置能力，收到 `GET /api/pacing`
- **THEN** 返回 `503 pacing_unavailable`，不崩溃

#### Scenario: 只读不改状态

- **WHEN** 反复请求 `GET /api/pacing`
- **THEN** 不产生任何写库副作用、不触发风控或配置状态迁移
