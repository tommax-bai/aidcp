## ADDED Requirements

### Requirement: 探针只能连接明确指定的本地 TikTok 环境
TikTok CDP 探针 SHALL 要求调用方明确提供 AdsPower profile id，并 SHALL 只连接该 profile 返回的 active 或新启动 debug port。当 AdsPower 本地 API 暂时不可用但该 profile 的浏览器仍存活时，探针 MAY 接受调用方显式提供的 CDP port，但 MUST 先在该端点的 page targets 中找到 `start.adspower.net` 且 `id` query 与目标 profile 精确相等的 marker；marker 缺失或不精确时 MUST 拒绝连接。探针 MUST NOT 搜索或回落到其他 profile，且 MUST NOT 在登录失效、验证码、挑战或非 TikTok 页面继续执行交互动作。

#### Scenario: 指定环境处于已登录 TikTok 页面
- **WHEN** 调用方提供 profile id 且该环境可通过 CDP 打开已登录 TikTok 网页
- **THEN** 探针连接该环境并进入只读页面探测

#### Scenario: 本地 API 不可用但现存端点自证 profile
- **WHEN** 调用方显式提供 CDP port，且该端点存在与目标 profile 精确匹配的 AdsPower start marker
- **THEN** 探针可连接该现存端点，但只断开自己的 CDP session，不接管浏览器关闭生命周期

#### Scenario: 直接端点缺少精确 profile marker
- **WHEN** 调用方显式提供的 CDP port 不含目标 profile 的精确 AdsPower start marker
- **THEN** 探针拒绝连接，不得仅因端点上存在 TikTok 页面而继续

#### Scenario: 环境出现挑战页
- **WHEN** URL 或可见页面结构表明登录、验证码、挑战或访问限制
- **THEN** 探针报告明确阻断原因并在任何点赞或评论输入前停止

### Requirement: 浏览探针必须证明当前视频发生变化
浏览探针 SHALL 从当前可见视频读取稳定 video id 和作者 handle，并参考现有 Facebook Reels 探针依次使用有界 ArrowDown 与单次 wheel fallback。每次输入后 SHALL 重新查询页面，不得复用滚动前 DOM node。只有滚动位置、当前稳定 video id 或可见视频集合至少一项发生可验证变化时，探针才 SHALL 报告浏览成功。

#### Scenario: 虚拟列表滚动到下一条视频
- **WHEN** 探针在当前视频上派发有界滚动且 TikTok 复用 DOM 节点展示下一条视频
- **THEN** 探针重新查询并以新的稳定 video id 记录浏览变化

#### Scenario: 滚动没有产生可验证变化
- **WHEN** 输入已派发但滚动位置、当前 video id 和可见视频集合都未变化
- **THEN** 探针报告 `no_change`，不得把输入派发本身当作浏览成功

### Requirement: 真实点赞必须双重授权且单向执行
点赞探针 SHALL 默认只读。真实点击 MUST 同时要求显式点赞开关，以及确认 profile 值与实际 AdsPower profile 精确相等。执行前后 MUST 唯一确认同一 video id；已经点赞时 MUST 返回 `already_liked` 且不得点击，未点赞时最多点击一次，只有同一视频 UI 转为 liked 才 SHALL 返回 `ui_confirmed`。

#### Scenario: 默认只读探测到可点赞目标
- **WHEN** 当前视频、作者和未点赞控件被唯一识别，但真实点赞双门未同时打开
- **THEN** 探针报告 `shadow` 并保持页面状态不变

#### Scenario: 显式授权一次真实点赞
- **WHEN** 双门打开、当前视频唯一且点赞前状态为 unliked
- **THEN** 探针点击一次，并仅在同一 video id 的状态变为 liked 后报告 `ui_confirmed`

#### Scenario: 当前视频已经点赞
- **WHEN** 探针确认目标状态为 liked
- **THEN** 探针报告 `already_liked` 且不得点击取消点赞

#### Scenario: 点赞后目标或状态无法确认
- **WHEN** 点击后当前 video id 变化、存在多个候选或 liked 状态在有界时间内未出现
- **THEN** 探针报告 `ambiguous`，不得重试点击或报告成功

### Requirement: 评论探针只能输入而不能发送
评论探针 SHALL 只在当前视频被唯一确认且页面没有阻断状态时定位一个可见编辑器。探针 SHALL 聚焦编辑器、通过 CDP 输入测试文本并回读确认；实现 MUST NOT 查询或点击发送控件、MUST NOT 派发 Enter、MUST NOT 调用表单提交，也 MUST NOT 暴露任何启用评论发送的运行开关。

#### Scenario: 评论文本成功写入编辑器
- **WHEN** 当前视频和唯一可见评论编辑器已确认，且提供非空测试文本
- **THEN** 探针输入文本并在回读匹配后报告 `filled_not_submitted`

#### Scenario: 评论编辑器不唯一或不可见
- **WHEN** 页面没有唯一可见评论编辑器
- **THEN** 探针报告 `editor_not_found` 或 `ambiguous`，不得向任意输入框写入文本

#### Scenario: 评论输入完成
- **WHEN** 探针已报告 `filled_not_submitted`
- **THEN** 浏览器保持打开且评论停留在编辑器中，探针不执行任何提交动作

### Requirement: 探针证据必须最小化且诚实
探针 SHALL 输出阶段、时间戳、页面 host/path、video id、作者 handle、动作是否执行及确认级别。探针 MUST NOT 读取或输出 cookie、token、localStorage 值、网络正文、原始账号身份或完整评论文本；评论证据 SHALL 只包含文本长度与回读匹配结果。UI 确认 MUST 明确标记为 UI 证据，不得表示服务器持久化。

#### Scenario: 生成真机探针报告
- **WHEN** 浏览、点赞或评论输入阶段完成或失败
- **THEN** 报告包含足以区分 executed、shadow、blocked 和 ambiguous 的最小证据，且不包含受限敏感字段
