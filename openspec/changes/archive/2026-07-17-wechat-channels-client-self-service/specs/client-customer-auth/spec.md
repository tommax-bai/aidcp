## ADDED Requirements

### Requirement: 客户只能修改当前环境的互动读取开关

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/interactions/read-controls`。请求 MUST 只接受 `expectedVersion`、`commentsReadEnabled` 与 `dmReadEnabled`，并在同一 enabled-user、env ownership、account binding 权威范围内以 CAS 更新；账号写总闸、评论回复、私信发送、图片发送、自动发送和风险配置 MUST 保持原值且不可由客户请求体覆盖。成功后 SHALL 复用 runtime-control 下发链通知所属 Edge，并返回 stored/applied/effective 真态，MUST NOT 把 Cloud 保存成功显示成 Edge 已应用。

#### Scenario: 客户开启两个读取渠道但不能开启写
- **WHEN** 当前环境所有者以正确 expectedVersion 同时开启评论和私信收取
- **THEN** Cloud 只更新两个 read 字段、递增版本并下发所属 Edge，所有 write 字段逐位保持原值

#### Scenario: 客户请求夹带发送字段被拒绝
- **WHEN** 客户请求体额外携带 commentsReplyEnabled、dmSendTextEnabled 或 writePaused
- **THEN** customer-auth 返回校验失败且不修改任何 runtime control

#### Scenario: 旧版本更新不覆盖管理员新配置
- **WHEN** 管理员已更新 controls 版本而客户仍提交旧 expectedVersion
- **THEN** customer-auth 返回版本冲突与当前版本，MUST NOT 用旧快照覆盖管理员修改

### Requirement: 客户互动投影必须包含回复配置就绪状态

interaction list/detail 与 read-controls 成功回包 SHALL 为当前 account/env 返回只读 `replyConfig` 投影，至少区分 `missing`、`draft_only`、`published` 并给出 current/draft/published version。该投影 MUST NOT 包含模板正文、规则条件、完整私信或 internal permission；查询失败 MUST 显示 unknown/fail-closed，不能伪造默认 published 配置。

#### Scenario: 无发布配置时客户端得到明确阻断
- **WHEN** 当前账号没有 config head 或只有未发布 draft
- **THEN** 客户回包分别返回 missing 或 draft_only，客户端可保持收件箱可读并禁用依赖 published 配置的生成/发送流程

#### Scenario: 已发布配置只暴露版本状态
- **WHEN** 当前账号存在 immutable published 配置
- **THEN** 客户回包返回 published 与版本号，不返回模板、规则、profile 或审计正文

### Requirement: 客户读取自助不得打通 internal 配置域

客户 JWT SHALL 继续不能访问 internal reply policy/template/rule/profile/preview/publish/audit 路径。客户侧读取开关 API MUST 使用独立 schema 与具名 renderer IPC，MUST NOT 接受任意 URL、internal token 或代理配置写入。

#### Scenario: 客户 token 调用内部配置发布仍被拒绝
- **WHEN** 客户使用有效 customer JWT 调用 internal reply-config/publish
- **THEN** 请求按认证域隔离被拒，已发布版本和 runtime write controls 均不变化
