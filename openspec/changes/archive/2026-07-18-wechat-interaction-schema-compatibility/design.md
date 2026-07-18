## Context

Cloud 当前把 interaction 域的启动与 migration `0046` 的最终 schema 形态绑定。`0046` 会替换发送尝试表的幂等唯一约束并删除旧列；由于 dev 与 ol 共用数据库，这个迁移被明确暂停。然而包含该启动检查的 Cloud 代码已经部署到 dev，导致 `InteractionStore.init()` 失败，customer interaction API 未注册，连不依赖发送重试 schema 的列表、同步、鉴权状态和评论/私信读取开关也一并返回 404。

现有数据库仍具备 migration `0042` 以后所需的基础 interaction schema，并保持 `0046` 之前的完整形态。因此可以恢复安全的读取能力，但不能假装新的发送重试语义已经可用。

## Goals / Non-Goals

**Goals:**

- 在基础 interaction schema 完整、`0046` 尚未执行时恢复 interaction customer API 和读取能力。
- 在兼容模式下从运行时控制投影到最终发送入口双重关闭评论回复和私信发送。
- 精确识别 `0046` 已完成、尚未开始和只完成一半三种状态。
- 保持 migration `0046` 完整执行后的现有读写行为不变。

**Non-Goals:**

- 不执行、重写或绕过 migration `0046`。
- 不改变 dev/ol 共用数据库的部署边界。
- 不改变 Edge、Console、WebSocket 协议或 customer API envelope。
- 不在旧 schema 上实现一套新的重试算法。

## Decisions

### 1. 将 schema readiness 拆成基础层与发送重试层

`InteractionStore.init()` 先验证 migration `0042` 后的基础表和列，再单独检查 `0046` 的两个标志：活动发送尝试部分唯一索引存在，以及旧 `retryable` 列不存在。

- 两个标志都满足：`full`。
- 部分唯一索引不存在且旧列存在：`legacy_read_only`。
- 只满足其中一个：视为半迁移/不一致状态并拒绝启动。
- 基础层不完整：拒绝启动并报告基础 schema 缺失。

这比只检查某一个对象更严格，避免在迁移中断后以错误模式运行。

### 2. 兼容模式只恢复读取，不开放任何出站发送

在 `legacy_read_only` 模式下仍装配 store、config、workflow、inbox 和 customer API。运行时控制保持 `commentsReadEnabled`、`dmReadEnabled` 的原有投影，但把全局写能力强制视为关闭，因此 `commentsReplyEnabled` 和 `dmSendTextEnabled` 为 false。

同时，发送 orchestrator 使用强制关闭的写环境初始化。这样即使某个调用方绕过运行时控制投影，最终发送门也会在创建发送尝试之前拒绝请求。双层 fail-closed 防止旧唯一约束破坏新的安全重试语义。

### 3. 不自动修改数据库

Cloud 启动只探测 schema，不执行 DDL。`0046` 仍由数据库边界明确后的正式发布流程执行。迁移完成并重启 Cloud 后，探测结果自动变为 `full`，现有配置中的全局写开关重新生效。

### 4. 启动日志明确报告降级原因和能力边界

兼容模式必须记录 `0046` 未完成、读取已恢复、出站写入被关闭。半迁移状态继续记录为启动错误并关闭 interaction 域，避免把数据安全问题伪装为普通降级。

## Risks / Trade-offs

- **迁移前无法回复评论或发送私信。** 这是有意的安全限制；读取和开关展示恢复后，客户端会明确显示写能力不可用，而不是一直“读取中”。
- **schema 模式只在进程启动时计算。** migration `0046` 完成后需要重启 Cloud；这与现有 migration 发布流程一致。
- **旧 schema 可能还有未知漂移。** 基础 schema 检查和 `0046` 两个标志的精确组合会让未知/半迁移形态继续 fail-closed。

## Migration Plan

1. 发布兼容代码并重启 dev Cloud；不执行任何数据库迁移。
2. 验证 interaction 列表、同步、鉴权状态和读取开关 API 恢复，回复/发送能力保持关闭。
3. 待 dev/ol 数据库边界解决后，按正式流程执行 migration `0046`。
4. 重启 Cloud，验证 schema 模式为 `full`，并由既有全局写配置决定是否恢复出站能力。

回滚应用代码不会改动数据库，但会重新触发当前的 interaction 域整体关闭，因此仅作为应用级紧急回滚使用。

## Open Questions

无。
