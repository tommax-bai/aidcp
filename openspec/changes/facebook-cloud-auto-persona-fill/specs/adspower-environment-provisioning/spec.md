## ADDED Requirements

### Requirement: Facebook 批量创建可提交云端自动补齐意图

桌面外壳 SHALL 仅在 Facebook 批量创建模式展示“创建后由云端自动补齐未设置人设”选项和一份整批发言语言选择；选项默认开启，发言语言只允许中文、英文或越南语。启用时，Edge SHALL 在本批产生至少一个已完成权威客户归属的环境后提交一次 Cloud 补齐运行，不得把账号导入行或客户端账号 ID 作为补齐目标上传。单个创建和其他平台 MUST NOT 展示或提交该能力。

#### Scenario: Facebook 批量创建启用自动补齐
- **WHEN** 客户以 Facebook 批量模式创建环境、保留默认自动补齐并选择受支持发言语言，且至少一个环境完成客户归属
- **THEN** Edge 在创建编排后提交一次无账号 ID 的 Cloud 补齐意图，并在原创建结果区域说明账号首次登录识别后由云端继续处理

#### Scenario: 用户关闭自动补齐
- **WHEN** 客户取消自动补齐后提交 Facebook 批量创建
- **THEN** 环境按既有规则创建，Edge 不创建 Cloud 人设补齐运行，也不要求选择发言语言

#### Scenario: 其他模式没有自动补齐控件
- **WHEN** 当前为 Facebook 单个创建或非 Facebook 平台
- **THEN** 自动补齐与整批发言语言控件隐藏且不会进入 IPC/Cloud 请求

### Requirement: 环境创建成功与补齐运行接受态诚实分离

环境创建或部分创建已经发生后，Cloud 补齐意图失败 MUST NOT 回滚或谎报本地环境未创建；回执 SHALL 分别表达已创建数量和“云端自动补齐未启动”。Cloud 只接受运行时，回执 SHALL 使用“已安排/首次登录后处理”语义，MUST NOT 表述为所有人设已生成或已设置。

#### Scenario: 环境创建成功但 Cloud 补齐请求失败
- **WHEN** Facebook 环境已创建并归属，但 customer-auth 补齐端点超时或拒绝
- **THEN** 客户端保留真实创建成功结果，同时明确提示自动补齐未启动，不把该批人设显示为成功

#### Scenario: Cloud 接受补齐运行
- **WHEN** customer-auth 幂等接受补齐运行
- **THEN** 客户端只提示云端将处理当前缺失人设并等待新环境首次登录识别，不展示虚构完成数
