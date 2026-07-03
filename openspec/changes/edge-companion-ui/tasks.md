# edge-companion-ui — tasks

> 全部落 `../aidcp-edge`（UI 三件套 + main.cjs + 新纯函数模块），本仓只回写进度。设计定稿：Artifact v3（https://claude.ai/code/artifact/86ccc89f-2ba4-4b62-b69b-387017ba4426 ）。红线：无构建链、零审批按钮、动效只由真实事件驱动、发布链路文件零触碰（与活跃 change `publish-edge-command-runtime` 防撞）。

## 1. aidcp-edge — 事件管线（先坐实数据面）

- [ ] 1.1 坐实现状：核心日志在发布候审 / 批准 / 已发布 / 拒绝四节点的现有文案（读 publish 相关运行时输出点，只读不改）；核对云端飞书审批卡是否展示 requestId（决定「编号」本期是否可见，宁缺毋假）
- [ ] 1.2 新建 `src/electron/ui-events.cjs` 纯函数模块：`[ui-event] {json}` 结构化行优先解析；既有中文日志行映射表兜底（活动句子 / loopStage / statsDelta / publish 状态），现有 stats 递增逻辑原样迁入
- [ ] 1.3 `main.cjs` 接入：status 新增 `presence` / `publish` 字段（旧字段全保留），新开 `ui:activity` IPC 推活动流条目；`preload.cjs` 暴露 `onActivity` 与 `openFeishu`（shell.openExternal 深链、失败返回 false）
- [ ] 1.4 vitest 单测：映射表锁文案（点赞 / 提取 / 评论 / 发布四节点）、结构化行优先、未识别行返回 null、statsDelta 与改版前计数行为一致、旧形状 status 渲染降级不炸

## 2. aidcp-edge — 窗框与标题带

- [ ] 2.1 `main.cjs` `createWindow()`：mac `titleBarStyle:'hidden'` + `trafficLightPosition`；win `titleBarStyle:'hidden'` + `titleBarOverlay{color,symbolColor,height:46}`；其余平台默认框；窗口尺寸随新布局微调
- [ ] 2.2 渲染器标题带：46px drag 区 + 控件岛 no-drag（账号名 / 健康药丸 / 齿轮）；风控状态染色（normal 平静 / warned 琥珀 / restricted·frozen 警示），win32 同步 `setTitleBarOverlay`（try/catch）
- [ ] 2.3 mac 本机冒烟：红绿灯 / 拖拽 / 控件点击互不冲突；win 打包件冒烟留待 §6

## 3. aidcp-edge — 主界面重排（renderer 三件套）

- [ ] 3.1 新建 `renderer/ui-logic.js` 纯函数：`synthesizeHealth(status)` 五路合成 +人话明细、在场感动效门（运行中且事件 <5min）、发布卡状态机（pending/reminded/approved/published/rejected + 30min 时长琥珀化）；vitest 单测
- [ ] 3.2 index.html/styles.css 按 v3 重排：在场感行（shimmer + 呼吸点 + 新鲜度走字）、循环 chip（刷 feed→选笔记→阅读→互动→返回续刷）、活动流（环形 ≤200 条）、「开发者详情」折叠收原始日志、「今日小结」条；`prefers-reduced-motion` 全局关动效
- [ ] 3.3 五徽章收进健康药丸点开的明细浮层（内部词改人话：边缘进程→本机引擎等）；旧 hero / stats / grid / log DOM 移除
- [ ] 3.4 无事件诚实态：待命 / 已暂停 / 需登录 / 等待云端静态文案；shimmer 门断言（停止态绝不动效）

## 4. aidcp-edge — 发布等待卡（纯展示）

- [ ] 4.1 发布卡组件：白底卡 + 四节点旅程步骤条 + 唯一琥珀呼吸点 + 脚注「通过/驳回在飞书」+「打开飞书 ↗」（深链失败降级纯文字）；零按钮断言（卡内不存在 button 元素，除非纯导航链接）
- [ ] 4.2 五状态接线：候审 / 超 30min（未证实不谎称「已再提醒」）/ 已通过择时（呼吸点转平静色 + 无需操作文案）/ 已发布收进流并计入小结 / 拒绝收起表述为「暂不发布、内容留档」
- [ ] 4.3 编号展示：仅当 1.1 核对确认飞书卡含 requestId 时展示尾 4 位，否则本期不显示

## 5. aidcp-edge — 设置抽屉

- [ ] 5.1 设置表单 DOM 整体迁入右滑抽屉（齿轮开合、选择器不变、探测/列表/手填/保存并入启动逻辑零改动）；稳态首屏无表单无「必填」
- [ ] 5.2 `populateEnvs` 增自动选中：恰好 1 个环境且分身 ID 为空 → 自动选中并明示；多环境不代选、已有值不覆盖
- [ ] 5.3 待配置态：首屏醒目主动步骤条（点击开抽屉），替代灰 notice；登录引导同步升级为主动步骤（检测到登录自动前进）

## 6. 回归与收口

- [ ] 6.1 `cd ../aidcp-edge && npm test && npm run typecheck`（含新增 ui-events / ui-logic 单测；FAB 三态与设置既有行为回归）
- [ ] 6.2 mac 端到端冒烟：启动 → 待配置引导 → 抽屉配置 → 登录 → 活动流滚动 → 暂停/恢复 → 模拟发布候审卡（喂日志行）
- [ ] 6.3 electron-builder 双平台打包，win-unpacked 验 titleBarOverlay 观感与窗控
- [ ] 6.4 结构化 `[ui-event]` 发射点（发布链路内）标记串行：待 `publish-edge-command-runtime` 收口后按需补插（或由其顺手带上），本 change 不触碰发布文件
- [ ] 6.5 `openspec validate edge-companion-ui --strict` → commit/push edge + 本仓进度回写 → archive
