# edge-companion-ui — 技术设计

## Context

现状（aidcp-edge `src/electron/`）：`main.cjs` 用默认窗框建窗（`createWindow()` 约 170–181 行未设 `titleBarStyle`），spawn 边缘核心进程并**字符串匹配其 stdout 日志行**来更新一个扁平 status 对象（`{auth, cloud, session, risk, edge, stats{views,likes,collects,comments}, lastMessage, provider, updatedAt}`），经 `status:update` IPC 推给渲染器；渲染器（`renderer.js` 470 行，纯浏览器 JS）维护 2 分钟滚动日志、五个徽章、四个计数、设置表单与三态 FAB。无构建链、无框架，这是硬约束（打包规格与 CLAUDE.md 均要求）。

设计定稿见 v3 样例（Artifact `edge-ui-redesign` v3）：陪伴式主界面 + 纯展示发布卡，审批授权只在飞书。

## Goals / Non-Goals

**Goals:**
- 客户观感从「配置工具」变为「替你干活的智能服务」：自定义标题带、叙述活动流、在场感、健康合成、今日小结、发布旅程卡。
- 所有「活着」的表达由真实事件驱动；无事件时诚实呈现待命 / 冷却 / 需登录（不静默假成功红线的 UI 面）。
- 端上零授权操作：发布卡零按钮，唯一可点的「打开飞书 ↗」是导航不是审批。
- 状态/事件管线从「单行字符串」升级为带类型事件，但对外 status 形状兼容（不破坏既有 FAB / 设置逻辑）。

**Non-Goals:**
- 不改协议 v2、云端、风控状态机、发布行为；不改飞书审批卡片本身（「编号对暗号」若需云端配合印编号，另起 change）。
- 不做托盘状态图标、深色模式、多账号总览、回放时间轴、三步首跑向导（登录/配置引导仅升级为醒目主动步骤，不做完整 wizard）。
- 不引入构建链 / 框架 / 外链字体；不做 `frame:false` 手绘窗口按钮。

## Decisions

### D1 标题栏：`titleBarStyle:'hidden'` + 平台原生控件，绝不 `frame:false`
- macOS：`titleBarStyle:'hidden'` + `trafficLightPosition:{x:14,y:16}`；Windows：`titleBarStyle:'hidden'` + `titleBarOverlay:{color,symbolColor,height:46}`。其余平台保持默认框（打包目标只有 mac/win）。
- 渲染器顶部 46px 标题带 `-webkit-app-region:drag`，齿轮 / 药丸等控件岛 `no-drag`。
- 风控状态染色：标题带背景色由渲染器按 `status.risk` 切换；Windows 侧同时 `win.setTitleBarOverlay({color…})`（仅 win32 且 overlay 存在时调用，try/catch 包裹——Electron 在未启用 overlay 时会抛错）。
- 弃选 `frame:false`：会丢原生关闭/最小化/缩放，非技术用户可能关不掉窗（对抗性评审结论）。

### D2 事件管线：结构化优先、字符串匹配兜底，双层解析收口 main 进程
- 新增纯函数模块 `src/electron/ui-events.cjs`（无 Electron 依赖，可单测）：输入一行核心日志 → 输出 `{kind:'activity'|'presence'|'publish', type, sentence, loopStage?, statsDelta?, publish?}` 或 `null`。
  - **结构化优先**：核心进程若输出 `[ui-event] {json}` 前缀行则直接解析（新契约，前缀常量两端共享）。
  - **字符串匹配兜底**：现有中文日志行（「点赞成功」「提取内容」等）经映射表转成人话句子——现网核心不改一行也能出活动流（MVP 路径）。现有 stats 递增逻辑迁入此模块，行为不变。
- `main.cjs`：status 对象**新增** `presence:{text,at}`、`publish:{state,noteTitle,code,at,extra}` 字段（形状兼容，旧字段全保留）；另开 `ui:activity` IPC 通道推活动流条目（带 ts / type / sentence），避免把无界日志塞进 status。
- 发布事件源：发布链路文件归活跃 change `publish-edge-command-runtime` 管——**本 change 只在其日志行上做字符串匹配（候审 / 已批 / 已发布 / 被拒），不改发布文件**；结构化 `[ui-event]` 发射点的插入标记为串行任务，待该 change 收口后按需补（或由对方顺手带上）。这消除了热点文件并行冲突。

### D3 发布卡状态机（渲染器侧，只读投影）
- `pending →(30min)→ reminded → approved → published | rejected`；全部由 main 推的 `status.publish` 驱动，渲染器只计时「已等 N 分钟」与超时观感升级（reminded 的「已在飞书再次提醒」文案仅在收到对应事件时展示；未收到则只琥珀化时长，不谎称已提醒）。
- `published / rejected`：卡片收起、折一条进活动流；无缩略图时用标题版卡（封面图现链路拿不到，不为 UI 造数据）。
- 编号：取审批 requestId 尾 4 位展示（`编号 ×××`）；「与飞书对暗号」依赖云端卡片也印 requestId——实装时只读核对云端飞书卡现状，若不含则**本期不显示编号**（宁缺毋假）。
- 「打开飞书 ↗」：`shell.openExternal('lark://…')` 经 preload 暴露；拉不起（无深链/未装）降级为纯文字说明。导航不是授权，符合零按钮红线。

### D4 健康合成与在场感：纯渲染器函数，可单测
- `synthesizeHealth(status)`：任一 {auth 异常, cloud 断连且会话运行, edge warning, risk restricted/frozen} → 「需要注意」；edge running && session running → 「运行中」；否则「就绪 / 已暂停」。五明细收进标题带药丸点开的浮层，内部词改人话（如「边缘进程→本机引擎」）。
- 在场感行 = 最近一条 presence/activity 事件句子 + 新鲜度走字（1s interval）；**shimmer 仅在会话运行且最近事件 < 5 分钟时开启**（看门狗 idle≈240s 会杀会话，超过即事实上不在跑），否则切换为诚实静态文案（待命 / 已暂停 / 需登录 / 等待云端）。
- 逻辑抽到 `renderer/ui-logic.js`（无 DOM 依赖的纯函数 + DOM 粘合分离），vitest 可直接 import 单测。

### D5 设置抽屉：DOM 迁移、逻辑复用
- 既有设置表单 DOM 整体移入右滑抽屉（齿轮开合，`aria-hidden` 同步），`renderer.js` 里的探测 / 列表 / 手填 / 保存并入启动逻辑**原样复用**（选择器不变）。
- 启动自动探测保留；`populateEnvs` 里新增：恰好 1 个环境且当前分身 ID 为空 → 自动 `selectProfile` 并提示「已自动选中唯一环境」。
- `auth==='config required'` 时首屏出全宽主动步骤条（点击即开抽屉），替代现有灰色 notice。

## Risks / Trade-offs

- [字符串匹配对核心日志文案脆弱] → 映射表集中一个模块 + 单测锁文案；结构化 `[ui-event]` 契约作为长期出路，映射表只是兜底。
- [发布文件与活跃 change `publish-edge-command-runtime` 撞车] → 本 change 零触碰发布文件（只消费日志行）；结构化发射点任务标记串行，集成前 rebase 协调（CLAUDE.md §7）。
- [Windows `titleBarOverlay` 行为差异（symbolColor、高度、深浅）] → 固定浅色主题 + 固定 46px；`setTitleBarOverlay` 全部 try/catch；打包后 win-unpacked 实测一次。
- [「已再提醒」可能谎报（飞书侧是否真的再提醒了端上不知道）] → 只在收到明确事件时展示该文案，否则仅时长琥珀化——宁少说不假说。
- [活动流无界增长] → 渲染器环形缓冲（上限 ~200 条），原始日志「开发者详情」沿用现有 2 分钟滚动。
- [大改 renderer 回归风险（设置/FAB 既有行为）] → 设置与 FAB 逻辑不动只挪 DOM；`ui-logic.js` / `ui-events.cjs` 纯函数化补单测；打包前跑既有 `npm test` + `typecheck` + 手动冒烟（mac 本机）。

## Migration Plan

纯客户端 UI，无数据迁移。合入 master → electron-builder 重打包分发即生效；回滚 = 回退 commit 重打包。不涉及 ECS 部署（云端零改动）。

## Open Questions

- 云端飞书审批卡是否已展示 requestId（决定「编号对暗号」本期是否可见）——实装时只读核对，不阻塞其余任务。
- 核心日志在发布候审 / 批准 / 发布 / 拒绝四节点的现有文案是否齐全稳定（决定发布卡 MVP 是否纯靠兜底匹配即可）——实装第一步坐实。
