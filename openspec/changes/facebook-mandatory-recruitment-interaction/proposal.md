## Why

Tianxing Bai 的人设已写成“越南招工帖必赞必评”，但当前浏览闭环仍把这句话只当 prompt 倾向：点赞可被互动判定判 `pass`，评论还会被热度门槛、评论判定、冷却、会话预算和逐条人审挡掉，因此配置语义与真实动作不一致。需要把运营员显式写入账号人设的“强制互动”升级为结构化、可验证的运行时合同，命中后不再由普通克制策略二次否决。

## What Changes

- 为账号 soul 新增可选的结构化 `mandatory_interactions` 规则：稳定 id、语义匹配条件、强制动作集合、评论写作指引和显式审批模式。
- 选卡与详情粗筛读取强制规则；详情确认命中后把规则上下文沿深读事件链透传，避免并行订阅竞态或二次语义判断不一致。
- 命中 `like` 后跳过普通点赞 LLM、会话软预算与冷却，确定性产生点赞意图；仍经过账号 `RiskController`，且只按 edge 真成功回执记账。
- 命中 `comment` 后跳过评论热度门槛、评论 LLM、每日评论预闸、会话软预算与冷却；评论撰写按规则指引生成，`auto_approve` 仅在免审通知成功后直通，通知失败则 fail-closed。
- 保留全局品牌安全、账号风险状态、分钟/小时/自然日硬配额、目标定位、验证码与提交后置校验；任何拦截或执行失败必须如实记录，绝不把“已决定必做”伪报成“真实成功”。
- 把 Tianxing Bai 的 dev 人设改为显式的“越南招工 → like + comment，auto_approve”，部署后热加载并核对实际角色 prompt/日志。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `account-persona-config`: 人设格式新增经严格校验、可热加载的结构化强制互动规则。
- `interaction-appraisal`: 强制点赞命中后成为普通选择性互动与软预算/冷却的显式例外，但不绕过硬风控与真实回执。
- `comment-interaction`: 强制评论命中后绕过普通热度/判定/逐条人审，显式免审必须先成功发送通知。
- `interaction-cooldown`: 强制互动规则成为动作冷却的显式、仅规则命中范围内的例外。

## Impact

- `aidcp-cloud`: soul 类型/加载/序列化、内容选卡与粗筛、浏览事件 payload、点赞/评论角色、评论审批通知接线、dispatcher 与 server 装配。
- `aidcp` control repo: 上述四份能力规格的 delta、设计、任务与 dev 验证记录。
- 无 edge 协议变化；edge 继续执行现有 note-scoped like/comment，并以真实后置校验回执决定是否成功。
- 运行时目标为 `dev`；不涉及 `ol`，不构建 Edge 安装包。
