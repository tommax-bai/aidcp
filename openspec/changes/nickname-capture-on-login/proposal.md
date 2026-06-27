## Why

账号平台真实昵称采集(change account-real-nickname,已归档)把那次性的「本人主页采昵称」挂在**浏览会话开始**(`feed.entered{session_start}`)。但浏览会话开始要先过**诚实人设启动闸**(multi-account-node-support D3):非 `default` 且未绑人设的账号被启动闸拦下、不开浏览会话——于是昵称采集**永远不触发**,该账号真名恒为 NULL,后台账号列只能回落显示原始 userid。

这是错的:采真名只需要「登录态 + 一次本人主页访问」,**不需要人设**(人设只决定浏览/发布的行为偏好,与读自己的名字无关)。真名采集应是**登录后的固定引导步骤**,不应被人设闸阻断。

真机案例:账号 `66cd1d4f…` 先连上(未绑人设被闸拦)→ 后补绑人设 → 但绑人设不重新驱动会话(且生产未带 auto-start-on-persona-bind)→ 采集从未触发 → 后台显示 ID。

## What Changes

- 真名采集从**浏览会话开始**解耦为**登录引导步骤**:账号登录(edge hello)后,只要它是真实 userid(非 `default`)且 `accounts.nickname` 为 NULL,云端 SHALL 驱动**恰一次**本人主页采集——**即便诚实人设启动闸因未绑人设拒绝开浏览会话**。
- **红线保持不变**:这条登录采集路径**只接「访问本人主页」一个动作**(`profile_open{direct}` → 读 → 单写),**MUST NOT** 接浏览反应链。未绑人设的账号采完真名即闲置、**绝不**在默认人设上浏览/点赞/关注/评论。绑了人设的账号行为不变(浏览会话照常,采集随会话开始触发同一采集体)。
- 沿用 account-real-nickname 的全部安全约束:恰一次/幂等(采到即不再绕)/~20s 兜底超时/登录态才采(采空诚实留空 + 有界退避)/风控·预算中性/edge 纯执行。
- 全局调度关闭(`/dispatch` off)时 MUST NOT 驱动边端(运营显式暂停一切,连采集也不动)。

## Capabilities

### Modified Capabilities

- `accounts-master-data`: 修改「账号平台真实昵称由云端角色驱动本人主页访问采集」要求——采集触发从「会话开始」改为「登录后引导步骤」,**MUST NOT 被人设启动闸阻断**;同时 MUST NOT 因此让未绑人设账号浏览(只接本人主页采集、不接浏览反应链)。

## Impact

- **cloud(aidcp-cloud)**:采集体(nickname_enricher)与其本人主页命令出口改为**永久接线**(独立于浏览会话);其依赖的边端上报(`page.cards`/`profile.detail`)本就由 handler 无条件上总线。dispatcher 在启动闸拦下未绑人设账号时调用采集体的登录引导触发。浏览反应链(contentEvaluator 等)仍只在会话激活时订阅(红线)。
- **不改**:edge;协议;风控/发布/概念表;`account_id` 主键;account-real-nickname 的持久化/展示/诚实空语义。
- **关系**:与同期 `auto-start-on-persona-bind`(绑人设自动唤醒已连接的被闸账号)互补——后者让「绑了人设的账号」无需重连即开跑;本改让「尚未绑人设的账号」也能在登录时采到真名。
