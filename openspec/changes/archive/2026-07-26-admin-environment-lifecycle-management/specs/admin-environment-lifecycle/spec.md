## ADDED Requirements

### Requirement: 管理后台提供独立环境资产页面

系统 SHALL 在管理后台「账号」分组提供独立环境页面，按 envKey 一行展示环境名、平台、生命周期、端用户归属、最近承载 Edge、挂载账号基本信息、账号风控和账号分组。环境名与账号显示名 MUST 使用不同字段；缺少当前确认时 MUST 显示“上次确认”或未知，MUST NOT 把历史绑定伪装成实时在线挂载。

#### Scenario: 已绑定环境显示账号基本信息与账号风控
- **WHEN** 环境存在最近确认的账号绑定且账号主数据、风控和分组可读
- **THEN** 环境行显示统一账号显示名、稳定 accountId、平台、运营状态、RiskController 当前风控投影和 groupLabel，并明确风控属于账号

#### Scenario: Edge 离线时不伪造实时挂载
- **WHEN** 环境只存在历史账号绑定且最近承载 Edge 已离线或观测过期
- **THEN** 页面显示“上次确认挂载”及确认时间，不显示“当前在线挂载”

#### Scenario: 未绑定环境仍独立可见
- **WHEN** 环境已登记但没有可证账号绑定
- **THEN** 环境页仍显示该 envKey、环境信息和归属状态，账号、风控与分组位置显示未挂载或未知

### Requirement: 账号页面显示环境可用性摘要

账号列表 SHALL 展示派生环境摘要，区分有效环境、删除中环境和没有可执行环境。已删除环境 MUST NOT 计入当前环境数量；删除环境 MUST NOT 删除账号、清空账号风控/分组/人设/历史或静默改变账号运营暂停态。

#### Scenario: 一个账号挂载多个环境
- **WHEN** 账号存在两个有效环境和一个删除中的环境
- **THEN** 账号页显示两个有效环境及一个删除中提示，并可跳转到按该 accountId 筛选的环境页

#### Scenario: 删除最后一个环境后账号保留
- **WHEN** 账号最后一个有效环境完成删除
- **THEN** 账号仍存在且显示“无可执行环境”，原风控、分组和运营状态不被环境删除改写

### Requirement: 管理删除使用诚实的异步生命周期

管理后台 SHALL 仅在操作者查看影响预览并逐字确认完整 envKey 后创建单环境删除申请。删除申请只代表 Cloud 期望状态并冻结新调度；AdsPower 删除成功或权威承载 Edge 明确证明已不存在之前，页面 MUST NOT 显示“已删除”。

#### Scenario: 删除申请已创建但 Edge 离线
- **WHEN** 操作者确认删除但目标 installation 未在线拉取
- **THEN** 页面显示“等待 Edge”，环境从新调度中排除但仍保留挂载和物理状态未知信息

#### Scenario: AdsPower 拒绝删除
- **WHEN** Edge 调用 `user/delete` 因环境仍在运行或 AdsPower 返回错误而失败
- **THEN** Cloud 保留 `delete_failed` 与真实错误，Console 显示可重试失败且不得移除环境记录

#### Scenario: AdsPower 回执后进入终态
- **WHEN** 匹配 claim 的权威 installation 回报 `deleted` 或可证明的 `already_missing` 且平台前置清理完成
- **THEN** Cloud 原子标记环境 `deleted`、记录审计并从账号有效环境摘要和调度候选中移除

### Requirement: 删除环境保留审计和历史查询

系统 MUST 软删除环境注册表行，至少保留删除请求、操作者、最后挂载账号、AdsPower 结果、失败原因和时间戳。环境页默认 MAY 隐藏已删除环境，但 SHALL 提供历史筛选；系统 MUST NOT 以物理删除数据库行掩盖生命周期。

#### Scenario: 查看已删除环境历史
- **WHEN** 操作者切换到已删除生命周期筛选
- **THEN** 页面显示环境最后名称、envKey、最后挂载账号、删除操作者、AdsPower 回执和完成时间

### Requirement: 删除请求后的调度失败关闭

Cloud SHALL 在删除申请事务成功后立即把环境从新自动化、发布和互动调度候选中排除，并在终态前保持该闸。账号仍有其它有效环境时 MAY 继续经其它环境执行；没有有效环境时 MUST 返回无可用环境，不得回退到已删除或删除中的环境。

#### Scenario: 删除中的环境不接收新任务
- **WHEN** 环境生命周期为 `waiting_edge|deleting|delete_failed`
- **THEN** Cloud 不向该环境创建或路由新的执行，且不得因它仍有 accountId 绑定而继续选择它
