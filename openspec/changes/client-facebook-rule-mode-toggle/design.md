## Context

`facebook-rule-mode-cadence` 已交付账号级 `FacebookRuleModeStore`、运行时批次、后台 API 和 Console 开关。配置属于账号且由 Cloud 仲裁，Edge 只执行 Cloud 已准入的原子命令。桌面客户端已有一个成熟的 Facebook 慢启动行：renderer 只提交 `envKey`，Electron main 通过 customer-auth 发起具名环境作用域请求，Cloud 复核客户环境归属并解析账号，写后真态再回到 UI；环境内核停止不阻止纯 Cloud 配置读写。

本变更复用这条信任边界，但规则模式与慢启动的数据归属不同：慢启动配置属于环境、未绑定时也能预设；规则模式配置属于账号，因此只有环境存在唯一持久账号绑定时才能读取或写入。客户端不得把这一区别抹成默认关闭。

## Goals / Non-Goals

**Goals:**

- 在当前 Facebook 环境的慢启动行附近提供规则模式开关。
- 让客户在环境内核停止时仍可读取和修改已绑定账号的 Cloud 配置。
- 保持 `envKey → customer ownership → unique account binding → Facebook platform → existing store` 的单一权威链。
- 使用写后回读和环境隔离的 pending/error 状态，避免乐观成功、跨环境回执污染和未知即关闭。
- 清楚呈现慢启动仍优先于已开启的规则模式。

**Non-Goals:**

- 在 Edge 保存规则配置、选择生效模式、累计十条浏览或触发动作。
- 更改规则定义、阈值、动作、风险、活跃时段、绑定人设入口或慢启动仲裁。
- 把后台完整批次详情或自由规则编辑器搬进桌面客户端。
- 新增数据库迁移、边云 WebSocket 消息或安装包发布。

## Decisions

### 1. 增加客户环境作用域的专用读写端点

Cloud customer-auth 增加：

```text
GET /environments/:envKey/facebook-rule-mode
PUT /environments/:envKey/facebook-rule-mode
body: { enabled: boolean }
```

两个端点先用既有 `resolveOwnedBoundAccount` 复核客户归属并解析唯一账号，再由 Cloud 校验平台并调用现有 `FacebookRuleModeStore`。响应只返回 `envKey` 与客户端所需的规则配置投影，不返回 `accountId`、`updatedBy` 或其它租户内部字段。

选择专用 customer-auth 端点而不是复用 Panel `/api/accounts/:id/facebook-rule-mode`，因为 Panel 属于独立 JWT 域且要求客户端持有账号键；把它暴露给桌面端会破坏现有客户环境边界。

### 2. 规则模式必须绑定账号，未知绑定不得预设

读写都要求持久绑定为唯一 `accountId`。`binding_unknown`、`binding_conflict`、`binding_unavailable` 和非归属环境继续沿用既有可区分失败码。非 Facebook 返回 `unsupported_platform`。

不仿照慢启动把规则开关先写在环境表：这会创建第二份配置权威，并在后续换绑时产生迁移、覆盖或悬空语义。运营员需要先让环境完成账号绑定，再配置账号规则模式。

### 3. 客户端只增加具名 IPC，不开放任意 HTTP

preload 暴露 `getFacebookRuleMode({ envKey })` 与 `setFacebookRuleMode({ envKey, enabled })`；main 固定路径、方法和字段白名单并复用 `interactionCustomerRequest`。renderer 无法提交账号、URL、HTTP 方法、令牌或规则定义。

这与慢启动 IPC 形状一致，也保留 customer-auth token 失效、响应 `envKey` 不一致和环境切换时的既有安全处理。

### 4. 采用独立状态缓存，但复用慢启动的非乐观交互语义

renderer 为每个 `envKey` 分别维护读状态与写反馈：

- 未读取/读取中：开关不展示为关，显示读取中或未知；
- 读取成功：由 Cloud `config.enabled` 决定 checked；
- 写入中：显示用户意图但禁用控件，并标记“等待 Cloud 确认”；
- 写入成功：仅使用 PUT 写后返回的权威配置收敛；
- 写入失败：恢复最近 Cloud 真态并显示失败原因；
- 切换/删除环境：旧环境回执不得修改当前环境。

不开启本地持久化，也不从慢启动状态、Cloud 连接标签或环境运行状态推断规则开关。

### 5. UI 与慢启动相邻，但明确两个开关不是对等运行权威

规则模式使用同一脚注区的紧凑静态行，紧邻慢启动行；仅当前环境平台为 Facebook 时展示。说明文字固定表达“开启后按 Cloud 固定规则运行；慢启动开启时由慢启动优先，规则模式暂停”。

开关表达的是“配置已启用”，不是“规则此刻正在运行”。本次不新增完整有效模式/批次面板，避免把活跃时段、绑定人设、批次和风险状态压缩成一个容易误读的绿灯。

## Risks / Trade-offs

- [已开启配置可能因慢启动、活跃时段或其它入口闸而不运行] → 文案明确开关是配置事实且慢启动优先，不把 checked 渲染为“运行中”。
- [环境尚未绑定时客户不能预设规则模式] → 返回并显示 `binding_unknown`，不另造环境影子配置。
- [Cloud 配置缓存刷新或组合根缺失导致接口不可用] → 端点返回 503，客户端保持 unknown/disabled，不退化为 off。
- [环境切换期间晚到回执串到新环境] → 读写状态按 `envKey` 隔离，落回执前复核当前环境键。
- [Edge 源码完成不等于客户已可使用] → 交付报告单独说明 Cloud DEV、Edge 源码和安装包边界。

## Migration Plan

1. 先交付 Cloud customer-auth 端点与测试；它是加法接口，不改变现有规则运行或后台入口。
2. 部署 Cloud 到 DEV，验证鉴权、归属、绑定、平台和写后回读；未升级 Edge 不受影响。
3. 集成 Edge UI/IPC 源码并完成本地测试；不在本变更内构建或发布安装包。
4. 回滚时先回退 Edge UI；Cloud 新端点没有旧客户端调用可安全保留。若需回退 Cloud，规则模式现有 Console 管理和运行逻辑不受影响。

## Open Questions

无。首版只提供配置开关；完整进度和批次结果仍在现有 Console 自动化视图查看。
