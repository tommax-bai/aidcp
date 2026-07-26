## MODIFIED Requirements

### Requirement: 云端解析发布时刻为距今小时数

云端 SHALL 以 `note.detail.arrived` 的事件时间为观测锚，调用统一平台发布时间标准化能力，再派生距今小时数 `hoursAgo`。“刚刚 / X分钟前 / X小时前 / 昨天[ HH:mm] / 前天 / X天前 / 裸日期”均 MUST 复用同一标准化结果；日精度结果 SHALL 按该自然日的可能时间区间做保守帖龄判断，不得把代表用零点伪装为精确发布时间。剥离受支持前缀与地区后缀后仍无法识别时 SHALL 返回 `null`。云端 MUST NOT 把无法识别的文案、首次发现时间或记录更新时间臆造成帖龄。

#### Scenario: 小时级文案

- **WHEN** `publishedAtText` 为“5小时前”且事件观测时刻确定
- **THEN** `hoursAgo` 解析为 `5`

#### Scenario: 分钟级 / 刚刚

- **WHEN** `publishedAtText` 为“刚刚”或“20分钟前”
- **THEN** 标准化结果为分钟精度，派生 `hoursAgo` 小于一小时并继续受既有分母下限保护

#### Scenario: 昨天无时刻

- **WHEN** `publishedAtText` 为“昨天”且无 HH:mm
- **THEN** 标准化结果落上一自然日并标记 `day` 精度，帖龄判断按该日区间保守计算而非宣称固定精确小时

#### Scenario: 裸日期转换为日精度时间

- **WHEN** `publishedAtText` 为“07-05”这类裸日期
- **THEN** 统一标准化器以观测本地日历推导最近非未来日期并标记 `day` 精度，热度闸按该日期区间判断是否超窗

#### Scenario: 无法识别

- **WHEN** 剥离前后缀后 `publishedAtText` 不匹配任何已知形态
- **THEN** `hoursAgo` 为 `null` 且热度闸 fail closed
