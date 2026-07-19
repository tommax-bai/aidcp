## ADDED Requirements

### Requirement: 环境创建不隐式触发人设设置

桌面外壳 SHALL 让 Facebook 单个/批量环境创建只负责创建与客户归属，MUST NOT 展示“创建后补齐人设”开关、批次人设语言或在创建结果后提交人设运行。客户需要批量设置人设时 SHALL 从环境栏 Facebook 筛选入口显式进入并人工确认一份人设。

#### Scenario: Facebook 批量创建环境
- **WHEN** 客户导入账号资料并批量创建 Facebook 环境
- **THEN** Edge 只创建与归属环境，不提交人设内容、补齐意图或独立语言字段

#### Scenario: 部分创建或创建失败
- **WHEN** Facebook 批量创建只完成部分环境或中途失败
- **THEN** 创建回执只表达真实环境结果，不夹带人设补齐受理、失败或等待绑定状态
