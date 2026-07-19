## ADDED Requirements

### Requirement: 环境 SHALL 可从浏览器缺席态出生并复用冷待机唤醒

当环境已取得可信控制面引导但没有浏览器槽位时，Edge SHALL 可直接初始化为 cold-standby/browser-absent 状态。该路径 MUST NOT 启动 AdsPower、附着 CDP、启动浏览循环或平台 watcher；其后取得槽位时 SHALL 复用既有 FIFO wake 路径。

#### Scenario: 首次启动无槽位不打开浏览器
- **WHEN** 环境首次启动时浏览器并发已满且控制面引导成功
- **THEN** 核心进入 standby 并连接 Cloud，而 AdsPower browser 保持关闭
- **AND** 浏览器槽位计数不增加

#### Scenario: 队头取得槽位后完成唤醒
- **WHEN** 一个运行环境进入冷待机并释放槽位
- **THEN** 等待队头的 browser-absent 环境经串行启动队列打开浏览器、重附着 CDP并复核身份
- **AND** 无需操作员再次点击启动

#### Scenario: 唤醒失败仍保持可恢复
- **WHEN** AdsPower 启动、CDP 附着、身份复核或 Cloud 重连任一步失败
- **THEN** Edge 归还浏览器槽位、保持控制面可诊断且允许后续再次唤醒
- **AND** MUST NOT 把环境永久卡成运行中或已暂停
