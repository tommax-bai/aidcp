## Context

Electron renderer 已在 `:root` 定义视频号平台身份色 `--plat-wechat`，左侧环境状态栏头像和顶栏身份区都复用该变量。环境选择列表的 `.env-plat` 默认规则代表小红书红色，只有 Facebook 具备覆盖规则；renderer 已正确生成 `plat-wechat_channels` 类名，但 CSS 没有消费它，导致截图中的视频号标签显示成红字和粉底。

## Goals / Non-Goals

**Goals:**

- 让“添加环境”列表的视频号平台标签与状态栏保持同一绿色身份语义。
- 继续让蓝色只表达交互选择，让绿色平台标签不改变列表选中边框或运行状态信号。
- 用静态契约测试锁定类名与色变量的连接。

**Non-Goals:**

- 不改变视频号平台识别、环境选择、花名册或启动逻辑。
- 不调整小红书、Facebook、状态色或全局主题色。
- 不构建或发布桌面安装包。

## Decisions

在现有 `.env-plat.plat-facebook` 规则旁增加 `.env-plat.plat-wechat_channels`，文字颜色直接引用 `var(--plat-wechat)`，背景使用与当前视频号绿色相配的浅绿色表面。这样沿用 renderer 已输出的规范平台类名，不增加 JS 分支，也避免复制一套新的身份色常量。

回归测试读取当前 renderer 与 CSS 源码，分别确认 renderer 仍生成平台类名、CSS 存在视频号选择器且引用 `--plat-wechat`。相比截图测试，这个窄契约能直接覆盖本次缺失点，且不引入 Electron 图形运行依赖。

## Risks / Trade-offs

- **[浅绿背景在不同屏幕上对比不足]** → 使用深绿色文字与非常浅的绿色背景，保留现有粗体和字号；CSS 契约同时锁定文字使用统一平台变量。
- **[未来平台 ID 改名导致样式失联]** → 测试同时锁定 renderer 的 `plat-${displayPlat}` 生成与 `plat-wechat_channels` CSS 选择器。
