## ADDED Requirements

### Requirement: 参照洗稿参考图上限对齐精选快照

参照洗稿在选择“带图参考”时，发布链路 SHALL 从触发时的来源笔记快照中携带最多 9 张可用参考图，且该上限 SHALL 统一应用于调度器冻结、图片 prompt guidance、图片 provider 输入和发布审计。系统 MUST 先过滤无可用 `ossUrl` 或 `sourceUrl` 的图片；普通发布与“仅文本参考”模式 MUST NOT 编造参考图。参考图只可作为生成阶段视觉指导，MUST NOT 直接复用或发布原图。

#### Scenario: 来源有九张参考图时新草稿审计九张
- **WHEN** 管理员对一条拥有 9 张可用参考图的精选图文触发带图参照洗稿
- **THEN** 发布链路冻结最多 9 张参考图，图片 provider 输入最多 9 张参考图，发布记录的参考图审计 `requestedCount` 和 `usableCount` 反映实际携带数量

#### Scenario: 来源超过上限时有界截断
- **WHEN** 参照输入包含超过 9 张可用参考图
- **THEN** 系统只携带前 9 张可用参考图，后续图片不进入 prompt guidance、provider 输入或本次发布审计

#### Scenario: 仅文本参考不携带图片
- **WHEN** 管理员在参照洗稿确认弹窗选择仅文本参考
- **THEN** 发布链路不携带参考图，发布记录不显示“已使用参考图”或参考图数量
