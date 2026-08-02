## Context

现有 Facebook Reel 节奏由 Cloud 全局 operation policy 持久化，`RoleDispatcher` 只对当前会话、当前有效模式下首次出现的规范单卡 Reel 计数。普通人设同时有点赞与关注阈值，冷启动、规则和消费模式目前只有关注阈值。Console 已在同一全局编辑器中展示这些 Reel 节奏和冷启动 7 天逐日上限。

本次变更跨 Cloud 数据模型/API/运行时与 Console 管理界面，但不需要新的 Edge 动作、协议字段或账号级配置。Cloud 仍是频率与动作意图的唯一裁决者，Edge 只执行已有 note-scoped Reel 点赞命令并回报可验证结果。

## Goals / Non-Goals

**Goals:**

- 让内部管理后台可以全局配置冷启动模式“每浏览 N 个唯一 Reel 点赞一次”。
- 保持 Reel 点赞计数按模式、会话和规范 Reel 身份隔离，并复用现有风险、配额、冷却、去重和后置确认门禁。
- 用向后兼容迁移给既有 DEV/OL 全局策略补充值为 `15` 的字段，避免升级时出现空值或运行时猜测。
- 保持 Console 写入全量、严格、带 revision 的 write-after-read 真态。

**Non-Goals:**

- 不改变冷启动总天数、逐日 view/like/comment/follow/publish/search/joinGroup 上限或增加天数时复制末日上限的行为。
- 不给规则模式或消费模式增加 Reel 点赞节奏，不新增账号、客户或环境级覆盖。
- 不改变 Feed、Feed 视频、详情页或搜索的点赞策略，不修改 Edge、协议 v2 或已安装客户端。
- 不把点赞意图下发、already、pending、ambiguous 或 submitted-unknown 记为平台成功。

## Decisions

### 1. 在现有全局 Reel cadence 对象中扩展 `slowStart.viewsPerLike`

Cloud 数据库增加一个非空整数列，默认 `15` 且约束 `1..100`；策略 DTO、bounds 和 Console 类型使用 `reels.slowStart: { viewsPerLike, viewsPerFollow }`。这样与普通人设结构和现有管理入口一致，也能继续通过全量对象与 revision 做原子更新。

替代方案是在冷启动逐日上限中增加频率字段，或增加环境级字段。前者混淆“每日最多多少次”和“每多少次浏览触发一次”，后者违反当前全局策略边界，因此不采用。

### 2. 复用当前模式的唯一 Reel ordinal，同时独立判断点赞和关注边界

冷启动不增加第二套浏览计数。每个合格 Reel 只推进一次当前模式 ordinal，然后分别计算 `ordinal % viewsPerLike` 和 `ordinal % viewsPerFollow`；两个阈值同刻命中时允许各产生一个既有动作意图，各自独立通过预算、风险、冷却与发送门禁。

这保持普通人设当前的双动作语义，也避免两个计数因重复上报或模式切换发生漂移。未命中、被门禁拒绝或结果失败都不形成补写债。

### 3. 将 Reel cadence 点赞分发从 persona 专用泛化为显式模式分发

`RoleDispatcher` 仅在 `persona` 或 `slow_start` 的 cadence 中存在合法 `viewsPerLike` 时允许点赞。日志 reason 使用可审计的模式化名称，测试覆盖慢启动命中、其它模式不获授权、模式隔离、门禁拒绝和会话边界。

不通过可选字段缺失来默许慢启动点赞；Cloud 的策略解析必须提供完整合法值。这样 schema 未应用或读模型陈旧时会失败关闭，而不是回退到概率或 Edge 常量。

### 4. Console 将点赞和关注放在“冷启动全局上限”同一行

编辑器在当前关注阈值前增加点赞阈值，并扩展摘要、校验、保存 payload 与测试。总天数和每日上限仍是独立对象，增加天数时继续复制当前最后一天上限。

## Risks / Trade-offs

- [Cloud 代码先于数据库迁移运行会读取不到新列] → 保持 migration/schema gate 顺序；运行时不为缺列或缺值伪造默认值。
- [点赞与关注阈值相同会在同一个 Reel 同时产生两个意图] → 这是两个独立可配置节奏的确定性结果；每个动作继续独立受预算、风险、冷却、能力和平台确认约束。
- [全量 PUT 客户端遗漏新字段会导致旧页面保存失败] → 内部管理 Console 与 Cloud 同批升级，Cloud 对缺失/额外字段严格拒绝，避免部分覆盖；不承诺旧 Console 对新 schema 的写兼容。
- [新增自动点赞提高真实平台动作量] → 默认频率与现有冷启动关注一致且仍受逐日点赞上限和所有既有门禁限制；本地验证不冒充真实账号验收。

## Migration Plan

1. 应用 Cloud 迁移，为每个 `execution_target` 的全局策略补充 `slow_start_reel_views_per_like = 15` 和范围约束。
2. 部署读取/写入新字段并执行冷启动 cadence 的 Cloud 版本，验证 schema gate、策略回读和运行时测试。
3. 部署匹配新 schema 的 Console 静态资源，验证读取、编辑、冲突与严格校验。
4. 回滚应用代码时保留新增列；列的默认值与约束不会改变旧代码读取的字段，避免破坏性回迁。若新策略已保存，旧 Console 只是不展示该字段。

## Open Questions

无。兼容默认值采用与当前冷启动 Reel 关注相同的 `15`。
