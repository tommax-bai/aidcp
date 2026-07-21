## ADDED Requirements

### Requirement: 桌面灵感库 SHALL 展示来源发布时间而非精选更新时间

桌面灵感库列表卡片与详情作者副行 SHALL 使用 Cloud 返回的来源发布时间证据。解析成功时 SHALL 按 `minute|hour|day` 精度格式化；不可解析但有原文时 SHALL 展示原文并标明未转换；完全缺失时 SHALL 显示“发布时间未知”。`updatedAt` MAY 继续用于缓存和治理，但 MUST NOT 在原稿发布时间位置显示或被描述为原稿时间。

#### Scenario: 列表展示来源发布日期

- **WHEN** 灵感列表项带日精度标准来源时间
- **THEN** 作者副行显示该来源日期，不显示精选记录更新时间

#### Scenario: 详情展示不可解析原文

- **WHEN** 灵感详情只带不可解析的来源时间原文
- **THEN** 作者副行显示原文与未转换标识，不猜测绝对时间

#### Scenario: 旧行显示未知

- **WHEN** 灵感行不带任何来源发布时间字段
- **THEN** 列表与详情显示“发布时间未知”，不回落到 `updatedAt`
