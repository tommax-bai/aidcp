## Why

管理后台「内容」页的待审核发布内容（`pending_approval`）目前已能就地改标题 / 正文（change `edit-note-draft-before-publish`），但配图明确「不可改」（`ContentPage.tsx` 就地写着「配图本期在此不可改（保留原值）」）。生成配图偶有跑偏 / 不合规 / 多余的一张，审核人只能整条驳回重生成或带着坏图批准，缺一个「删掉这张、留下其余照发」的轻操作。本 change 补上待审草稿的逐张删配图能力，复用既有的乐观 CAS 编辑通道，不新起写路径。

## What Changes

- 待审草稿编辑通道（`PUT /api/publish/:id/draft` → `PublishLogStore.editDraft`）新增一个 `images` 补丁字段：提交「保留下来的配图 URL 列表」，落库 `publish_log.images` 并同步封面 `image_url = kept[0] ?? null`，照常 `content_version + 1`（复用「编辑即作废旧飞书审核卡、审=发版本闸」不变量）。
- **只删不注入（红线）**：提交的每个 URL MUST 是该记录当前 `images` 的成员（保序过滤），任一非成员即具名拒 `invalid_field`，绝不接受把任意外部 URL 写进待发帖。
- 仅 `pending_approval` 记录可删（非则 `not_pending`）；已发布记录配图不可删。允许删到 0 张 = 纯文字帖（发布管线已支持 M=0 降级），前端删空需二次确认。
- 只从发布记录移除配图引用，**不删除 OSS 实体对象**（孤儿对象接受，存储清理是另一议题）。
- 前端 `ContentPage` 待审详情浮层的配图区：可编辑态下每张图加删除按钮 + 二次确认，走既有 `editDraft` mutation 带 `images` 补丁 + `expectedVersion` 乐观 CAS，成功后非乐观回读真态刷新；查看态 / 已发布不显示删除。

## Capabilities

### New Capabilities
<!-- 无新增 capability：本 change 扩展既有管理后台写操作能力。 -->

### Modified Capabilities
- `console-write-operations`: 「待审草稿编辑」能力扩展——除标题 / 正文 / 可见范围 / 话题外，新增经**同一乐观 CAS 单写通道**的逐张删配图；带「只删不注入（提交列表须为当前配图子集）」红线、封面随之重算、删到零合法（纯文字帖）、前端删除非乐观回读真态。写仍只经拥有 `publish_log` 的进程内对象、绝不裸 SQL、绝不乐观假成功。

## Impact

- **aidcp-cloud**：`src/publish-agent/publish-log-store.ts`（`EditDraftPatch` + `editDraft()`：SELECT 增读 `image_url,images`；`images` 子集校验与防注入；UPDATE 同步 `images` + `image_url`；`EditDraftResult`/`RETURNING` 带回新 images）；`src/panel/panel-server.ts`（`PUT /api/publish/:id/draft` 解析 `images` 补丁、响应回带 images）；`src/panel/panel-store.ts` / `src/panel/types.ts`（回带 images 类型，`PanelPublish.images` 已存在）。
- **aidcp-console**：`src/pages/ContentPage.tsx`（`ImagesStrip` 可编辑态删除按钮 + 确认 + 乐观 CAS mutation 扩展）；`src/types/api.ts`（editDraft 请求/响应类型加 images）；`src/api/errorText.ts`（复用既有 `invalid_field`/`version_conflict`/`not_pending` 映射，必要时补文案）。
- **协议 / 风控 / 发布下发链无改动**：不触碰边-云协议四处、不碰 `RiskController`、不改审批写回逐字节契约；下发段读回 `images` 逐张上传的既有逻辑天然消费删后结果。
- **部署**：cloud 纯代码（env 无关）落 dev；console 构建发 `/opt/aidcp/console`。
- **数据**：无 schema 迁移（`publish_log.images TEXT[]` / `image_url` 已存在）；遗留 OSS 对象在删图后成孤儿（可接受）。
