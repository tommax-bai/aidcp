## ADDED Requirements

### Requirement: 接管前浏览原子动作有界且可诊断

任何会在 `quiesceForTask()` 前占用浏览原子区的 `note.open` SHALL 有整体墙钟预算，并记录选卡、点击、弹窗等待、详情就绪、抽取/上报和阅读阶段的耗时。预算耗尽前已发送的 CDP 命令 MUST 先返回、报错或走其自身有界超时；edge 仅能在其后的安全检查点停止后续输入并让原子区收敛，MUST NOT 以并行 timer 伪造操作结束。详情尚未上报时超时 MUST 上报真实 `open_timeout` 失败；详情已上报时 MUST 停止非必要的后续阅读而不撤销已交付的详情。

#### Scenario: CDP 输入迟滞时接管最终可继续
- **WHEN** `note.open` 的拟人化点击或等待阶段耗尽其整体预算，且发布 lease 正在等待浏览接管
- **THEN** edge 在当前 CDP 调用的安全结束点停止后续 `note.open` 工作、记录超时阶段与耗时；若尚未上报详情则如实回 `open_timeout`，随后 `quiesceForTask()` 能结束并使等待的 lease 正常 acquired 或被 cloud 正常取消

#### Scenario: 正常打开保留详情与阶段观测
- **WHEN** `note.open` 在整体预算内打开并提取到详情
- **THEN** edge 正常上报 `note.detail`，并记录总耗时及各阶段耗时；MUST NOT 因新增预算改变已成功详情的内容
