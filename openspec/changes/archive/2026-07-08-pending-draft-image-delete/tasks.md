# Tasks — pending-draft-image-delete

> cloud 后端 + console 前端；已实装 + 测试全绿 + 集成 master + 部署 dev。
> <!-- aidcp-cloud 0be613f / aidcp-console 8ce490f landed→master; deployed dev 2026-07-08 -->

## 1. aidcp-cloud — 后端 store 单写（editDraft 扩展）

- [x] 1.1 `EditDraftPatch` 增 `images?: string[]` <!-- aidcp-cloud 0be613f -->
- [x] 1.2 `editDraft()` FOR UPDATE SELECT 增读 `image_url, images` <!-- aidcp-cloud 0be613f -->
- [x] 1.3 事务内 images 子集校验（非成员→invalid_field 回滚）+ 算 kept/cover <!-- aidcp-cloud 0be613f -->
- [x] 1.4 UPDATE SET `images`+`image_url`；RETURNING 增 image_url/images <!-- aidcp-cloud 0be613f -->
- [x] 1.5 `EditDraftResult` 回带 `images`；未含 images 补丁零回归 <!-- aidcp-cloud 0be613f -->
- [x] 1.6 store 单测（删一张/防注入/删空/version_conflict/not_pending/only-title 回归）<!-- aidcp-cloud 0be613f -->

## 2. aidcp-cloud — 面板 API 路由 + 投影

- [x] 2.1 `PUT /api/publish/:id/draft` 解析 images 补丁 + 响应回带 images <!-- aidcp-cloud 0be613f -->
- [x] 2.2 EditDraftResult→响应带 images（PanelPublish.images 已存在）<!-- aidcp-cloud 0be613f -->
- [x] 2.3 panel-server 路由单测（透传 + 防注入映射 400）<!-- aidcp-cloud 0be613f -->
- [x] 2.4 typecheck + test:acceptance(AC-PUB-*) + 全量绿 <!-- aidcp-cloud 0be613f -->

## 3. aidcp-console — 前端删除交互

- [x] 3.1 editDraft 请求/响应类型加 images（PanelPublish.images 已有）<!-- aidcp-console 8ce490f -->
- [x] 3.2 `ImagesStrip` 可编辑态删除角标 + Popconfirm（删空提示纯文字帖）<!-- aidcp-console 8ce490f -->
- [x] 3.3 deleteImage mutation + onDeleteImage（乐观 CAS→回读真态刷新）<!-- aidcp-console 8ce490f -->
- [x] 3.4 查看态/非待审不渲染删除入口；改「配图不可改」提示文案 <!-- aidcp-console 8ce490f -->
- [x] 3.5 errorText 补 invalid_field 映射 <!-- aidcp-console 8ce490f -->
- [x] 3.6 ContentPage.test.tsx 删图交互测试（删一张/删空/版本冲突/invalid_field/查看态无入口）<!-- aidcp-console 8ce490f -->
- [x] 3.7 typecheck + 全量(66) + build 全绿 <!-- aidcp-console 8ce490f -->

## 4. 验证与部署

- [x] 4.1 `openspec validate pending-draft-image-delete --strict` 通过
- [x] 4.2 cloud 走 §5 安全序列部署 dev（备份→rsync→restart→healthcheck 全绿）<!-- 2026-07-08 deployed dev(0be613f) -->
- [x] 4.3 console 构建发 `/opt/aidcp/console`（rsync 无 --delete）<!-- 2026-07-08 deployed dev(8ce490f) -->
- [ ] 4.4 真机项已登记 backlog：待审删一张后批准发布验证少那张 + 删空发纯文字帖 <!-- backlog registered; 真机待核 -->
- [x] 4.5 archive change（delta 合并进 `openspec/specs/console-write-operations`）
