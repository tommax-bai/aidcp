## ADDED Requirements

### Requirement: 节奏兜底配置写操作经拥有对象单写、诚实非乐观、服务端夹逼

面板 API SHALL 暴露写端点 `PUT /api/pacing`，用于编辑每类操作的兜底 floor 区间。该写 SHALL 只经拥有该配置的进程内 facade 对象（UPSERT `ON CONFLICT DO UPDATE` + 先写库后刷内存镜像 + 审计），MUST NOT raw UPDATE、MUST NOT 乐观假成功——写后 SHALL 返回真实落库态（console 侧写后 invalidate 重取，非乐观更新）。服务端 SHALL 二次校验并诚实映射错误：未知 `operation` → `404 unknown_operation`；`minMs`/`maxMs` 非法（非负整数、`min ≤ max`、`max ≥ min × 1.5` 最小展宽、`≤ CAP`）任一不满足 → `400 invalid_value`；无合法字段 → `400 no_valid_fields`；整块拒绝、MUST NOT 部分落库。写入的兜底值 MUST 经读出口 `clamp(防呆下限, CAP)` 后才对边缘生效，保证配置**只能抬高延迟、抬不穿非零下限**（绝不零延迟红线不可经配置绕过）。审计 `updatedBy` SHALL 取自校验通过的调用者身份（JWT `sub`）。

#### Scenario: 写后回读真态

- **WHEN** 运营 `PUT /api/pacing` 调大 `action` 区间成功
- **THEN** 返回体为落库后的真实生效值（含夹逼护栏），console 侧 invalidate 后重取到该真态，非乐观显示

#### Scenario: 非法值整块拒绝

- **WHEN** 提交的 `maxMs < minMs × 1.5`（展宽不足）或 `minMs` 为负
- **THEN** 返回 `400 invalid_value`，不落库任何字段（整块拒绝、非部分写）

#### Scenario: 未知操作拒绝

- **WHEN** 提交的 `operation` 不在白名单（非 `action`/`scroll`/`card_gap`/`detail_dwell`）
- **THEN** 返回 `404 unknown_operation`，不写库

#### Scenario: 配置抬不穿非零下限

- **WHEN** 运营提交某 op `minMs = 0`
- **THEN** 即便通过表单，读出口 `clamp` 使对边缘生效的值 ≥ 非零防呆下限，边缘实测间隔不为零
