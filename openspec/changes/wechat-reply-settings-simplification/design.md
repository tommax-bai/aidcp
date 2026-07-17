## Context

当前 Console 直接暴露冻结 DTO 的 `mode`、`generateDrafts`、`sendReplies`、渠道 `allowAutoSend` 与规则 `allowAutoSend`。这些字段在 Cloud 中承担不同范围的判定，但普通管理员看到的是连续多次“允许”，并可保存不会产生预期效果的组合。即时 runtime controls 又与版本化策略相邻，进一步让“长期策略许可”和“立即停写”看起来像重复开关。

本变更只调整 Console 的意图表达和确定性映射。Cloud 仍消费原 DTO，Edge、数据库、API schema、RiskController 与发送状态机均不改变。

## Goals / Non-Goals

**Goals:**

- 让管理员只选择一次账号级回复处理方式，不能从 UI 生成矛盾的 `mode/generateDrafts/sendReplies` 组合。
- 保持账号、渠道、规则三层约束的单调性：上层确定自动化上限，下层只能收紧。
- 清楚区分版本化回复策略、立即生效的 runtime controls、只读 Cloud 硬门禁和无副作用预览权限。
- 对已存在的非规范组合 fail closed，绝不因打开抽屉或保存而静默扩大写权限。

**Non-Goals:**

- 不删除 Cloud 的 `sendReplies`、runtime controls 或任何硬门禁。
- 不修改 frozen DTO、internal API、WS v2、数据库或 Edge 行为。
- 不开放图片私信、DM AI、真实账号写验证或新的角色权限。

## Decisions

### 1. 用四态 UI preset 映射现有三字段

Console 新增仅供展示的处理方式：

| 处理方式 | `mode` | `generateDrafts` | `sendReplies` |
| --- | --- | ---: | ---: |
| `off` 不自动处理 | `draft_only` | false | false |
| `draft` 只生成草稿 | `draft_only` | true | false |
| `review` 人工审核后发送 | `review_before_send` | true | true |
| `auto` 低风险模板自动发送 | `auto_safe` | true | true |

保存仍调用现有 policy PUT，不增加前后端字段。加载历史非规范组合时使用不扩权归一化：`generateDrafts=false` 显示 `off`；`sendReplies=false` 或 `mode=draft_only` 显示 `draft`；只有生成与发送均开启时才显示 `review/auto`。保存后写回对应规范组合。

备选方案是修改 Cloud schema 为单一枚举。它会扩大跨仓协议、migration 和兼容范围，而当前问题可以由 Console 确定性适配解决，因此拒绝。

### 2. 渠道和规则只表达范围或收紧条件

渠道 `enabled` 改称“处理该渠道的互动”，明确关闭后仍可由独立读取开关继续同步。渠道 `allowAutoSend` 只在账号处理方式为 `auto` 时展示，表达“此渠道的低风险模板可自动发送”。

规则编辑器把底层 `allowAutoSend` 反向呈现为“此规则必须人工审核”。勾选表示写入 `allowAutoSend=false`；未勾选只表示继承账号与渠道的自动化上限，不承诺一定自动发送。规则启用 AI 润色时同时收紧为 `allowAutoSend=false`，并禁用取消人工审核，符合现有硬门禁。

### 3. 即时开关与策略分区但不删除

runtime controls 保留独立 CAS 和立即生效语义，区域标题与提示明确为“紧急运行控制”。账号写总闸、评论回复和私信文本发送继续作为即时刹车。策略卡只描述发布后对新 job 生效的长期处理方式。

Cloud 硬门禁继续只读展示。Console 不增加任何“关闭硬门禁”交互，也不把它们混入普通策略选项。

### 4. 保留 draft/published 发布边界

策略的保存与发布不是重复授权：保存只更新可编辑 draft，发布才原子切换 immutable published 版本。因此本变更保留 CAS、局部保存、发布确认与审计，只简化发布摘要为用户选择的处理方式及当前即时写状态。

### 5. 预览权限错误解释为访问控制而非运行结果

预览仍只调用 Cloud `reply-preview`。403 文案明确说明预览没有运行；评论需要 `interaction.config.preview`，私信还需要 `interaction.dm.view_full`。权限提示不进入发送策略或硬门禁列表。

## Risks / Trade-offs

- [历史非规范配置被收紧归一化] → UI 明确按不扩权规则选择 preset；测试断言保存不会把 false 变为 true，除非管理员主动选择更高处理方式。
- [隐藏底层字段降低排障可见性] → 发布确认显示映射后的处理方式，审计和 API DTO 仍保留底层字段，开发者可从服务端真态排障。
- [规则反向文案导致布尔映射出错] → 用纯函数和单测覆盖 `mustReview = !allowAutoSend`，AI 润色路径强制人工。
- [渠道自动设置在非 auto 模式下成为 dormant state] → 非 auto 模式不展示且不生效；重新选择 auto 时发布摘要重新暴露渠道自动范围，最终仍受 Cloud 全部门禁。

## Migration Plan

1. 在 Console worktree 实现 preset 映射、分区和文案，不改 API。
2. 用组件测试覆盖四态映射、历史组合 fail-closed、渠道上下文显示、规则人工映射、预览拒绝文案。
3. 运行 focused tests、Console 全量测试与 build；严格校验 OpenSpec。
4. 合入 Console `master` 并部署 `dev`；出现回归时回滚 Console 静态产物即可，Cloud/Edge 无需回滚。

## Open Questions

无。当前产品只需要账号级处理方式加渠道级自动范围；不引入每渠道独立的完整运行模式。
