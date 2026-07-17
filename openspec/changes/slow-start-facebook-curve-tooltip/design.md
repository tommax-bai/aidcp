## Context

`account-level-slow-start` 已在 Edge「今日进展」卡内提供账号级开关，renderer 按云端 `dailyUsage.slowStart` 三态投影展示真态。云端同时支持 Facebook 与小红书慢启动，但当前产品入口只应面向 Facebook。现有投影只带当前日 `dayQuotas`，未携带完整 7 天计划；Facebook 曲线在 cloud `FB_COLD_START_PLANS` 中是固定常量。

本 change 只调整 Edge 展示，不修改开关写入、配额裁剪、云端投影或协议。用户看到的表格必须与现行 Facebook 曲线上界一致，同时必须保留“曲线是上限、7 天后走账号档位”的边界。

## Goals / Non-Goals

**Goals:**

- 只有当前明确选中的 Facebook 环境展示慢启动整行。
- 用用户指定的短文案替换现有说明。
- 提供鼠标与键盘均可访问的问号提示，展示 7 天 Facebook 曲线上限表。
- 保留既有未知态、提交中、失败回滚、断连与毕业态的诚实语义。

**Non-Goals:**

- 不停用云端的小红书慢启动数据或历史状态。
- 不修改 Facebook 曲线、账号档位或 `min(曲线, 档位)` 的实际计算。
- 不扩展 `ui.snapshot` / PUT 回执协议，也不由客户端推算当前天数或当天实际执行量。

## Decisions

### 1. 在 renderer 最外层按当前选中环境的平台隐藏整行

`renderSlowStart` 在读取慢启动投影前先检查当前环境的归一化平台；只有 `facebook` 继续渲染，其余平台统一隐藏并清除 pending/stale 样式。平台判断复用已有 `normPlatform` 和 fleet 当前选中环境，不从账号文案或云端 eligibility 反推。

选择隐藏整个行，而不是在小红书上保留禁用开关，因为产品要求是“不展示开关”，且残留说明、徽章或帮助入口仍会暗示小红书支持该能力。

### 2. 使用原生可聚焦触发器承载非交互表格

问号用 `button type=button`，通过 CSS 的 `:hover` / `:focus-visible` / `:focus-within` 展开帮助面板。面板是静态 `table`，触发器带 `aria-label`，无需新增状态机、点击监听或依赖；点击问号仍在慢启动行内阻止冒泡，不改变「今日进展」收展状态。

### 3. 表格复制 Facebook 固定曲线的每日确定性上界

表格列只展示 Facebook 有实际语义的六项：浏览、点赞、评论、关注、发布、加组。数值逐格复制 cloud `FB_COLD_START_PLANS` 的区间上界，因为 `coldStartDailyCap` 正是用这些上界裁剪每日计划。小红书专属或全程为零的 collect / comment_like / dm_reply 不展示，避免无意义宽表。

不扩协议的替代方案代价是曲线变更时需要同步两仓。当前 change 以聚焦 DOM 测试锁住 7×6 表格，并在源码注释指向云端常量；未来云端改曲线时，测试和注释构成显式同步提醒。扩协议传完整曲线会把纯展示改动升级为 protocol v2 跨仓迁移，本次不采用。

### 4. 文案与数值边界分层

常驻文案严格改为“开启后头 7 天按曲线逐日放开量，7天后按账号档位运行。”帮助面板标题使用“Facebook 慢启动曲线限额”，避免把曲线上界冒充当天实际执行量。既有 badge 仍在 `binding=false` 时说明当前档位已更严，保留运行真相。

## Risks / Trade-offs

- [云端曲线更新后客户端表格漂移] → 表格代码注释绑定 `FB_COLD_START_PLANS`，测试逐格锁定现行曲线；修改云端曲线时必须同步 Edge。
- [窄窗中 7×6 表格溢出] → 帮助面板限制最大宽度并允许横向滚动，向卡片内侧定位。
- [仅 hover 导致键盘用户不可见] → 触发器使用原生 button，并在 `focus-visible` / `focus-within` 时同样展示。
- [平台切换残留上一环境样式] → 非 Facebook 分支每次渲染都主动隐藏整行并清除 pending/stale/aria-busy。
