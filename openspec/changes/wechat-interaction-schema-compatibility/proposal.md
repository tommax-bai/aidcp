## Why

dev Cloud 在数据库 migration `0046` 尚未执行时部署了已包含 `0046` 启动预检的主干代码。预检因此关闭整个 interaction 域，连不依赖 `0046` 的互动列表、同步和评论/私信读取开关也一并返回 404；而 `0046` 因 dev/ol 共用数据库且含破坏性 DDL，当前不能直接在 dev 单边执行。

## What Changes

- 将 interaction schema 启动检查拆成“基础互动 schema 可用”和“`0046` 出站重试 schema 可用”两级。
- 基础 schema 完整但 `0046` 尚未执行时，以明确的兼容只读模式启动 interaction 域：互动读取、同步、鉴权真态和读取开关继续服务。
- 兼容模式下关闭评论回复和私信发送能力，并在所有出站入口 fail-closed，避免旧的全局幂等键唯一约束破坏安全重试语义。
- `0046` 完整落地后，Cloud 重启自动恢复现有完整读写行为；检测到半迁移/不一致 schema 时仍关闭 interaction 域并明确报错。
- 不在本变更中执行或改写 `0046`，不改变 dev/ol 共享数据库边界。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `wechat-channels-interaction`: 增加 interaction schema 分级启动、旧 schema 兼容只读和出站 fail-closed 契约。

## Impact

- Cloud: `InteractionStore.init()` schema 探测、interaction runtime 装配、启动日志及聚焦测试。
- Customer API: 基础 schema 可用时恢复互动列表与读取开关；URL、envelope 与授权边界不变。
- Edge/Console/WS protocol: 无改动。
- Database: 无 DDL、无数据写迁移；`0046` 仍是恢复安全出站重试的正式迁移。
