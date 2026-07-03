# edge-companion-ui — tasks

> 全部落 `../aidcp-edge`（UI 三件套 + main.cjs + 新纯函数模块），本仓只回写进度。设计定稿：Artifact v3（https://claude.ai/code/artifact/86ccc89f-2ba4-4b62-b69b-387017ba4426 ）。红线：无构建链、零审批按钮、动效只由真实事件驱动、发布链路文件零触碰（与活跃 change `publish-edge-command-runtime` 防撞）。
> 开发位：worktree `../aidcp-edge.wt/edge-companion-ui`（分支 `edge-companion-ui`，自 master ce05a57 开出）。

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

## 4. aidcp-edge — 发布等待卡（纯展示）

- [x] 4.1 发布卡组件：白底卡 + 四节点旅程步骤条 + 唯一琥珀呼吸点 + 脚注「通过/驳回在飞书」+「打开飞书 ↗」（深链失败降级纯文字）；零按钮断言（卡内不存在 button 元素） <!-- aidcp-edge 50a8b23 深链依次试 feishu://、lark://；jsdom 断言 card.querySelectorAll('button').length===0 -->
- [x] 4.2 五状态接线：候审 / 超 30min（未证实不谎称「已再提醒」）/ 已通过择时（呼吸点转平静色 + 无需操作文案）/ 已发布收进流并计入小结 / 拒绝收起表述为「暂不发布、内容留档」 <!-- aidcp-edge 50a8b23 状态由 status.publish 驱动（[ui-event] 契约就绪）；终态折进活动流按签名去重 -->
- [x] 4.3 编号展示：仅当 1.1 核对确认飞书卡含 requestId 时展示尾 4 位，否则本期不显示 <!-- 1.1 已核对：飞书卡不含可见 requestId → 本期不显示；渲染层保留 code 字段支持，云端补印后即可点亮 -->

## 5. aidcp-edge — 设置抽屉

- [x] 5.1 设置表单 DOM 整体迁入右滑抽屉（齿轮开合、选择器不变、探测/列表/手填/保存并入启动逻辑零改动）；稳态首屏无表单无「必填」 <!-- aidcp-edge 50a8b23 旧 renderer-smoke 20 条设置回归零改动全过 -->
- [x] 5.2 `populateEnvs` 增自动选中：恰好 1 个环境且分身 ID 为空 → 自动选中并明示；多环境不代选、已有值不覆盖 <!-- aidcp-edge 50a8b23 加一道「核心未在运行」闸（运行中绝不偷改配置），delta spec 已同步补该措辞 -->
- [x] 5.3 待配置态：首屏醒目主动步骤条（点击开抽屉），替代灰 notice；登录引导同步升级为主动步骤（检测到登录自动前进） <!-- aidcp-edge 50a8b23 登录检测自动前进沿用既有 cookie 轮询（checkLoginAndStart），文案与样式升级 -->

## 6. 回归与收口

- [x] 6.1 `cd ../aidcp-edge && npm test && npm run typecheck`（含新增 ui-events / ui-logic 单测；FAB 三态与设置既有行为回归） <!-- worktree 内 490/490 全量 + 11/11 acceptance + typecheck 干净（2026-07-03，分支 50a8b23） -->
- [x] 6.2 mac 端到端冒烟：启动 → 待配置引导 → 抽屉配置 → 登录 → 活动流滚动 → 暂停/恢复 → 模拟发布候审卡（喂日志行） <!-- 2026-07-03 用 worktree 本地演示假核心（gitignored dist/main.js，按剧本打日志、零真实副作用）真机驱动全链路：标题带/在场感 shimmer/循环 chip/活动流/今日小结/发布候审卡（含结构化 [ui-event] pending→approved→published 流转）均如 v3 设计呈现且进程全程无崩溃（首帧截图存档，后续帧被用户前台窗口遮挡未截）；抽屉交互/暂停恢复/五状态断言由 companion-ui jsdom 冒烟 13 条覆盖。注意：本机存量旧实例会占单实例锁，冒烟前先清（见 memory edge-companion-ui-rollout） -->
- [x] 6.3 electron-builder 双平台打包，win-unpacked 验 titleBarOverlay 观感与窗控 <!-- 2026-07-03 worktree 内双平台产物齐：mac dmg+zip×双架构（AIDCP-0.2.0*）+ win NSIS（AIDCP Setup 0.2.0.exe，signAndEditExecutable:false 使 mac 交叉构建免 wine）；asar 核验新界面五文件与新窗框代码均打入。win titleBarOverlay 实际观感需 Windows 真机，已挂 docs/real-machine-acceptance-backlog.md 簇 7；打包配置零改动（renderer/**、*.cjs 通配自动覆盖新文件） -->
- [ ] 6.4 结构化 `[ui-event]` 发射点（发布链路内）标记串行：待 `publish-edge-command-runtime` 收口后按需补插（或由其顺手带上），本 change 不触碰发布文件
- [ ] 6.5 `openspec validate edge-companion-ui --strict` → 合回 master + 部署分发 → archive <!-- 2026-07-03 已合回：rebase 到 master 44d56ad 后 493/493+typecheck+acceptance 全绿，ff 合并推送（master 9ef116e）；双平台安装包产物在 worktree dist-electron/（AIDCP-0.2.0*.dmg/zip + AIDCP Setup 0.2.0.exe）。archive 待 6.4（[ui-event] 发射点，等 publish-edge-command-runtime 收口）与分发落定后执行 -->
