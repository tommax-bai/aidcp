# adspower-environment-provisioning Specification

## ADDED Requirements

### Requirement: LocalAPI 操作先建立托管服务，元数据操作不下载内核

`adspower` 模式下，桌面外壳的环境创建、代理编辑、删除、对账和状态/分身读取 SHALL 使用托管 CLI 实际上报的 LocalAPI base。写操作 SHALL 先完成服务确保；状态/分身读取在已有 base 时 SHALL 直接读取，仅在传输失败后清空 base、重新确保服务并重读一次。例行面板轮询 MUST NOT 每次执行 CLI 子进程。元数据操作 MUST NOT 触发浏览器内核下载。

环境创建 SHALL 先经 `group/list` 解析名称严格等于 `aidcp` 的预置分组，再把其当前 id 交给 `user/create`。本 change MUST NOT 调用 `group/create`，也 MUST NOT 在分组缺失或查询失败时继续创建。

#### Scenario: 冷机创建环境

- **WHEN** 运营在托管服务尚未就绪时创建环境
- **THEN** 桌面外壳先确保 CLI 服务、解析当前 `aidcp` 分组，再调用 `user/create`
- **AND** 服务或分组确保失败时返回真实错误，不暴露裸端点错误或声称创建成功
- **AND** 该流程不下载浏览器内核

#### Scenario: 状态读取复用权威 base

- **WHEN** 设置面板周期性刷新分身或状态
- **THEN** 已有权威 base 时直接读取，不重复运行 CLI 子进程
- **AND** 只有传输失败才重新确保服务并重读一次

#### Scenario: 预置分组缺失

- **WHEN** 当前托管运行时的 `group/list` 没有名称严格等于 `aidcp` 的分组
- **THEN** 桌面外壳报告预置分组不可用，并且不调用 `group/create` 或 `user/create`
