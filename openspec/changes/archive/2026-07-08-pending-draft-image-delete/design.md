## Context

「内容」页（`aidcp-console/src/pages/ContentPage.tsx`）的待审详情浮层已支持就地改标题 / 正文并「保存并批准」（change `edit-note-draft-before-publish`）。该编辑落到 `PublishLogStore.editDraft()`（`aidcp-cloud/src/publish-agent/publish-log-store.ts:320`）——一个 `FOR UPDATE` 行锁 + `content_version` 乐观 CAS 事务，`EditDraftPatch` 现支持 `title/content/visibility/topics`。配图存在 `publish_log.images TEXT[]`（封面 `image_url = images[0]`，`publish-log-store.ts:169-171` 双写），发布下发段读回 `images` 逐张上传。浮层配图区 `ImagesStrip` 现为只读，代码里明写「配图本期在此不可改」。

本设计在**不新起写路径**的前提下，把「逐张删配图」接进这条已成熟的 CAS 编辑通道。

## Goals / Non-Goals

**Goals:**
- 审核人能在待审草稿里删掉某张（或全部）生成配图后照发其余，无需整条驳回重生成。
- 复用既有乐观 CAS + 版本闸 + 飞书旧卡失效 + 诚实非乐观回读，安全语义零回退。
- 严守「写只经拥有者对象、绝不裸 SQL、绝不乐观假成功」核心不变量，并新增「只删不注入」红线。

**Non-Goals:**
- 不做配图**新增 / 替换 / 重排 / 重新生图**（只删）。
- 不删除 OSS / 存储实体对象（孤儿清理是另一议题）。
- 不动已发布记录的配图、不动参照图（精选页 reference images 是另一条链）。
- 不改边-云协议、风控、审批写回逐字节契约。

## Decisions

### 决策 1：删配图表达为「保留子集」补丁，而非「删除下标」
`EditDraftPatch` 增加 `images?: string[]`，语义是「编辑后应保留的配图 URL 有序列表」。写方法在同一 `FOR UPDATE` 事务里读出当前 `images`，校验提交列表每项都是当前成员（保序过滤），任一非成员即拒 `invalid_field`。

- **为何不用「删除下标 `deleteIndex`」**：下标在并发下语义脆（版本一变下标就错位）；虽然 CAS 版本已能挡住并发，但「保留子集」与既有 `visibility/topics`「提交新值」范式同构，store 校验逻辑更直白，且天然幂等。
- **为何要子集校验（不接受任意 URL 列表）**：这是防注入红线——待发帖的图 MUST NOT 被前端/被篡改请求塞进任意外部 URL。只允许「当前集合的子集」把能力严格限死为「删」。

### 决策 2：复用 `editDraft` 事务，不加新方法 / 不加新端点
删配图作为 `editDraft` 的又一个可选补丁字段，走 `PUT /api/publish/:id/draft`。这样自动继承：`pending_approval` 门禁、`content_version + 1`、飞书旧卡失效、在途授权 `already_decided` 探测、`edited_by/edited_at` 审计、写后回读真态。

- **实现落点**：`editDraft()` 的 `SELECT … FOR UPDATE` 增读 `image_url, images`；纯字段校验段加 `images` 子集校验（沿用「先校验后进事务」但子集校验必须在事务内、因为要对当前值比对——放在 `FOR UPDATE` 之后、`UPDATE` 之前）；`UPDATE … SET` 增 `images = $k, image_url = $k0`；`RETURNING` 增 `image_url, images`；`EditDraftResult` 与 panel-server 响应带回 `images`。
- **panel-server**：`PUT …/draft` 的 body 解构加 `images`，仅出现时进 patch（与既有 `visibility/topics` 同）。

### 决策 3：封面随删重算，删空合法
`image_url` 恒等于保留列表首项（空 → NULL）。删到 0 张走既有纯文字发布路径（`imageUrls` 空 → 下发段 M=0），前端删空前二次确认（避免误删成纯文字帖）。

### 决策 4：前端非乐观，删除入口只在可编辑态
`ImagesStrip` 加 `editable` 分支：可编辑态每张缩略图叠一个删除角标 + `Popconfirm`，确认后调 `editDraft` mutation 带 `images = 当前列表去掉该张` + `expectedVersion`；成功用后端回读的真态（新 `images` + 新 `contentVersion`）刷新 `viewing` 与列表行，绝不先乐观移除。错误码经既有 `errorText` 映射（`version_conflict`/`not_pending`/`already_decided`/`invalid_field`）。查看态与已发布不渲染删除入口。

## Risks / Trade-offs

- **孤儿 OSS 对象**：删图只改记录、不删存储 → 对象残留。→ 缓解：可接受（仅存储成本），未来的存储 GC 统一清理（属 `cloud-oss-storage` 议题），本 change 不背。
- **审核人误删成纯文字**：删到 0 张会静默变纯文字帖。→ 缓解：前端删空二次确认 + 文案提示；后端删空仍合法不报错（诚实语义）。
- **`images_attached_count` 语义**：该列是**发布时**真实附着张数，待审阶段通常为 0；删配图只动 `images`/`image_url`，不动 `images_attached_count`（它在实际发布后由 `markImagesAttached` 写）。→ 无回退，读侧 `imagesAttachedCount` 仍诚实反映「发布时」事实。
- **子集校验放事务内**：与既有「先纯校验后进事务」略有出入（子集校验需当前值，必须进事务）。→ 缓解：仅多一次已持锁行的内存比对，无额外查询、无额外锁竞争。
- **console↔cloud 类型对齐**：`PanelPublish.images` 已存在，本 change 只让 editDraft 请求/响应带 `images`，不新增枚举 → 规避 memory `console-cloud-enum-drift-whitescreen` 的白屏类风险。

## Migration Plan

- 无 DB 迁移（`publish_log.images` / `image_url` 早已在）。
- 部署：cloud 纯代码落 dev（`AIDCP_*` env 无关）→ `npm run typecheck` + `npm test`（含新 store/panel 用例，安全红线 `AC-PUB-*` 全过）→ 走 §5 安全序列部署 dev；console `npm run build` + typecheck → 发 `/opt/aidcp/console`（rsync 绝不 `--delete`）。
- 回滚：纯代码，回滚到前一 commit 重部署即可；无数据形态变更、无需数据回滚。

## Open Questions

- 无阻塞性未决项。（可选后续：删图操作是否要在发布记录里留一条「删了哪几张」的审计明细，本期靠 `content_version` + `edited_by/edited_at` 已足够，不额外做。）
