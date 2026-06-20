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

## 0. 实机校准探针（BLOCKS 模块形状；运营机、gated AIDCP_E2E）

- [ ] 0.1 在运营机对真实小红书发布页跑 CDP，确认文件输入是**点击前即在的静态隐藏 `<input type=file>`** 还是懒加载/拖拽区。验证：`Runtime.evaluate({returnByValue:false})` 能解析到 input 的 `objectId` 且 `DOM.setFileInputFiles` 真填充 `input.files`；若为懒加载则改走 `Page.setInterceptFileChooserDialog` + `fileChooserOpened` 兜底（仍经 `FileInputSetter` 接口，先于编写 uploader 决定形状）
- [ ] 0.2 同探针：确认发布页**编辑器是否被"成功传图"门控**（无图时标题/正文是否可填）。验证：若门控，则记录"全图失败 MUST 转 `failed`（非纯文字帖）"并反哺 §1.3 降级决策；若不门控，纯文字降级成立
- [ ] 0.3 同探针：定位该图的**控件成功态节点**（缩略图/预览/进度完成）与**封面激活态节点**。验证：两者均可经 `LocatingEngine` 定位、且与"仅 `input.files` 有值"可区分（后置校验红线的实锚点来源）
- [ ] 0.4 同探针：取一个真实 DashScope 结果 URL，确认是**直链 CDN 无 3xx 重定向**。验证：`redirect:'error'` 不会误拒合法图（若有跳转则调整安全策略并记录）

## 1. aidcp-cloud — CommandSequencer 配图 emit + 降级 + 落库回正

- [ ] 1.1 `src/publish-agent/command-sequencer.ts:29-48` 给 `PublishSequenceInput` 加 `cover?: string`、`PublishSequenceResult` 加 `imagesOk: boolean`（**内部类型，非协议**）。验证：`npm run typecheck` 过、`src/comm/protocol.ts` 零改动
- [ ] 1.2 `src/publish-agent/command-sequencer.ts:84-125` `buildCommandSequence` 按 `input.images` 在 `select_mode`（:92）后、`fill_field`（:93）前 emit `upload_image×N`（`params.imageUrl`，计数无关循环、前向兼容多图）；**此处不 emit `set_cover`**。验证：`images=[a,b]` 时序列含 `upload_image×2` 于正确位次且无 `set_cover`；`images` 为空时不 emit
- [ ] 1.3 `src/publish-agent/command-sequencer.ts:128-155` `executePublishSequence` 特判 `kind==='upload_image'`：回 `ok:false` **或**该 kind 抛异常/超时 → 置 `imagesOk=false` 并 `continue`（**不**走 :140/:144 中断）；非配图 kind 仍 fail-fast。加显式注释标明这是**唯一一处 fail-fast 放宽、仅限配图**。验证：AC-MEDIA-DEGRADE——`upload_image ok:false` 与超时异常两路均不中断、非配图 `ok:false` 仍中断
- [ ] 1.4 `src/publish-agent/command-sequencer.ts`（execute，配图块之后）`imagesOk` 仍真时才经 `sendAndWaitResult` 动态下发**一条** `set_cover`（`params.imageUrl=input.cover`），否则跳过；`imagesOk` 入 `PublishSequenceResult`。验证：仅全图成功才下发 `set_cover`；`result.imagesOk` 如实
- [ ] 1.5 `src/publish-agent/command-sequencer.ts` 确保 `upload_image` 单指令超时预算 > 边缘"下载+CDP+后置校验"预算（提高 `upload_image` 的 `timeoutMs` 或文档化边缘上限），使边缘先返回干净 `ok:false`（:162-165）。验证：慢下载边缘桩在云端超时前先回 `image_fetch_failed`
- [ ] 1.6 `src/publish-agent/roles/publish-executor.ts:129,192-211` `executePublishSequence` 后 `result.imagesOk===false` 时**回正预存 `imageUrl`**（置空 / 标 `imagesAttached=false`），使纯文字帖不留"有图"假信号。验证：降级一次落库无伪造有图信号

## 2. aidcp-edge — upload_image（CDP 文件输入桥）

- [ ] 2.1 `src/cdp/file-input-setter.ts`（新）定义 `FileInputSetter` 接口 + `CdpFileInputSetter`：`DOM.enable`（once、幂等守护）→ `Runtime.evaluate({returnByValue:false})` 取 input `objectId` → `cdp.send('DOM.setFileInputFiles',{objectId,files})`；stale-handle 单次有界重解析重试（不无限循环）；由 `session.cdp` 单例构建。验证：`typecheck` 过、最多一次重试
- [ ] 2.2 `src/flows/image-uploader.ts`（新）`ImageUploader`：注入 `fetchImpl` + `FileInputSetter`；线性流程 URL 校验 → 下载到临时文件（**私有方法**，非单独 module）→ 解析+经 `FileInputSetter` 设置 → 后置校验控件成功态（绑定式轮询，**非仅 `input.files.length>0`**）→ `finally` 清理。验证：成功路径设文件+见缩略图+清理；各失败路径回正确分类 error 且仍清理
- [ ] 2.3 `src/flows/image-uploader.ts` 下载私有方法：`globalThis.fetch`（注入 `fetchImpl`）+ `AbortController`/`AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` + `redirect:'error'` + `Content-Length` 预检与流式字节上限（`AIDCP_*` env，默认 ~10MB）+ magic-byte（jpeg/png/webp）+ `mkdtemp` 于 `os.tmpdir()/aidcp-img-*` 随机名。验证：超时→`image_fetch_failed`；超限→`image_too_large`；非图→`image_format_unsupported`；非 https→`image_url_rejected`；3xx→`image_fetch_failed`
- [ ] 2.4 `src/flows/anchors.ts` 加文件输入 / 缩略图成功态 anchors（goal/anchorHint，**来自 task 0 校准**）；未命中诚实 `no_target`。验证：jsdom fixture 定位命中；无 input → `no_target`
- [ ] 2.5 `src/flows/publish-command-handlers.ts:210` 用 `ImageUploader` 替换 `upload_image` 的 `notImplemented` 桩，结果经 :245-249 verbatim 回报。验证：AC-MEDIA 成功→`ok:true`；各失败→`ok:false`+真实 error，绝不 `ok:true`

## 3. aidcp-edge — set_cover

- [ ] 3.1 `src/flows/anchors.ts` 加封面入口 / 封面激活态 anchors（**来自 task 0 校准**）。验证：jsdom fixture 定位命中
- [ ] 3.2 `src/flows/publish-command-handlers.ts:211` 用 `runAtom` + **封面专用 validator**（断言所选图真成为当前封面，非仅点到）替换 `set_cover` 的 `notImplemented` 桩。验证：点击未改封面态→`ok:false`；真改封面→`ok:true`

## 4. aidcp-edge — 放开 v1 带图硬拒（显式改道）

- [ ] 4.1 `src/flows/publish-post.ts:294-296` 把"images are not supported in phase one"静默丢弃改为**显式报错指向指令路径**。验证：v1 `publishPost` 带图返回 `ok:false` + 改道 error（绝不静默丢图、绝不假成功）；不在 v1 加上传步骤

## 5. aidcp-edge — 接线 + 临时目录清扫

- [ ] 5.1 `src/main.ts:154-159` 由 `session.cdp` 构建 `CdpFileInputSetter` + `ImageUploader`（默认 `fetchImpl`）传入 `PublishCommandDispatcher`；复用既有 `session`/`cache`/`cdp` 单例。验证：dispatcher 正常构造；无重建 session/cdp
- [ ] 5.2 `src/main.ts`（boot）启动时 best-effort `rm({recursive,force})` 清扫 `os.tmpdir()/aidcp-img-*` 残留。验证：植入的陈旧 `aidcp-img-*` 目录被清；清扫仅命中该前缀（绝不碰 isales/其它 tmp）

## 6. 验收（中控触发，落 sub-repo 执行）

- [ ] 6.1 edge AC-MEDIA：`test/flows/publish-command-handlers.test.ts:140-149` 删 `upload_image`/`set_cover` 的 `kind_not_implemented` 锁；加成功（`FakeFileInputSetter` 记录临时路径 + jsdom 渲染缩略图、fake fetch 返回合法字节）→ `ok:true`+清理。验证：通过
- [ ] 6.2 edge AC-MEDIA 失败四路：下载超时→`image_fetch_failed`；非图→`image_format_unsupported`；无 input→`no_target`；**后置校验失败（红线反例：`FakeFileInputSetter` 设了 files 但不渲染缩略图）→ `image_not_attached`**。验证：各回精确 error，`input.files.length>0` 单独不被当成功
- [ ] 6.3 cloud AC-MEDIA-SEQ：`images=[a,b]` 时 sequencer 在 `select_mode` 后 / `fill_field` 前 emit `upload_image×2`、随后条件 `set_cover`，提交/抓取仍受人审闸。验证：顺序与授权闸正确
- [ ] 6.4 cloud AC-MEDIA-DEGRADE（两路）：`upload_image` 回 `ok:false` **与** 抛超时 → `imagesOk=false`、不下发 `set_cover`、文字/元数据照走、提交仍受人审、executor 回正 `imageUrl`。验证：两路均通过
- [ ] 6.5 cloud AC-PUB 回归（精化）：在 **executor 授权闸**（`publish-executor.ts:184-190`）断言未授权时零下发；`buildCommandSequence` 截止作为冗余下层守护保留。验证：未授权发零指令

## 7. 双仓全量回归（先 acceptance 再全量再 typecheck）

- [ ] 7.1 edge：`cd ../aidcp-edge && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；AC-PROTO-*（无协议漂移、消息数 54）、AC-PUB-*、AC-RISK-* 全过
- [ ] 7.2 cloud：`cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；两份 protocol.ts MessageType 键仍不漂移
- [ ] 7.3 中控：`openspec validate publish-media-upload --strict` 通过；确认 `docs/protocol.md` 头部计数仍 54、无需加表行（doc-only no-op）

## 8. 部署（ECS 安全序列 + 实机；执行前先做 §0 前置检查；与 A 全阶段统一）

- [ ] 8.1 §0 前置检查：`ls -d ../aidcp-edge ../aidcp-cloud` + 私钥 `~/codes/isales-4.pem` 存在且 `chmod 600`；缺失即停手告知
- [ ] 8.2 ECS 经 SSH 确认 `/opt/aidcp/cloud/.env` 是否设 `WANXIANG_API_KEY`（**不记录值**）。验证：已设则部署后配图路径可被触达；未设则本能力标"已合入、休眠待 key"而非"已上线"
- [ ] 8.3 ECS 部署 cloud 安全序列（备份 → dry-run rsync 暴露范围 → `rsync --exclude .env/node_modules/.git` → `systemctl restart aidcp-cloud.service` → healthcheck active+8787+飞书+PG → 失败回滚）；**绝不碰 isales**
- [ ] 8.4 运营机 edge 跑、连 `ws://121.89.85.150:8787`，gated `AIDCP_E2E` 实机验证配图端到端：锚点 + 控件成功态 + `redirect:'error'` + 降级真相落库

## 备注（设计已明确排除/延后，非本 change 范围）

- 多图选择与 CoverSelector 多图逻辑（云端 `imageCount` 写死 1；本 change 循环已计数无关但不建多图生成）→ 后续云端单独 change。
- 视频上传（`upload_video` / mp4 magic-byte / 更大上限）→ 保留；落地时建议复用 `upload_image` 加 `mediaType` 参数而非新 kind，以维持消息数 54。
- `FileChooser` 拦截兜底仅当 task 0 证实懒加载输入才建（slots 于 `FileInputSetter` 接口后）。合成 drag-drop / 粘贴（`isTrusted=false`）完全不在范围。
- v1 整页路径整体下线 → 另案；本 change 仅改其带图分支为显式改道。
- 远程/转发 CDP（浏览器与 edge 异机）→ 不在范围；`FileInputSetter` 为未来 swap 点。
- DashScope URL 过期的 re-host/regenerate-on-approve → 已知运营缺口、不建；若降级率高再开案。
