## ADDED Requirements

### Requirement: 分号批命令必须逐段独立受理与回报

Feishu 命令入口 SHALL 接受有界数量的、由 ASCII 分号 `;` 或全角分号 `；` 分隔的已支持 slash 命令。分隔符只有在其后出现已识别的 slash 命令 token 时才构成命令边界；系统 MUST NOT 把 URL、昵称或普通参数中的分号盲目切开。

每个子命令 SHALL 独立完成作用域校验、解析、账号绑定、幂等与入队，且 SHALL 并发进入准备阶段而非按文本顺序串行等待。一个子命令无效 MUST NOT 阻止其它有效子命令入队；每个子命令的拒绝或后续业务结果 SHALL 独立、诚实回报。入口 fast-ack、不发送“已完成”式中间卡、发布/评论真实终态口径均保持不变。

#### Scenario: 发布与评论从同一消息独立入队

- **WHEN** 管理群发送 `/publish Tianxing Bai; /comment Tianxing Bai --join --contact --force`
- **THEN** 系统 SHALL 创建一个发帖任务和一个加群评论任务，而不是把分号后文本并入发帖昵称
- **AND** 两个任务 SHALL 独立进入准备阶段
- **AND** 评论任务 SHALL 同时携带 `joinGroup=true`、`injectContact=true` 与 `force=true`

#### Scenario: 一个子命令无效不吞掉有效兄弟

- **WHEN** 一个批消息中一个子命令合法、另一个子命令因昵称不存在而被拒
- **THEN** 合法子命令 SHALL 正常入队
- **AND** 无效子命令 SHALL 独立回报真实拒绝原因
- **AND** 系统 MUST NOT 把整批伪装成全部成功或全部失败

#### Scenario: 批命令仍然 fast-ack 且不发启动成功卡

- **WHEN** 一条批消息包含两个长耗时写命令
- **THEN** Feishu 事件处理器 SHALL 在受理后立即回帧，MUST NOT 等两个命令执行完成
- **AND** 精确写命令入队阶段 MUST NOT 发送暗示已经发布或评论完成的中间卡
- **AND** 后续审批卡、评论结果卡与发布结果 SHALL 仍按各自真实业务状态独立送达

#### Scenario: 重放按子命令稳定去重但同批重复命令保持独立

- **WHEN** Feishu 重放同一个 message id 的批消息
- **THEN** 每个原子子命令 SHALL 以稳定的 message-id 加子命令序号进行幂等，不产生重放副本
- **AND** 同一原始批消息中由不同序号表达的两条相同命令 SHALL 仍被视为两个显式子命令

#### Scenario: 参数内分号不被误切

- **WHEN** 昵称或 `--join=<url>` 参数中包含分号，但分号后不是已支持的 slash 命令 token
- **THEN** 该分号 SHALL 保留在当前命令参数中
- **AND** 系统 MUST NOT 因简单字符串切分创建伪命令
