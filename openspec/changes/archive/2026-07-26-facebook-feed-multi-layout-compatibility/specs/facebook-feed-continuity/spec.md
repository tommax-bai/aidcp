## MODIFIED Requirements

### Requirement: Facebook feed 滚动断言在页是幂等的、绝不重置滚动位置

边缘在执行 Facebook feed 滚动前对「是否在 feed」的断言 SHALL 是幂等的：先**探测一次**当前页面（当前 URL、由 URL 归类的 surface、是否存在可识别 feed 结构、已水合真卡数、是否有打开的 dialog）。可识别 feed 结构 SHALL 同时支持：① 语义化 `[role="feed"]` + 顶层 `[role="article"]`；② 无 `[role="feed"]` / 真卡无 `[role="article"]`、但在主内容区域存在可见 story-message 与至少一个链接作者标题共同界定的轻量卡片布局。当页面**已在目标列表面**（explore 首页或搜索结果页）且任一受支持 feed 结构在场时，MUST 直接放行、MUST NOT 发起整页 `Page.navigate`。仅当**不在目标列表面**（surface 不匹配）或**目标列表面上没有任一受支持 feed 结构**时才导航到目标列表 URL。

**`[role="dialog"]` 的存在 MUST NOT 作为「需导航」的判据**：Facebook 首页会常驻瞬时良性 dialog，而 Facebook feed 就地读不弹内容模态。`dialogOpen` 字段 MAY 继续被探测并写入边缘诊断日志，但 MUST NOT 参与 onTarget 判定。

surface 归类 SHALL 复用既有的 URL surface 归类器区分「首页」与「搜索页」，MUST NOT 写死为首页。轻量布局识别 MUST 使用 locale-neutral 的 DOM 结构/属性，MUST NOT 依赖中文、英文、越南文等可见文案或账号专属标记。

红线（fail-closed 不得被省略）：不导航的放行路径 SHALL 仍执行与导航路径同等的登录态复检、验证码/阻断浮层复检、consent 预清理。真正的登录失效 / 验证码 / 阻断浮层 SHALL 由该 fail-closed 复检识别并诚实回报对应失败、MUST NOT 放行滚动。

#### Scenario: 已在语义化首页则直接放行、不重新导航
- **WHEN** 收到 feed 滚动命令时页面已在 explore 首页且语义化 feed 容器在场
- **THEN** 边缘不发起 `Page.navigate`，直接执行滚动手势；连续多次滚动命令下 `scrollY` 严格递增、整页 document-load / `timeOrigin` 保持不变

#### Scenario: 已在轻量布局首页也直接放行
- **WHEN** 页面已在 explore 首页、没有 `[role="feed"]` 且真卡没有 `[role="article"]`，但主内容区域存在受支持的轻量 story-message 卡片结构
- **THEN** 边缘判定 feed 在场并直接放行滚动，MUST NOT 因语义 role 缺失反复整页导航

#### Scenario: 首页挂着瞬时良性 dialog 时仍不导航
- **WHEN** 页面已在任一受支持首页 feed 布局，但存在瞬时良性 `[role="dialog"]`
- **THEN** 边缘 MUST NOT 因该 dialog 发起整页 `Page.navigate`，直接放行滚动；`timeOrigin` 保持不变

#### Scenario: 已在搜索结果页则按搜索页放行、不被带回首页
- **WHEN** 会话处于任一受支持布局的搜索结果页并收到 feed 滚动命令
- **THEN** 边缘按搜索页 surface 放行滚动，MUST NOT 导航回 explore 首页、MUST NOT 丢失搜索结果

#### Scenario: 不在目标列表面才导航
- **WHEN** 收到 feed 滚动命令时页面停在详情/通知/其它非列表面，或目标列表面不存在任一受支持 feed 结构
- **THEN** 边缘导航到目标列表 URL 后再滚动

#### Scenario: 放行路径仍 fail-closed 复检
- **WHEN** 页面虽在目标列表面、但登录已失效或存在验证码/阻断浮层
- **THEN** 边缘 MUST NOT 放行滚动，MUST 回报对应诚实失败，与走导航路径时的复检等价

### Requirement: feed 卡片在 loading-aware 累积判稳后才上报

边缘上报 Facebook feed 卡片前 SHALL 执行一个 loading-aware 累积判稳循环（每轮约 450–600ms 复扫一次，直接对卡片抽取结果比对），并 SHALL 对语义化顶层 article 与轻量 story-message 卡片使用同一共享的顶层卡片发现口径。仅当**同时满足**下列三条件才算稳、才上报：① 至少 `minCards`（默认 1）张真卡（已水合、有作者且可抽出既有白名单接受的规范帖子 permalink；绝不把虚拟化空壳或只有歧义媒体 ID 的卡当真卡）；② 相邻两轮真卡集合相等（按 noteId 集合比较，非按数量）；③ feed 区域内无 loading 信号。loading 信号 SHALL 仅按可访问性语义识别（`role="progressbar"` / `aria-busy="true"`），MUST NOT 依据 Facebook 骨架屏的 CSS 类名判定。

该判稳循环 SHALL 合并替换既有的两道 existence gate，MUST NOT 与它们叠加串行。判稳 SHALL 直接对卡片抽取输出判稳，MUST NOT 另起一个抽取口径不同的探针。初始扫描与后续 feed 就地读/操作的卡片定位 SHALL 复用同一共享多布局口径，MUST NOT 出现“已上报但后续按另一布局无法定位”的分叉。

判稳循环 SHALL 有硬 wall-clock 上限（导航后约 6s、滚动后约 3.5s）。达上限时：有 ≥1 真卡则 SHALL 照实上报已抽到的真卡并在边缘诊断日志标记 degraded；0 真卡且仍有 loading 信号 SHALL 回报可重试的「仍在加载」；识别到 feed 结构但 0 张稳定身份真卡 SHALL 继续走既有有界滚动/no-target 逻辑，MUST NOT 因卡片身份不足反复重载页面；页面无任一受支持 feed 结构且无 loading 信号才 SHALL 回报「无 feed」作为升级候选。

#### Scenario: 两类布局集合连续两轮相等且无 loading 即上报
- **WHEN** 任一受支持布局中相邻两轮扫到的真卡 noteId 集合相等、feed 区域无 loading 信号、且真卡数 ≥ minCards
- **THEN** 边缘上报该批真卡

#### Scenario: 集合已稳但仍在 loading 则继续等
- **WHEN** 相邻两轮真卡集合相等，但 feed 区域仍存在 loading 信号
- **THEN** 边缘 MUST 继续等待，直到 loading 信号消失或触达 wall-clock 上限

#### Scenario: 触达上限有真卡则照实上报并标 degraded
- **WHEN** 判稳循环到达 wall-clock 上限且已抽到 ≥1 张真卡
- **THEN** 边缘照实上报已抽到的真卡，并仅在边缘诊断日志标记 degraded，MUST NOT 把 degraded 写进上报 payload

#### Scenario: 触达上限 0 卡且仍 loading 则可重试
- **WHEN** 判稳循环到达上限仍为 0 真卡、但仍有 loading 信号
- **THEN** 边缘回报可重试的「仍在加载」，MUST NOT 上报空批、MUST NOT 假成功

#### Scenario: 轻量 feed 存在但卡片身份不可靠时不重载不造卡
- **WHEN** 轻量布局结构在场，但当前卡片只暴露 photo/video 资源 ID、无法通过既有规范帖子身份白名单
- **THEN** 边缘保持在 feed 并继续有界滚动寻找真卡，MUST NOT 把媒体 ID 当 noteId 上报、MUST NOT 因 `[role="feed"]` 缺失重载页面

#### Scenario: 触达上限 0 卡且无任何 feed 结构则升级候选
- **WHEN** 判稳循环到达上限仍为 0 真卡、无 loading 信号、且不存在任一受支持 feed 结构
- **THEN** 边缘回报「无 feed」作为升级候选，MUST NOT 静默当作已上报

#### Scenario: 虚拟化空壳绝不被当卡上报
- **WHEN** feed 中除顶部若干张真卡外存在大量未水合的虚拟化空壳文章
- **THEN** 边缘 MUST NOT 把空壳计入真卡集合或上报，只上报有作者与规范 permalink 的真卡
