## Context

`aidcp-edge` 已具备 AdsPower profile 生命周期和 CDP 基础设施，昨日的 TikTok 探针也证明了“独立手动探针 + 双重动作授权 + 代码级 no-submit”可以在不接入生产协议的前提下获得真实页面证据。抖音与 TikTok 虽同为短视频网页，但不是同一产品表面：域名、登录体系、页面路由、作品标识、列表容器、创作者平台和开放 API 均不同，不能共享选择器或直接继承动作成功语义。

2026-07-22 对本地 `k1evgky5` 的只读观察得到以下证据：

- profile 对应的 Chromium 正在运行，AdsPower active API 在其他会话占用时可能返回 `Inactive`；profile 的 `DevToolsActivePort` 仍可给出动态 CDP 端口，且 `start.adspower.net/?id=k1evgky5` marker 可精确证明 profile 归属。
- `https://www.douyin.com/jingxuan` 可正常加载，没有可见安全验证 iframe、访问受限提示或阻断 dialog；页面存在登录按钮和手机号登录表单，说明抖音账号当前未登录。
- 精选页在一个 `overflow:auto` 的内部容器中承载作品卡片，`window.scrollBy` 不会推进内容。该容器当前包含 52 个唯一 `data-aweme-id`；页面另有导航和横向 tab 滚动容器，不能选择“第一个可滚动元素”。
- 未登录状态可观察精选卡片，但单作品互动控件、评论编辑器和创作者上传页不能形成有效验收证据；这些必须在用户手工登录后重新调研。

抖音开放平台当前提供网站应用 OAuth、`video.create` 权限、视频上传与创建、授权账号视频列表和视频数据查询。官方文档还明确要求代用户创建视频时，除授权外，每次调用都要在产品设计中让用户明确感知。由此，正式发布应优先走官方 API；网页 CDP 只用于调研页面能力和补充尚无官方接口的窄交互，不作为绕开授权的发布通道。

## Goals / Non-Goals

**Goals:**

- 复用现有 AdsPower + CDP 原语，安全连接一个精确指定且可自证归属的本地抖音 profile。
- 建立适配精选卡片流和单作品详情的页面探测模型，以稳定作品 ID 和有界推进证明浏览变化。
- 为点赞建立默认 shadow、双重显式授权、单向动作和同作品前后确认的设计。
- 为评论建立只有 fill API、没有 submit API 的代码级安全边界。
- 只读调研网页创作者/上传表面，并给出正式发布采用抖音开放平台的后续架构边界。
- 对登录、可见验证、访问限制、目标歧义和确认超时诚实失败，并输出最小化脱敏证据。

**Non-Goals:**

- 不注册 `douyin` 为生产 `PlatformId`，不修改 Cloud command mapping、调度、持久化、发布队列或风险状态机。
- 不绕过验证码、实名、登录、账号限制或平台安全措施，不调用网页私有接口。
- 不实现批量浏览、批量点赞、关注、收藏、评论发送、私信或最终网页发布。
- 本变更不选择上传文件、不创建平台草稿、不调用抖音开放平台上传/创建接口。
- 不保证本次页面结构可跨灰度实验长期稳定，也不把 UI 状态宣称为服务端持久化事实。

## Decisions

### 1. 抖音使用独立探针模块，不复用 TikTok 选择器或注册生产平台

在未来的 `aidcp-edge` change worktree 中新增 `src/douyin/probes/` 和独立 runner。可以复用 CDP transport、AdsPower API client 和通用可见性工具，但抖音的页面探测、作品身份、阻断状态和动作结果类型必须独立定义。

备选方案是给 TikTok 模块增加域名分支，或立即增加生产 `PlatformId`。前者会把两个持续分化的网页契约耦合在一起；后者在登录后详情页和创作者页尚未验收时扩大协议与风险范围，因此均不采用。

### 2. 连接前要求 profile 所有权证据，并区分拥有生命周期与仅附着

首选使用 AdsPower API 获取目标 profile 的动态 `debug_port` 和生命周期状态。如果 API 因 profile 被当前桌面会话占用而无法返回活动信息，runner 可显式使用 profile cache 中的 `DevToolsActivePort`，但必须同时满足：

1. 进程 `--user-data-dir` 精确指向目标 profile cache；
2. `/json/list` 中存在 `start.adspower.net` marker；
3. marker 的 `id` 与目标 profile 完全一致。

任何一项不满足都返回 `ownership_unconfirmed`。fallback 只拥有 CDP 附着权，不拥有浏览器生命周期，运行结束不得关闭该浏览器。

备选方案是扫描本机端口后连接第一个可用 CDP endpoint；这可能驱动错账号，故不采用。

### 3. 阻断判断只使用可见、结构化证据，并规定优先级

阻断优先级为：可见访问限制 → 可见安全验证/挑战 → 页面损坏 → 登录状态 → 页面能力。隐藏的验证码 iframe、登录表单字段中的“验证码”文本、后台预加载节点都不能单独判定为 challenge。

探针报告统一区分 `access_restricted`、`visible_challenge`、`page_unavailable`、`login_required` 和 `ready`。遇到前三类状态时不得继续动作；浏览可在未登录公开表面继续观察，但点赞、评论和发布调研必须返回 `login_required`。

备选方案是扫描 `body.innerText` 关键词；本次观察已证明未登录手机号表单会导致“验证码”假阳性，因此不采用。

### 4. 浏览使用 surface adapter、稳定作品 ID 和目标容器归属

浏览探针先识别 surface：

- `jingxuan_grid`：以 `data-aweme-id` 为作品身份，从唯一拥有作品后代且可纵向滚动的容器推进；
- `video_detail`：以规范 URL、页面 `data-aweme-id` 或二者一致性确定当前作品，并使用详情页自身的下一条/滚动机制；
- 其他 surface：只报告结构，不猜测动作。

每次推进前后重新扫描、去重并比较作品 ID 集合，不缓存 DOM node，不用 `nth-child`，也不默认滚动 `window` 或第一个可滚动元素。有界尝试后作品集合未变化时返回 `no_change`，而不是假报已浏览。

备选方案是按卡片文本、列表序号或视频播放状态识别内容；这些证据会受推荐排序、节点复用、自动播放和文案变化影响，故不采用。

### 5. 点赞保持双重运行门、单向动作和同作品确认

真实点赞必须同时满足：

- `AIDCP_DOUYIN_PROBE_LIKE=1`；
- `AIDCP_DOUYIN_PROBE_CONFIRM_PROFILE` 与实际 profile 精确相等；
- 抖音已登录，页面无阻断；
- 当前作品 ID 唯一，点赞控件唯一且状态可读。

默认仅返回 `shadow_ready`。已点赞时返回 `already_liked` 且绝不点击；未点赞时最多点击一次，并在重新探测后要求同一作品变为 liked，才返回 `ui_confirmed`。作品变化、控件歧义或状态未闭环均返回 `ambiguous`，不得重试点击或宣称服务器已持久化。

备选方案是单布尔开关、按计数变化确认或点击后盲等；前两者易误用/误判，后者可能造成重复动作，故不采用。

### 6. 评论探针在类型和 DOM 行为上都没有发送能力

评论 API 只接受 `fillComment(videoId, text)`，实现只定位唯一可见编辑器、聚焦、使用 CDP 输入文本并回读长度/匹配结果。源码不得查询发送按钮，不得派发 Enter、Ctrl+Enter 或 Meta+Enter，不得调用 `form.submit()`/`requestSubmit()`，也不暴露 `submit` 参数或环境变量。

输入前后都重新确认同一作品 ID。成功结果固定为 `filled_not_submitted` 且 `submitted=false`；目标变化、编辑器不唯一或回读不匹配均诚实失败。聚焦测试须包含静态 no-submit 断言。

备选方案是复用未来生产评论 executor 的 dry-run 分支；该路径仍拥有发送能力，配置错误会突破用户边界，因此不采用。

### 7. 正式发布优先官方 API；网页发布探针本期只读

本期网页探针最多发现创作者/上传入口、路由、文件输入 accept/multiple、编辑器和阻断状态，不选择文件、不填写文案、不寻找或点击最终发布控件，结果固定包含 `uploaded=false`、`submitted=false`。

未来正式发布另建 OpenSpec change，推荐数据流为：

`用户批准 → 抖音 OAuth 授权 → /video/upload/ → /video/create/ → item_id → /video/list/ 或 /video/data/ 回查审核/公开状态`

Cloud 负责审批、调度、token 生命周期、幂等和最终状态；Edge 不保管开放平台 client secret。`/video/create/` 的调用必须绑定可审计的本次用户批准，不得仅依赖历史 OAuth 授权。若官方应用/权限尚未审核通过，产品状态必须是 `official_api_unavailable`，不能自动降级到网页最终提交。

备选方案是直接把创作者网页 CDP 作为生产发布器；它缺少稳定契约和可靠服务端回查，也弱化官方要求的每次用户感知，因此不采用。

### 8. 证据最小化并显式区分 UI、官方 API 和未知状态

结构化报告只允许记录 profile id、host/path、surface、作品 ID、动作门状态、元素候选数、阻断类别、状态枚举和时间戳。不得读取或输出 cookie、local/session storage、token、手机号、完整正文、评论列表、请求或响应正文。

状态名必须携带证据边界：CDP 只能产生 `observed`、`shadow_ready`、`ui_confirmed`、`filled_not_submitted` 等 UI 结果；只有未来官方 API 的 `item_id` 和回查结果才可进入服务端发布状态。未知或超时保持 `ambiguous`/`unknown`，不得映射成成功。

## Risks / Trade-offs

- [抖音页面 DOM、语言或灰度实验变化] → 使用作品 ID、route、role、可见性和容器归属的组合证据；候选不唯一时失败并更新 fixture。
- [隐藏验证 iframe造成误阻断] → 只把可见且占据页面的验证结构视为 challenge，并为隐藏 iframe 建测试。
- [内部滚动容器选择错误] → 要求候选容器拥有作品后代且纵向可推进；导航和横向 tab 容器必须被排除。
- [点赞 UI 乐观更新但服务端未持久化] → 结果命名为 `ui_confirmed`，不宣称服务端成功；正式能力需另行设计回查。
- [评论草稿被网页本地保存] → no-submit 只保证不发送，不保证没有本地草稿；真实 fill 必须另获明确授权并由操作员清理。
- [官方发布权限或应用审核不可用] → 显示 `official_api_unavailable` 并停止，不回退到网页提交。
- [已运行 profile 被其他操作者占用] → 仅附着模式不控制生命周期；任何 target 不唯一或 ownership 不完整都停止。
- [当前未登录，详情/创作者页证据不完整] → 将登录后结构调研列为实现前置验收，不能从未登录页面推断选择器。

## Migration Plan

1. 在独立 `aidcp-edge` worktree 实现纯探测模块、runner 和 fixture 测试，不接生产导出或 command router。
2. 先用 `k1evgky5` 运行只读预检，复现精选页、隐藏验证 iframe、内部滚动容器和稳定作品 ID 证据。
3. 用户手工完成抖音登录后，先重新运行只读结构探针；未经新的明确授权，不执行点赞、评论输入、上传或发布。
4. 通过聚焦测试、静态 no-submit 检查和 Edge typecheck；只提交探针代码，不部署、不打安装包。
5. 如需生产接入，另建跨 Edge/Cloud/Console 的 OpenSpec change，先完成抖音开放平台应用、权限、OAuth、批准和回查设计。

回滚仅需移除独立探针模块、runner 和测试；本变更不修改生产数据、协议或运行时路由。

## Open Questions

- 用户手工登录 `k1evgky5` 后，精选卡片进入单作品详情的稳定 route、点赞状态属性和评论编辑器语义分别是什么？
- 抖音创作者网页当前的上传入口、文件 input、文案编辑器和草稿持久化边界是什么？本期只读观察能否获得足够证据？
- AIDCP 计划申请哪一种抖音开放平台应用，是否已具备 `video.create`、`video.list`、`video.data` 和所需互动管理权限？
- 产品首期目标是仅做研究探针，还是在官方权限到位后优先交付“人工批准的一键发布 + 状态回查”？
