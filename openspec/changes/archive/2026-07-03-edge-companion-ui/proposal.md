# edge-companion-ui — Electron 客户端从「配置工具」改版为「陪伴式 AI 同事」

## Why

现有 aidcp-edge Electron 客户端（`src/electron/`）自用没问题，但给客户装机时观感是「要你伺候的浏览器自动化配置工具」：系统默认标题栏、首页正中一整块 AdsPower 配置表单（「分身 ID 必填」）、四个恒为 0 的计数器、五个各自独立的技术徽章、主体是一段原始日志——「认真在读」和「卡死了」分不出来，客户读不出「智能服务」。设计方向已定稿（方向 A「陪伴式」+ 发布卡 v3，样例：https://claude.ai/code/artifact/86ccc89f-2ba4-4b62-b69b-387017ba4426 ），现按 v3 实装。

## What Changes

- **自定义标题栏**：隐藏系统标题栏（`titleBarStyle:'hidden'` + macOS `trafficLightPosition` / Windows `titleBarOverlay`，**绝不用 `frame:false`**），腾出的一条改为「账号身份 + 综合健康药丸」标题带，整条按风控状态染色；内容区可拖拽（`-webkit-app-region: drag`）、控件岛 no-drag。
- **配置表单请出首页**：浏览器切换 / AdsPower 探测 / 环境列表 / 分身 ID / API 地址 / API Key 整体收进齿轮「设置抽屉」；启动即自动探测 AdsPower，**恰好一个环境时自动选中**——「必填」不再出现在客户首屏。
- **原始日志 → 叙述式活动流**：一句人话一条、最新在上、相对时间戳，顶部带「刚刚更新 · N 秒前」新鲜度；原始日志收进「开发者详情」折叠。
- **呼吸式在场感行**：首屏一行会变的当前动作（CSS shimmer 微光 + 呼吸点），**由真实事件驱动**——没事件就如实展示待命 / 冷却 / 需登录，绝不用动画盖住死会话（不静默假成功红线的 UI 面）。
- **五徽章合成一条健康结论**：登录 / 云端 / 会话 / 风控 / 边缘进程五个信号合成「运行中 / 就绪 / 需要注意」一句话（标题带药丸），五个明细点开可见、内部词改人话。
- **四计数器降级为「今日小结」条**：浏览 / 点赞 / 收藏 / 评论 + 风险，从首屏门面挪到收尾横条。
- **发布等待卡（纯展示、零按钮）**：白底卡 + 四节点旅程步骤条（写好内容 → 发到飞书 → 等你确认 → 择时发布）；唯一琥珀呼吸点 = 当前节点，唯一飞书蓝 =「打开飞书 ↗」真实深链（不可用则降级纯文字）；卡上编号与飞书审批消息对暗号；五个只读状态（等你确认 / 等超 30 分钟已再提醒 / 已通过择时发布 / 已发布收进流 / 暂不发布收起）。**审批授权动作只在飞书完成，端上绝不放确认按钮**——发布卡状态需要边缘核心在发布链路（候审 / 已批 / 已发布 / 被拒）向 Electron 主进程暴露结构化事件。
- **会话 FAB 保留三态**（启动 / 暂停 / 恢复），行为不变。
- 主进程状态解析从「字符串匹配单行 lastMessage」升级为**带类型的 UI 事件**（活动流条目 / 在场感行 / 发布卡状态各有载体），现有 status 对象形状保持兼容。

## Capabilities

### New Capabilities
- `edge-companion-ui`: Electron 客户端的陪伴式主界面——自定义标题栏与健康合成、叙述式活动流与在场感（真实事件驱动、诚实待命）、今日小结、发布等待卡（纯展示零按钮、审批只在飞书、五个只读状态）。

### Modified Capabilities
- `adspower-desktop-env-picker`: 配置面板从首页常驻改为齿轮设置抽屉承载（探测 / 列表 / 手填 / 保存并入启动等既有要求不变，仅承载位变化）；新增「启动自动探测、恰好一个环境时自动选中」要求。

## Impact

- **仅 aidcp-edge**：`src/electron/main.cjs`（BrowserWindow 选项、状态/事件管线）、`src/electron/preload.cjs`（新增 UI 事件通道）、`src/electron/renderer/` 三件套（index.html / styles.css / renderer.js，全重排）；保持无构建链（纯 HTML/CSS/JS，不引框架、不引外链字体）。
- **边缘核心轻触**：发布链路需在候审 / 批准 / 发布 / 拒绝节点向 stdout 或 IPC 暴露结构化 UI 事件——**与活跃 change `publish-edge-command-runtime`（43/56）可能碰同一批发布文件，该部分标记串行、集成前先 rebase 协调**；UI 三件套当前无活跃 change 触碰。
- 不改协议 v2、不改云端、不改风控状态机；发布行为零变化（`publish-pipeline` 规格不动，端上只是只读投影）。
- 打包（electron-builder）不受影响；Windows `titleBarOverlay` 与 macOS 红绿灯内嵌均为 Electron 原生能力，无新依赖。
