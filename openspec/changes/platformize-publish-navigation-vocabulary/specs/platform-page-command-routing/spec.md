## MODIFIED Requirements

### Requirement: 本人身份结果独立、可关联且决定恢复动作

运行期本人身份命令 SHALL 返回专用 `identity.observed` 结果，至少携 Cloud 生成并由 Edge 原样回传的 `captureId`、会话绑定 `accountId`、可选已验证昵称、读取来源与真实页面副作用。Cloud 仅接受与当前在途 captureId、accountId 和平台匹配的结果；当前页读取完成 MUST NOT 下发 Feed 恢复命令，仅本人主页读取产生离开 Feed 的副作用后才可执行恢复。

#### Scenario: 迟到或错账号结果被忽略
- **WHEN** Cloud 收到 captureId 不匹配、accountId 不匹配或平台不匹配的 `identity.observed`
- **THEN** 该结果不写昵称、不完成当前采集，也不触发页面恢复

#### Scenario: Facebook 就地读取完成
- **WHEN** Facebook `identity.read_current_page` 返回匹配结果且 `pageEffect=none`
- **THEN** Cloud 按非空昵称差异写规则处理结果
- **AND** MUST NOT 下发 `facebook.navigation.back`、`facebook.feed.scroll` 或 Feed refresh

#### Scenario: Xiaohongshu 本人主页读取完成
- **WHEN** Xiaohongshu `identity.read_self_profile` 返回匹配结果且页面已进入本人主页
- **THEN** Cloud 按非空昵称差异写规则处理结果并恢复 Feed
