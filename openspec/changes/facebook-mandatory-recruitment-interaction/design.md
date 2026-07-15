## Context

现有人设只有自由文本 `engagement_rules` / `behavior_guidelines`。浏览闭环实际由多层角色决定：`ContentEvaluator` 选卡、`ContentCuratorRole` 粗筛、`InteractionAppraiserRole` 决定点赞、`CommentAppraiser` 再过预算/冷却/热度/LLM，之后撰写、去 AI 味和 `CommentApprovalGate`。因此“必赞必评”会在至少五处被当作普通倾向覆盖。Facebook 又是 feed 就地点赞、detail 评论的两 surface 路径，不能靠临时点击脚本或账号 id 特判补洞。

本变更只改变 cloud 决策与评论授权；edge 已具备 note-scoped like/comment、目标归属与后置校验，不需要协议变化。账号风险状态仍由 cloud `RiskController` 单写。

## Goals / Non-Goals

**Goals:**

- 让运营员在单账号人设中显式声明“某类内容命中后必须做哪些互动”，并让该声明热加载。
- 对 Tianxing Bai 表达“越南招工帖 → like + comment”的站立授权；命中后普通质量克制、热度、模型自由选择、软预算、冷却与逐条人审不再否决。
- 免审评论先发可读通知再提交；通知、撰写、目标定位或平台确认失败时 fail-closed 并留下稳定原因。
- 不影响没有 `mandatory_interactions` 的账号，不影响 XHS 既有人审评论路径。

**Non-Goals:**

- 不承诺 LLM 对自然语言主题的 100% 识别率，也不把失败提交伪装为成功。
- 不绕过全局品牌安全、账号风险状态或分钟/小时/自然日硬配额。
- 不修改 edge 协议、Facebook DOM 定位器或桌面安装包。
- 不把账号名、账号 id、越南语关键词硬编码进业务代码。

## Decisions

### 1. 使用结构化、可选的人设规则，而非解析“必须/一定”自由文本

人设新增：

```yaml
mandatory_interactions:
  - id: "vietnam-recruitment"
    when: "Bài đăng tuyển dụng hoặc tuyển người tại Việt Nam"
    actions:
      - "like"
      - "comment"
    comment_guidance: "Bình luận bằng tiếng Việt, hỏi tự nhiên về lương, ca làm, địa điểm hoặc cách ứng tuyển."
    comment_approval: "auto_approve"
```

loader 限制规则数、id 格式/唯一性、文本长度、动作枚举与审批枚举；`comment` 规则必须同时含 `like` 且提供评论指引。缺字段或非法组合使整份 persona `persona_invalid`，绝不半生效。没有该字段时行为逐位不变。

拒绝的替代方案：

- **从 `behavior_guidelines` 搜“BẮT BUỘC/必须”**：语言相关、不可审计、改一句文案就漂移。
- **硬编码 Tianxing Bai / 越南招聘**：污染多租户架构，无法由运营员显式开关。
- **只加强 prompt**：后续硬门槛仍会否决，不能兑现“确定性动作”。

### 2. 复用详情粗筛 LLM 做唯一语义确认，并沿事件链透传结果

`ContentEvaluator` 只负责在卡片层优先打开“看起来可能命中”的内容；`ContentCuratorRole` 在拿到全文后把规则与全局品牌安全一起评估，输出已校验的 `mandatoryRuleId`。未知 id / 非法输出 fail-closed。

命中上下文（rule id、actions、comment guidance、approval mode）从 `quality.pass` 依次透传至 `reading.images_done`、`reading.done`、`interaction.completed` 和 `comment.*`。不使用 dispatcher 的旁路 `Set`：EventBus 同步嵌套 emit 已有过同级订阅顺序竞态，payload 透传才能保证本篇上下文与事件因果同源。

### 3. “一定”定义为确定性意图，绕过软策略但不绕过硬安全与真实执行

命中 `like`：`InteractionAppraiserRole` 不调点赞判定 LLM、不检查会话 likes 余额，直接 emit `interaction.completed{actions:['like']}`；dispatcher 对该 action 跳过动作冷却，但仍调用 `canInteract('like')`，仍由 edge 后置校验回执决定成功与记账。

命中 `comment`：`CommentAppraiser` 跳过会话/每日预闸、评论冷却、`likeCount > 300` 与评论 LLM，直接进入撰写。评论命令下发前仍调用 `canInteract('comment')`。这样普通克制与软节奏不再否决，但 `restricted/frozen`、硬配额或平台失败仍会诚实阻止真实写入。

### 4. 强制评论仍走撰写与去 AI 味；失败有界重试，不用模板伪造

`CommentComposer` 收到规则指引后把“本篇必须产一条具体评论”写入 prompt，并在模型弃权/空/超长时最多补一次重试。第二次仍失败则 `comment.skipped`，绝不回退到“支持一下/还招吗”之类固定模板，因为那会制造与内容无关的公开垃圾评论。

`CommentDeAiFlavor` 与反照搬护栏保留，且透传 mandatory context；清洗为空或仍近似照搬照常 fail-closed。

### 5. `auto_approve` 是账号人设里的站立授权，仍要求先通知成功

`CommentApprovalGate` 对普通评论继续逐条飞书审批。只有详情语义确认命中的结构化规则明确写 `comment_approval: auto_approve` 时，才走免审通知口：通知卡成功后 emit `comment.approved`；通知口未接线或发送失败则 `comment.skipped{reason:'auto_approve_notice_failed'}`，不下发 edge 评论。

通知口与既有排期评论 `auto_approve` 使用同一“先通知、后授权、失败关闭”范式，由 server 抽成共享闭包后分别注入 scheduler 与浏览 dispatcher。XHS 未配置规则时零变化。

## Risks / Trade-offs

- **[语义误判导致不该互动]** → 只在全文详情阶段确认，规则需稳定 id，未知输出拒绝；全局品牌安全优先级高于 mandatory rule。
- **[LLM 漏判使“看到”未命中]** → 选卡 prompt 优先规则候选、详情 prompt 显式输出 rule id并补测试；日志区分 `mandatory_match` 与普通路径。仍不宣称自然语言分类 100% 完美。
- **[强制互动频率过高]** → 仅绕过软预算/冷却，硬 `RiskController` 与平台真实失败仍生效；成功才计数。
- **[自动评论变成模板垃圾]** → 不提供硬编码文本兜底；保留内容落地、去 AI 味、反照搬和最多一次重试。
- **[通知与提交语义漂移]** → 通知携账号、目标与终稿；通知成功才授权，通知失败不提交。
- **[事件上下文在嵌套 emit 中丢失]** → mandatory context 随 typed payload 逐跳透传，不依赖并行共享集合。

## Migration Plan

1. 在独立 cloud worktree 完成可选 schema 与零配置回归测试。
2. 跑相关单测、acceptance、全量测试与 typecheck，提交并推送分支。
3. 通过 `scripts/land-change` 串行落到 clean `aidcp-cloud/master`，再次验证。
4. `scripts/deploy-target dev --check` 后按安全序列备份、rsync、重启并核健康；不碰同机 isales。
5. 通过 persona API 给 Tianxing Bai 加结构化规则，回读并用 role prompt 预览确认热加载。
6. 日志观测一次真实匹配；若无可安全观测的帖子，只记录“代码/配置已生效、真帖动作待观测”，不冒充已发生。

回滚：先从该账号 persona 删除 `mandatory_interactions` 即时恢复普通策略；代码回滚则回退 cloud master 到部署前备份并重启。无需 edge 回滚。

## Open Questions

- 无阻塞问题。未来若需要非文本/图片-only 招工识别，应单独引入视觉证据；本变更只基于当前卡片与详情真实文本/评论，不臆测图片内容。
