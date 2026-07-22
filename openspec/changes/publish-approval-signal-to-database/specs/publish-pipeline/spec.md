## MODIFIED Requirements

### Requirement: submit_publish 前强制人审闸（AC-PUB）

系统 SHALL 在 `submit_publish` 指令下发前强制通过人审授权，判据为**持久授权记录**：按 `requestId` 读取该记录的活跃行，MUST 以严格相等 `approved === true` 判定，且授权所载 `contentVersion` MUST 与待下发草稿的当前版本一致。记录不存在、活跃行缺失、`approved !== true`、或授权状态查询超时 / 不可达时，`CommandSequencer` MUST 在序列中止于 `submit_publish` 之前、绝不下发提交指令，MUST NOT 静默发布、MUST NOT 按缺省或异常放行。

授权判据 MUST NOT 依赖本机文件、本机临时目录或写方与读方共享文件系统。执行侧读取授权 MUST 经其所有者服务的窄内部接口或持久命令，MUST NOT 直读授权表。查询不可达属「授权状态不可读」：稿件保持待审、授权保持活跃、记录附可读阻塞原因，MUST NOT 置为失败终态。

过渡窗口内写方 MAY 在持久记录写入成功后额外影子写一份同格式本机文件供未迁移的本机开发夹具使用；该文件 MUST NOT 被任何生产判定路径读取，其存在与否 MUST NOT 改变本闸的结论。

#### Scenario: 已授权且版本一致才下发 submit_publish
- **WHEN** 该 `requestId` 的活跃授权记录 `approved === true` 且其 `contentVersion` 等于草稿当前版本
- **THEN** `CommandSequencer` 在序列中加入并下发 `submit_publish`，随后 `capture_postId` 抓取真实 postId

#### Scenario: 未授权时序列截止在提交前
- **WHEN** 活跃授权记录不存在、`approved !== true`、或版本不一致
- **THEN** `CommandSequencer.buildCommandSequence` 截止在 `submit_publish` 之前（不加入提交指令），不下发任何提交动作

#### Scenario: 授权状态不可读按未授权处理且不烧稿
- **WHEN** 下发前的授权查询超时或返回错误
- **THEN** 不下发 `submit_publish`、稿件保持待审、授权保持活跃、记录附「授权状态不可读」阻塞原因，MUST NOT 置为失败终态

#### Scenario: 红线反例——缺省直发（禁止）
- **WHEN** 授权记录缺失或查询异常，但程序把缺省 / 异常当作放行仍下发了 `submit_publish`
- **THEN** 这违反 AC-PUB，MUST NOT 发生；严格相等判定 + 提交前截止 MUST 保证「未明确授权 == 不发布」

#### Scenario: 授权判定不依赖同机路径
- **WHEN** 写方与执行侧被部署到不同进程、不同容器或不同主机，或运行环境启用了私有临时目录
- **THEN** 本闸的判定结果不变，因为判据是持久授权记录；MUST NOT 因文件系统不共享而出现「已批准却永不下发」的静默停滞
