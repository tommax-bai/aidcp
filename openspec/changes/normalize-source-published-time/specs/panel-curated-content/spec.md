## ADDED Requirements

### Requirement: 精选面板 SHALL 如实展示原稿发布时间

精选面板列表与详情 DTO SHALL 返回来源发布时间原文、标准时间、精度、解析状态和观测锚。Console SHALL 在原稿时间位置优先按精度格式化标准时间；不可解析但有原文时 SHALL 展示原文并标明未转换；完全缺失时 SHALL 展示“发布时间未知”。界面 MUST NOT 以精选 `updatedAt`、`firstSeenAt` 或计数采集时间冒充原稿发布时间。

#### Scenario: 日精度只显示日期

- **WHEN** 精选行来源发布时间已解析且精度为 `day`
- **THEN** Console 显示来源日期而不补造具体时分

#### Scenario: 有原文但不可转换

- **WHEN** 精选行状态为 `unparseable` 且保留原文
- **THEN** Console 显示该原文并明确未转换，不显示记录更新时间代替

#### Scenario: 历史行发布时间未知

- **WHEN** 历史精选行没有来源发布时间证据
- **THEN** Console 显示“发布时间未知”，仍可单独保留既有更新时刻治理信息
