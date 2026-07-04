# Proposal: 内容页展示参照洗稿来稿件

## Why

管理后台「精选」页已经可以对单条精选图文触发参照洗稿，生成后的草稿或已发布记录会出现在「内容」tab。但当前内容列表只展示发布稿本身，运营无法从发布历史里看出哪一条是参照洗稿触发，也无法点开查看当时参考的来稿件。

这会带来两个问题：

- 审核与复盘时缺少来源上下文，只能回到精选池或飞书消息里猜来源。
- 精选行之后可能被删除、清理或更新，发布历史不再能稳定回答「这篇当时参考的是哪篇」。

## What Changes

- 参照洗稿触发发布时，云端把触发时的来稿快照随发布记录持久化，作为发布血缘的一部分。
- `GET /api/content/published` 在发布记录投影中加性返回来稿快照字段，仅参照洗稿记录有值，普通发布为 `null`。
- 管理后台「内容」tab 在发布内容列表中标识「洗稿来源」，点击可查看来稿件详情；发布详情浮层中也提供同一入口。
- 来稿件详情展示标题、作者、正文、话题、原精选 sourceId 和可用来源链接；缺链接时诚实显示无链接，不渲染死链。

## Non-goals

- 不改变参照洗稿的生成 prompt、非照抄红线、人审闸或发布下发行为。
- 不把普通精选素材抽样消费都展示为「洗稿来源」；只有人工/旁路指定单条 `referenceNote` 的发布记录展示来稿件。
- 不要求从当前 `curated_content` 实时 join 回源行；展示以触发时快照为准。
- 不新增 edge 协议或边缘端能力。
- 不实现相似度查重或版权风险打分。

## Impact

- **aidcp-cloud**：扩展参照触发输入与 `publish_log` 持久化字段；发布记录面板投影返回来稿快照。
- **aidcp-console**：扩展 `PanelPublish` DTO 镜像；内容页列表和详情浮层展示可点击来稿件。
- **OpenSpec**：更新发布管线、面板 API、精选行级动作的加性契约。

## Validation

- `openspec validate publish-reference-source-panel --strict`
- 后续实现阶段：
  - cloud：publish log/store、panel store、curated action 接线、DTO 对拍或单测、typecheck
  - console：ContentPage 行展示和弹窗测试、typecheck/build
