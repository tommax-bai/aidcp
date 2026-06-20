# publish-pipeline

本 change 是 A 重构发帖流水线的**配图收口**：把 stage-4（`publish-trigger-and-apply`）已在 spec 描述、但按五项收敛**延后实装**的
配图应用真正接通，并补齐设计探针阶段发现的**更硬的不变量**。下列 requirement 名与 stage-1/2/3/4 的 `publish-pipeline` delta
**互不重叠、互不矛盾**——它们是对 stage-4「配图 emit / 边缘配图处理器 / 降级 / 放开硬拒」的**加固与精化**（真实后置校验、唯一 fail-fast
放宽 + 落库回正、下载安全封套、v1 显式改道而非静默丢弃），归档时依序并入同一 `publish-pipeline` spec。

## ADDED Requirements

### Requirement: 配图上传经 CDP 文件输入桥并以控件成功态真实校验

边缘 `upload_image` 处理器 SHALL 经 **CDP `DOM.setFileInputFiles`** 把已下载到本机的图片喂给发布页的文件输入控件
（复用既有 `CdpClient.send`，零新依赖；自管 `DOM.enable` + `Runtime.evaluate({returnByValue:false})` 解析 `objectId`），
而非 JS 值注入（浏览器安全机制下文件输入不可被 `value` 注入）。上传后 MUST **以该控件自身的成功态（渲染出的缩略图/预览节点）做后置校验**，
经 `LocatingEngine` 定位、绑定式轮询至超时；**MUST NOT 以 `input.files.length > 0` 作为成功的充分条件**——`setFileInputFiles` 同步无条件
填充 `files`，单看它正是要规避的假成功。定位/下载/桥接/校验任一失败 MUST 回 `ok:false` + 真实分类 error（`image_url_rejected` /
`image_fetch_failed` / `image_too_large` / `image_format_unsupported` / `no_target` / `engine_error` / `image_not_attached`），
**MUST NOT 伪造 `ok:true`、MUST NOT 伪造一个 `value` 掩盖失败**。`set_cover` SHALL 经 `LocatingEngine` 的定位+点击+**封面激活态后置校验**
（断言所选图确实成为当前封面，而非仅"点到了"）。配图主路径的具体控件形状（静态隐藏 `<input type=file>` vs 懒加载/拖拽区）与成功态选择器
MUST 经一次运营机实机 CDP 校准确定后再锁定，校准前以 `no_target` 诚实回报而非猜测命中。

#### Scenario: upload_image 经 CDP 桥并校验控件成功态
- **WHEN** 边缘收到 `upload_image {imageUrl}` 且图片下载、`DOM.setFileInputFiles` 写入成功
- **THEN** 处理器 MUST 进一步等待并校验该图的控件成功态节点（缩略图/预览）真实出现后才回 `ok:true`；成功态在超时内未出现 MUST 回 `ok:false, error:'image_not_attached'`

#### Scenario: 红线反例——以 files.length 充数当成功（禁止）
- **WHEN** 有实现在 `DOM.setFileInputFiles` 返回后立即读 `input.files.length > 0` 即回 `ok:true`，未校验控件成功态
- **THEN** MUST 视为违规、不予合入；`files.length > 0` 至多是必要条件，成功 MUST 以控件自身成功态为准，否则即「静默假成功」

#### Scenario: set_cover 校验封面真激活
- **WHEN** 边缘收到 `set_cover` 并点击目标图为封面
- **THEN** 处理器 MUST 后置校验该图已处于封面激活态才回 `ok:true`；点击未改变封面态 MUST 回 `ok:false`

### Requirement: 配图上传失败是唯一的 fail-fast 放宽且落库回正

云端 `executePublishSequence` SHALL 把 `upload_image` 失败（回 `ok:false` **或**该 kind 的超时/异常）特判为 **降级而非中断**：
置 `imagesOk = false`、**继续**下发余下文字/元数据指令、跳过依赖该图的 `set_cover`，并把 `imagesOk` 带回 `PublishSequenceResult`。
这是对逐步 fail-fast（其它任何 kind 失败 MUST 仍按序停止）的**唯一一处有意放宽，且仅限配图**——因为纯文字是诚实可接受的结果、而标题失败不是；
该放宽 MUST 有显式注释与 AC 锁定，防止后人误"修"回中断。`set_cover` SHALL 为**执行期条件下发**（全部 `upload_image` 成功才下发），
非构建期固定 emit。`PublishExecutor` 在 `imagesOk === false` 时 MUST **回正已预存的 `imageUrl`**（置空或标 `imagesAttached=false`），
使 `publish_log` 不在纯文字帖上留下"有图"假信号。若实机校准证实发布页编辑器被"成功传图"门控（无图则标题/正文不可填），则**全图失败 MUST 转为诚实
`failed` 而非纯文字帖**。

#### Scenario: 配图失败降级纯文字、imagesOk 如实、落库回正
- **WHEN** `upload_image` 回 `ok:false`（或该指令超时）
- **THEN** sequencer MUST 置 `imagesOk=false`、不下发 `set_cover`、继续文字/元数据指令至 `submit`（仍受人审闸），`PublishExecutor` MUST 回正预存 `imageUrl` 使落库记录为纯文字真相

#### Scenario: 非配图指令失败仍 fail-fast
- **WHEN** `fill_field(title/content)` 或 `set_option` 回 `ok:false`
- **THEN** sequencer MUST 仍按既有逐步 fail-fast 停止于该步、记 `failedAt`，**MUST NOT** 套用配图的降级继续语义

#### Scenario: 红线反例——降级回正缺失致观测面假成功（禁止）
- **WHEN** 配图失败已降级纯文字，但 `publish_log` 仍保留生成的 `imageUrl`，下游据此判定该帖"有图"
- **THEN** MUST 视为违规、不予合入；降级 MUST 伴随 `imageUrl` 回正 / `imagesAttached=false`，杜绝纯文字帖被读成带图

### Requirement: 配图 URL 下载安全封套与临时文件生命周期

边缘下载配图 SHALL 施加与"来源为本方云端"相称的纵深防御（非全量 SSRF 代理）：① 仅接受 `https:`（`http:` 仅在显式测试 env 下），
拒绝 `file:` / `data:` / `blob:` / `ftp:`；② **`redirect:'error'`**（拒绝任何 3xx，防原始 URL 白名单被首跳重定向绕过到内网/本地）；
③ `Content-Length` 预检 **+ 流式累计字节上限**（Content-Length 可伪造），超限中断回 `image_too_large`；④ 以 **magic-byte** 判定
jpeg/png/webp（非扩展名 / 非仅凭 Content-Type 头），非图回 `image_format_unsupported`；⑤ `AbortController` + `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS`
显式超时，且边缘"下载+CDP 设置+后置校验"总预算 MUST **低于云端单指令超时**，确保慢/过期 URL 时边缘先返回干净 `ok:false` 而非把整条序列拖到云端超时中断；
⑥ 临时文件 MUST 用 `mkdtemp` + 随机名落在专用 `os.tmpdir()/aidcp-img-*` 前缀（非可预测静态路径），`finally` 必清理，并在启动时清扫该前缀的崩溃残留
（单一前缀，MUST NOT 触碰同机 isales 或其它 tmp）。文档/日志 MUST NOT 记录密钥或敏感值，只记路径约定。

#### Scenario: 过期/慢 URL 在云端超时前先返回降级
- **WHEN** DashScope 图 URL 已过期或下载缓慢
- **THEN** 边缘 MUST 在云端单指令超时前因 `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` 触发 `image_fetch_failed` 回 `ok:false`，由云端按配图降级处理，而非拖致整条序列被云端超时中断

#### Scenario: 重定向与非图被拒
- **WHEN** 图 URL 返回 3xx 重定向，或响应体非 jpeg/png/webp magic-byte
- **THEN** 下载 MUST 分别因 `redirect:'error'` 与 magic-byte 校验失败回 `ok:false`（`image_fetch_failed` / `image_format_unsupported`），绝不把重定向目标或非图字节喂给文件输入

#### Scenario: 临时文件清理与崩溃残留回收
- **WHEN** 一次 `upload_image` 完成（成功或失败），以及边缘进程崩溃后重启
- **THEN** 当次临时文件 MUST 在 `finally` 清理；重启时 MUST 清扫 `os.tmpdir()/aidcp-img-*` 前缀残留，且清扫范围 MUST NOT 越出该前缀

### Requirement: v1 整页路径带图显式改道而非静默丢弃

v1 整页发布路径（无上传步骤）收到带图 payload 时 SHALL **显式报错改道指令驱动路径**，MUST NOT 再返回
`images are not supported in phase one` 硬拒、更 MUST NOT 静默丢图后按纯文字假成功。本 change MUST NOT 在近废弃的 v1 路径内新建上传能力、
亦不整体删除 v1（属另案）。

#### Scenario: v1 带图改道指令路径
- **WHEN** v1 `publishPost` 收到 `images.length > 0`
- **THEN** MUST 回 `ok:false` 并显式指向指令驱动路径（配图经 `upload_image` 处理），MUST NOT 静默丢图、MUST NOT 假报成功

#### Scenario: 红线反例——v1 静默丢图后假成功（禁止）
- **WHEN** v1 路径丢弃 `images` 后仍按纯文字返回 `ok:true`
- **THEN** MUST 视为违规、不予合入；带图在 v1 MUST 显式失败改道，绝不静默降级伪装成功
