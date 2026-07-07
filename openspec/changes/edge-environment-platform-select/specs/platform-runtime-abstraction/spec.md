## ADDED Requirements

### Requirement: 边缘平台按 AdsPower 环境选择并在启动时注入核心

edge 桌面应用 SHALL 支持按 AdsPower 环境选择运行时平台（小红书 / Facebook），并在启动核心进程时把该平台注入为进程配置（`AIDCP_PLATFORM`），使核心据此选平台驱动、决定启动打开哪个平台首页与握手上报的平台。平台 MUST 与该环境持久绑定（写入 AdsPower 分身 remark、随环境列表读回），MUST NOT 依赖操作者每次手动设进程环境变量。未标注平台的历史环境 MUST 回落 `xiaohongshu`，保持零回归。

#### Scenario: 创建 Facebook 环境并从 Facebook 启动
- **WHEN** 操作者在创建环境时选择 Facebook 平台，随后选中该环境点启动
- **THEN** 桌面壳把 `AIDCP_PLATFORM=facebook` 注入核心，核心以 Facebook 平台驱动启动、打开 facebook 首页并在握手上报 `platform=facebook`

#### Scenario: 旧环境与默认零回归
- **WHEN** 一个在本能力之前创建、remark 无平台字段的环境被选中启动
- **THEN** 平台回落 `xiaohongshu`，注入 `AIDCP_PLATFORM=xiaohongshu`，与本能力上线前逐位等价（核心默认即 xhs 驱动）

#### Scenario: 平台驱动缺失时诚实失败
- **WHEN** 选择的平台在当前 edge 构建里没有对应驱动
- **THEN** 核心启动即诚实报错（如「platform=… has no edge driver in this build」），MUST NOT 静默回落其它平台或伪装启动成功
