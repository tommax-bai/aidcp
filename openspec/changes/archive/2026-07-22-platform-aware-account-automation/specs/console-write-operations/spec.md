## ADDED Requirements

### Requirement: 内容排期写入按账号平台校验动作能力

`PUT /api/content-schedule/:accountId` SHALL 在写入前读取并规范化账号平台，并按服务端平台注册声明校验 `post*`、`comment*`、`contactComment*` 动作字段簇。对支持动作，非关闭模式 MUST 属于该平台允许模式且日上限 MUST 不超过平台注册上限；对不支持动作，启用、非 `off` 模式或正日上限写入 MUST 以可区分的 `unsupported_automation_action` 整块拒绝、绝不部分落库。显式安全关闭值（`enabled=false`、`mode=off`、`dailyCap=0`）SHALL 允许用于清理遗留配置，公共总开关和周历字段不得因其它动作不支持而被误拒。

#### Scenario: 视频号开启自动评论被整块拒绝
- **WHEN** 运营或外部调用为视频号账号提交 `commentMode=review` 或正数 `commentDailyCap`
- **THEN** Cloud 返回 `unsupported_automation_action` 并且该请求中的任何字段都不落库

#### Scenario: Facebook 不允许的免审发帖被拒绝
- **WHEN** 为当前只允许待审发帖的 Facebook 账号提交 `postMode=auto_approve`
- **THEN** Cloud 返回平台动作不支持的可区分拒绝且不改变原排期

#### Scenario: 不支持动作可安全清零
- **WHEN** 视频号历史排期含评论配置且运营提交 `commentEnabled=false`、`commentMode=off`、`commentDailyCap=0`
- **THEN** Cloud 允许写入并回读关闭真态，便于清理遗留脏配置

#### Scenario: 公共周历写入不被动作矩阵误伤
- **WHEN** 运营只为无内容动作的平台账号修改总开关或账号周历覆盖，未提交任何动作启用值
- **THEN** 写入口继续按既有公共字段规则校验和落库，不因平台动作列表为空而拒绝
