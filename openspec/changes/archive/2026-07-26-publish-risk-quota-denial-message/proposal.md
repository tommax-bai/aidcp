## Why

委托发帖被安全闸拒绝时，当前回执只显示 `风控拒绝本次发帖（状态 normal）`，把风控威胁状态、配额档位和真正触发拒绝的配额窗口压成一句互相矛盾的提示。运营无法据此判断是平台风险、档位配置，还是分钟／小时／每日额度已用尽。

## What Changes

- 委托发帖的 governed 风控闸改用 `RiskController.explain('publish')`，在不改变放行语义的前提下保留机器可读的拒绝原因。
- 风控拒绝 attempt 原因同时携带风控状态、配额档位、配额窗口与该窗口生效上限。
- 用户可见终态提示分别展示风控状态与配额档位的中英文含义，并说明真正命中的拒绝原因；未知原因保持诚实透传，不作猜测。
- Console 与 Edge 精选内容页中由用户明确点击触发的单篇洗稿使用独立、服务端可信的操作员来源；与精确 `/publish` 一样越过发布前风控／配额闸，但仍强制发布前人审。
- 人工洗稿若最终由平台确认发布成功，仍按账号记录真实 `publish` 计数；“不受配额限制”只影响发布前放行，不得变成“不占配额”。
- 自然语言委托、通用结构化发帖、自动排期与后台自动创作仍受风控／配额闸约束；配额数字、重试和诚实终态语义不改变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `user-delegated-tasks`: 委托发帖因风控或配额闸未开始时，attempt 与终态失败回执必须明确区分风控状态、配额档位和实际拒绝原因；服务端可信的人工洗稿按操作员主动指令越过发布前配额闸，但真实发布后仍计数。

## Impact

- `aidcp-cloud/src/publish-agent/publish-scheduler.ts`：保留 governed 发布风控判定的解释信息。
- `aidcp-cloud/src/delegated-task/reason-humanize.ts`：将稳定机器码翻译为清晰的中文提示。
- `aidcp-cloud/src/delegated-task/types.ts`、`executors.ts` 与两个人工精选洗稿入口：区分可信操作员动作并透传 `operatorOverride`。
- Cloud 聚焦测试、AC-RISK / AC-PUB、安全回归与类型检查。
- 不修改 PostgreSQL 配额、Tmax 账号状态、Edge／Console 客户端代码或协议 v2。
