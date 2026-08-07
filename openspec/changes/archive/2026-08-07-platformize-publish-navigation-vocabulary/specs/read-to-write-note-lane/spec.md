## MODIFIED Requirements

### Requirement: Electron 客户端 SHALL 在发布稿件过程中展示写笔记状态

Electron 客户端 SHALL 将发布稿件过程投影为浏览循环中的 `写笔记` 状态。该状态 SHALL 通过既有 UI event / loopStage 机制更新，MUST NOT 新增边云协议字段，MUST NOT 改变发布审批、发布终态或失败回执语义。

（原「旧整页发布路径也进入写笔记状态」场景随 `publish.request` 消息类型删除而移除——该场景要求边缘对一条已不存在的消息有行为；原子指令与发布快照两个场景不变，覆盖不降。）

#### Scenario: 原子发布指令进入写笔记状态

- **WHEN** edge 接收到并执行 `{platform}.publish.command`
- **THEN** Electron 客户端当前 loop stage SHALL 切换为 `写笔记`
- **AND** 该状态更新 SHALL NOT 产生活动流计数

#### Scenario: 发布快照进入写笔记状态

- **WHEN** Electron 客户端收到发布审批或发布终态的结构化 UI 事件
- **THEN** 客户端 SHALL 将当前 loop stage 置为 `写笔记`
- **AND** 发布卡仍 SHALL 按既有 pending / approved / published / rejected / failed 状态展示
