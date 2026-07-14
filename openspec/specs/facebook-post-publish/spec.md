# facebook-post-publish Specification

## Purpose
TBD - created by archiving change facebook-post-publish. Update Purpose after archive.
## Requirements
### Requirement: Facebook 发帖图片素材池按账号管理

系统 SHALL 为 Facebook 账号提供独立的发帖图片素材池。运营在控制台按账号批量上传图片后，cloud MUST 校验图片类型与大小、通过可注入 `ObjectStore` 转存到 OSS 稳定公网 URL，并把图片写入该账号的素材池。素材池 MUST 记录图片组、组内顺序、状态、原文件名、内容类型、字节数、sha256、OSS URL、可选素材说明、创建/更新时间。素材池写入 MUST 先确认账号存在且 `accounts.platform === 'facebook'`，MUST NOT 为不存在账号、退役账号、或非 Facebook 账号创建素材。上传失败、OSS 未配置、类型非法、大小超限时 MUST 诚实拒绝，MUST NOT 写入假 URL 或本地临时路径。

#### Scenario: Facebook 账号批量上传图片成功
- **WHEN** 运营在控制台为一个已存在的 Facebook 账号批量上传 3 张合法图片，且 OSS 上传能力就绪
- **THEN** cloud SHALL 把 3 张图片转存为 OSS 稳定公网 URL，并为该账号写入 3 个默认单图图片组，状态均为 `available`

#### Scenario: 非 Facebook 账号不能写入 FB 发帖素材
- **WHEN** 运营请求为一个 `accounts.platform='xiaohongshu'` 的账号上传 Facebook 发帖图片
- **THEN** API SHALL 返回拒绝原因（如 `platform_not_supported`），MUST NOT 写入任何素材行或 OSS 假记录

#### Scenario: OSS 上传失败不写假素材
- **WHEN** 某张图片校验通过但 OSS `put` 失败或未配置
- **THEN** 该图片 SHALL 不进入素材池，API SHALL 如实返回失败项与原因，MUST NOT 存储本地临时路径、占位 URL、或伪造 OSS URL

### Requirement: Facebook 草稿从账号素材池锁定图片组

Facebook 发帖草稿生成时，系统 SHALL 从该账号素材池选择下一组 `available` 图片组并原子锁定为 `reserved`，把该组 OSS URL 按顺序写入 `publish_log.images`，并记录 `reserved_record_id`。素材不足时 MUST fail-closed：不生成可发布草稿、不调用 edge、不改走纯文字发布、不复用已用素材。草稿被人审拒绝或在提交前失败时，系统 SHALL 将对应图片组释放回 `available`；提交已发生但确认不明时 SHALL 标记 `quarantine`；服务端确认发布成功后 SHALL 标记 `used` 并记录 `used_record_id`。状态转换 MUST 与发布记录保持一致，MUST NOT 静默重复消费同一图片组。

#### Scenario: 生成 FB 草稿时锁定下一组图片
- **WHEN** 某 Facebook 账号有至少一组 `available` 图片，排期或手动发布触发草稿生成
- **THEN** 系统 SHALL 原子锁定排序最靠前的可用图片组为 `reserved`，把该组图片 URL 写入 `publish_log.images`，并把 `reserved_record_id` 指向该草稿

#### Scenario: 素材不足不生成可发布草稿
- **WHEN** 某 Facebook 账号没有 `available` 图片组
- **THEN** 发布触发 SHALL fail-closed 并返回“图片素材不足”类原因，MUST NOT 生成可提交草稿、MUST NOT 发布纯文字、MUST NOT 复用 `used` / `reserved` / `quarantine` 素材

#### Scenario: 人审拒绝释放素材
- **WHEN** 一个使用素材池图片的 Facebook 草稿在人审中被拒绝，且尚未下发提交
- **THEN** 该草稿关联图片组 SHALL 从 `reserved` 释放回 `available`，并清除 `reserved_record_id`

#### Scenario: 提交后确认不明隔离素材
- **WHEN** edge 已可能点击 Facebook Post，但没有取得可靠服务端确认
- **THEN** 关联图片组 SHALL 标记为 `quarantine`，MUST NOT 自动释放为可用，也 MUST NOT 自动重试该草稿

### Requirement: Facebook 个人主页发帖执行器支持宽窄布局且独立于 XHS

edge SHALL 提供 Facebook 发帖执行器，负责个人主页/首页 composer 的打开、聚焦、正文逐字输入、图片上传、提交与确认。该执行器 MUST 使用 Facebook driver 的 `publish` 能力装配，MUST NOT 调用 XHS 发布 URL、XHS 发布 tab、XHS 标题/话题/封面处理器。执行器 MUST 覆盖宽屏与窄屏桌面布局，以结构定位和可见性判断为主，MUST NOT 依赖固定坐标或宽屏专属导航。正文输入 MUST 使用逐字符的拟人化键盘节奏，MUST NOT 通过一次性整段粘贴或一次性 `Input.insertText` 灌入正文。当前页面的 dialog 消失或明确正向提交提示 SHALL 表示用户可见的“已提交”；只有从当前页面取得稳定帖子 ID/permalink 才能表示“已发布”。正常发布链路 MUST NOT 通过刷新页面获得该结论。提交前失败、页面已提交但链接缺失、以及已取得链接 MUST 区分上报。

#### Scenario: 宽屏 composer 可打开并输入
- **WHEN** Facebook edge 在 `1365x900` desktop viewport 收到 no-submit composer probe
- **THEN** 执行器 SHALL 打开 composer、聚焦正文编辑器、逐字输入并清空测试文本，且不提交任何内容

#### Scenario: 窄屏 composer 可打开并输入
- **WHEN** Facebook edge 在 `430x932` 或 `768x900` desktop viewport 收到 no-submit composer probe
- **THEN** 执行器 SHALL 通过结构定位完成 composer 打开、聚焦、逐字输入、清空，MUST NOT 依赖宽屏导航或固定坐标

### Requirement: 正文填写的单步预算随长度伸缩，且边缘必先于云端答复

逐字符输入是 O(正文长度) 的操作，MUST NOT 由云端用与长度无关的常数窗口去等它——否则云端先判失败、边缘仍在往活着的编辑器里写字，形成「记录已 failed、页面上却躺着半篇正文」的错位。

cloud SHALL 按正文长度算出 Facebook `fill_field` 的执行预算，随指令下发（`PublishCommandPayload.timeoutMs`）。云端等待窗口 SHALL 为「下发预算 + 兜底余量」，使边缘**必定先答**；该 timer 的语义 SHALL 退化为「边缘真的失联」的兜底，MUST NOT 作为正常路径的收敛手段。指令**不带**预算时（小红书全路径）等待窗口 MUST 逐字节沿用既有常数窗口。

预算上限 MUST 严格小于边缘发布租约 TTL（安全比例 0.4），否则边缘会在打字途中单方面过期租约、恢复浏览循环去驱动半写的编辑器。正文长度超出预算上限所能打完的范围时，cloud MUST 诚实失败（`content_too_long`）并 MUST NOT 截断正文发出。

edge SHALL 按下发预算自我掐表：预算耗尽即停止输入、清空编辑器、诚实回报，MUST NOT 继续写入已被上游放弃的编辑器。清场失败 MUST 如实上报（而非谎报干净页）。

#### Scenario: 长正文在下发预算内打完
- **WHEN** 云端为一篇 300 字正文下发按长度算出的 `fill_field` 预算
- **THEN** edge SHALL 在预算内逐字输完全文并通过校验；cloud MUST NOT 在边缘答复之前判超时

#### Scenario: 预算耗尽即停手清场
- **WHEN** 正文在下发预算内打不完
- **THEN** edge SHALL 停止输入、清空编辑器、回报 `fill_deadline_exceeded`（清不干净则回报为 dirty），MUST NOT 提交，MUST NOT 让输入循环继续写入编辑器

#### Scenario: 正文超出可打完的上限
- **WHEN** 正文长度超出预算上限所能容纳的字符数
- **THEN** cloud SHALL 诚实 `failed`，MUST NOT 截断正文，MUST NOT 下发任何指令

### Requirement: 正文校验必须回读全文

「插入调用没报错」不等于「文本进去了」。正文校验 MUST 回读编辑器**全文**并确认完整包含终稿正文；MUST NOT 以正文前缀片段作为接受判据——前缀探针会把「编辑器吞掉正文主体」判成成功，从而真的发出一篇被截断的帖子。

编辑器内出现超出终稿正文的额外内容（如打字途中被 typeahead 劫持插入）MUST 视为失败，MUST NOT 提交。

打字前 edge MUST 先清空编辑器并校验其为空：composer 复用已存在的编辑区、输入在光标处追加，不清空即会把上一次失败留下的残稿与本篇拼接后发出。

#### Scenario: 编辑器吞掉正文主体
- **WHEN** 编辑器只接受了正文的前若干字符，其余被静默丢弃
- **THEN** edge SHALL 回报 `content_not_accepted` 并清空编辑器，MUST NOT 判成功、MUST NOT 提交

#### Scenario: composer 带着上一篇残稿
- **WHEN** 打开的 composer 内已存在上一次失败留下的正文
- **THEN** edge SHALL 先清空并校验为空再开始输入；清不干净则回报 `composer_not_clean`，MUST NOT 在残文之上追加

#### Scenario: 不调用 XHS 发布器
- **WHEN** Facebook 账号执行发布下发
- **THEN** edge SHALL 走 Facebook 发帖执行器，MUST NOT 导航到 XHS creator URL、MUST NOT 选择“上传图文”tab、MUST NOT 执行 XHS topic/cover/title 专用步骤

#### Scenario: 页面已提交但未取得链接
- **WHEN** Post 按钮点击后，当前页面的 composer 消失或出现正向提交提示，但同页没有稳定帖子 ID/permalink
- **THEN** edge SHALL 返回 `submitted_unconfirmed` 或等价可区分状态，cloud SHALL 将发布记录置为用户可见的 `submitted`，展示“已提交，待链接确认”，并隔离素材；系统 MUST NOT 刷新页面、MUST NOT 报失败、也 MUST NOT 自动重试

#### Scenario: 同页帖子链接确认发布
- **WHEN** Post 按钮点击后，当前页面取得稳定帖子 ID/permalink
- **THEN** edge SHALL 返回 `published_confirmed`，cloud SHALL 将发布记录置为 `published` 并将素材标记为 `used`

### Requirement: Facebook 发帖真实提交受显式探针门禁保护

Facebook 发帖真实提交 SHALL 在 no-submit composer 和媒体探针通过后才能启用。真实写入探针 MUST 仅允许在操作员自有 disposable Facebook 账号/目标上运行，并要求显式环境门禁；成功判定 MUST 是 reload/server confirmation，而不是按钮点击或乐观 DOM。探针输出 MUST 只包含状态、计数、哈希和原因码，MUST NOT 输出 raw cookie、raw token、raw 评论/正文秘密或未脱敏账号敏感信息。

#### Scenario: 无门禁时真实提交被阻止
- **WHEN** 运行 Facebook real-submit probe 但缺少任一显式门禁或 disposable 确认
- **THEN** probe SHALL 在提交前停止并返回 blocked reason，MUST NOT 点击 Post

#### Scenario: 真实提交以服务端确认为成功
- **WHEN** gated real-submit probe 在 disposable 目标上执行并点击 Post
- **THEN** 只有 reload/server confirmation 或稳定 permalink 证据出现时才判成功；否则 SHALL 返回未确认状态，MUST NOT 把点击动作本身当成功

#### Scenario: 探针输出脱敏
- **WHEN** probe 输出结果
- **THEN** 结果 SHALL 只含布尔值、数量、哈希、状态和原因码，MUST NOT 输出 raw token、cookie、正文全文或账号敏感字段

### Requirement: 控制台提供 Facebook 发帖素材管理

控制台 SHALL 在 Facebook 账号配置中提供发帖素材管理入口，展示可用/已锁定/已使用/停用/隔离图片组数量，并支持批量上传、缩略图预览、排序、素材说明、停用与删除。写操作 MUST 非乐观：只有服务端写入成功并回读真态后，前端才显示成功状态。非 Facebook 账号 MUST NOT 展示该入口。删除/停用已 `reserved` 或 `quarantine` 的图片组 MUST 有明确限制或确认文案，MUST NOT 静默破坏在途草稿。

#### Scenario: Facebook 账号显示素材管理入口
- **WHEN** 账号列表中的某账号 `platform === 'facebook'`
- **THEN** 控制台 SHALL 在 FB 配置中显示发帖素材管理入口，并展示素材池状态汇总

#### Scenario: 非 Facebook 账号不显示素材入口
- **WHEN** 账号平台不是 Facebook
- **THEN** 控制台 SHALL 不展示 Facebook 发帖素材入口，避免把素材写入错误平台

#### Scenario: 上传成功后回读真态
- **WHEN** 运营上传图片并服务端写入成功
- **THEN** 控制台 SHALL 依据服务端返回的素材列表/状态刷新展示，MUST NOT 在请求未完成时乐观宣称已入库

