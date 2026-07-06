## Context

`aidcp-console` 的精选内容池列表图片列已经通过 `ReferenceImageThumb` 打开站内 `Modal` 预览，并在同一浮层里切换多张参考图。查看笔记详情中的 `ReferenceImageStrip` 仍把图片渲染为外链 `<a>`，点击后会打开原图 URL；部分 OSS/源站响应可能被浏览器处理为下载，也会打断运营在详情浮层里的阅读流程。

本次只修正 console 展示交互。图片数据仍来自 cloud 已返回的 `referenceImages`，不改变 edge 抓取、cloud 存储、API shape 或图片保留数量。

## Goals / Non-Goals

**Goals:**

- 查看笔记详情里的参考图点击后打开站内图片预览浮层。
- 列表缩略图、详情图、参考创作弹窗中的参考图使用一致的预览状态和上一张 / 下一张切换逻辑。
- 点击参考图不导航、不下载、不触发行点击或其它父级操作。
- 用页面测试覆盖详情图片点击预览与多图切换。

**Non-Goals:**

- 不新增图片下载、复制链接或外链打开入口。
- 不改变 `referenceImages` 的后端字段、过滤规则、排序或保留上限。
- 不调整精选准入、图片抓取、OSS 上传或发布生成逻辑。

## Decisions

- 将 `ReferenceImageStrip` 从外链列表改为图片按钮列表，并接收 `onPreview(images, index)` 回调。这样详情和参考创作弹窗都能复用列表已有的 `imagePreview` modal，而不引入第二套预览组件。
- `usableReferenceImages()` 继续作为唯一过滤入口，保证只预览有可用 `ossUrl` 或 `sourceUrl` 的图片，缺图仍显示现有空态。
- 预览 modal 继续以当前 `imagePreview.index` 驱动上一张 / 下一张，点击某张详情图时初始 index 使用该图在可用图片数组中的位置。

## Risks / Trade-offs

- [Risk] 图片按钮替换外链后少了直接打开原图的临时排障方式 → Mitigation：本需求明确不要下载/跳转；如未来需要排障链接，应单独设计显式复制链接入口，而不是复用图片点击。
- [Risk] 浮层嵌套浮层时焦点管理更复杂 → Mitigation：复用现有 Ant Design `Modal` 预览，不新增自定义 portal；点击图片时只更新预览状态，不关闭详情弹窗。
