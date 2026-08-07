# read-to-write-note-lane Specification

## Purpose
TBD - created by archiving change read-to-write-note-lane. Update Purpose after archive.
## Requirements
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

### Requirement: Electron 客户端 SHALL 在阅读页发布评论时展示评论创作状态

Electron 客户端 SHALL 将阅读页进入发布评论的过程投影为 `评论创作` 状态。评论创作状态只表达当前正在写/发评论，MUST NOT 把失败行计为评论成功。

#### Scenario: 评论命令进入评论创作状态

- **WHEN** edge 接收到 `xiaohongshu.note.comment`
- **THEN** Electron 客户端当前 loop stage SHALL 切换为 `评论创作`

#### Scenario: 评论真实成功后仍处于评论创作状态并计数

- **WHEN** edge 验证评论编辑器清空且自己的评论行出现
- **THEN** Electron 客户端 SHALL 记录一条评论成功活动
- **AND** 评论计数 SHALL 增加 1
- **AND** 当前 loop stage SHALL 保持为 `评论创作`

#### Scenario: 非创作互动仍使用互动状态

- **WHEN** edge 执行点赞、收藏、关注或评论点赞
- **THEN** Electron 客户端 SHALL 使用既有 `互动` 状态

### Requirement: 阅读完成 SHALL NOT 自动触发写笔记或洗稿

系统 SHALL NOT 在阅读完成后仅凭内容强参照程度自动触发写笔记/洗稿发布链。洗稿或参照创作 MUST 来自显式用户/后台动作、飞书命令、排期或既有发布触发器。

#### Scenario: 强参照笔记也不自动发布

- **WHEN** 浏览闭环阅读到一篇对账号人设有启发的笔记
- **THEN** 系统 SHALL 继续既定阅读、互动、评论或返回 feed 流程
- **AND** 系统 SHALL NOT 自动调用发布调度器生成参照草稿

#### Scenario: 后台手动洗稿仍可触发参照创作

- **WHEN** 管理后台精选内容池用户点击 `洗稿`
- **THEN** 系统 SHALL 以该精选内容作为 `referenceNote` 进入既有发布生成和人审链路
- **AND** 触发成功只表示已受理生成，MUST NOT 表示已经发布

### Requirement: 精选内容池 SHALL 使用洗稿文案并避免操作列溢出

管理后台精选内容池 SHALL 将参照创作动作展示为 `洗稿`，MUST NOT 在该动作上展示 `写笔记`。表格 SHALL 收窄 `纳入原因` 和 `更新时刻` 列且不折行，并为 `操作` 列预留足够宽度以容纳行内按钮。

#### Scenario: 行级参照创作展示为洗稿

- **WHEN** 管理后台展示精选内容池行操作
- **THEN** 参照创作按钮、确认按钮、成功提示和失败提示 SHALL 使用 `洗稿`

#### Scenario: 表格关键列不折行且操作不溢出

- **WHEN** 管理后台展示精选内容池列表
- **THEN** `纳入原因` 与 `更新时刻` 单元格 SHALL 不折行
- **AND** `操作` 列 SHALL 能容纳 `洗稿`、`评论`、`删除` 三个按钮

