# source-published-time-normalization Specification

## Purpose
TBD - created by archiving change normalize-source-published-time. Update Purpose after archive.
## Requirements
### Requirement: 平台发布时间标准化 SHALL 保留证据与精度

Cloud SHALL 提供可复用的纯函数，把平台原始发布时间文案连同显式观测时刻、平台 UTC 偏移转换为结构化结果。结果 MUST 保留 trim 后原文与观测时刻，并返回 `parsed|unparseable` 状态；仅解析成功时返回标准 epoch 时间与 `minute|hour|day` 精度。转换 MUST NOT 隐式读取当前时钟，MUST NOT 以首次发现、记录更新时间或计数采集时间代替来源发布时间。

#### Scenario: 相对小时文案以观测时刻为锚

- **WHEN** 原文为“3小时前”、观测时刻为确定值且平台偏移为 `+08:00`
- **THEN** 标准时间为观测时刻减三小时，精度为 `hour`，原文与观测锚完整保留

#### Scenario: 未知文案保留但不造时间

- **WHEN** 原文不匹配任何已知平台时间格式
- **THEN** 状态为 `unparseable`、标准时间与精度为空，并保留原文与观测锚

#### Scenario: 无原文不产生来源时间

- **WHEN** 调用方没有取得非空发布时间文案
- **THEN** 标准化结果为空，MUST NOT 使用观测时刻或其它记录时间补造发布日期

### Requirement: 日历与相对日期 SHALL 按平台本地日历诚实转换

标准化器 SHALL 支持“刚刚 / N分钟前 / N小时前 / 昨天[ HH:mm] / 前天 / N天前 / MM-DD / YYYY-MM-DD / 中文年月日”形态。无时分的相对日与日期 SHALL 标为 `day` 精度；`MM-DD` SHALL 选择不晚于观测本地日期的最近年份。非法日期、负数或无法验证的文本 MUST 返回 `unparseable`。

#### Scenario: 昨天带时分

- **WHEN** 原文为“昨天 14:30”且观测锚位于上海本地某日
- **THEN** 标准时间落在上海上一自然日 14:30，精度为 `minute`

#### Scenario: 裸月日跨年

- **WHEN** 观测本地日期为一月初且原文为“12-31”
- **THEN** 标准时间解析为上一年度 12 月 31 日，精度为 `day`

#### Scenario: 日精度不伪装时分

- **WHEN** 原文只提供“昨天”或“07-05”
- **THEN** 结果精度为 `day`，任何消费者 MUST 按日期展示或按日区间计算，MUST NOT 宣称平台给出了精确时分

