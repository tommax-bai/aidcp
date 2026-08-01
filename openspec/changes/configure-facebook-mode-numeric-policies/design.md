## Context

当前普通 Reel 点赞使用固定 `0.25`，Reel 关注使用固定 `0.10`。点赞函数还覆盖 Feed 视频；关注只覆盖 Reel。规则和消费模式会跳过这两条普通决策，但慢启动不会，因此慢启动仍会复用普通人设的 Reel 点赞/关注。Cloud 已有 target-global Facebook operation policy 与管理后台编辑器，适合作为这些数字的唯一配置权威。

## Goals / Non-Goals

**Goals:**

- 普通人设 Reel 点赞只能在 `mode=persona` 时执行。
- 四种模式的 Reel 关注频率互相独立，普通人设另有独立 Reel 点赞频率。
- 只统计当前会话内首次出现的、单卡、规范 `/reel/<id>` Reel。
- 配置只在现有管理后台全局数值入口维护，并由 Cloud 严格校验与审计。

**Non-Goals:**

- 不改变规则模式每 N 个确认浏览点赞、消费模式浏览到点赞/入群/评论的既有持久节奏。
- 不给慢启动增加 Reel 点赞频率；慢启动仍由其既有人设互动与配额上限裁决点赞。
- 不修改普通 Feed、Feed 视频或详情页策略。
- 不新增客户、账号、环境覆盖，不开放动作、Prompt、顺序、概率或安全闸配置。
- 不构建或发布 Edge 安装包，不执行真实 Facebook 动作验收。

## Decisions

### 1. N 表示本会话第 N 个唯一 Reel，而不是概率倒数

RoleDispatcher 按当前有效模式维护会话内唯一 Reel 访问序号。只有单卡 `listKind='reels'` 且 noteId 为规范 Facebook Reel 的首次上报计数；重复上报、Feed、Feed 视频、详情页、无效目标均不计数。达到 N 时产生一次动作意图，随后从新的 N 段继续计数。会话重启按既有普通 Reel 决策边界清零，不跨账号或连接搬运计数。

达到 N 后若预算、RiskController、冷却、Edge 能力、作者、去重或下发闸拒绝，本次尝试诚实结束且不形成动作债；下一次机会仍需再访问 N 个该模式下的唯一 Reel。

### 2. 普通人设点赞与四模式关注分开裁决

全局策略新增：

- `reels.persona.viewsPerLike`，默认 4；
- `reels.persona.viewsPerFollow`，默认 10；
- `reels.slowStart.viewsPerFollow`，默认 15；
- `reels.rule.viewsPerFollow`，默认 15；
- `reels.consumption.viewsPerFollow`，默认 15。

全部为 `1..100` 整数。点赞路径只有 `mode=persona` 才读取 `reels.persona.viewsPerLike`。关注路径把 `persona|slow_start|facebook_rule|consumption` 映射到对应字段；未知、blocked、unsupported 或策略不可用时不计数、不下发。普通人设点赞仍把每个已处理 Reel 标为外部普通互动决策，避免后续 LLM 再给同一 Reel 做第二次普通点赞判断。

### 3. 新数字只属于 target-global policy

API-owner 追加 `0104` expand migration，在 `facebook_operation_global_policy` 增加五个受 CHECK 约束的整数列并以 4/10/15/15/15 回填。环境独立 cadence 不增加这些字段；所有环境都读取其 execution target 当前全局 Reel 策略。全局 PUT 使用现有 revision CAS、审计和写后回读，任何缺字段、额外字段、非整数或越界值整块拒绝。

### 4. 不改变动作成功口径

达到节奏只允许发送既有 note-scoped `like`/`follow` intent。只有 Edge 对同一 Reel/作者返回平台确认的新动作回执，Cloud 才记成功、扣会话预算并展示活动；already、ambiguous、submitted_unknown、失败、未开始均不计成功。

## Risks / Trade-offs

- [会话短于 N 导致本场无动作]：这是本会话节奏的明确结果；不引入跨会话持久动作债，避免重连后对已经离开的 Reel 补写。
- [规则/消费既有点赞与新增关注同一 Reel 同时到期]：两者是独立意图并继续分别通过现有动作闸和回执；关注不改写规则/消费的持久进度。
- [全局策略迁移未应用]：schema capability 失败关闭，Cloud 不回落编译期 N 值冒充配置已生效。
- [DEV/OL schema 兼容]：按现有部署门禁检查；共享数据库 gate 不兼容时只交付源码，不进行 DEV 迁移或部署。

## Migration Plan

1. 追加 0104 migration 与 schema ownership/version 声明，默认值逐位保持当前普通人设平均频率并为其它模式设 15。
2. 先部署能读写新列的 Cloud，再部署 Console；迁移与服务部署仅在 DEV/OL schema gate 兼容时进行。
3. 回滚只回退应用行为到 policy-aware 版本；不删除迁移。若需恢复数字，在管理后台写回 4/10/15/15/15。
