## Why

A 重构发帖流水线四阶段（stage-1 指令运行时、stage-2 生产角色、stage-3 元数据决策、stage-4 触发+元数据应用+人审+血缘+落库）已全部落地、双仓全绿。stage-4 在 2026-06-20 按 design §6 做了**五项一体收敛**，把**配图应用整块显式延后**到本 change（`publish-trigger-and-apply/tasks.md:16-17` + Migration）——根因是配图唯一可靠机制（CDP `DOM.setFileInputFiles`）依赖真实浏览器、CI 测不了，且其**模块形状取决于一次实机校准探针**（小红书发布页是静态隐藏 `<input type=file>` 还是懒加载拖拽区、编辑器是否被"先传图"门控、上传成功态节点是哪个），这只能在运营机上对真实页面跑 CDP 才能定。

配图的云端地基其实**已经就绪、只差最后一接线**：

1. **云端已产出真图 URL**：`ImageGenerator` 调通义万相得到真实有时效的 DashScope CDN https URL（`wanxiang-client.ts:172-177`），经 `ContentAssembler` 进 `AssembledContent.imageUrl`，`PublishExecutor` 已包成 `images:[url]` 喂进 `PublishSequenceInput.images`（`publish-executor.ts:197`）。
2. **但这条 `images` 输入没人读**：`CommandSequencer.buildCommandSequence` 从不 emit `upload_image` / `set_cover`（唯一痕迹是 `command-sequencer.ts:100` 的延后注释）；边缘 `PublishCommandDispatcher` 对这两个 kind 仍诚实回 `kind_not_implemented`（`publish-command-handlers.ts:209-212`）。
3. **v1 整页路径还硬拒带图**（`publish-post.ts:294-296` "images are not supported in phase one"）。

本 change 就**只**收口这一块：把已生成的图真正传到小红书发布页、设封面、上传失败如实降级纯文字，并放开 v1 硬拒。**协议零改动、消息数维持 54**（`upload_image` / `set_cover` 是 `publish.command` 信封内的 `PublishCommandKind` 子类、`imageUrl` 是 `PublishCommandParams` 字段，均 stage-1 已随运行时发出，非 MessageType 成员，穷举守护不受影响）。多图与视频**保留不建（YAGNI）**。

## What Changes

> 配图主路径的模块形状由 **task 0 实机校准探针**先定，再锁实现。CI 可测部分（云端 emit/降级、边缘下载/临时文件、`FileInputSetter` 接口 + stub、全部 AC-MEDIA）与实机依赖部分（真 CDP 文件输入桥接线、锚点、上传成功态选择器、放开硬拒的端到端验证）分离。

- **【实机前置】配图能力实机校准探针（task 0，BLOCKS 模块形状）**：运营机上（gated `AIDCP_E2E`）对真实小红书发布页跑 CDP，确认：① 文件输入是点击前即在的静态隐藏 `<input type=file>`，还是懒加载/拖拽区（决定主路径 vs `FileChooser` 兜底）；② 编辑器是否被"成功传图"门控（决定全图失败时是降级纯文字还是诚实 `failed`）；③ 该图的上传成功态节点与封面激活态节点（决定后置校验选择器）；④ DashScope 真 URL 是否直链无 3xx（决定 `redirect:'error'` 不误伤）。
- **【云端】`CommandSequencer` 配图 emit + 降级不中断**：`buildCommandSequence` 按 `input.images` 在 `select_mode` 后、`fill_field` 前 emit `upload_image×N`（计数无关循环，前向兼容多图）；`executePublishSequence` 对 `upload_image` 失败（回 `ok:false` 或该 kind 超时异常）特判为 `imagesOk=false` 并**继续**（唯一一处对 fail-fast 的有意放宽，仅限配图），全图成功后才动态下发一条 `set_cover`；`imagesOk` 进 `PublishSequenceResult`。`PublishSequenceInput` 加内部字段 `cover?`，`PublishSequenceResult` 加 `imagesOk`（均内部类型、非协议）。
- **【云端】落库如实**：`PublishExecutor` 在 `imagesOk===false` 时**回正已预存的 `imageUrl`**（置空 / 标 `imagesAttached=false`），杜绝纯文字帖在 `publish_log` 留下"有图"假信号（观测面红线）。
- **【边缘】实装 `upload_image`**：URL 校验 → 下载到边缘本机临时文件（注入 `fetchImpl`、`redirect:'error'`、`AbortController` 超时、流式大小上限、magic-byte 格式校验）→ 解析文件输入 `objectId` → `DOM.setFileInputFiles`（经既有 `CdpClient.send`，零新依赖）→ **后置校验该图的控件成功态**（绑定式轮询缩略图/预览节点，**不以 `input.files.length>0` 为足够条件**）→ `finally` 清理临时文件。失败按错误分类如实回 `ok:false`，**绝不伪造 `ok:true`、绝不伪造有图**。
- **【边缘】实装 `set_cover`**：经 `LocatingEngine` 的 `runAtom` 定位+点击+**封面激活态后置校验**（不止"点到了"）。
- **【边缘】放开 v1 带图硬拒**：`publish-post.ts:294-296` 的静默丢弃改为**显式报错指向指令路径**（红线：绝不静默丢图、绝不假成功；不在近废弃的 v1 路径里建上传、不整体删 v1）。
- **【边缘】新接缝与清理**：新增 `FileInputSetter` 接口 + `CdpFileInputSetter`（实机 CDP 实现，单一 swap 点，亦为未来远程浏览器扩展点）+ `ImageUploader`（下载为私有方法、单注入接缝，避免过度拆分）；启动时清扫 `os.tmpdir()/aidcp-img-*` 前缀的崩溃残留（单一前缀，绝不碰 isales/其他 tmp）。复用既有 `session`/`cache`/`cdp` 单例，**绝不重建**。
- **【验收】AC-MEDIA / AC-MEDIA-SEQ / AC-MEDIA-DEGRADE**：成功 / 下载超时 / 非图 / 无目标 / 后置校验失败（红线反例：写了 files 但无缩略图 → `image_not_attached`）；序列 emit 顺序 + 提交仍受人审闸；降级两路（回 `ok:false` 与超时异常）→ `imagesOk=false`、不发 `set_cover`、文字/元数据照走、提交仍人审、落库回正。CDP 部分经 `FakeFileInputSetter` + fake fetch 单测，无需真 Chrome。

## Impact

- **Specs**: `publish-pipeline`（ADDED 配图应用相关 requirement；与 stage-1/2/3/4 的 `publish-pipeline` delta requirement 名互不重叠，归档时依序并入同一 spec）。
- **Code**:
  - `aidcp-cloud`：`src/publish-agent/command-sequencer.ts`（emit + 降级 + 内部类型）、`src/publish-agent/roles/publish-executor.ts`（落库回正）。
  - `aidcp-edge`：`src/flows/publish-command-handlers.ts`（接 `upload_image`/`set_cover`）、`src/flows/image-uploader.ts`（新）、`src/cdp/file-input-setter.ts`（新）、`src/flows/anchors.ts`（配图/封面锚点）、`src/flows/publish-post.ts`（放开硬拒）、`src/main.ts`（接线 + 启动清扫）、对应单测。
- **协议**: 零改动、消息数维持 54；`docs/protocol.md` 无需改（`publish.command` 行已抽象覆盖 kind 集）。
- **不变量/红线**: MUST NOT 静默假成功（失败/不可校验 → `ok:false` + 真实 error，绝不伪造有图）；AC-PUB 不变（配图指令在提交前下发，`submit_publish`/`capture_postId` 仍由 `approved===true` 把闸）；复用持久化单例、不重建；不碰同机 isales。
- **部署**: 随 A 全阶段统一部署；若 ECS 未设 `WANXIANG_API_KEY`，本能力"已合入、休眠待 key"而非"已上线"。
- **冲突面**: 与并发 WIP（notification-monitor / aidcp-console-panel-mvp / skip-profile-visit-if-followed 等）无重叠——本 change 只动发帖指令序列与边缘配图处理器，不碰浏览闭环 `role-dispatcher` / `session-monitor`。
