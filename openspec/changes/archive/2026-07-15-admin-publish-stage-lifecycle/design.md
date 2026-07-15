## Context

`GET /api/content/queue` 当前直接返回 `PublishOrchestrator.getStatus()`：生成中的 `runs`、聚合 `status/snapshot`，以及无生成轮时保留在内存中的最近终态快照。Console 再按五组黑板字段推断阶段，并以 `some(field exists)` 判定完成。该模型只能观察生成候审段，既不知道 `publish_log` 的待审/终态，也不知道 `PublishDispatcher` 是否正在下发，因此会产生过早完成和终态冒充活跃两类错误。

发布流程本身保持现状：生成候审段由 orchestrator 驱动，终稿落 `publish_log`，人工批准后由 dispatcher 下发。面板只读组合这些已有真相，不成为新的业务状态写入者。

## Goals / Non-Goals

**Goals:**

- 由 cloud 为后台提供稳定、可测试的八阶段生命周期投影。
- 区分正在生成、等待人工、正在下发和最近终态，终态不进入活跃集合。
- 在不改数据库 schema 的前提下，用已有运行态和持久化状态给出最强可证实结论。
- 保持旧 `status/snapshot/runs` 兼容和原始快照排障入口。

**Non-Goals:**

- 不改变生成角色依赖、图片重试、审批授权或平台下发序列。
- 不在本次增加飞书送达审计、通知路由修复或新的数据库事件表。
- 不伪造目前没有持久化的逐命令下发进度；平台下发阶段只承诺“未开始/在途/终态”和已有图片附着事实。

## Decisions

### 1. 云端组合生命周期投影，Console 不再解析黑板判阶段

`GET /api/content/queue` 新增 `lifecycle`：

- `active`：当前 orchestrator runs，以及 `publish_log.status = pending_approval` 的稿件。
- `recent`：最近若干条非活跃发布记录和无 record 的最近生成失败/跳过结果。
- 每个 journey 含稳定 id、账号、标题、来源类型、总状态、是否活跃、八个 stages、可选 recordId、原始 snapshot 引用。

旧字段原样保留，旧 Console 可继续工作。新 Console 只在 `lifecycle` 缺失时回落旧五阶段渲染。

选择云端组合而非 Console 同时请求后自行 join，是因为状态优先级和终态定义属于业务契约；多个客户端各自推断会再次漂移。

### 2. 状态真相按来源分层，不新增数据库迁移

真相优先级如下：

1. 当前生成：orchestrator run snapshot/status。
2. 人工审批与最终结果：`publish_log.status`。
3. 平台下发在途：`PublishDispatcher` 暴露只读的 in-flight record id 集合。
4. 图片附着：`publish_log.images_attached_count`。

`PublishDispatcher` 只新增快照式只读方法，不允许 panel 修改其 in-flight 集合。这样可以准确区分“待审批”和“已批准正在下发”，无需新增写路径或持久化表。

### 3. 八阶段允许分支并行，完成条件采用阶段终点而非任意字段

阶段固定为：

1. `source` 触发与选题
2. `content` 正文生成
3. `text_quality` 文本质检
4. `visual_plan` 视觉策划
5. `image_review` 出图复核
6. `package` 成稿封装
7. `approval` 人工审批
8. `dispatch` 平台下发

阶段状态支持 `pending/running/retrying/waiting_human/completed/partial/failed/skipped`。正文产出后，文本质检与视觉策划可同时为 running；视觉策划完成后才进入出图复核；文本与图片分支均收敛后进入成稿封装。

生成阶段的完成条件使用该阶段必需终点字段集合；`pipelineAbort.role` 映射到具体失败阶段。无法从现有数据证明的事实保持 pending，不用字段存在推断成功。

### 4. 持久化稿件负责审批与下发阶段

- `pending_approval` 且不在 dispatcher in-flight：审批 `waiting_human`，下发 `pending`。
- `pending_approval` 且在 in-flight：审批 `completed`，下发 `running`。
- `needs_review`：审批 `failed`（已驳回），下发 `skipped`。
- `published`：审批与下发 `completed`。
- `submitted`：审批 `completed`，下发 `partial`，明确“已提交，链接未确认”。
- `failed`：审批 `completed`，下发 `failed`；正文提示提交是否可由已有证据确认，不能确认时不声称已发布。
- `draft`：审批与下发 `skipped`。

活跃集合只包含 running/waiting_human/in-flight；终态只进入 recent。服务重启后 dispatcher in-flight 会自然为空，`publish_log` 仍能恢复待审与终态真相。

### 5. Console 使用“活跃稿件 / 最近结果”双区展示

发布队列卡顶部显示活跃数量和总状态。活跃稿件可切换查看；无活跃稿时不再展开假进度。最近一条终态单独显示为“最近结果”，其失败/部分完成横幅优先说明“是否已发布”。八阶段使用可横向滚动的卡片或网格，阶段详情显示摘要、进度和事实；原始 snapshot 仍在折叠区。

## Risks / Trade-offs

- [下发阶段没有逐命令持久化] → 本次只显示 in-flight 与最终状态，附着图片数按已有账本展示；不编造“标题已填”等没有 API 证据的细节。
- [运行快照与新落库稿件存在极短重复窗口] → 以 snapshot 中的 `publishResult.recordId` 去重；无 recordId 时保留生成 run，避免错误合并同账号并行稿件。
- [旧 cloud 与新 console 滚动发布期间字段缺失] → Console 保留 legacy 回落；API 为纯字段新增，可先部署 cloud 后部署 console。
- [pending 草稿数量较多] → API 对 active 待审集合使用既有按状态查询，Console 使用选择器而非无限铺开所有详情。

## Migration Plan

1. 在 cloud 实现投影纯函数、dispatcher 只读 in-flight 接口和 panel API 组合，并跑单测/typecheck。
2. 部署 cloud 到 `dev`，确认旧 Console 仍可读取旧字段。
3. 在 console 增加 DTO 与八阶段展示、legacy 回落，并跑测试/build。
4. 发布 console 静态资源到 `dev`，验证活跃、待审、下发中、失败和空闲五类页面状态。
5. 回滚时先回滚 console（继续使用旧字段），再回滚 cloud；无数据库迁移需要撤销。

## Open Questions

无。本次不承诺逐命令下发明细，后续若需要应由 CommandSequencer 产生可持久化事件，而不是由后台猜测。
