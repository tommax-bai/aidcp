## MODIFIED Requirements

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
