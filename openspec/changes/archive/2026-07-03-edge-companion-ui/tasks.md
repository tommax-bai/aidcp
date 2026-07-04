# edge-companion-ui — tasks

> 全部落 `../aidcp-edge`（UI 三件套 + main.cjs + 新纯函数模块），本仓只回写进度。设计定稿：Artifact v3（https://claude.ai/code/artifact/86ccc89f-2ba4-4b62-b69b-387017ba4426 ）。红线：无构建链、零审批按钮、动效只由真实事件驱动、发布链路文件零触碰（与活跃 change `publish-edge-command-runtime` 防撞）。
> 开发位：worktree `../aidcp-edge.wt/edge-companion-ui`（分支 `edge-companion-ui`，自 master ce05a57 开出）。
> **接手剩余任务（7.4/8.1/7.5）先读同目录 `handoff.md`**（2026-07-03 交接：契约、发射点位置、协议四处同步与 edge-client 白名单坑、验收标准全在里面）。

## 1. aidcp-edge — 事件管线（先坐实数据面）

- [x] 1.1 坐实现状：核心日志在发布候审 / 批准 / 已发布 / 拒绝四节点的现有文案（读 publish 相关运行时输出点，只读不改）；核对云端飞书审批卡是否展示 requestId（决定「编号」本期是否可见，宁缺毋假） <!-- 结论：①审批文件闸只服务旧 publish.request 路径 + 本地 mock/e2e（approval-gate.ts 头注），静默轮询、四节点均无日志——生产目标路径（命令式）审批在云端先行、边缘看不到候审 → 发布卡状态实装为「契约 + 状态机就绪、由 [ui-event] 结构化行驱动」，发射点按 6.4 串行补；②飞书审批卡（aidcp-cloud src/feishu/cards.ts buildPublishApprovalCard）只展示标题/正文摘要/话题，requestId 仅在不可见的回调值里 → 「编号对暗号」本期不做（渲染层已支持 code 字段、云端补印后即可点亮） -->
- [x] 1.2 新建 `src/electron/ui-events.cjs` 纯函数模块：`[ui-event] {json}` 结构化行优先解析；既有中文日志行映射表兜底（活动句子 / loopStage / statsDelta / publish 状态），现有 stats 递增逻辑原样迁入 <!-- aidcp-edge 50a8b23 有意偏离：旧 substring 计数（includes('like')/'collect'/'上报'/'提取内容'）会把失败行、命令下发行、每轮 page.cards 上报都计进数，违反不虚报 → 改为仅 ✓ 成功行精确计数（点赞/收藏/评论/评论点赞），浏览数 = 真打开并上报 note.detail 的笔记数；宁少不虚，模块头注 + 单测锁定 -->
- [x] 1.3 `main.cjs` 接入：status 新增 `presence` / `publish` 字段（旧字段全保留），新开 `ui:activity` IPC 推活动流条目；`preload.cjs` 暴露 `onActivity` 与 `openFeishu`（shell.openExternal 深链、失败返回 false） <!-- aidcp-edge 50a8b23 另含：status.account（账号身份行带出昵称）、逐行处理多行 chunk、生命周期各点诚实 presence 文案、win32 setTitleBarOverlay 随风控染色（try/catch） -->
- [x] 1.4 vitest 单测：映射表锁文案（点赞 / 提取 / 评论 / 发布四节点）、结构化行优先、未识别行返回 null、statsDelta 与改版前计数行为一致、旧形状 status 渲染降级不炸 <!-- aidcp-edge 50a8b23 实际测试栈为 node:test + tsx（仓库既有栈，非 vitest）：ui-events 13 条 + ui-logic 15 条 + companion-ui jsdom 13 条；「与改版前计数行为一致」按 1.2 偏离改为「失败行绝不计数」的红线断言 -->

## 2. aidcp-edge — 窗框与标题带

- [x] 2.1 `main.cjs` `createWindow()`：mac `titleBarStyle:'hidden'` + `trafficLightPosition`；win `titleBarStyle:'hidden'` + `titleBarOverlay{color,symbolColor,height:46}`；其余平台默认框；窗口尺寸随新布局微调 <!-- aidcp-edge 50a8b23 760x640 / min 640x520 -->
- [x] 2.2 渲染器标题带：46px drag 区 + 控件岛 no-drag（账号名 / 健康药丸 / 齿轮）；风控状态染色（normal 平静 / warned 琥珀 / restricted·frozen 警示），win32 同步 `setTitleBarOverlay`（try/catch） <!-- aidcp-edge 50a8b23 -->
- [x] 2.3 mac 本机冒烟：红绿灯 / 拖拽 / 控件点击互不冲突；win 打包件冒烟留待 §6 <!-- 2026-07-03 真机截图验证：系统标题栏消失、红绿灯内嵌标题带、账号「@晚风手作」+ 小红书标 + 绿色「运行中 · 一切正常」药丸 + 齿轮齐备；注意本机若有旧实例在跑会触发单实例锁把旧窗口带前台（≠新代码未生效），冒烟前先清 -->

## 3. aidcp-edge — 主界面重排（renderer 三件套）

- [x] 3.1 新建 `renderer/ui-logic.js` 纯函数：`synthesizeHealth(status)` 五路合成 +人话明细、在场感动效门（运行中且事件 <5min）、发布卡状态机（pending/reminded/approved/published/rejected + 30min 时长琥珀化）；单测 <!-- aidcp-edge 50a8b23 UMD 形（window.uiLogic + module.exports 双出口），15 条单测 -->
- [x] 3.2 index.html/styles.css 按 v3 重排：在场感行（shimmer + 呼吸点 + 新鲜度走字）、循环 chip（刷 feed→选笔记→阅读→互动→返回续刷）、活动流（环形 ≤200 条）、「开发者详情」折叠收原始日志、「今日小结」条；`prefers-reduced-motion` 全局关动效 <!-- aidcp-edge 50a8b23 -->
- [x] 3.3 五徽章收进健康药丸点开的明细浮层（内部词改人话：边缘进程→本机引擎等）；旧 hero / stats / grid / log DOM 移除 <!-- aidcp-edge 50a8b23 五徽章 ID 原样保留（#auth-status 等），迁入 #health-pop -->
- [x] 3.4 无事件诚实态：待命 / 已暂停 / 需登录 / 等待云端静态文案；shimmer 门断言（停止态绝不动效） <!-- aidcp-edge 50a8b23 「运行中但事件过期>5min → 如实说没有新动态」也覆盖（与看门狗有界 idle 对齐） -->
- [x] 3.5 修「今日小结」空数字（用户验收反馈）：updateStatus 先整体替换再合并，局部计数补丁会把其余计数清空（老 bug，被新小结条放大）→ 抽纯函数 mergeStats 先合并成完整 stats 再落 + 渲染层各计数 ??0 兜底 + 零值弱化样式；回归单测 2 条 <!-- aidcp-edge 35d9b1e 已 ff 合回 master；495/495 + typecheck 过 -->
- [x] 3.6 真机验收反馈第 1 轮（5 条）：①标题带昵称优先、无昵称显「账号 …尾4位」绝不摆长 id（in-place 身份读取无 displayName 属常态，昵称仅 navigate 路径有——核心侧取昵称另议）；②活动流身份句同理不暴露长 id；③暂停等静态态补「状态更新 · N 前」时间戳消大空白；④「开发者详情」默认不显示、设置抽屉开关 + settings.devDetails 持久化；⑤FAB 改白底药丸+状态点与整体风格一致；⑥活动流加类型记号字（赞/藏/评/读/注/发）+ 空态重设计，治无发布卡时的纯文字墙 <!-- aidcp-edge 24954fd 已 ff 合回 master；499/499 + typecheck；+6 断言 -->
- [x] 3.7 账号标签兜底链（用户追问「环境列表为何有名字」）：小红书昵称（@ 前缀）> AdsPower 环境名（操作者起的分身名，随设置持久化 adsProfileName、平铺不加 @ 不冒充昵称、手填 id 即清空）> 账号 …尾4位；adspower 启动流程即点亮标题带、不等身份确立 <!-- aidcp-edge be7161d 已 ff 合回 master；501/501 + typecheck -->

## 4. aidcp-edge — 发布等待卡（纯展示）

- [x] 4.1 发布卡组件：白底卡 + 四节点旅程步骤条 + 唯一琥珀呼吸点 + 脚注「通过/驳回在飞书」+「打开飞书 ↗」（深链失败降级纯文字）；零按钮断言（卡内不存在 button 元素） <!-- aidcp-edge 50a8b23 深链依次试 feishu://、lark://；jsdom 断言 card.querySelectorAll('button').length===0 -->
- [x] 4.2 五状态接线：候审 / 超 30min（未证实不谎称「已再提醒」）/ 已通过择时（呼吸点转平静色 + 无需操作文案）/ 已发布收进流并计入小结 / 拒绝收起表述为「暂不发布、内容留档」 <!-- aidcp-edge 50a8b23 状态由 status.publish 驱动（[ui-event] 契约就绪）；终态折进活动流按签名去重 -->
- [x] 4.3 编号展示：仅当 1.1 核对确认飞书卡含 requestId 时展示尾 4 位，否则本期不显示 <!-- 1.1 已核对：飞书卡不含可见 requestId → 本期不显示；渲染层保留 code 字段支持，云端补印后即可点亮 -->
- [x] 4.5 发布卡空态观感（用户验收反馈第 3 轮）：脚注固定模板关键词加粗（确认/拒绝、通过后才会发布、无需操作、已发布——零插值富文本渲染无注入面）；「打开飞书」蓝链三态常驻（纯导航）；v3 封面占位回归（珊瑚渐变、空态淡化虚线默认形态）；编号以「—」作默认形态（云端飞书卡印 requestId 后自动点亮） <!-- aidcp-edge d8c0f4a（rebase 过并发 ads-fingerprint 后 527/527 + acceptance 11 + typecheck）已 ff 合回 master -->
- [x] 4.6 发布卡收展 dock（用户验收反馈第 4 轮）：flow 永远展开；运行中且无在途审批自动收起成薄条（小封面记号+「发布」+摘要+折角，同设计语言，0.28s 折叠动画、reduced-motion 关闭；点击临时展开、新审批到来复位）；未运行保持展开（空态旅程有引导价值）。同轮空态观感修正：占位从自造的虚线破图框改回「同渐变降饱和+白色封面记号」、旅程限宽 540 居中防拉稀、空态 meta 改「等待第一条笔记 · 编号 —」——headless Chrome 截图对照设计稿逐态核过 <!-- aidcp-edge d8c0f4a + 4a88182（rebase 过并发 bfc9faa）已 ff 合回 master；530/530 + typecheck -->
- [x] 4.4 发布卡改常驻三态（用户验收反馈第 2 轮）：flow 进行中（原旅程）/ last 上次发布（四节点全勾 + 相对时间，userData/ui-state.json 本地持久化、重启不丢；云端快照接入后以云端为准）/ empty 从未发布（幽灵旅程 + 空态文案，同设计语言）；「打开飞书」仅 flow 态出现；拒绝折进流后回落 last/empty、不渲染成失败 <!-- aidcp-edge 163b018 + 72e106f（测试类型补丁）已 ff 合回 master；504/504 + typecheck -->

## 5. aidcp-edge — 设置抽屉

- [x] 5.1 设置表单 DOM 整体迁入右滑抽屉（齿轮开合、选择器不变、探测/列表/手填/保存并入启动逻辑零改动）；稳态首屏无表单无「必填」 <!-- aidcp-edge 50a8b23 旧 renderer-smoke 20 条设置回归零改动全过 -->
- [x] 5.2 `populateEnvs` 增自动选中：恰好 1 个环境且分身 ID 为空 → 自动选中并明示；多环境不代选、已有值不覆盖 <!-- aidcp-edge 50a8b23 加一道「核心未在运行」闸（运行中绝不偷改配置），delta spec 已同步补该措辞 -->
- [x] 5.3 待配置态：首屏醒目主动步骤条（点击开抽屉），替代灰 notice；登录引导同步升级为主动步骤（检测到登录自动前进） <!-- aidcp-edge 50a8b23 登录检测自动前进沿用既有 cookie 轮询（checkLoginAndStart），文案与样式升级 -->

## 6. 启动行为与文案（用户验收反馈第 5 轮）

- [x] 6.a 客户端启动不自动开跑：whenReady 只做轻量预检（缺配置亮「待配置」引导 / 配置齐备诚实「就绪」），任务由用户点「启动」开跑；恢复/重新登录/按新设置重启仍为用户主动动作；delta spec 增「客户端启动不自动开跑任务」要求 <!-- aidcp-edge de0ee62 已 ff 合回 master；538/538 + typecheck -->
- [x] 6.b 发布卡空态卡头与收起薄条标题改「发布过的 AI 写好的笔记」；脚注只加粗「通过/驳回」；编号值加设计稿灰底小片 <!-- aidcp-edge d1eeaa6 + de0ee62 -->
- [x] 6.c 默认态选中上次用的账号：预检直接用持久化设置（分身 ID + 环境名）点亮标题带，不再依赖启动流程；设置抽屉本就按持久化 ID 高亮上次环境 <!-- aidcp-edge 6b9d708 已 ff 合回 master；538/538 + typecheck -->

## 7. 回归与收口

- [x] 6.1 `cd ../aidcp-edge && npm test && npm run typecheck`（含新增 ui-events / ui-logic 单测；FAB 三态与设置既有行为回归） <!-- worktree 内 490/490 全量 + 11/11 acceptance + typecheck 干净（2026-07-03，分支 50a8b23） -->
- [x] 6.2 mac 端到端冒烟：启动 → 待配置引导 → 抽屉配置 → 登录 → 活动流滚动 → 暂停/恢复 → 模拟发布候审卡（喂日志行） <!-- 2026-07-03 用 worktree 本地演示假核心（gitignored dist/main.js，按剧本打日志、零真实副作用）真机驱动全链路：标题带/在场感 shimmer/循环 chip/活动流/今日小结/发布候审卡（含结构化 [ui-event] pending→approved→published 流转）均如 v3 设计呈现且进程全程无崩溃（首帧截图存档，后续帧被用户前台窗口遮挡未截）；抽屉交互/暂停恢复/五状态断言由 companion-ui jsdom 冒烟 13 条覆盖。注意：本机存量旧实例会占单实例锁，冒烟前先清（见 memory edge-companion-ui-rollout） -->
- [x] 6.3 electron-builder 双平台打包，win-unpacked 验 titleBarOverlay 观感与窗控 <!-- 2026-07-03 worktree 内双平台产物齐：mac dmg+zip×双架构（AIDCP-0.2.0*）+ win NSIS（AIDCP Setup 0.2.0.exe，signAndEditExecutable:false 使 mac 交叉构建免 wine）；asar 核验新界面五文件与新窗框代码均打入。win titleBarOverlay 实际观感需 Windows 真机，已挂 docs/real-machine-acceptance-backlog.md 簇 7；打包配置零改动（renderer/**、*.cjs 通配自动覆盖新文件） -->
- [x] 6.4 结构化 `[ui-event]` 发射点（发布链路内）标记串行：待 `publish-edge-command-runtime` 收口后按需补插（或由其顺手带上），本 change 不触碰发布文件 <!-- aidcp-edge 326faad + 评审修正 b0055bd（2026-07-03，publish-edge-command-runtime 已当日先行归档、闸门解除）：新增 src/flows/ui-event-lines.ts（纯函数可单测）——PublishUiEventTracker 从 fill_field(title) 截获标题、submit_publish 成功→published 行、在途发布被回收→failed 行、每 recordId 终态只发一次；发射点接在 main.ts 的 publish.command 结果处与回收闭包内。有意设计：单条指令 ok:false **不**在边缘抢判 failed——云端序列对增强步（话题/选项/定时）与 submit 后抓 postId 是 best-effort 容错继续的（command-sequencer.ts 实证），边缘抢判会虚报；终判 failed 由云端经 ui.snapshot 推（见 8.1）。单测 test/flows/ui-event-lines.test.ts 8 条锁红线（宁缺毋假/终态一次/不抢判） -->
- [x] 6.5 `openspec validate edge-companion-ui --strict` → 合回 master + 部署分发 → archive <!-- 2026-07-03 已合回：rebase 到 master 44d56ad 后 493/493+typecheck+acceptance 全绿，ff 合并推送（master 9ef116e）；双平台安装包产物在 worktree dist-electron/（AIDCP-0.2.0*.dmg/zip + AIDCP Setup 0.2.0.exe）。archive 待 6.4（[ui-event] 发射点，等 publish-edge-command-runtime 收口）与分发落定后执行 --> <!-- 2026-07-03 尾批收口：6.4/8.1 完成后 edge 合回 master b0055bd、cloud 合回 master 1f013e7（双仓 acceptance→全量→typecheck 全绿：edge 11+556、cloud 36+1208）；双平台安装包按合并后代码**重打**（22:37，AIDCP-0.2.0*.dmg/zip 双架构 + AIDCP Setup 0.2.0.exe，asar 已核验含 ui.snapshot 核心码与壳修正）；edge 无 ECS、合 master+安装包即交付；cloud 部署顺延随 console-cloud-panel-hardening 的 cloud+console 同步部署批（理由与证据见 8.1 注记；跟踪＝backlog 簇 3「edge-companion-ui 真数据流转」前置项）；win 真机项在 backlog 簇 7、真数据流转验收在簇 3、评论点赞白名单顺手修观察项在簇 4；validate --strict 过 → archive --> <!-- 2026-07-04 deployed：cloud master 1f013e7 已上 ECS（09:06 与 console 首帧鉴权新构建同步切换：cloud src 全树 md5 核对 + restart + healthcheck 全绿——active/8787/8090/8088/PG/飞书 onReady/isales 四服务未触碰；nginx /downloads/ autoindex 已关；生产库时间索引随重启自建。console 构建恰逢并发方同刻部署（09:03 其构建先落、index.html 以其为准，同为 wave-5 首帧鉴权版，配对等效）。ui.snapshot 通道即刻起随边缘上线生效） -->

## 8. 云端数据回填（串行批：与 7.4[原6.4] 同等 publish-edge-command-runtime 收口）

- [x] 8.1 云端账号资料快照下发：边缘握手确认（或会话启动）时云端下发 {昵称, 最近发布摘要 {title, at}}——昵称云端账号主数据已有、发布记录云端已有；edge 核心收到后转 `[ui-event]` 行给壳（壳侧已就绪：status.account source='xhs' 优先于环境名、status.lastPublish 以云端为准替代本地 ui-state）。热点提醒：动协议载荷 = 两份 protocol.ts 逐字同步 + docs/protocol.md + 视需要 command-bridge，按并行规范串行、绝不与并行 change 同时碰 <!-- aidcp-cloud 27f84a9 + 评审修正 1f013e7；aidcp-edge 326faad + b0055bd（2026-07-03）。设计：新增主动消息 ui.snapshot（协议 56→57，两份 protocol.ts 逐字一致——顺手修齐存量漂移 isVideo/注释 4 处；docs/protocol.md 头部+§2.1 表+§3.1 载荷节同步；command-bridge 无需登记——直发 makeEnvelope 不走浏览映射；edge-client onMessage 白名单放行 + 回归断言，顺手修掉存量静默丢弃缺口 interaction.like_comment 并入回归表）。云端 UiSnapshotService（src/comm/ui-snapshot.ts）：①hello 注册完成后推全量快照{昵称,lastPublish,在途候审/已批}——钩在 ws-server 新增 onEdgeRegistered（edges.set+welcome 回发之后，避开 sent=0 前科）；②审批生命周期实时推 pending（executor 落库+发卡后）/approved（dispatcher 双闸核过后）/rejected（飞书取消+面板拒绝首写）/failed（dispatcher 各终判点含边缘离线路径）；published 不经此通道（边缘自知，防双源）。PublishLogStore 新增 lastPublishedForAccount/pendingApprovalForAccount；飞书审批卡加「编号 #<id>」字段与界面对暗号（publish-<n> 才带）。壳侧新增 lastPublish 结构化 kind（不折活动流不计数、以云端为准覆盖 ui-state）+ 核心（重）启动清发布卡在途态（离线窗错过的终态不滞留成陈卡、真候审由快照重建）。对抗性评审（多 agent workflow）4 项 confirmed：3 项已修（注册时序竞态/陈卡/暂停闸吞终态+离线失败不通知），1 项记为已知限制——拒绝决定只落 /tmp 信号、DB 行永远 pending_approval，信号文件丢失（重装/清 tmp）后已拒草稿会在 hello 快照复现为 pending（仅界面观感，发布安全不受影响：下发闸仍要求 approved===true 信号在场）；彻底修法=审批决定持久化进 DB，属审批信号子系统后续 change。云端 ECS 部署顺延：ECS 现役为 pre-wave-5 云端 + 旧版 ?token= console（实测配对一致），cloud master 已捆绑 console-cloud-panel-hardening wave-5 的 WS 首帧鉴权（breaking、须 cloud+console 同步部署，见 backlog 簇 9）——单方面推 cloud 会当场打断线上后台，故随该批次同步部署上线（master 1f013e7 已含本 change 全部云端代码） -->
