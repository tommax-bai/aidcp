# Design: 内容页展示参照洗稿来稿件

## 1. 现状依据

- 参照洗稿已经由精选页行级动作触发，`curated-note-actions` 要求单条精选笔记以独立 `referenceNote` 注入完整发布链，并保留人审闸。
- cloud 现有 `TriggerInput.generateInput.referenceNote` 只有 `sourceId/title/body/topics/author`，用于 prompt 注入；发布落库血缘目前只记录 `source_concepts` 和 `source_liked_ids`。
- 内容页数据来自 `GET /api/content/published`，cloud `PanelPublish` 与 console `PanelPublish` 已包含标题、正文、账号、状态、图片和详情链接，但没有参照来源字段。
- console `ContentPage` 已经有整行点击打开发布详情浮层的交互，可在该浮层内复用展示入口。

## 2. 数据模型

在 `publish_log` 增加一个加性 JSONB 字段，建议命名为 `source_reference`：

```json
{
  "kind": "curated_reference",
  "curatedContentId": 123,
  "accountId": "acc-1",
  "sourceId": "xhs-note-id",
  "title": "原笔记标题",
  "body": "触发时来稿正文快照",
  "author": "原作者",
  "topics": ["话题1"],
  "sourceUrl": "https://...",
  "capturedAt": 1783180000000
}
```

设计要点：

- 写入时机：生成候审段 `publish_log` insert 同步写入；若本次发布因无图等在生成段直接落 `failed`，也应保留同一来稿快照，方便排障。
- 快照权威：内容页展示只读 `publish_log.source_reference`，不依赖当前 `curated_content`。精选行删除、更新或清空后，历史记录仍能查看当时来稿。
- 普通发布：字段为 `NULL`，前端不展示来源入口。
- 体积控制：来稿正文可设置有界上限，但 prompt 截断与展示快照要分离。推荐保留一个足够审核查看的正文快照，并在 prompt 构造处继续按现有上限截断，避免为了 UI 回显扩大模型输入。
- 兼容图片参考：若 `curated-reference-images` 落地并在 `referenceNote` 携带图片引用，`source_reference` 可加性带 `images`，但本 change 的最小闭环只要求文本来稿可查。

## 3. API 投影

扩展 cloud 与 console 的 `PanelPublish` 镜像，新增：

```ts
sourceReference: null | {
  kind: 'curated_reference';
  curatedContentId: number | null;
  accountId: string;
  sourceId: string;
  title: string | null;
  body: string | null;
  author: string | null;
  topics: string[];
  sourceUrl: string | null;
  capturedAt: number;
};
```

`GET /api/content/published` 保持同一端点、同一分页与账号过滤；新增字段是加性的。查询仍以 `publish_log` 为主表，按账号过滤继续走 `publish_log.account_id` 索引，不为了来源展示 join `curated_content`。

## 4. 触发链路

精选页 `POST /api/curated/contents/:id/create-post` 读到行后，传给发布调度器的参照对象需要补齐展示血缘字段：

- `curatedContentId`: 精选行 id
- `accountId`: 行归属账号
- `sourceUrl`: 原来源链接，可空
- `capturedAt`: 触发时刻
- 原有 `sourceId/title/body/topics/author`

发布调度器继续把参照作为 `referenceNote` 进入既有发布链；`PublishExecutor` 从 trigger 上读取 `referenceNote`，写入 `publish_log.source_reference`。普通 `/publish` 手动触发或自动发布没有 `referenceNote`，不会写来源。

## 5. UI 方案

内容 tab 列表：

- 新增窄列「来源」或在标题列副信息中展示 `Tag("洗稿") + sourceReference.title`。
- 只有 `sourceReference != null` 的行展示；普通发布不占明显视觉噪声。
- 点击来源标签或标题时 `stopPropagation`，直接打开「来稿件」弹窗；点击整行仍打开发布稿详情。

发布稿详情浮层：

- 在标题/正文/元信息附近展示一条「洗稿来源：<来稿标题>」。
- 点击同样打开「来稿件」弹窗。
- 来稿件弹窗展示：作者、标题、正文（保留换行）、话题、sourceId、触发快照时间、来源链接按钮。
- `sourceUrl` 为空时显示「无来源链接」禁用按钮；有链接时新标签打开并加 `rel="noopener noreferrer"`。

交互口径：

- 「洗稿来源」只表示本发布记录由单条参照来稿触发，不宣称内容已照搬，也不绕过现有审核。
- 待审、已发布、失败、已否决状态都可展示来源；状态不影响来源查看。

## 6. 风险与取舍

- 只存 `curated_content.id` 的方案被否决：精选行可能被删除或改写，历史会断链。
- 实时 join 当前精选池的方案被否决：读侧变重，且展示的可能不是触发时人审所基于的来源。
- 把来源塞进 `publish_metadata` 的方案可行但不够清晰：`publish_metadata` 已承担发布选项与合规元数据，来稿血缘是独立审计面，单列 JSONB 更易投影与回滚。
- 新增独立详情端点暂不需要：内容列表已经返回完整发布正文和图片，且 limit 为 50。若后续来稿图片或全文体积变大，再拆 `GET /api/content/published/:id/source-reference`。

## 7. 实现顺序

1. OpenSpec 先落契约并 validate。
2. cloud 添加 `source_reference` schema、类型、insert 参数、参照触发接线和 panel 投影。
3. console 扩展 DTO，内容页列表与详情浮层增加来源入口和弹窗。
4. cloud 与 console 分别补测试；确认普通发布 `sourceReference=null`，参照洗稿发布有可点击来稿。
