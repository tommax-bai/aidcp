## Why

管理后台「运行监控」页的「按笔记互动」表当前只对运营有限可用：笔记列只显示一串裸笔记 id（不可读、点不开），评论虽计入配额但从不出现在表里，关注根本进不了表（它针对作者、不针对笔记，而底层去重表强制按笔记 id 建主键），动作列是无色标签难区分。运营看不清「这个账号到底对哪些内容、哪些作者做了什么」。本次把这张表升级成一个诚实、可读、可跳转的互动流。

## What Changes

- **四类动作齐全**：点赞 / 收藏 / 评论 / 关注都进入面板互动流（当前只有点赞 / 收藏）。评论按笔记归属，关注按作者归属。
- **可读 + 可跳转的目标**：笔记动作显示笔记标题，点击跳转到带 `xsec_token` 的真实笔记详情页；关注显示作者昵称，点击跳转到作者主页。
- **诚实置空红线（不可妥协）**：抓不到带 token 的真实链接、抓不到标题 / 昵称时，**一律置空、绝不用裸 id 拼一个打不开的假链接**（沿用发布链 `postUrl` 既有约定）。
- **动作配色**：动作列改为按类型着色的标签，便于区分。
- **新增云端两表**（迁移 0019）：`interaction_feed`（事件流，面板读它）+ `interaction_target_meta`（标题 / 链接旁表，按目标 id，读时 join）。**`risk_interactions` 完全不动**（它仍作去重台账，但不再是面板数据源）—— 零回归。
- **协议仅加可选上报字段**：详情页上报 +`url`，作者主页上报 +`nickname` +`url`。**不新增消息类型、不新增 cloud→edge 命令** → 不动指令映射、不动边缘主动命令白名单。
- **边缘新增诚实抓取**：进笔记详情 / 进作者主页时读取真实地址栏 URL；作者主页额外从 DOM 抓真实昵称。

## Capabilities

### New Capabilities
- `panel-interaction-feed`: 管理后台互动流的端到端契约——记录四类动作（笔记动作按笔记、关注按作者）、以标题 / 昵称 + 真实可点链接展示、诚实置空不造假链接、动作按类型着色；并约束其底层存储为「事件表 + 元数据旁表、读时 join」、与去重台账解耦。

### Modified Capabilities
<!-- 无。risk_interactions 去重 / 归因行为不变，故 interaction-attribution 既有要求仍成立；console-panel-api 既有要求（独立端口 / JWT / 只读聚合 / WS 隔离）亦不变。本变更只新增契约，不改写既有要求。 -->

## Impact

- **aidcp-cloud**：迁移 0019（两张新表，`IF NOT EXISTS`）；`src/comm/protocol.ts`（+可选上报字段，须与 edge 逐字一致）；`src/comm/handler.ts`（暂存当前作者 id、upsert 元数据、互动事件带目标 id、不再排除评论 / 关注）；`src/agents/session-context.ts`（+`currentAuthorId`）；`src/server.ts`（互动事件写 `interaction_feed`，纯观测、不碰风控终态）；`src/panel/panel-store.ts` + `src/panel/types.ts`（读新表 + join，响应增 `targetId/title/url`、动作扩到四类）；`panel-store.test.ts` + 新增 AC-PANEL 验收。
- **aidcp-edge**：`src/comm/protocol.ts`（与 cloud 逐字一致）；`src/browse/browse-session.ts`（详情 / 主页读 `location.href`，诚实置空）；`src/browse/note-extractor.ts`（作者昵称抽取）；边缘验收用例（无 token → `url` 不造假）。
- **aidcp-console**：`src/types/api.ts`（`PanelInteraction` +`title?/url?`、动作 union +`follow`）；`src/types/aidcp-enums.ts`（新增 `RISK_ACTION_COLOR`）；`src/pages/MonitorPage.tsx`（动作着色标签 + 目标列标题可点链接 + token 时效提示）。
- **关联但不改写**：`console-panel-api`（互动接口仍是其下的只读聚合接口）、`interaction-attribution`（`interaction.occurred` 归因不变，去重表落地不变）、`author-profile-visit`（主页访问行为不变，仅多带回 url/昵称）、`docs/protocol.md`（改既有上报行说明，消息类型计数不变）。
- **已知局限（诚实披露，非缺陷）**：`xsec_token` 有时效，较旧的笔记链接会失效（重开笔记时元数据 COALESCE 刷新最新 token，UI 提示「链接可能过期」）；`interaction_feed` 从零开始、不回填历史 `risk_interactions`；裸 `/user/profile/<id>` 假定无需 token 可开 —— 待真机校验，不可靠则诚实置空。
- **协调**：跨 edge + cloud + console 三仓 + 迁移 + ECS 部署；本机有并发会话在 edge / cloud 改动中（不在本变更涉及的 `protocol.ts` / `browse-session.ts`），只暂存自己的文件，迁移用 `IF NOT EXISTS` 防并发抢号。
