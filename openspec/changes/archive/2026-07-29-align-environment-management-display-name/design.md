## Context

客户端外侧环境栏已经从当前 fleet 投影调用共享显示名解析器，按“人工昵称 → 平台昵称 → AdsPower / 花名册环境名 → 环境尾号”展示。环境管理浮层则从 AdsPower `user/list` 构造物理环境行，虽然能按 `profileId` 找到花名册成员，却直接把 `prof.name` 写入列表和操作提示。因此人工改名后，数据持久化正确，但同一环境在浮层内外显示不同。

本次只调整 Edge renderer 的显示投影。AdsPower profile ID、环境 key、花名册持久化、平台和代理写入协议均保持不变。

## Goals / Non-Goals

**Goals:**

- 已加入环境在环境管理列表和相关操作提示中复用客户端现有共享显示名解析器。
- 未加入或无法匹配本地环境投影的 AdsPower profile 保持可识别的原始名称回落。
- 显示名与所有修改、删除、代理和选择动作使用的稳定身份字段彻底分离。
- 用 renderer 集成测试锁定人工昵称与 AdsPower 原始名不同时的内外一致性。

**Non-Goals:**

- 不改变人工昵称的保存、同步、回滚或来源优先级。
- 不修改 AdsPower 环境本身的 `name`，也不增加 Cloud、Console、数据库或协议字段。
- 不构建或发布 Edge 安装包。

## Decisions

### 1. 在环境管理渲染边界合并身份数据

环境管理仍以 AdsPower `user/list` 作为物理环境全集。对每个 `prof.userId`，renderer 按稳定 profile ID 查找权威 fleet 环境；若 fleet 尚未形成，则回落本地花名册成员。合并后的展示候选交给现有 `resolveEnvironmentDisplayName()`，不复制一套昵称优先级。

直接使用 `member.name` 虽能修复人工昵称，但会绕过平台昵称与尾号回落，也会再次形成独立规则，因此不采用。

### 2. 未加入环境保留 AdsPower 名称回落

无法匹配 fleet 或花名册的 profile 没有客户端人工昵称或平台身份来源，列表继续按 AdsPower `name → username → profileId` 展示。这样环境管理仍能承担发现和加入物理环境的职责。

把所有 AdsPower 原始名都替换为 roster 名会让未加入环境失去名称来源，因此不采用。

### 3. 显示文本不参与动作寻址

解析结果只用于列表主昵称、批量选择可访问名称、代理弹层/预览、平台修改提示和删除确认。加入、移出、平台修改、代理保存和删除继续传递 `prof.userId` 或既有 `envKey`，不得以显示名匹配目标。

### 4. 复用现有重绘时机

环境管理每次填充列表时重新解析显示名；人工昵称提交后的既有身份锚点刷新在浮层已打开时同步重绘管理列表。失败回滚继续使用相同重绘入口，因此浮层不会保留仅存在于乐观内存中的昵称。

## Risks / Trade-offs

- [fleet 投影短暂未形成] → 使用花名册成员作为同一稳定 ID 的回落；两者都不存在时才显示 AdsPower 原始名。
- [显示名变化误导操作目标] → 所有 mutation 继续只使用 profile ID / env key，并在测试中断言载荷未改。
- [重绘影响管理列表交互态] → 只复用现有列表填充函数，不重新请求 AdsPower，也不改变批量模式和选择集合。

## Migration Plan

1. 合入 Edge renderer 与回归测试。
2. 重启运行包含该提交的开发客户端后验证；旧 renderer 不会热加载新源码。
3. 若需回滚，回退 Edge 提交即可；无数据迁移、协议迁移或服务端回滚。

## Open Questions

无。
