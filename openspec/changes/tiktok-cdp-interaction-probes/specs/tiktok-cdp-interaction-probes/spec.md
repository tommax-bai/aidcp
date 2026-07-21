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

### Requirement: 发布探针必须先只读发现上传入口与编排器
发布探针 SHALL 先通过语义属性唯一识别 TikTok 上传入口，并在进入上传页面后重新执行登录、挑战和页面阻断分类。探针 SHALL 只报告页面 host/path、唯一文件输入的接受类型以及编排器字段种类，不得读取或输出 cookie、token、网络正文或账号身份。

#### Scenario: 上传入口与文件输入唯一
- **WHEN** 已登录环境中可唯一识别上传入口，且目标页面存在唯一可用文件输入
- **THEN** 探针报告上传路由、输入接受类型和可见编排字段，不选择任何文件

#### Scenario: 页面阻断或文件输入不唯一
- **WHEN** 上传页面出现登录、验证、挑战，或不存在唯一可用文件输入
- **THEN** 探针诚实报告阻断或歧义并停止，不向任意输入设置文件

### Requirement: 合成素材暂存必须绑定精确输入并验证页面状态
只有调用方显式提供现存的无敏感测试素材路径时，发布探针 MAY 将该精确路径设置到已唯一确认的文件输入。探针 SHALL 等待页面给出上传已确认或编排器可编辑的有界证据；超时、错误或页面移动时 MUST 报告失败，不得假定上传成功。

#### Scenario: 合成视频进入编排器
- **WHEN** 唯一文件输入接受调用方提供的合成视频，且页面在有界时间内显示上传确认或可编辑编排器
- **THEN** 探针报告 `upload_acknowledged`，并明确该证据不等于公开发布

#### Scenario: 上传结果不明确
- **WHEN** 设置文件后页面出现错误、移动到非预期页面或无法确认上传状态
- **THEN** 探针报告 `ambiguous` 或明确错误，不重试其他输入且不继续填写

### Requirement: 发布编排器探针只能填写而不能提交
发布探针 MAY 在上传已确认后定位唯一可见文案编辑器、填入无敏感测试文案并回读。实现 MUST NOT 查询或点击最终发布控件、MUST NOT 派发 Enter、Ctrl+Enter 或 Meta+Enter、MUST NOT 调用表单提交，且 MUST NOT 暴露启用最终发布的运行开关。

#### Scenario: 编排器文案成功写入
- **WHEN** 上传已确认且唯一可见文案编辑器可编辑
- **THEN** 探针写入并回读文案，只报告长度和匹配结果，状态为 `composer_ready_not_submitted`

#### Scenario: 到达可发布前状态
- **WHEN** 文件上传和文案回读均已确认
- **THEN** 探针保持浏览器打开，不查找、不点击最终发布控件，也不得报告 `published`

### Requirement: 发布探针必须区分文件选择、上传确认和公开发布
发布证据 SHALL 分别记录文件是否被选择、平台页面是否确认上传、编排器是否就绪以及最终提交是否执行。`submitted` SHALL 永远为 `false`；探针不得把本地文件选择、传输完成、平台草稿或按钮可用性描述为公开发布成功。

#### Scenario: 生成发布探针报告
- **WHEN** 发布探针完成或失败
- **THEN** 报告以脱敏状态区分 `file_selected`、`upload_acknowledged` 和 `composer_ready_not_submitted`，并明确 `submitted=false`
