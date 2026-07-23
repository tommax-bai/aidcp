<!--
文档性质：TikTok 网页能力调研、抖音对照和后续研究建议。
形成时间：2026-07-23。
事实来源：TikTok / 抖音 OpenSpec、Edge 独立探针、受控真机证据、TikTok 官方开发者文档。
可信度边界：
1. “已验证”只表示指定本地 profile 和当时网页版本上的 CDP / UI 证据；
2. UI 状态不等于服务端持久化、消息送达或内容公开；
3. “官方能力”来自当前官方文档，仍受应用审核、scope、用户授权、账号权限和地区策略约束；
4. 本文是研究结论和路线建议，不是生产能力清单或行为契约。
-->

# TikTok 网页能力调研与抖音对照（2026-07-23）

## 0. 文档定位

本文回答四个问题：

1. TikTok Web 目前通过 AdsPower + CDP 实际验证了什么；
2. 内容发布网页的真实步骤和已证明边界是什么；
3. 抖音调研中哪些经验可以复用、哪些结果不能直接套用；
4. TikTok 下一阶段还应调研哪些能力，尤其是回复消息时的语言和目标安全。

状态统一使用以下口径：

| 状态 | 含义 |
| --- | --- |
| 已验证 | 在指定本地环境得到前后闭环的页面证据 |
| UI 确认 | 页面状态已变化，但未证明服务端持久化、对方收到或内容公开 |
| 只读观察 | 只读取结构，没有执行写动作 |
| 已填写未提交 | 内容进入编辑器并回读一致，代码路径不拥有发送或发布能力 |
| 待调研 | 尚无足够页面、官方权限或真机证据 |
| 明确不做 | 当前阶段主动排除，不应以 fallback 绕过 |

## 1. 一眼看完

TikTok Web 可以通过 Chromium CDP 控制，但目前只交付了隔离的研究探针，不是生产平台接入。

已经完成：

- 精确绑定本地 AdsPower profile，识别登录、挑战、访问限制和页面歧义；
- 在虚拟化信息流中重新读取稳定视频标识，执行有界浏览并证明内容变化；
- 默认 shadow、双门授权、单向且最多一次的点赞探针；
- 评论只填写不发送，输入后回读，源码没有发送按钮、回车或表单提交路径；
- 进入 TikTok Studio，选择合成视频、等待页面进入编排器、填写文案并停在最终发布之前；
- 只读观察编排器的立即发布/定时、受众、位置、高质量上传和内容检查等设置；
- 分别盘点 For You、Following 和个人主页 surface，以及搜索、消息、通知、直播、音乐等入口；
- 以 TikTok 精确控件把关注、收藏和分享报告为 shadow，不执行点击；
- 形成后续正式接入的系统设计输入，明确复用 Facebook/XHS 机制但隔离平台适配。

尚未完成：

- Following、搜索、作者主页、标签/音乐页等 surface 的生产浏览闭环；
- 关注、收藏、分享的正负状态 fixture、真实动作和后置确认；
- 评论列表读取、精确评论回复和普通评论真实发送；
- 私信、通知、直播聊天和直播定向回复；
- 图片轮播、封面、草稿恢复、定时规则和发布后回查；
- TikTok Login Kit、Display API、Content Posting API 的应用级接入；
- 生产平台枚举、Cloud 协议、调度、风控、审批、持久化和 Console 操作面。

结论：下一步不应继续寻找网页“发布”按钮。发布优先调研官方 Content Posting API；CDP 继续用于官方 API 未覆盖的窄网页交互和真机证据。

## 2. 调研环境与安全边界

### 2.1 环境

- 本地 AdsPower profile：`k1eu5amn`；
- 控制对象：TikTok Web / Chromium，不是 TikTok 原生移动应用；
- CDP 端口由 AdsPower 动态分配；
- AdsPower 本地 API 不可用但浏览器仍存活时，只允许显式端口，并要求
  `start.adspower.net/?id=k1eu5amn` marker 精确自证 profile；
- 仅附着模式只关闭探针自己的 CDP session，不接管浏览器生命周期。

### 2.2 写动作边界

- 真实点赞需要：
  - `AIDCP_TIKTOK_PROBE_LIKE=1`；
  - `AIDCP_TIKTOK_PROBE_CONFIRM_PROFILE=k1eu5amn`；
  - 当前视频唯一、点赞前明确未点赞、动作后仍是同一视频；
- 已点赞时绝不反向取消；
- 评论探针没有发送开关和发送实现；
- 发布编排器探针没有最终发布控件定位、Enter/Ctrl+Enter/Meta+Enter 或 form submit；
- 浏览器页面出现登录、验证、限制、目标歧义或后置状态不明时停止，不把输入派发当作成功。

### 2.3 隐私边界

探针不读取或输出：

- cookie、token、local/session storage；
- 网络请求或响应正文；
- 原始账号身份、手机号、私信联系人或消息正文；
- 完整评论文本。

结构化证据只保留 profile、host/path、视频标识、候选数、动作状态、文本长度和确认级别。

## 3. TikTok 已验证能力

| 能力 | 真实结果 | 证据边界 |
| --- | --- | --- |
| Profile 绑定 | 精确 marker 证明 `k1eu5amn` 与动态 CDP 端点归属 | 不允许只因端点中存在 TikTok 页面就连接 |
| 登录/阻断识别 | 可区分已登录、登录失效、挑战、访问限制和非 TikTok 页面 | 只使用可见/结构化证据 |
| 信息流浏览 | 有界 ArrowDown + 单次 wheel fallback；重新读取视频 ID，变化后才报告 browsed | 虚拟列表不缓存 DOM node，不按序号操作 |
| 点赞 | 一次未点赞 → 已点赞，点击一次，同视频 UI 状态确认 | `ui_confirmed`，不证明服务端长期持久化 |
| 评论输入 | 唯一编辑器写入 42 字符测试草稿并回读一致 | `filled_not_submitted`；未发送，之后进入上传页时草稿被放弃 |
| 上传入口 | 唯一 `data-e2e="nav-upload"` 指向 TikTok Studio | 只观察语义入口，不按坐标猜测 |
| 视频选择 | 唯一启用的 `input[type=file][accept="video/*"]`，单文件 | 文件选择可能产生平台侧暂存 |
| 编排器 | 合成视频选择后文件输入消失，出现 blob 缩略图和 canvas 预览 | 这是页面已接收/进入编排器的 UI 证据，不证明永久草稿 |
| 文案 | 唯一 `contenteditable="true" role="combobox"`；自动文件名被替换为 38 字符测试文案并回读一致 | `composer_ready_not_submitted` |
| 编排设置 | 只读观察到立即/定时、受众、位置、高质量上传、版权/内容检查 | 未操作最终发布，未验证全部设置持久化 |

### 3.1 虚拟列表经验

TikTok 信息流会复用页面节点。正确机制是：

```text
动作前读取当前视频 ID
        ↓
派发一次有界滚动或点击
        ↓
重新查询当前视频和控件
        ↓
同目标后置状态明确？──否──→ no_change / ambiguous / blocked
        │
        是
        ↓
记录 UI 证据
```

不能使用：

- 长期缓存的 DOM node；
- `nth-child` 或“第几个卡片”；
- 鼠标/键盘事件已派发作为成功；
- 点赞计数缩写变化作为唯一确认；
- 上传文件已经进入 `FileList` 作为发布成功。

## 4. 内容发布机制

### 4.1 TikTok Web 编排器

本次验证的页面链路：

```text
视频页
  → a[data-e2e="nav-upload"]
  → /tiktokstudio/upload?from=webapp&tab=video
  → 唯一 input[type=file][accept="video/*"]
  → 页面处理素材
  → blob 缩略图 + canvas 预览
  → contenteditable 文案
  → 隐私/定时/位置/质量/检查设置
  → 最终发布（本次未定位、未点击）
```

已观察的细节：

- 上传前没有文案编辑器；
- 选择素材后进入另一种编排状态，文件输入不再存在；
- 文案编辑器会以文件名作为初始内容；
- 位置搜索是独立文本输入，不能被误识别为文案；
- 首次使用出现越南语编辑功能教程，只有唯一
  `role="alertdialog"` 和精确“Đã hiểu”匹配后才关闭；
- 教程遮罩未关闭时，不能把下层控件视为可操作；
- 浏览器最终保持在编排器页面，`submitted=false`。

未证明：

- 素材是否形成长期服务端草稿；
- 刷新或重新登录后草稿是否存在；
- 最终发布按钮结构及其成功语义；
- 审核、公开可见、发布后视频 ID；
- 定时发布是否真正进入服务端队列；
- 图片轮播、封面选择、音乐授权或品牌内容的完整网页流程。

### 4.2 官方发布路径

TikTok 官方 Content Posting API 提供两条产品路径：

1. **Upload API**：将素材上传为待编辑内容，用户在 TikTok 收件箱收到通知，继续编辑并完成发布；
2. **Direct Post API**：应用在获得用户授权和明确同意后，直接向其 TikTok 账号提交内容。

推荐的未来链路：

```text
账号绑定 / Login Kit OAuth
        ↓
读取当前 creator info 和可用发布权限
        ↓
用户查看素材、文案、受众和互动设置
        ↓
本次明确批准
        ↓
Upload draft 或 Direct Post init
        ↓
传输素材
        ↓
publish_id
        ↓
状态轮询 / webhook
        ↓
处理中 / 失败 / 公开可用 post_id
```

Direct Post 当前文档化的设置包括：

- caption/title、hashtag、mention；
- 当前账号可用的 privacy level；
- 是否允许评论、Duet、Stitch；
- 视频封面时间点；
- 品牌内容声明；
- 当前账号最大视频时长。

官方接入的前置条件：

- TikTok for Developers 注册应用；
- Login Kit OAuth 和安全的服务端 token 生命周期；
- `video.upload` 或 `video.publish` scope 的审核和用户授权；
- Direct Post 前重新查询 creator info，不能缓存历史隐私权限；
- 用户在本次操作中明确看到并批准目标账号、素材和设置；
- 未审计客户端存在私密可见等限制；
- 用 status API 或 webhook 回查，不把 HTTP 受理当成公开发布。

架构建议：

- Cloud：应用凭据、OAuth token、审批、幂等、调度、状态轮询/webhook 和最终发布状态；
- Edge：需要本地文件时完成受控读取/传输，或继续承担网页窄交互；
- Console：账号授权、素材预览、发布设置、本次批准和状态展示；
- CDP：不作为官方权限缺失时的最终发布 fallback。

## 5. 抖音调研对照

抖音和 TikTok 必须保持两个平台标识。域名、登录、作品 ID、页面 surface、创作者平台和官方接口均不同，不能共享选择器或动作成功语义。

抖音研究分支：

- Control：`codex/douyin-cdp-research-and-probes`；
- Edge：`codex/douyin-cdp-research-and-probes`；
- 未合并、未部署、未注册生产平台。

### 5.1 抖音实际状态

| 能力 | 抖音调研结果 | 对 TikTok 的启示 |
| --- | --- | --- |
| 页面建模 | 精选网格、详情 modal、直播、私信是不同 surface | TikTok 也应分 For You、搜索、主页、详情、私信、直播 |
| 详情进入 | 脚本 click/直链 hydration 不稳定；trusted pointer + `modal_id` 才形成闭环 | 不以 URL 已变化或 JS click 已执行作为 ready |
| 点赞 | 正负状态 fixture 后才开放一次动作 | TikTok 新控件也要先收集正反样本 |
| 关注/收藏 | 独立开关、单向动作、同作品回查 | 不使用一个“允许互动”总开关 |
| 新手遮罩 | 精确“我知道了”并做 `elementFromPoint` 命中检查 | 关闭已知遮罩后必须重新预检目标 |
| 私信 | 最初一次固定文本被误发到群聊，不能计为有效私聊验收 | TikTok 必须先证明私聊/群聊和消息方向 |
| 直播 | 普通发言与定向回复分开；找不到评论级回复入口时没有发送替代消息 | 不把第二条普通聊天冒充回复 |
| 普通作品评论 | 评论与“发一条弹幕吧”容易混淆，真实评论发送未运行 | TikTok 也要绑定具体视频/评论 surface |
| 发布 | 只读看到上传入口，未选文件；建议正式发布优先官方 API | TikTok 已进一步验证编排器，但最终发布仍应走官方能力 |

### 5.2 不能忽略的抖音偏差

抖音调研曾把一条长度为 2 的 allowlist 回复输入并提交到群聊。编辑器清空只证明“发生了提交动作”，不证明：

- 会话是私聊；
- 目标联系人正确；
- 最近消息来自对方；
- 对方收到；
- 这是有效的私信验收。

后续修正增加了群聊特有结构、私聊正样本和消息方向 fixture。TikTok 私信调研必须从这个修正后的边界起步，不能先发送再补分类。

### 5.3 可复用的设计原则

1. 一个 surface 一个适配器，不把所有页面塞进一个全能选择器；
2. 一个真实写动作一个独立环境开关和单次预算；
3. 动作前后绑定同一作品、作者、会话、评论或直播间；
4. 遮罩、目标、状态或语言不明时，写动作失败关闭；
5. UI 证据只写 `ui_confirmed`，不扩大成服务端成功；
6. 正式发布优先官方 API，网页探针不能绕过 OAuth、审核和本次用户批准。

## 6. TikTok 后续能力调研清单

### P0：先调研

| 能力 | 最小调研内容 | 本阶段允许的动作 |
| --- | --- | --- |
| 回复语言与账号语言 | UI locale、账号写作语言、入站语言理解、语言一致性守卫 | 只读；不输入、不发送 |
| 多 surface 浏览 | For You、Following、搜索、作者主页、标签/音乐页、视频详情的稳定标识和滚动容器 | 只读浏览 |
| 关注/收藏/分享 | 控件正负状态、目标绑定、遮罩命中、分享面板结构 | 默认 shadow；分享不选收件人 |
| 官方 API 准备度 | 应用类型、审核状态、OAuth redirect、scope、账号权限、素材限制、状态回查 | 不申请权限、不上传、不发布 |

### P1：结构明确后调研

| 能力 | 主要风险 | 最小安全门 |
| --- | --- | --- |
| 评论列表与回复 | 普通评论、回复、视频描述、直播聊天混淆 | 唯一 video + comment 目标；先 fill-only |
| 私信 | 群聊误判、错误联系人、出入站方向不明、语言不一致 | 私聊 + 最近入站 + 唯一会话 + 明确语言 |
| 通知 | 点赞/关注/评论/系统通知混淆，可能暴露身份数据 | 只输出类型和计数，不输出人名/正文 |
| 直播 | 普通聊天、定向回复、礼物/付费控件混淆 | 聊天与回复分能力；明确排除礼物和充值 |

### P2：产品需要明确后再调研

- 图片轮播和照片 Content Posting API；
- 封面选择和封面后置校验；
- 网页定时发布与服务端任务状态；
- 品牌内容、音乐版权和商业内容声明；
- 草稿恢复、取消和残留清理；
- 授权账号资料、公开视频列表和发布后视频回查；
- 账号限制、最大视频时长、隐私权限和地区差异。

### 明确不做

- 批量点赞、关注、收藏或私信；
- 群发、自动找陌生人私信；
- 礼物、充值或任何付费动作；
- 验证码、实名或账号限制绕过；
- 网页私有接口逆向后作为生产发布通道；
- 官方权限不可用时自动回退到网页最终发布；
- 语言、目标或提交结果不明时把 unknown 改写成 success。

## 7. 回复消息的语言规则

### 7.1 UI 语言与对外语言正交

`k1eu5amn` 的 TikTok Studio 当时显示越南语，这只说明页面 locale 和选择器词表，不代表账号应始终用越南语回复。

禁止以下推断：

- 浏览器按钮是越南语 → 私信必须用越南语；
- 最近一条消息含英文单词 → 账号自动切换英语；
- 模型觉得某种语言更自然 → 覆盖账号配置。

### 7.2 手动探针

任何真实回复测试必须由用户明确提供：

- 目标能力：评论、私信、直播普通聊天或定向回复；
- 语言枚举；
- 精确允许文本；
- 精确 profile；
- 单次授权。

探针不得内置抖音式固定“好的”或“ok”作为 TikTok 默认回复。语言或文本缺失时只做 shadow，不得进入编辑器。

### 7.3 生产能力

建议复用现有 Facebook 的账号级受控 `writing_language` 机制，但 TikTok 是否支持相同语言枚举必须另立 OpenSpec 决定。

推荐规则：

1. Cloud 权威保存账号对外写作语言；
2. 入站文本用于理解语义，不自动覆盖账号语言；
3. 生成、去 AI 味和重写从第一步就使用同一写作语言；
4. 审核前执行语言一致性检查；
5. 缺配置、非法或明显不匹配时拒绝公开写入；
6. 已人工审核的正文原样下发，Edge 不再翻译。

私信还必须同时满足：

```text
精确 profile
  + 唯一会话
  + 明确一对一私聊
  + 最近消息明确入站
  + 账号写作语言已配置
  + 回复文本语言校验通过
  + 本次用户批准
```

任一条件不成立时，不输入、不发送。

## 8. 系统边界

如果后续进入正式接入：

| 层 | 职责 |
| --- | --- |
| Edge | 浏览器页面观测和动作、目标绑定、输入/点击后置校验 |
| Cloud | 选题、回复/发布规划、语言、审批、幂等、主要节奏、风险状态、官方 API token 和状态回查 |
| Console | 账号授权、素材/正文预览、语言配置、本次批准和真实状态展示 |
| OpenSpec | 平台能力、协议、风险、审批、失败语义和跨仓同步契约 |

研究探针不得直接升级为生产执行器。正式接入至少需要另一个跨 Edge/Cloud/Console 的 OpenSpec change。

## 9. 建议实施顺序

### Phase A：只读研究

1. TikTok surface 矩阵和稳定目标标识；
2. 关注/收藏/分享 shadow；
3. 评论、私信、通知和直播结构 fixture；
4. 回复语言合同；
5. 官方 API 应用、scope、审核和账号权限 readiness。

### Phase B：单次受控动作

仅在页面正负状态 fixture 完整、用户逐项授权后：

- 一次关注；
- 一次收藏；
- 分享面板打开但不选收件人；
- 评论/私信/直播仍优先 fill-only。

### Phase C：生产设计

- 官方发布 API；
- 账号 OAuth 和 token 托管；
- Cloud 审批、幂等、调度、风控和状态回查；
- Console 账号/语言/素材/发布设置；
- Edge 未被官方 API 覆盖的窄网页交互。

## 10. 证据与来源

### 本地证据

- TikTok OpenSpec：`openspec/changes/tiktok-cdp-interaction-probes/`
- TikTok Edge 模块：
  - `aidcp-edge/src/tiktok/probes/interaction-probe.ts`
  - `aidcp-edge/src/tiktok/probes/publish-composer-probe.ts`
  - `aidcp-edge/src/tiktok/probes/capability-research-probe.ts`
- TikTok runner：
  - `aidcp-edge/scripts/tiktok-interaction-probe.ts`
  - `aidcp-edge/scripts/tiktok-publish-composer-probe.ts`
  - `aidcp-edge/scripts/tiktok-capability-research-probe.ts`
- TikTok tests：
  - `aidcp-edge/test/tiktok/interaction-probe.test.ts`
  - `aidcp-edge/test/tiktok/publish-composer-probe.test.ts`
  - `aidcp-edge/test/tiktok/capability-research-probe.test.ts`
- 系统设计输入：`docs/design/tiktok-system-design-input-2026-07-23.md`
- TikTok Edge commits：`c5e0fa0`、`a6b0ee0`、`0a1dac1`
- TikTok Control commits：`9695885`、`9885784`、`6ff0fbe`、`6370acb`、`1bd15b4`、`435fdde`、`ff9e97a`
- 抖音 OpenSpec：`openspec/changes/douyin-cdp-research-and-probes/`
- 抖音 Edge 模块：`aidcp-edge/src/douyin/probes/interaction-probe.ts`
- 抖音 Edge commits：`11022ec`、`49aeb4e`
- 抖音 Control commits：`52ae98d`、`b6061d3`、`0396606`

验证记录：

- TikTok 聚焦测试：34/34；
- TikTok Edge typecheck：通过；
- TikTok OpenSpec strict validation：探针与 Douyin 差异阶段通过，28/28 tasks；
- 抖音聚焦测试：21/21；
- 抖音 Edge typecheck：通过；
- 抖音 OpenSpec strict validation：通过，但 tasks 中仍有明确未完成的浏览、评论和发布研究项；
- 两个研究分支均未合并、未部署、未打包、未归档为生产能力。

### TikTok 官方资料

- [Login Kit](https://developers.tiktok.com/doc/login-kit-overview/)
- [Content Posting API 产品说明](https://developers.tiktok.com/products/content-posting-api/)
- [Direct Post API](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)
- [Upload API](https://developers.tiktok.com/doc/content-posting-api-reference-upload-video/)
- [Query Creator Info](https://developers.tiktok.com/doc/content-posting-api-reference-query-creator-info)
- [Get Post Status](https://developers.tiktok.com/doc/content-posting-api-reference-get-video-status)
- [Content Sharing Guidelines](https://developers.tiktok.com/doc/content-sharing-guidelines/)
- [Display API](https://developers.tiktok.com/doc/display-api-overview/)

官方资料会变化；进入实现前必须重新核对审核状态、scope、限额、媒体约束、隐私选项和 webhook 行为。
