## Context

现有 `mode=creatable` 只用 `curated_content.content_type='image_text'` 和非空正文判断是否具备参考创作能力。客户与后台发起精选洗稿时都会先持久化 `delegated_tasks`，其 `source_constraints` 带 `curatedId` 和 `sourceId`；这条任务记录在排队、执行或失败后都会保留，正好表达“曾经触发过洗稿”，无需等待发布链形成稿件。

## Goals / Non-Goals

**Goals:**

- 默认向用户展示仍未生成过洗稿稿件的可创作灵感。
- 用真实持久化任务记录区分已创作和未创作，不依赖内存点击态或稿件生成结果。
- 保持筛选总数、分页和当前页一致，并维持账号隔离。
- 隐藏列表滚动条而不破坏滚动能力。

**Non-Goals:**

- 不改变精选准入、内容可创作判定或参考创作生成链路。
- 不改变稿件审核、发布状态机或“标题栏已成稿总数”的既有保守口径。
- 不迁移或删除历史数据。
- 不隐藏详情页或整个内容工作区的滚动条；只处理灵感库列表右侧滚动条。

## Decisions

### 1. 客户筛选枚举改为 `uncreated | created | all`

Edge 默认传 `uncreated`，新 UI 只发送三种新枚举。为保证 Cloud 与桌面客户端可滚动发布，Cloud 暂时兼容旧 `creatable`，并精确保留其原语义（全部正文非空图文，即 `uncreated ∪ created`）；未知值仍明确拒绝。`all` 保持精选池全量语义，标题栏汇总继续复用它。兼容别名不出现在新客户端标签或状态中。

### 2. “已创作”以持久化洗稿触发记录为准

Cloud 在 `curated_content` 查询中使用账号约束的 `EXISTS`：

- `delegated_tasks.account_id = curated_content.account_id`；
- `delegated_tasks.action = 'publish_post'`；
- 优先以 `source_constraints.curatedId` 匹配精选行 id；对没有该 id 的历史任务，以同账号 `sourceId` 回退匹配。

`created` 要求“原可创作条件 AND EXISTS”；`uncreated` 要求“原可创作条件 AND NOT EXISTS”；兼容 `creatable` 只要求原可创作条件；`all` 不加创作能力或触发条件。任务状态不参与筛选：任务一经成功持久化，排队中、执行中、已完成、已取消或后续失败都属于“已创作”。客户端按钮点击但服务端未写入任务时仍属于“未创作”，避免用本地乐观状态编造触发成功。

### 3. 筛选下推 SQL

存储方法接收具名 `creationStatus`，把创作能力和 `EXISTS` 条件都放入主列表与 offset 越界补 COUNT 的相同 WHERE。不得先分页再在内存中过滤。

### 4. 只隐藏视觉滚动条

`.curated-list` 保留 `overflow-y: auto`，补充 Firefox 的 `scrollbar-width: none` 与 WebKit/Blink 的 `::-webkit-scrollbar { display: none; }`。DOM、焦点与 `scrollTop` 恢复逻辑不变。

## Risks / Trade-offs

- **历史任务缺少精选 id**：以同账号 `sourceId` 回退，既覆盖旧任务又不跨账号串数据。
- **JSONB 关联查询成本**：精选池与委派任务均按账号先收窄，使用 `EXISTS` 避免重复行，并为 `curatedId` / `sourceId` 增加按账号的局部表达式索引；通过存储 SQL 测试锁定账号谓词和一致 COUNT。
- **旧客户端仍发送 `creatable`**：Cloud 在滚动发布期按旧语义兼容，避免 Cloud 先上线时打断旧客户端；新客户端不再产生该值。

## Migration Plan

无数据迁移。先集成并验证 Cloud 与 Edge；Cloud 可先部署 dev（兼容旧值），再发布客户端代码。回滚新客户端时旧筛选仍可工作。
