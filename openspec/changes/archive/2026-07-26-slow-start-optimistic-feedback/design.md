## Context

`account-level-slow-start` 已在 Edge 的“今日节奏”卡中提供开关。当前浏览器会先切换 checkbox，但 renderer 只用一个布尔 `slowStartPending` 阻止旧快照覆盖，并在 PUT 完成前继续展示旧徽章和旧说明。对 Facebook 环境常见的慢网络路径，这个变化过于微弱，用户会把等待理解成点击无效。

现有云端 PUT 成功回执已经包含 `slowStart` 写后真态与 `dayQuotas` 生效值，因此客户端不需要自行计算天数或计划量。失败回执也已有可展示的 `message` / `error`。

## Goals / Non-Goals

**Goals:**

- 点击后同一帧进入醒目的提交中状态，明确区分“正在开启”与“正在关闭”。
- 在途期间不被旧 `ui.snapshot` 拨回，也不允许重复提交。
- 成功后立即用云端写后真态和当日计划值对齐 UI；失败后恢复点击前权威态并保留可见原因。
- 环境切换时，某一环境的提交反馈不得串到另一环境。

**Non-Goals:**

- 不修改慢启动配额、天数算法、云端路由、鉴权或协议。
- 不把临时态写入主进程或持久化；客户端退出后仍以云端快照为准。
- 不新增通用 toast / notification 基建。

## Decisions

### D1：用 env-scoped mutation state 表达临时态

将 renderer 的单一布尔改为带 `envKey`、目标 `enabled` 和阶段的临时状态。`renderSlowStart` 只有在当前环境匹配时才展示“正在开启…”或“正在关闭…”，并给整行加 `is-pending` / `aria-busy`。

这比直接改 `dailyUsage.slowStart` 更诚实：权威快照仍保持原值，临时态只表达网络请求进行中。替代方案“先把 state 改成 active/off”会把未确认的本地愿望冒充云端事实，拒绝采用。

### D2：成功回执作为第一次权威 reconcile

PUT 200 后读取已有回执中的 `data.slowStart` 和 `data.dayQuotas`，只更新发起请求的环境状态，再走正常 renderer。客户端不得自行推算 `day`、`binding` 或配额。

这样成功后不必再等待最长 60 秒的下一次快照，同时仍只有云端一个事实源。若回执缺少预期字段，则结束 pending、保留当前快照，等待后续权威推送，不编造成功细节。

### D3：失败回滚由权威快照重绘，错误作为独立反馈保留

请求失败、异常或超时后清除 pending，再从未被篡改的环境快照重绘开关和徽章；错误文本放在独立的 env-scoped feedback 中，避免被 `renderSlowStart` 同一轮覆盖掉。下一次同环境提交开始时清除旧错误。

不采用“手工 `checked = !enabled` 后立即丢弃错误”的方式，因为它既依赖 DOM 当前值，也会在 finally 重绘时吞掉失败原因。

## Risks / Trade-offs

- **[旧快照在成功回执后到达，短暂覆盖回执]** → 现有推送缺少版本号；提交中继续屏蔽旧快照，PUT 成功后以回执先对齐。随后快照理论上来自同一云端写后状态；若未来存在乱序窗口，应另加版本协议，当前 change 不伪造版本。
- **[用户在请求中切换环境]** → 临时态和错误都按 envKey 归属，成功只更新原环境的缓存状态，绝不把旧环境结果画到新环境。
- **[响应极慢]** → 主进程 fetch 的现有超时/失败语义不变；客户端持续显示“等待云端确认”，避免沉默等待。

## Migration Plan

1. 先以 jsdom 锁定 pending、成功 reconcile、失败回滚和环境隔离。
2. 仅发布 Edge 源码变更；cloud 不部署，协议不变。
3. 回滚时恢复 renderer 与样式提交即可，云端数据与接口无需迁移。

## Open Questions

无。
