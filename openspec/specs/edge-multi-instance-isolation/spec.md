# edge-multi-instance-isolation Specification

## Purpose
TBD - created by archiving change edge-multi-instance-userdata-isolation. Update Purpose after archive.
## Requirements
### Requirement: 实例级 userData 隔离开关

监督者启动时 SHALL 读取环境变量 `AIDCP_USER_DATA_DIR`；当其为非空值时，SHALL 在请求单实例锁与读取任何 userData 派生路径**之前**，将 Electron 用户数据目录（userData）覆盖为该值。当该变量未设置或为空时，监督者 SHALL 使用默认用户数据目录，行为与引入本能力前逐字一致。

覆盖用户数据目录 SHALL 同时使以下全部本机状态按实例分离：单实例锁、设置 / 名册文件、界面状态文件、边端日志文件、内置浏览器运行时落地目录。

#### Scenario: 设置了隔离目录

- **WHEN** 监督者以非空 `AIDCP_USER_DATA_DIR` 启动
- **THEN** 其 userData 指向该目录，且单实例锁 / 设置 / 名册 / 界面状态 / 日志 / 运行时落地目录均在该目录下

#### Scenario: 未设置隔离目录（零回归）

- **WHEN** 监督者启动且未设置 `AIDCP_USER_DATA_DIR`（或为空）
- **THEN** userData 使用默认目录，路径解析与引入本能力前完全一致

#### Scenario: 顺序保证

- **WHEN** 设置了 `AIDCP_USER_DATA_DIR`
- **THEN** userData 覆盖在 `requestSingleInstanceLock()` 与任何 userData 派生路径读取之前完成，使单实例锁落在隔离后的目录

### Requirement: 同机多监督者并存

当两个监督者实例被赋予**不同**的用户数据目录时，系统 SHALL 允许它们在同一台机器上并行运行；各自的单实例锁互相独立，第二个实例 SHALL NOT 因单实例锁而被拒绝启动。各实例的云端目标沿用既有 `AIDCP_CLOUD_URL` 机制独立选择，本能力不新增云端选择逻辑。

#### Scenario: 两实例分连 dev 与 ol

- **WHEN** 实例甲以某 userData 目录 + 指向 dev 的 `AIDCP_CLOUD_URL` 启动，实例乙以另一 userData 目录 + 指向 ol 的 `AIDCP_CLOUD_URL` 启动
- **THEN** 两实例均成功启动、各连各的云、互不因单实例锁而被拦

#### Scenario: 相同 userData 仍被单实例锁拦截

- **WHEN** 第二个监督者以与第一个**相同**的 userData 目录启动
- **THEN** 单实例锁按原有逻辑拒绝第二个实例（本能力不改动锁逻辑）

### Requirement: 并存的运营前置约束

本能力仅隔离本机 userData 派生状态，不隔离机器全局资源，也不强制分身互斥。并存两实例 SHALL 遵守以下前置约束（由运营保证，本能力不落代码强制）：两实例使用的 AdsPower 分身集合 SHALL 不重叠；SHALL 先启动一个实例、待机器全局 AdsPower 本机服务稳定后再启动第二个；两实例 SHALL 保持默认 AdsPower 浏览器模式。

#### Scenario: 分身不重叠

- **WHEN** 两并存实例各自的环境名册使用不重叠的 AdsPower 分身
- **THEN** 因边缘身份与图片上传临时目录均按分身划分，两实例的浏览器会话、身份、上传暂存天然互不干扰

#### Scenario: 分身重叠（被禁止的配置）

- **WHEN** 同一 AdsPower 分身出现在两个并存实例的名册中
- **THEN** 两实例会驱动同一个物理浏览器窗口而互相干扰；本能力不提供跨实例保护，此配置被运营前置约束明令禁止

