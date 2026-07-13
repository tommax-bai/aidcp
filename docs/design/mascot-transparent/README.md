# 吉祥物透明图状态映射

这组图来自同一张 4x2 行为设定图，顺序按从左到右、从上到下读取。UI 集成时建议优先使用 `ui-512/` 下的统一 512x512 透明 PNG；原始裁切图保留在当前目录，适合需要更紧凑包围盒的场景。

## 位置与状态

| 状态 ID | 图片位置 | 文件 | 含义 | 推荐使用场景 |
| --- | --- | --- | --- | --- |
| `welcome` | 第 1 行第 1 个，左上 | `ui-512/mascot-welcome-512.png` | 欢迎、引导、主动打招呼 | 新手引导、空状态首次进入、功能入口提示 |
| `thinking` | 第 1 行第 2 个，上排偏左 | `ui-512/mascot-thinking-512.png` | 思考中、分析中、正在理解任务 | AI 正在生成方案、读取上下文、等待模型推理 |
| `task_execution` | 第 1 行第 3 个，上排偏右 | `ui-512/mascot-task-execution-512.png` | 执行动作、点击确认、开始处理 | 自动化任务启动、执行按钮反馈、命令已下发 |
| `reminder` | 第 1 行第 4 个，右上 | `ui-512/mascot-reminder-512.png` | 温和提醒、需要注意、轻量通知 | 表单未完成、配置缺失、低风险提醒、待办提示 |
| `celebration` | 第 2 行第 1 个，左下 | `ui-512/mascot-celebration-512.png` | 成功、完成、正向反馈 | 任务完成、保存成功、发布成功、里程碑达成 |
| `risk_warning` | 第 2 行第 2 个，下排偏左 | `ui-512/mascot-risk-warning-512.png` | 风险提示、防护、拦截确认 | 风控提示、需要二次确认、权限/安全相关提示 |
| `error_apology` | 第 2 行第 3 个，下排偏右 | `ui-512/mascot-error-apology-512.png` | 出错、抱歉、需要修复 | 请求失败、任务异常、系统暂不可用、可恢复错误 |
| `monitoring` | 第 2 行第 4 个，右下 | `ui-512/mascot-monitoring-512.png` | 监控中、值守中、观察面板 | 后台运行、连接状态、日志/指标监控、长任务等待 |

## 选择建议

- 普通提示优先用 `welcome` 或 `reminder`，避免过度使用警告图。
- 模型仍在处理但没有具体进度时，用 `thinking`；已经开始执行外部动作时，用 `task_execution`。
- 成功闭环只用 `celebration`，不要用欢迎图替代完成态。
- 涉及账号、安全、权限、风控、不可逆动作前确认时，用 `risk_warning`。
- 已经失败且需要用户重新操作、重试或联系支持时，用 `error_apology`。
- 长时间后台运行、连接保持、巡检和值守场景，用 `monitoring`。

## 短期动画 Demo

短期动效预览入口：

- `animation-demo.html`：本地 HTML 预览页，展示挥手、眨眼、转头、点击按钮。
- `animation/manifest.json`：动画动作与图层映射，供开发接入时读取。
- `animation/animation-preview.gif`：GIF 预览，便于快速评审动效方向。

这版是“完整静态 PNG + 局部叠层 + CSS 动画”的快速方案。它适合先验证 UI 氛围和动效节奏；如果后续要产品级质量，需要重新生成真正分层原画，或进入 Rive/Lottie 动画工作流。

## 分层动画 V2 原型

`animation-rig-v2-demo.html` 使用重新生成的独立身体与翅膀图层。挥手图层不包含头部、脸部或身体像素，因此旋转时不会再出现旧版的头部贴图重叠。

- `animation-rig-v2/mascot-body.png`：512x512 身体与头部层。
- `animation-rig-v2/mascot-wing-left.png`：512x512 独立挥手翅膀层。
- `animation-rig-v2/manifest.json`：图层、转轴与动作触发映射。
- `animation-rig-v2/wave-preview.gif`：挥手效果预览。

这版用于验证“真正分层后是否能解决重叠”。正式产品若采用 Rive，应继续将头、眼睛、眼皮、嘴、双翼、身体和道具拆成可编辑图层，再建立状态机。

## 身体遮挡分层 V3

`animation-rig-v3-demo.html` 修复了 V2 的肩部断口。V3 不再把翅膀直接贴在身体表面，而是采用以下渲染顺序：

```text
眼皮与表情层
完整身体层
独立挥手翅膀层
```

翅膀根部是实心延伸结构，并藏在完整身体轮廓后方。`connection-angle-preview.png` 覆盖 `-16deg` 到 `16deg` 的摆动范围，用于检查极限角度是否露缝。

- `animation-rig-v3/mascot-body.png`：完整身体遮挡层。
- `animation-rig-v3/mascot-wing-left.png`：无插槽、实心根部的独立翅膀层。
- `animation-rig-v3/manifest.json`：渲染顺序、转轴和动作范围。
- `animation-rig-v3/wave-preview.gif`：最终挥手预览。

## 头部独立分层 V4

`animation-rig-v4-demo.html` 在 V3 挥手结构上增加了独立头部层。身体包含封闭完整的颈部表面，头部下方保留延伸羽毛并渲染在身体上方，因此左右转动时不会出现空洞或双重头部贴图。

```text
眼皮与表情层
独立头部层
完整身体层
独立挥手翅膀层
```

- `animation-rig-v4/mascot-torso.png`：无头但颈部完整的身体层。
- `animation-rig-v4/mascot-head.png`：带延伸颈羽的独立头部层。
- `animation-rig-v4/mascot-wing-left.png`：复用并固化到 V4 包内的挥手层。
- `animation-rig-v4/anchor-calibration.png`：头部颈底与身体颈口的锚点定位图。
- `animation-rig-v4-calibration.html`：可直接点击设置身体/头部锚点，并自动计算位移的接缝校准页。
- `animation-rig-v4/render_previews.py`：从清单锚点参数重新生成静态图和 GIF，避免预览与运行时参数漂移。
- `animation-rig-v4/head-angle-preview.png`：`-6deg` 到 `6deg` 的颈部连接检查。
- `animation-rig-v4/combined-preview.gif`：挥手与转头同时播放的组合预览。
- `animation-rig-v4/manifest.json`：渲染顺序、转轴、动作事件和测试角度。

V4 使用两个明确接点定位：头部 `neckBase=(232,366)`，身体 `neckSeat=(220,270)`。运行时先用两点差值得到头部位移 `(-12,-96)`，再对完整骨架应用 `scale=0.84`、`translateY=24` 的画布适配。不要再用整张图的透明像素重心推算头部位置。

校准页中的数值使用 512x512 逻辑画布坐标，页面渲染时转换为百分比，因此桌面和移动窗口下不会因 CSS 像素尺寸变化而漂移。分别进入“身体锚点”和“头部锚点”模式点击图片，再到“合成预览”检查结果；“复制参数”会生成可直接回填到清单的 JSON。

V4 的转头属于小角度二维旋转。正式 Rive 若需要明显的左右朝向变化，应增加头部网格变形或左右方向姿态，而不是继续扩大刚性旋转角度。

## 源图位置

源行为设定图为 4 列 2 行布局：

```text
第 1 行: welcome | thinking | task_execution | reminder
第 2 行: celebration | risk_warning | error_apology | monitoring
```

若按原始设定图像素裁切，单元格为 `384x512`：

| 状态 ID | 原始网格范围 |
| --- | --- |
| `welcome` | x: 0-383, y: 0-511 |
| `thinking` | x: 384-767, y: 0-511 |
| `task_execution` | x: 768-1151, y: 0-511 |
| `reminder` | x: 1152-1535, y: 0-511 |
| `celebration` | x: 0-383, y: 512-1023 |
| `risk_warning` | x: 384-767, y: 512-1023 |
| `error_apology` | x: 768-1151, y: 512-1023 |
| `monitoring` | x: 1152-1535, y: 512-1023 |
