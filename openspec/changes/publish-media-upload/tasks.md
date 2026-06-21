# Tasks — publish-media-upload（A 配图收口）

> **依赖序**：**task 0 实机校准探针先行**（决定主路径模块形状：静态隐藏 input vs 懒加载/拖拽区、编辑器是否被传图门控、上传成功态/封面激活态选择器、DashScope 直链是否无 3xx）。
> task 0 未结之前可并行推进**与探针无关的 CI 可测部分**（§1 云端 emit/降级、§2 的下载/临时文件骨架、`FileInputSetter` 接口 + stub、全部 AC-MEDIA stub 测）；
> **依赖探针结论才能锁定**的部分（真 CDP 文件输入桥接线、锚点、上传成功态选择器、`FileChooser` 兜底是否需要、放开硬拒的端到端验证）必须等 task 0。
> 然后：edge upload_image → edge set_cover → edge 放开 v1 硬拒 → edge 接线+清扫 → 验收 AC-MEDIA/SEQ/DEGRADE → 双仓全量回归 → 部署。
>
> **回写格式**：task 完成后用 HTML 注释把 `[ ]` 标 `[x]`，写清 commit-sha / 偏离说明 —— `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。进度按 sub-repo 分节回写本仓。
>
> **协议**：零改动、消息数维持 54（`upload_image` / `set_cover` 是 `publish.command` 信封内的 `PublishCommandKind`、`imageUrl` 是 `PublishCommandParams` 字段，stage-1 已随运行时发出；非 MessageType 成员，穷举守护不受影响）。`docs/protocol.md` 无需改。
>
> **红线**：MUST NOT 静默假成功（失败/不可校验 → `ok:false` + 真实 error，绝不伪造有图）；后置校验 MUST NOT 以 `input.files.length>0` 为充分条件；配图失败降级 MUST 伴随落库回正；AC-PUB 不变（提交仍由 `approved===true` 把闸）；复用持久化单例不重建；不碰同机 isales。

## 0. 实机校准探针（BLOCKS 模块形状；本机已跑）

> <!-- 2026-06-20 本机实机校准完成（创作平台发布页，CDP，只读+一次测试图上传从未发布、草稿已丢弃）。
> 探针脚本：aidcp-edge/scripts/calibrate-publish-probe.ts / calibrate-imgtab-probe.ts / calibrate-upload-probe.ts。
> 结论详见 design.md「Task-0 calibration results」。 -->

- [x] 0.1 文件输入形态。验证：图文模式下页面唯一 `input.upload-input[type=file]`（accept jpg/png/webp、multiple、hidden），**点击前即在=静态**；`DOM.setFileInputFiles` 实测真填充并触发 SPA 渲染缩略图+编辑器。→ PRIMARY 路径成立、**无需 FileChooser 兜底**。<!-- 发布页默认在「上传视频」标签，select_mode 须先点「上传图文」（现有 anchor text「图文」命中，已确认）。选择器锁定注入 main.ts -->
- [x] 0.2 编辑器是否被传图门控。验证：上传前 editables=0、上传后 editables=4（标题 input.d-text「填写标题会有更多赞哦」、正文 div.tiptap.ProseMirror）→ **图文帖必须有图**。已反哺：sequencer 全图失败→诚实 `failed`（`all_images_failed`），不假装纯文字。<!-- aidcp-cloud command-sequencer all-images-failed guard -->
- [x] 0.3 成功态节点 +「files.length 不可信」。验证：上传成功后 `input.files.length===0`（XHS 消费 FileList），真实成功态=`div.img-preview-area` 内带 src 的缩略图（img.img.preview / #creator-preview-image-0）。已锁定 hasThumbnail 注入 main.ts。封面：单图自动取该图、无独立设封面控件 → set_cover 仅多图下发。<!-- 多图 cover-active 选择器待多图启用再校准 -->
- [ ] 0.4 DashScope URL 直链无 3xx。<!-- 本机无 WANXIANG_API_KEY、无真实 URL 可测；redirect:'error' 守卫保留，部署 E2E（task 8.4）对真实 URL 验证 -->

## 0b. 校准结论落码（locked from task-0）

- [x] 0b.1 aidcp-edge `src/main.ts` 注入校准选择器：CdpFileInputSetter inputSelector=`input.upload-input[type=file]`（fallback `input[type=file]`）；ImageUploader hasThumbnail=`.img-preview-area img / #creator-preview-image-0` 带 src。验证：typecheck 过、edge 全量绿
- [x] 0b.2 aidcp-cloud `command-sequencer.ts`：set_cover 仅 `images.length>1` 下发（单图封面自动）；请求了配图而全失败 → 进 fill_field 前诚实 `failed`（`all_images_failed`），非配图失败仍 fail-fast。验证：AC-MEDIA-DEGRADE/SEQ 更新后全过

## 1. aidcp-cloud — CommandSequencer 配图 emit + 降级 + 落库回正

- [x] 1.1 `src/publish-agent/command-sequencer.ts:29-48` 给 `PublishSequenceInput` 加 `cover?: string`、`PublishSequenceResult` 加 `imagesOk: boolean`（**内部类型，非协议**）。验证：`npm run typecheck` 过、`src/comm/protocol.ts` 零改动 <!-- aidcp-cloud ce016b1 cover? + imagesOk + uploadTimeoutMs；protocol.ts 零改动、AC-PROTO 54 -->
- [x] 1.2 `src/publish-agent/command-sequencer.ts:84-125` `buildCommandSequence` 按 `input.images` 在 `select_mode`（:92）后、`fill_field`（:93）前 emit `upload_image×N`（`params.imageUrl`，计数无关循环、前向兼容多图）。验证：`images=[a,b]` 时序列含 `upload_image×2` 于正确位次；`images` 为空时不 emit <!-- aidcp-cloud ce016b1 AC-MEDIA-SEQ 测过 -->
- [x] 1.3 `src/publish-agent/command-sequencer.ts:128-155` `executePublishSequence` 特判 `kind==='upload_image'`：回 `ok:false` **或**该 kind 抛异常/超时 → 置 `imagesOk=false` 并 `continue`（**不**中断）；非配图 kind 仍 fail-fast。显式注释标明唯一放宽、仅限配图。验证：AC-MEDIA-DEGRADE——`ok:false` 与超时异常两路均不中断、非配图 `ok:false` 仍中断 <!-- aidcp-cloud ce016b1 AC-MEDIA-DEGRADE 三测过（含非配图 fail-fast 红线） -->
- [x] 1.4 `imagesOk` 仍真时才下发 `set_cover`（`params.imageUrl=input.cover`），否则跳过；`imagesOk` 入 `PublishSequenceResult`。验证：仅全图成功才下发 `set_cover`；`result.imagesOk` 如实 <!-- aidcp-cloud ce016b1 偏离：set_cover 入构建序列、执行期按 imagesOk 跳过（等价于"仅全图成功才下发"，免动态 seq 注入）；spec 已改为机制无关表述 -->
- [x] 1.5 确保 `upload_image` 单指令超时预算 > 边缘"下载+CDP+后置校验"预算（`uploadTimeoutMs` 缺省 60s），使边缘先返回干净 `ok:false`。验证：慢下载边缘桩在云端超时前先回 `image_fetch_failed` <!-- aidcp-cloud ce016b1 sendAndWaitResult 按 kind 选 uploadTimeoutMs；AC-MEDIA-DEGRADE 超时路覆盖 -->
- [x] 1.6 `src/publish-agent/roles/publish-executor.ts` `executePublishSequence` 后 `result.imagesOk===false` 时**回正预存 `imageUrl`**（标 `images_attached=false`），使纯文字帖不留"有图"假信号。验证：降级一次落库无伪造有图信号 <!-- aidcp-cloud ce016b1 markImagesAttached(false) + publish_log.images_attached 列；executor 降级测过。附带修 stage-4 server 适配器漏接（真血缘被 tags/[] 覆盖、recordMetadata 未接线）-->

## 2. aidcp-edge — upload_image（CDP 文件输入桥）

- [x] 2.1 `src/cdp/file-input-setter.ts`（新）`FileInputSetter` 接口 + `CdpFileInputSetter`：`DOM.enable`（once）→ `Runtime.evaluate({returnByValue:false})` 取 `objectId` → `DOM.setFileInputFiles`；stale-handle 单次有界重试；由 `session.cdp` 单例构建。验证：`typecheck` 过、最多一次重试 <!-- aidcp-edge 07af4dd -->
- [x] 2.2 `src/flows/image-uploader.ts`（新）`ImageUploader`：注入 `fetchImpl` + `FileInputSetter`；URL 校验 → 下载到临时文件（私有方法）→ 经 `FileInputSetter` 设置 → 后置校验控件成功态（绑定式轮询，**非仅 `input.files.length>0`**）→ `finally` 清理。验证：成功+见缩略图+清理；各失败回分类 error 且仍清理 <!-- aidcp-edge 07af4dd image-uploader.test.ts 7 测过（含红线反例 image_not_attached）-->
- [x] 2.3 下载私有方法：注入 `fetchImpl` + `AbortController`/`AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` + `redirect:'error'` + `Content-Length` 预检与流式字节上限（默认 ~10MB）+ magic-byte（jpeg/png/webp）+ `mkdtemp` 于 `os.tmpdir()/aidcp-img-*` 随机名。验证：超时→`image_fetch_failed`；超限→`image_too_large`；非图→`image_format_unsupported`；非 https→`image_url_rejected` <!-- aidcp-edge 07af4dd 五分类失败均有测 -->
- [x] 2.4 文件输入 / 缩略图成功态真实选择器（**来自 task 0 校准**）。<!-- 偏离：选择器在 main.ts 组合根注入（非 anchors.ts 常量）——库模块保持 fail-closed/通用、XHS 具体选择器集中在组合根。inputSelector=input.upload-input[type=file]；hasThumbnail=.img-preview-area img 带 src。库默认仍 fail-closed（uncalibrated 即诚实失败）。 -->
- [x] 2.5 `src/flows/publish-command-handlers.ts` 用 `ImageUploader` 替换 `upload_image` 的 `notImplemented` 桩（未注入 uploader 仍诚实 `kind_not_implemented`），结果 verbatim 回报。验证：成功→`ok:true`；各失败→`ok:false`+真实 error，绝不 `ok:true` <!-- aidcp-edge 07af4dd runUploadImage；AC-MEDIA 透传测过 -->

## 3. aidcp-edge — set_cover

- [ ] 3.1 封面入口 / 封面激活态真实 anchors（**来自 task 0 校准**；多图才需，本 change 单图不触发）。<!-- task-0 实测：单图封面自动取该图、发布页无独立设封面控件 → set_cover 仅多图下发，当前单图产品不触发。多图 cover-active 真实选择器待多图能力启用时再校准；coverActiveValidator 保持 fail-closed 占位、handler+测试就位（前向兼容）。本 change 单图路径无需此校准。 -->
- [x] 3.2 `src/flows/publish-command-handlers.ts` 用 `runAtom` + **封面专用 validator**（断言所选图真成为当前封面，非仅点到）替换 `set_cover` 的 `notImplemented` 桩。验证：封面入口缺失→`ok:false`；定位+激活态→`ok:true` <!-- aidcp-edge 07af4dd coverActiveValidator；AC-MEDIA set_cover 两测过 -->

## 4. aidcp-edge — 放开 v1 带图硬拒（显式改道）

- [x] 4.1 `src/flows/publish-post.ts:294-296` 把"images are not supported in phase one"静默丢弃改为**显式报错指向指令路径**。验证：v1 `publishPost` 带图返回 `ok:false` + 改道 error（绝不静默丢图、绝不假成功）；不在 v1 加上传步骤 <!-- aidcp-edge 07af4dd 改道 error "use command-driven path (upload_image)"；publish-post.test.ts 已更新 -->

## 5. aidcp-edge — 接线 + 临时目录清扫

- [x] 5.1 `src/main.ts` 由 `session.cdp` 构建 `CdpFileInputSetter` + `ImageUploader`（默认 `fetchImpl`）传入 `PublishCommandDispatcher`；复用既有 `session`/`cache`/`cdp` 单例。验证：dispatcher 正常构造；无重建 <!-- aidcp-edge 07af4dd 4th 参注入 uploader，复用 session.cdp -->
- [x] 5.2 `src/main.ts`（boot）启动时 best-effort `rm({recursive,force})` 清扫 `os.tmpdir()/aidcp-img-*` 残留。验证：仅命中该前缀（绝不碰 isales/其它 tmp） <!-- aidcp-edge 07af4dd sweepImageTempDirs()，前缀限定 aidcp-img-* -->

## 6. 验收（中控触发，落 sub-repo 执行）

- [x] 6.1 edge AC-MEDIA：删 `upload_image`/`set_cover` 的 `kind_not_implemented` 锁；加成功（`FakeFileInputSetter` + jsdom 缩略图、fake fetch）→ `ok:true`+清理。验证：通过 <!-- aidcp-edge 07af4dd image-uploader.test + handlers test -->
- [x] 6.2 edge AC-MEDIA 失败路：下载超时→`image_fetch_failed`；非图→`image_format_unsupported`；无 input→`no_target`；**后置校验失败（红线反例：设了 files 但无缩略图）→ `image_not_attached`**。验证：各回精确 error，`files.length>0` 单独不被当成功 <!-- aidcp-edge 07af4dd 全覆盖 + url_rejected/too_large -->
- [x] 6.3 cloud AC-MEDIA-SEQ：`images=[a,b]` 时在 `select_mode` 后 / `fill_field` 前 emit `upload_image×2`、随后条件 `set_cover`，提交/抓取仍受人审闸。验证：顺序与授权闸正确 <!-- aidcp-cloud ce016b1 含未授权 AC-PUB 第2闸子测 -->
- [x] 6.4 cloud AC-MEDIA-DEGRADE（两路）：`ok:false` **与** 超时 → `imagesOk=false`、不下发 `set_cover`、文字照走、提交仍受人审、executor 回正。验证：两路均通过 <!-- aidcp-cloud ce016b1 sequencer 两路 + executor markImagesAttached(false) 测 -->
- [x] 6.5 cloud AC-PUB 回归（精化）：在 **executor 授权闸**断言未授权时零下发（绝不调 executePublishSequence）；`buildCommandSequence` 截止作冗余下层守护保留。验证：未授权发零指令 <!-- aidcp-cloud ce016b1 publish-executor.test 新增 AC-PUB executor 闸测 -->

## 7. 双仓全量回归（先 acceptance 再全量再 typecheck）

- [x] 7.1 edge：`test:acceptance`（11）→ `npm test`（279）→ `typecheck` 全绿；AC-PROTO-*（消息数 54）、AC-PUB-* 全过 <!-- aidcp-edge 07af4dd -->
- [x] 7.2 cloud：`test:acceptance`（18）→ `npm test`（279）→ `typecheck` 全绿；两份 protocol.ts MessageType 键不漂移 <!-- aidcp-cloud ce016b1 -->
- [x] 7.3 中控：`openspec validate publish-media-upload --strict` 通过；本 change **新增 0 个消息类型**（upload_image/set_cover/imageUrl 仍在 publish.command 信封内），`docs/protocol.md` 无需因本 change 改表行 <!-- 2026-06-20 strict 通过。注：协议绝对计数已由并发会话从 54→55（非本 change），两端一致、AC-PROTO 全过；本 change 对协议零改动 -->

## 8. 部署（ECS 安全序列 + 实机；执行前先做 §0 前置检查；与 A 全阶段统一）

- [x] 8.1 §0 前置检查：私钥 `~/codes/isales-4.pem` 存在且 `600`、sub-repo 在；cloud 本机 == origin/master（63128e6，无落后/regress）。<!-- 2026-06-21 通过 -->
- [x] 8.2 ECS 确认 `WANXIANG_API_KEY`：**UNSET**（值未记录）→ 本配图能力**「已合入、休眠待 key」**（无 key→无图→图文编辑器门控→/publish 会诚实失败，不假发）。DASHSCOPE_API_KEY 已设；AIDCP_PUBLISH_AUTO 未设（仅手动 /publish）。<!-- 2026-06-21 设 WANXIANG_API_KEY 后配图链路即可用 -->
- [x] 8.3 ECS 部署 cloud 安全序列：备份（cloud.bak.20260621-091931.tar.gz + .env.bak.20260621-091931）→ dry-run 暴露范围（全 master 快照，net-new=并发 comment agents + 本 change）→ rsync（--exclude .env/node_modules/.git/*.zip）→ npm install（up to date）→ restart → healthcheck 全过（active+NRestarts=0、8787、PG select 1、image_url/images_attached 列+liked_notes 已建、飞书长连接已建立）；**isales 未碰**。<!-- aidcp-cloud 63128e6 2026-06-21 deployed -->
- [ ] 8.4 运营机 edge 跑、连 `ws://121.89.85.150:8787`，gated `AIDCP_E2E` 实机验证配图端到端。<!-- 需先在 ECS 设 WANXIANG_API_KEY（否则无图、图文发不出）；edge 本机已就位（profile 已登录、5d32ff9）。运营触发：飞书 /publish → 人审 → 配图上传 → 真实发布 -->

> <!-- 2026-06-21 deployed：cloud 63128e6 上线 ECS（全 master 快照），配图链路代码就绪但 **休眠待 WANXIANG_API_KEY**。
> 设 key 后即活；edge 本机就位。剩余 8.4 = 设 key 后运营机一次真机端到端验证（含 0.4 DashScope redirect 校验）。 -->

## 备注（设计已明确排除/延后，非本 change 范围）

- 多图选择与 CoverSelector 多图逻辑（云端 `imageCount` 写死 1；本 change 循环已计数无关但不建多图生成）→ 后续云端单独 change。
- 视频上传（`upload_video` / mp4 magic-byte / 更大上限）→ 保留；落地时建议复用 `upload_image` 加 `mediaType` 参数而非新 kind，以维持消息数 54。
- `FileChooser` 拦截兜底仅当 task 0 证实懒加载输入才建（slots 于 `FileInputSetter` 接口后）。合成 drag-drop / 粘贴（`isTrusted=false`）完全不在范围。
- v1 整页路径整体下线 → 另案；本 change 仅改其带图分支为显式改道。
- 远程/转发 CDP（浏览器与 edge 异机）→ 不在范围；`FileInputSetter` 为未来 swap 点。
- DashScope URL 过期的 re-host/regenerate-on-approve → 已知运营缺口、不建；若降级率高再开案。
