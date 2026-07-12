# client-user-env-registry

## Why

后台「端用户 · 环境归属」抽屉的「待分配」池此前**只能从 `client_env_scope`（已归属表）反推**——即系统只「认识」已经分配给过某个端用户的环境。这带来两个死结：

1. **无法表达「已导入但尚未分配给任何人」的环境**：全新系统 / 尚未分配时，注册表恒为空，抽屉只提示手动登记。
2. **存量环境无从批量纳入**：运营手上有一批 AdsPower 环境（分身），想先全部进池、再自己逐个分配给客户，但没有承载「未归属环境」的地方。

根因是缺一张**独立于归属**的环境台账。cloud 全库只有 `alerts.edge_id` 偶发持久化过真实分身标识，`accounts` 表不含分身 id，故也无法从既有数据反查全集。

## What Changes

- **新增独立环境注册表 `client_environments`**（env_key 主键 + label/platform/source）：环境可以**只登记、不归属**。
- **`registerEnvironments()` 批量幂等 upsert**：供三条入池路径——① 一次性导入存量环境（`source='import'`）；② 边缘一连上云端**自动登记**（`source='auto'`，`onEdgeRegistered` 钩子，只登记不归属）；③ 后台手动登记（`source='admin'`，沿用抽屉手填兜底）。
- **`listAllEnvironments()` 改为「注册表 ∪ 归属表」并集**：未分配给任何人的环境（assigneeCount=0）也会列出——这正是「待分配」池要的。label/platform 优先取归属行最新非空值、回落注册表登记值。
- **一次性导入**：把运营提供的存量 AdsPower 环境（只取 env_key / 名字 / 平台，**绝不含 Cookie/账号密码/2FA**）灌入注册表、不归属任何端用户。
- console **零改**：环境归属抽屉的「待分配」已从该端点渲染，注册表返回未归属环境后即自动出现。

## Impact

- Affected specs: `client-customer-auth`（ADDED：独立环境注册表 + 自动登记 + 并集全集读）。
- Affected code: `aidcp-cloud/src/client-auth/client-user-store.ts`（建表 + registerEnvironments + listAllEnvironments 并集）、`aidcp-cloud/src/server.ts`（onEdgeRegistered 自动登记）。
- 安全边界不变：跨用户聚合读仍**只接内部 JWT 的 panel 端点**、绝不注入 client-auth-server（N2）；自动登记**只登记不归属**，fail-closed 归属边界不破（绝不误把环境塞给某客户）。
- 无迁移器：`client_environments` 由 `init()` 的 `CREATE TABLE IF NOT EXISTS` 自建；不碰 accounts 热点表、协议零改。
