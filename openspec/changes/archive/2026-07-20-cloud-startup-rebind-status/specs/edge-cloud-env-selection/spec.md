## MODIFIED Requirements

### Requirement: Current cloud is always visible and matches actual connection

客户端 SHALL 在界面常驻显示每环境 core 实际连接的 Cloud 及已保存目标，而非仅显示全局选择。只有实际 Cloud 已知且与目标不一致时，才 SHALL 显示“实际 X / 目标 Y / 待连接或失败”；首次启动尚未报告实际 Cloud 时 MUST NOT 显示为“待重绑”或暗示需要人工重绑。客户端 MUST NOT 把保存成功等同于连接成功。浏览器状态 SHALL 独立展示，不能用浏览器开关推断 Cloud。ol 环境 SHALL 醒目标注为线上生产。

#### Scenario: 首次启动尚未报告实际 Cloud

- **WHEN** core 刚启动、实际 Cloud 尚未报告，已保存目标为 dev
- **THEN** 顶部 Cloud 状态不显示红色“待重绑”，也不提供仅因实际值为空而产生的重绑提示

#### Scenario: 目标待连接时诚实显示

- **WHEN** 已把目标从 dev 保存为 ol，但 core 仍实际连接 dev
- **THEN** UI 显示“实际 dev / 目标 ol / 待连接”，不显示成已连接 ol

#### Scenario: 浏览器关闭不影响实际 Cloud 显示

- **WHEN** core 已连接 dev 且浏览器关闭
- **THEN** UI 仍显示 Cloud 已连接 dev，同时独立显示浏览器关闭

#### Scenario: ol marked as production

- **WHEN** 某 core 实际连接 ol 或目标选择 ol
- **THEN** 对应实际/目标标签均以醒目方式标注线上生产含义
